#!/usr/bin/env ruby
# frozen_string_literal: true

require 'bundler/setup'
Bundler.require
require 'rss/maker'
require 'json'
require 'tmpdir'

DATA = {
  client_id: 'MOBrBDS8blbauoSck0ZfDbtuzpyT',
  client_secret: 'lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj',
  get_secure_url: 1
}.freeze
HEADERS = {
  'App-OS' => 'ios',
  'App-OS-Version' => '9.3.3',
  'App-Version' => '6.0.9'
}.freeze
PIXIV_URI = 'https://www.pixiv.net/bookmark_new_illust.php'

Dotenv.load("#{__dir__}/../.env")
@client = OAuth2::Client.new(DATA[:client_id], DATA[:client_secret],
  site: 'https://app-api.pixiv.net', headers: HEADERS)

def get(uri_s)
  if @token.expired?
    # 2019/06/30現在、pixivのoauthのレスポンスが標準的ではないため、必ず
    # OAuth2::Errorが発生する
    client = OAuth2::Client.new(DATA[:client_id], DATA[:client_secret],
      site: 'https://oauth.secure.pixiv.net', headers: HEADERS)
    client.options[:token_url] = '/auth/token'
    token = OAuth2::AccessToken.from_hash(client, @token.to_hash)
    begin
      token.refresh!
    rescue OAuth2::Error => e
      token = e.response.parsed['response']
      raise e if token.nil?

      @token = OAuth2::AccessToken.from_hash(@client, token)
    end
    File.write(@token_file, @token.to_hash.to_json)
  end

  @token.get(uri_s)
end

def login(username, password)
  @token_file = File.join(Dir.tmpdir, "pixiv.#{username}.token")
  if @token.nil? && File.exist?(@token_file)
    @token = OAuth2::AccessToken.from_hash(@client,
      JSON.parse(File.read(@token_file)))
    return @token
  end

  client = OAuth2::Client.new(DATA[:client_id], DATA[:client_secret],
    site: 'https://oauth.secure.pixiv.net', headers: HEADERS)
  client.options[:token_url] = '/auth/token'
  begin
    # 2019/06/30現在、pixivのoauthのレスポンスが標準的ではないため、必ず
    # OAuth2::Errorが発生する
    client.password.get_token(username, password, get_secure_url: 1)
  rescue OAuth2::Error => e
    token = e.response.parsed['response']
    raise e if token.nil?

    @token = OAuth2::AccessToken.from_hash(@client, token)
  end
  File.write(@token_file, @token.to_hash.to_json)
  @token
end

def illust_follow
  get('/v2/illust/follow?restrict=public')
end

def main
  login(ENV['PIXIV_USER'], ENV['PIXIV_PASS'])
  data = illust_follow.parsed

  data['illusts'].each do |j|
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
rescue StandardError => e
  data = {}
  data[:id] = Time.now.strftime('%Y%m%d%H%M%S')
  data[:title] = e.to_s
  data[:content] = e.to_s
  e.backtrace.each do |trace|
    data[:content] += '<br>'
    data[:content] += trace
  end
  data[:date] = Time.now

  @feed_items << data
end

feed = RSS::Maker.make('atom') do |maker|
  maker.channel.about = 'pixiv_feed'
  maker.channel.title = 'pixivフォロー新着作品'
  maker.channel.description = 'pixivフォロー新着作品のフィードです'
  maker.channel.link = PIXIV_URI
  maker.channel.updated = Time.now
  maker.channel.author = 'sanadan'
  @feed_items.each do |d|
    item = maker.items.new_item
    item.id = d[:id] if d[:id]
    item.link = d[:link] if d[:link]
    item.title = d[:title]
    item.date = d[:date]
    item.content.content = d[:content]
    item.content.type = 'html'
  end
end

puts 'Content-Type: application/atom+xml; charset=UTF-8'
puts
puts feed

