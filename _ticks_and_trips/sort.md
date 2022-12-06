---
layout: page
title: Faster sort
date: 2022-12-06
excerpt: |
  TLDR:<br>
  <pre>alias sort="LC_ALL=C \sort"</pre>
permalink: /ticks_and_trips/sort.html
---

# Faster sort

The standard (GNU, BSD, etc.) `sort` is really slow by default because of
some fancy string handling, i18n or something I usually don't care about. 
If you don't care about it either and just want your sort to be reasonably
fast (like 15x faster!) then set environment variable `LC_ALL=C`.

You can even make it the default by adding this to your `~/.bashrc`:
```
alias sort="LC_ALL=C \sort"
```

Here are some results:
```
▸ time cat test_data.txt | sort > /dev/null
real	0m35.810s
user	0m35.622s
sys	0m0.216s

▸ alias sort="LC_ALL=C \sort"
▸ time cat test_data.txt | sort > /dev/null
real	0m2.357s
user	0m2.248s
sys	0m0.164s
```

It even speeds up the random sort too!

#### Links
 - [https://unix.stackexchange.com/questions/564303/sort-lc-all-c-vs-lc-all-c-utf8](https://unix.stackexchange.com/questions/564303/sort-lc-all-c-vs-lc-all-c-utf8)
 - [https://unix.stackexchange.com/questions/67680/what-would-break-if-the-c-locale-was-utf-8-instead-of-ascii](https://unix.stackexchange.com/questions/67680/what-would-break-if-the-c-locale-was-utf-8-instead-of-ascii)
 - [https://unix.stackexchange.com/questions/346228/besides-the-non-c-locale-what-else-is-messing-up-my-sort](https://unix.stackexchange.com/questions/346228/besides-the-non-c-locale-what-else-is-messing-up-my-sort)
 - [https://infoheap.com/linux-sort-lc_all-sorting-rules/](https://infoheap.com/linux-sort-lc_all-sorting-rules/)

