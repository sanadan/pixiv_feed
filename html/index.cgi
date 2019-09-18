#!/usr/bin/env ruby
# frozen_string_literal: true

require 'bundler/setup'
Bundler.require
require 'rss/maker'
require 'json'
require 'net/http'
require 'tmpdir'
require 'time'
require 'digest/md5'

DATA = {
  client_id: 'MOBrBDS8blbauoSck0ZfDbtuzpyT',
  client_secret: 'lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj',
  get_secure_url: 1
}.freeze
HEADER = {
  'User-Agent' => 'PixivAndroidApp/5.0.64 (Android 6.0)'
}.freeze
PIXIV_URI = 'https://www.pixiv.net/bookmark_new_illust.php'
HASH_SECRET = '28c1fdd170a5204386cb1313c7077b34f83e4aaf4aa829ce78c231e05b0bae2c'

Dotenv.load("#{__dir__}/../.env")

def get(uri_s)
  header = HEADER.dup
  header['Authorization'] = "Bearer #{@token['access_token']}"
  uri = URI.parse(uri_s)
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = uri.scheme == 'https'
  response = http.get(uri.request_uri, header)
  if response.code == '400'
    if @retry
      @retry = false
      File.delete(@token_file)
      return response.body
    end

    @retry = true
    json_s = login
    # File.write('retry.log', json_s)
    return json_s if JSON.parse(json_s)['has_error']

    return get(uri_s)
  end
  response.body
end

def login(username = nil, password = nil) # rubocop:disable Metrics/PerceivedComplexity, Metrics/MethodLength, Metrics/CyclomaticComplexity, Metrics/LineLength
  if username
    @username = username
  elsif @username.nil?
    return '{"has_error":true,"errors":{"system":{"message":"-1:ユーザー名を設定してください","code":-1}}}'
  end

  @token_file = File.join(Dir.tmpdir, "pixiv.#{@username}.token")
  if @token.nil? && File.exist?(@token_file)
    @token = JSON.parse(File.read(@token_file))
    return @token.to_json
  end

  data = DATA.dup
  if @token
    data[:grant_type] = 'refresh_token'
    data[:refresh_token] = @token['refresh_token']
  elsif password
    data[:grant_type] = 'password'
    data[:username] = @username
    data[:password] = password
  else
    return '{"has_error":true,"errors":{"system":{"message":"-2:パスワードを設定してください","code":-2}}}'
  end

  uri = URI.parse('https://oauth.secure.pixiv.net/auth/token')
  http = Net::HTTP.new(uri.host, uri.port)
  http.use_ssl = uri.scheme == 'https'
  post_data = data.map { |k, v| "#{k}=#{v}" }.join('&')
  local_time = Time.now.iso8601
  header = HEADER.dup
  header['X-Client-Time'] = local_time
  header['X-Client-Hash'] = Digest::MD5.hexdigest(local_time + HASH_SECRET)
  response = http.post(uri.request_uri, post_data, header)
  if response.code == '200'
    @token = JSON.parse(response.body)['response']
    File.write(@token_file, @token.to_json)
  end
  response.body
end

def illust_follow
  get('https://app-api.pixiv.net/v2/illust/follow?restrict=public')
end

def main
  json = JSON.parse(login(ENV['PIXIV_USER'], ENV['PIXIV_PASS']))
  #pp json
  raise json['errors']['system']['message'] if json['has_error']

  json = JSON.parse(illust_follow)
  #pp json
  raise json['errors']['system']['message'] if json['has_error']
  raise json.to_json if json['illusts'].nil?

  json['illusts'].each do |j|
    #pp j
    item = {}
    item[:link] = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=#{j['id']}"
    item[:title] = j['title']
    thumbnail = ENV['THUMBNAIL'] ? "<img src=\"https://embed.pixiv.net/decorate.php?illust_id=#{j['id']}\">" : ''
    item[:content] = "<a href=\"#{item[:link]}\">#{thumbnail}</a> #{j['user']['name']}"
    item[:date] = j['create_date']

    @feed_items << item
  end
end

# entry
@feed_items = []
begin
  main
rescue
  data = {}
  data[ :id ] = Time.now.strftime( '%Y%m%d%H%M%S' )
  data[ :title ] = $!.to_s
  data[ :content ] = $!.to_s
  $!.backtrace.each do |trace|
    data[ :content ] += '<br>'
    data[ :content ] += trace
  end
  data[ :date ] = Time.now

  @feed_items << data
end

feed = RSS::Maker.make( 'atom' ) do |maker|
	maker.channel.about = 'pixiv_feed'
	maker.channel.title = 'pixivフォロー新着作品'
 	maker.channel.description = 'pixivフォロー新着作品のフィードです'
  # 2019/09/18 Feedeenからpixivのfaviconを取得しようとするとエラーになるの
  # で、linkを設定しないようにした
 	# maker.channel.link = PIXIV_URI
 	maker.channel.updated = Time.now
 	maker.channel.author = 'sanadan'
	@feed_items.each do |d|
    item = maker.items.new_item
	  item.id = d[ :id ] if d[ :id ]
    item.link = d[ :link ] if d[ :link ]
    item.title = d[ :title ]
	  item.date = d[ :date ]
	  item.content.content = d[ :content ]
	  item.content.type = 'html'
  end
end

print "Content-Type: application/atom+xml; charset=UTF-8\n"
print "\n"
print feed

