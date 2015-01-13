# pixiv_feed
Generate atom feed from pixiv follow new illusts.

## install
For Ubuntu 14.04

    cd /var/www
    git clone https://github.com/sanadan/pixiv_feed.git
    cd pixiv_feed
    bundle install
    ./index.cgi
    sudo ln -s /var/www/pixiv_feed/pixiv_feed.conf /etc/apache2/conf-enabled
    sudo service apache2 restart

## Licence
MIT

## Copyright
Copyright (C) 2015 sanadan <jecy00@gmail.com>
