---
layout: page
title: Gnuplot cheatsheet
date: 2022-12-06
excerpt: ""
permalink: /blog/ticks_and_trips/gnuplot.html
---

# Gnuplot

Good manual:
[hirophysics](https://hirophysics.com/gnuplot/gnuplot01.html)

### Data

Data format is TSV

### Commands

Plot 1st and 3rd columns:

```
plot "file.tsv" u 1:3 w linespoints
```

<br>

Don't hide the window instantly when running a script:
end the file with:

```
pause mouse close
```

[StackOverflow](https://unix.stackexchange.com/questions/257679/how-to-keep-gnuplot-x11-graph-window-open-until-manually-closed)

Alternatively run gnuplot with `--persist` argument

<br>

Use dates on X axis:

```
set timefmt "%Y-%m-%d"
set xdata time
```

<br>

Grid:

```
set grid
```

Tics:

```
set ytics 100
```

<br>

Process input with a script:

```
plot "< tail +20 input.tsv"
#       ^ shell command here
```

<br>

Example:

```
set timefmt "%Y-%m-%d"
set xdata time
set autoscale y
set tics
set grid #  mxtics mytics

set ytics 100

plot "< tail +20 data.tsv" u 1:3 w linespoints smooth bezier
pause mouse close

```
