#!/bin/sh

set -e

jekyll build

scp _srv_deploy.sh root@unmb.pw:/usr/local/bin/static_unmb_pw_deploy.sh
rsync -avz --delete _site/ unmb.pw:_site/

ssh root@unmb.pw sh /usr/local/bin/static_unmb_pw_deploy.sh
