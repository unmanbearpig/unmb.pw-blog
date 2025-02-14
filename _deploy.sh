#!/bin/sh

set -e

# bundle exec jekyll build
# 
# scp _srv_deploy.sh root@unmb.pw:/usr/local/bin/static_unmb_pw_deploy.sh
# rsync -avz --delete _site/ unmb.pw:_site/
# 
# echo "sshing to the server..."
# ssh root@unmb.pw sh /usr/local/bin/static_unmb_pw_deploy.sh
# echo "ssh completed"
