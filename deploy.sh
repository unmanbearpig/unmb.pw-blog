#!/usr/bin/env bash

set -euo pipefail

remote_host="${REMOTE_HOST:-unmb.pw}"
remote_path="${REMOTE_PATH:-/var/www/htdocs/unmb.pw/blog}"
remote_owner="${REMOTE_OWNER:-www:daemon}"

# Avoid mirroring local 600/700 modes into the web root.
rsync \
  --archive \
  --verbose \
  --compress \
  --delete \
  --no-owner \
  --no-group \
  --no-perms \
  --chmod=Du=rwx,Dg=rx,Do=rx,Fu=rw,Fg=r,Fo=r \
  _site/ "${remote_host}:${remote_path}/"

ssh "${remote_host}" \
  "doas chown -R ${remote_owner} '${remote_path}' && doas find '${remote_path}' -type d -exec chmod 755 {} + && doas find '${remote_path}' -type f -exec chmod 644 {} +"
