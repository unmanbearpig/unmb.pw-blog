#!/bin/sh

set -e

cd /var/www/htdocs/

if [[ ! -d prev_unmb.pw ]]; then
	mkdir prev_unmb.pw
fi

rm -rf prev_unmb.pw/*
mv unmb.pw/* prev_unmb.pw

cp -r /home/user/_site/* unmb.pw
chown -R www unmb.pw
