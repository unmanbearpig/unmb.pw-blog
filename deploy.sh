#!/bin/sh

set -e

jekyll build

scp srv_deploy.sh root@unmb.pw:/usr/local/bin/web_deploy.sh
rsync -avz --delete _site/ unmb.pw:_site/

ssh root@unmb.pw sh /usr/local/bin/web_deploy.sh
