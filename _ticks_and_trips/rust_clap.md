---
layout: page
title: Rust Clap Cheatsheet
date: 2022-12-14
excerpt: ""
permalink: /ticks_and_trips/rust_clap.html
---

# [Clap](https://docs.rs/clap/latest/clap/) with "derive" feature

I keep forgetting the syntax and the documentation is large and complicated,
so here is a cheatsheet for things I use most.

#### Add clap
```sh
cargo add clap --features derive
```

#### Simple example

```rust
// We need it only to be able to call Args::parse()
use clap::Parser;

#[derive(Debug, Clone, clap::ValueEnum)]
enum ColorMode {
    /// Everything's black, can't see anything
    NoColor,

    /// Now the text is white
    DarkMode,

    /// Just random colors
    Rainbows,
}

#[derive(Debug, clap::Subcommand)]
enum Command {
    /// Self explanatory
    ReticulateSplines,

    /// Prints hello world
    PrintHelloWorld,
}

#[derive(Debug, Clone, clap::ValueEnum)]
enum Thing {
    This,
    That,
}

#[derive(Debug, clap::Parser)]
struct Args {
    /// This is documentation for color_mode argument
    #[arg(long, value_enum, default_value_t = ColorMode::NoColor)]
    color_mode: ColorMode,

    /// List of values
    #[arg(short, long, value_delimiter = ',')]
    things: Vec<Thing>,

    /// Unintuitively (in my opinion) this would be the last positional argument
    #[command(subcommand)]
    command: Option<Command>,

    /// This is 0 or more positional arguments
    #[arg()]
    files: Vec<String>
}

fn main() {
    // Prints the parsed arguments
    println!("{:?}", Args::parse());
}
```

#### Help output

```
Usage: claptest [OPTIONS] [FILES]... [COMMAND]

Commands:
  reticulate-splines
          Self explanatory
  print-hello-world
          Prints hello world
  help
          Print this message or the help of the given subcommand(s)

Arguments:
  [FILES]...
          This is 0 or more positional arguments

Options:
      --color-mode <COLOR_MODE>
          This is documentation for color_mode argument

          [default: no-color]

          Possible values:
          - no-color:  Everything's black, can't see anything
          - dark-mode: Now the text is white
          - rainbows:  Just random colors

  -t, --things <THINGS>
          List of values

          [possible values: this, that]

  -h, --help
          Print help information (use `-h` for a summary)
```

It doesn't say it in help, but things would allow you to specify multiple items, 
for example:

```
> claptest --things that,this
Args { color_mode: NoColor, things: [That, This], command: None, files: [] }
```
