---
layout: page
title: Video Pipeline
date: 2025-02-16
excerpt: |
  TLDR:<br>
  DaVinci Resolve for editing, ffmpeg for transcoding, Backblaze B2 for hosting
permalink: /blog/ticks_and_trips/video.html
---

# Video Editing and Hosting Pipeline

After trying many different tools for video editing and hosting, here's what 
worked best for me as a traveler who needs to process and upload videos on slow 
connections.
Still work in progress, so far it's like 10% of what I want, but it's a start.

## Editing Tools

### DaVinci Resolve - ⭐️⭐️⭐️⭐️⭐️
The best of what I used. Pretty easy to use, exports good quality if you set 
bitrate higher than its "High" setting. Can cut, transform, do all kinds of 
stuff.

### QuickTime - ⭐️⭐️⭐️⭐️⭐️
In case you didn't know - quicktime is not just a video player but a very simple 
video editor. It's perfect for making simple cuts. Starts up quickly, exports quickly.
I'd say that if you only need to to trim a video, this is the way to go.

### Videoproc Vlogger - ⭐️⭐️⭐️
I'm not sure it's possible to make it export video in high quality.
Some basic editing features. Pretty usable if QuickTime is not enough.
But also lacks features of DaVinci Resolve, so I don't see a reason to use it.

### Others (Not Recommended)
- iMovie - I could'nt figure out how to use it haha.
- OpenShot - Extremely slow and weird, couldn't figure out how to use it. Tried 
  launching it while writing this, and it just couldn't start.
- Shotcut - Hard to use and couldn't find the transform feature (like zoom in, 
  rotate the frame, etc)

## Transcoding

ffmpeg is the only thing that worked, the video editors suck at it big time.

I tried handbrake, but couldn't tune the settings to be any good at all.
Just ask ChatGPT to give you the ffmpeg flags, and tune them for your preferences.

## Video Hosting Options

### YouTube
Hard to use and super weird and low quality, but free. Hard to upload on slow 
connection, which is a problem while travelling. Relatively low quality 4k video, 
very compressed.

### Cloud Storage
- Amazon S3 - expensive and hard-ish to use. Still easier than YouTube, haha
- Wasabi - doesn't have public URLs, so can't use for web.
- Backblaze B2 - seems ok so far

## Web Video Player
DIY WebComponent. Super simple so far, but it's work in progress.

## Scripts

- Pick the poster frame from the video
It gets the frames every 5 seconds, and opens a folder with them so you can pick 
the best one by entering the number. Not precise, but fast, no need to mess with 
complicated tools. 

```bash
#!/bin/bash

VIDEO_FILE="$1"

# Ensure input file exists
if [[ ! -f "$VIDEO_FILE" ]]; then
  echo "Usage: $0 <video-file>"
  exit 1
fi

# Generate a unique directory based on the video filename (sanitized)
BASE_NAME=$(basename "$VIDEO_FILE" | sed 's/\.[^.]*$//' | sed 's/[^a-zA-Z0-9]/_/g')
FRAME_DIR="/tmp/video_frames_${BASE_NAME}_$RANDOM"
OUTPUT_FILE="${BASE_NAME}.jpg"

# Create temp directory for frames
mkdir -p "$FRAME_DIR"

# Extract frames every 5 seconds, naming them numerically
ffmpeg -i "$VIDEO_FILE" -vf "fps=1/5" -q:v 2 "$FRAME_DIR/%d.jpg" -hide_banner -loglevel error

# Open the folder so the user can manually browse and pick a frame
open "$FRAME_DIR"

# Ask user to enter the number of the selected frame
echo "Enter the number of the selected frame (without extension):"
read -r FRAME_NUMBER

SELECTED_FRAME="$FRAME_DIR/$FRAME_NUMBER.jpg"

# Ensure the selected frame exists
if [[ -f "$SELECTED_FRAME" ]]; then
  gm convert "$SELECTED_FRAME" -resize 3840x2160! "$OUTPUT_FILE"
  echo "Selected frame saved as $OUTPUT_FILE (4K resolution)"
else
  echo "Invalid selection. No file found."
fi

# Cleanup extracted frames
rm -rf "$FRAME_DIR"


```

- Transcode video to multiple resolutions

```bash
# ask chatgpt for the code haha
```

- Upload video to B2
```bash
# ask chatgpt for the code haha
```
