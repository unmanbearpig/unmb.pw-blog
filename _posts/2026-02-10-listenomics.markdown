---
layout: post
title:  "listenomics - Last.fm charts"
date:   2026-02-10 12:00:00 +0000
categories: project
excerpt: "listenomics.unmb.pw"
---

I made a small Last.fm stats site: [listenomics.unmb.pw](https://listenomics.unmb.pw/).

You can open a user page like
[listenomics.unmb.pw/user/unmanbearpig/charts](https://listenomics.unmb.pw/user/unmanbearpig/charts)
and get charts for listens over time, artist listens, track listens, unique tracks,
new artists, and a few ratio/age metrics.

Behind the scenes it stores scrobbles in SQLite and fetches updates in background
workers, with incremental fetches instead of re-downloading everything.

_UI is shit now, will improve_

## Things that lastfm doesn't have

- How many unique artists / tracks you listened within a month / week
  It shows if you're listening to the same song over and over, or a lot of songs each one time, or somewhere in between.
- How many new artists / tracks you find in each month / week
- Track age: Do you mainly listen to things you found years ago or stuff you just found today?
