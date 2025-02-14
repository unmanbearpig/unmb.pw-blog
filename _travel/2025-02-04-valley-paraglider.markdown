---
layout: post
title:  "Valley Paraglider"
date:   2025-02-14 17:02:13 +0400
categories: travel
excerpt: Cool surprise on my ride - spotted a paraglider soaring through the valley!
permalink: /travel/2025-02-14-valley-paraglider.html
---

<div class="video-container">
  <video id="paraglider_vid" controls loading="lazy" preload="none" 
    poster="https://f005.backblazeb2.com/file/motovids/valley_paraglider_1400.jpg">
    <source src="https://f005.backblazeb2.com/file/motovids/valley_paraglider_1400_2160p_crf23.mp4" 
      type="video/mp4" size="2160" media="(min-width: 3920px)">
    <source src="https://f005.backblazeb2.com/file/motovids/valley_paraglider_1400_1440p_crf25.mp4" 
      type="video/mp4" size="1440" media="(min-width: 2640px)">
    <source src="https://f005.backblazeb2.com/file/motovids/valley_paraglider_1400_1080p_crf26.mp4" 
      type="video/mp4" size="1080" media="(min-width: 2000px)">
    <source src="https://f005.backblazeb2.com/file/motovids/valley_paraglider_1400_720p_crf27.mp4" 
      type="video/mp4" size="720">
    Your browser does not support the video tag.
  </video>
</div>

<div class="quality-selector">
  <select id="quality_select" onchange="changeQuality()">
    <option value="720">720p</option>
    <option value="1080">1080p</option>
    <option value="1440">1440p</option>
    <option value="2160">2160p</option>
  </select>
</div>

<script>
function changeQuality() {
  const vid = document.getElementById('paraglider_vid');
  const sel = document.getElementById('quality_select');
  const curr_time = vid.currentTime;
  const was_playing = !vid.paused;
  
  const quality = sel.value;
  const sources = {
    '720':  'valley_paraglider_1400_720p_crf27.mp4',
    '1080': 'valley_paraglider_1400_1080p_crf26.mp4',
    '1440': 'valley_paraglider_1400_1440p_crf25.mp4',
    '2160': 'valley_paraglider_1400_2160p_crf23.mp4'
  };
  
  vid.src = 'https://f005.backblazeb2.com/file/motovids/' + sources[quality];
  vid.currentTime = curr_time;
  if (was_playing) vid.play();
}
</script>

<style>
.quality-selector {
  margin-top: 10px;
  text-align: right;
}
#quality_select {
  padding: 5px;
  border-radius: 4px;
}
</style>
