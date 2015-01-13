#!/usr/bin/env ruby

PIXIV_PIT = 'www.pixiv.net'
PIXIV_URI = 'http://www.pixiv.net/bookmark_new_illust.php'

require 'bundler/setup'
Bundler.require
require 'rss/maker'
require 'pp'

def main
  config = Pitcgi.get( PIXIV_PIT, :require => {
    "id" => "Mail address",
    "password" => "Password",
    "thumbnail" => true
  })

  pixiv = Pixiv.client( config[ 'id' ], config[ 'password' ] )
  page = pixiv.agent.get( PIXIV_URI )

  page.search( '.image-item' ).each do |data|
    item = {}
    link = data.at( '.work' )[ 'href' ]
    item[ :link ] = URI.join( 'http://www.pixiv.net', link ).to_s
    link2 = URI.join( 'http://touch.pixiv.net', link ).to_s
    thumbnail = ""
#pp config[ 'thumbnail' ]
    if config[ 'thumbnail' ] then
      thumbnail = data.at( '._thumbnail' )[ 'src' ]
      thumbnail.sub!( /150x150/, '128x128' )
      thumbnail = "<img src=\"#{thumbnail}\" border=\"0\">"
    end
    item[ :content ] = "<a href=\"#{link2}\">mobile</a><br><a href=\"#{item[ :link ]}\">#{thumbnail}</a>"
    item[ :title ] = data.at( '.title' ).text
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

