---
layout: default
title: Writing
description: Engineering, product, photography and travel notes by Ivan Fedyunin.
permalink: /blog/
theme: editorial
body_class: writing-page
---

<header class="writing-page__intro">
  <p class="page-kicker">Writing</p>
  <h1>Things I built, investigated or needed to understand.</h1>
  <p>Engineering notes are primary. Photography, music and travel remain part of the archive.</p>
</header>

<ol class="archive-list">
  {%- assign default_content_lang = site.default_content_lang | default: "en" -%}
  {%- for post in site.posts -%}
    {%- assign post_lang = post.lang | default: default_content_lang -%}
    {%- if post.translation_key and post_lang != default_content_lang -%}
      {%- continue -%}
    {%- endif -%}
    <li>
      <time datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%Y.%m.%d" }}</time>
      <div>
        <h2><a href="{{ post.url | relative_url }}">{{ post.title | escape }}</a></h2>
        {%- if post.excerpt -%}<p>{{ post.excerpt | strip_html | normalize_whitespace }}</p>{%- endif -%}
      </div>
    </li>
  {%- endfor -%}
</ol>

<section class="archive-sections">
  <h2>Other sections</h2>
  <div>
    <a href="{{ "/blog/ticks_and_trips/" | relative_url }}"><strong>Ticks and Trips</strong><span>Short technical notes</span></a>
    <a href="{{ "/blog/travel/" | relative_url }}"><strong>Travel</strong><span>Photographs and field notes</span></a>
    <a href="{{ "/blog/links/" | relative_url }}"><strong>Links</strong><span>Useful things from the internet</span></a>
    <a href="{{ "/blog/feed.xml" | relative_url }}"><strong>RSS</strong><span>Follow new writing</span></a>
  </div>
</section>
