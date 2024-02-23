#!/bin/sh

set -e

echo "running on the server..."

cd /var/www/htdocs/unmb.pw

if [[ ! -d prev_blog ]]; then
	mkdir prev_blog
fi

# this is dangerous so I'm using rsync without `--delete` instead

echo "copying to prod directory..."
rm -rf prev_blog/*
mv blog/* prev_blog

cp -r /home/user/_site/* blog


echo "setting permissions..."
chown -R www blog

echo "done running on the server"
