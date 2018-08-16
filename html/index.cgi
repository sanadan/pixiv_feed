#!/usr/bin/env ruby

PIXIV_PIT = 'www.pixiv.net'
PIXIV_URI = 'http://www.pixiv.net/bookmark_new_illust.php'

require 'bundler/setup'
Bundler.require
require 'rss/maker'
#require 'pp'
require 'json'

def main
  config = Pitcgi.get( PIXIV_PIT, :require => {
    "id" => "pixiv ID or mail address",
    "password" => "Password",
    "thumbnail" => 'true or false'
  })

  pixiv = Pixiv.client( config[ 'id' ], config[ 'password' ] )
  page = pixiv.agent.get( PIXIV_URI )

  json = JSON.load( CGI.unescapeHTML( page.body.scan( /data-items=\"(.+?)\"/ )[ 0 ][ 0 ] ) )
  json.each do |j|
    #pp j
    item = {}
    item[ :link ] = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + j[ 'illustId' ]
    item[ :title ] = j[ 'illustTitle' ]
    thumbnail = config[ 'thumbnail' ] ? "<img src=\"https://embed.pixiv.net/decorate.php?illust_id=#{j[ 'illustId' ]}\" border=\"0\">" : ''
    item[ :content ] = "<a href=\"#{item[ :link ]}\">#{thumbnail}</a>"
    item[ :date ] = Time.now

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
	@feed_items.each do |data|
    item = maker.items.new_item
	  item.id = data[ :id ] if data[ :id ]
    item.link = data[ :link ] if data[ :link ]
    item.title = data[ :title ]
	  item.date = data[ :date ]
	  item.content.content = data[ :content ]
	  item.content.type = 'html'
  end
end

print "Content-Type: application/atom+xml; charset=UTF-8\n"
print "\n"
print feed

