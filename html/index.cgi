#!/usr/bin/env ruby

PIXIV_URI = 'https://www.pixiv.net/bookmark_new_illust.php'

require 'bundler/setup'
Bundler.require
require 'rss/maker'
require 'json'

Dotenv.load

def main
  json = JSON.load(`#{__dir__}/../pixiv_new_works.js #{ENV['PIXIV_USER']} #{ENV['PIXIV_PASS']}`)
  #pp json
  raise json['errors']['system']['message'] if json['has_error']

  json['illusts'].each do |j|
    #pp j
    item = {}
    item[:link] = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id=#{j['id']}"
    item[:title] = j['title']
    thumbnail = ENV['THUMBNAIL'] ? "<img src=\"#{j['image_urls']['medium']}\">" : ''
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
 	maker.channel.link = PIXIV_URI
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

