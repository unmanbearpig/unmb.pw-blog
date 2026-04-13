Source code for my blog at [unmb.pw](https://unmb.pw/)

## Bilingual posts

Posts can have multiple language versions while only showing one version in the
homepage post list.

How it works:

- Each language version is a separate file in `_posts/`
- Related versions share the same `translation_key`
- Section index pages only show entries whose `lang` matches
  `default_content_lang` in `_config.yml`
- Individual post and collection item pages show a language switcher linking to
  the sibling translations

Example:

```yaml
---
layout: post
title: "My article"
date: 2026-04-13 12:00:00 +0000
lang: en
language_name: English
translation_key: my-article
excerpt: Short summary
---
```

```yaml
---
layout: post
title: "Mi articulo"
date: 2026-04-13 12:00:00 +0000
lang: es
language_name: Espanol
translation_key: my-article
excerpt: Resumen corto
---
```

Notes:

- `lang` should be a short code like `en` or `es`
- `language_name` is the label shown in the switcher
- If a post has no `translation_key`, it behaves like a normal single-language
  post
