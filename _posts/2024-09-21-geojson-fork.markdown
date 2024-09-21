---
layout: post
title:  "geojson.io fork - no tap-drag zoom"
date:   2024-09-21 17:02:13 +0400
categories: project
excerpt: "geojson.unmb.pw"
---

Tap-drag zoom is very annoying when trying to edit polygons on a tablet.
Got rid of it. Feel free to use it at [geojson.unmb.pw](https://geojson.unmb.pw/)

Here is the line that fixed it:

```js
context.map.touchZoomRotate['_tapDragZoom']['_enabled'] = false;
```

That's it, folks!

