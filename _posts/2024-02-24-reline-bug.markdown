---
published: false
layout: post
title:  "Reline bug"
date:   2024-01-24 17:02:13 +0400
categories: misc
excerpt: "reline regression debugging and fixing"
---

1. Got error
2. Is it because of the missing term database?
   Test without tmux - it works. Test with random TERM - it crashes again.
- Error:

```
/Users/ivan/.local/share/mise/installs/ruby/3.2.3/lib/ruby/3.2.0/reline/terminfo.rb:108:in `setupterm': The terminfo database could not be found. (Reline::Terminfo::TerminfoError)
	from /Users/ivan/.local/share/mise/installs/ruby/3.2.3/lib/ruby/3.2.0/reline/ansi.rb:21:in `<class:ANSI>'
	from /Users/ivan/.local/share/mise/installs/ruby/3.2.3/lib/ruby/3.2.0/reline/ansi.rb:6:in `<top (required)>'
	from <internal:/Users/ivan/.local/share/mise/installs/ruby/3.2.3/lib/ruby/3.2.0/rubygems/core_ext/kernel_require.rb>:86:in `require'
	from <internal:/Users/ivan/.local/share/mise/installs/ruby/3.2.3/lib/ruby/3.2.0/rubygems/core_ext/kernel_require.rb>:86:in `require'
	from /Users/ivan/.local/share/mise/installs/ruby/3.2.3/lib/ruby/3.2.0/reline.rb:594:in `<top (required)>'
	from <internal:/Users/ivan/.local/share/mise/installs/ruby/3.2.3/lib/ruby/3.2.0/rubygems/core_ext/kernel_require.rb>:86:in `require'
	from <internal:/Users/ivan/.local/share/mise/installs/ruby/3.2.3/lib/ruby/3.2.0/rubygems/core_ext/kernel_require.rb>:86:in `require'
	from debug.rb:4:in `<main>'
```

3. What's reline
4. How does it work? imports libs, does some ffi
5. What does the readme says
6. If it's compatible with readline, let's test it. And readline works, unless it's 3.3.0 which replaced readline with reline?
7. Why doesn't readline fails? Does it revert to some default?
- Test in Linux - there is no bug. Interesting!
- Which line makes it crash? Quick way to find out - prints
```ruby
puts " -> start" # printed
require 'reline'
puts " -> required" # not printed
```

- How does readline work?

ruby/3.2.0/readline.rb

```ruby
begin
  require 'readline.so'
rescue LoadError
  require 'reline' unless defined? Reline
  Object.send(:remove_const, :Readline) if Object.const_defined?(:Readline)
  Readline = Reline
end
```
- Let's confirm that it's the correct file and that it actually imports the `readline.so`

```ruby
puts "imported readline.rb"
begin
  require 'readline.so'
  puts "imported readline.so"
rescue LoadError
  puts "error importing readilne.so"
  require 'reline' unless defined? Reline
  Object.send(:remove_const, :Readline) if Object.const_defined?(:Readline)
  Readline = Reline
end
puts "end of readline.rb"
```

Both macos and Linux:
```
TERM=blahterm ruby test_readline.rb
imported readline.rb
imported readline.so
end of readline.rb
This is echo program by Readline.
```

- 2 paths forward:
  1. Compare reline and readline and see what readline does instead of crashing
  2. Compare reline in mac and reline in linux and see why reline in linux doesn't crash and potentially make it do the same on mac

- I'm thinking the second path should be easier

- How FFI works and is that `readline.so` a file bundled with ruby or is it the GNU Readline?
- Ruby documentation says there's readline.c https://ruby-doc.org/stdlib-2.5.1/libdoc/readline/rdoc/Readline.html but not in my installed ruby. Let's check the sources.

- The reline error
```ruby
  def self.setupterm(term, fildes)
    errret_int = Fiddle::Pointer.malloc(Fiddle::SIZEOF_INT)
    ret = @setupterm.(term, fildes, errret_int)
    errret = errret_int[0, Fiddle::SIZEOF_INT].unpack1('i')
    case ret
    when 0 # OK
      0
    when -1 # ERR
      case errret
      when 1
        raise TerminfoError.new('The terminal is hardcopy, cannot be used for curses applications.')
      when 0
        raise TerminfoError.new('The terminal could not be found, or that it is a generic type, having too little information for curses applications to run.')
      when -1
        # This is the error
        raise TerminfoError.new('The terminfo database could not be found.')
      else # unknown
        -1
      end
    else # unknown
      -2
    end
  end
```

- What happens in linux then?

```ruby
  def self.setupterm(term, fildes)
    puts "-> setupterm #{term}, #{fildes}"
    errret_int = Fiddle::Pointer.malloc(Fiddle::SIZEOF_INT)
    puts "   errret_int = #{errret_int}"
    ret = @setupterm.(term, fildes, errret_int)
    errret = errret_int[0, Fiddle::SIZEOF_INT].unpack1('i')
    case ret
```

And it's never called! What the hell?

Let's go back to mac stack trace and add prints in the caller functions

- Reline::ANSI terminfo disabled on linux. Let's investigate where the `enabled?`
  function gets the value it returns...

- Back in terminfo.rb, patch 2 Terminfo.enabled? methods
  And indeed, curses_dl is falsy, let's keep going down this path, why is it falsy?

- It's not LoadError in the beginning of the file...

- Anyway, we know that some library is not loaded in linux and we're skipping the problematic brach. Let's try to make it load that thing?
  So, what's `fiddle`? FFI wrapper, got it.

Here we're deciding which library we want to load based on the platform.
```ruby
    case RUBY_PLATFORM
    when /mingw/, /mswin/
      # aren't supported
      []
    when /cygwin/
      %w[cygncursesw-10.dll cygncurses-10.dll]
    when /darwin/
      %w[libncursesw.dylib libcursesw.dylib libncurses.dylib libcurses.dylib]
    else
      %w[libncursesw.so libcursesw.so libncurses.so libcurses.so]
    end
```
There is no way I don't have libcurses installed in Linux though.

- Why can't it find it? I can probably debug this issue, or I can try a different linux distro.
  It's possible it's another bug, who knows. But let's try Debian first.

- And I get the same thing. Hmm...
  Does it ever work in linux?

- Again 2 paths forward
  1. Maybe it just never loads a linux library? If so then which features does it break? What does it matter? Try to find other bugs that this thing could've caused.
  2. Force it to load the library somehow

Second path seems easier, but we might look into the first later as well.

I was going to dig into `fiddle` documentation, but on the second thought, let's just try giving it the full path and see what happens.
 => same thing, it just cannot load the file for some reason.

Let's get a better error out of it then.

-> "Invalid ELF header" 

What the hell?

And it's indeed just a text file. What???

Let's find others then.

```sh
find / -name 'libncursesw.so*' | xargs file
```

```
/lib64/libncursesw.so.6.4: ELF 64-bit LSB shared object, x86-64, version 1 (SYSV), dynamically linked, with debug_info, not stripped
/lib64/libncursesw.so.6:   symbolic link to libncursesw.so.6.4
/usr/lib64/libncursesw.so: ASCII text
```

- Add /lib64/libncursesw.so.6 to our list

And we get 

```
unmbp -> curses_dl
unmbp reline terminfo enabled 1 = true
unmbp Reline ansi terminfo enabled
unmbp -> setupterm term=0 ; fildes=2
unmbp    errret_int=
/home/unmanbearpig/.rubies/ruby-3.2.3/lib/ruby/3.2.0/reline/terminfo.rb:121:in `setupterm': The terminal could not be found, or that it is a generic type, having too little information for curses applications to run. (Reline::Terminfo::TerminfoError)
        from /home/unmanbearpig/.rubies/ruby-3.2.3/lib/ruby/3.2.0/reline/ansi.rb:22:in `<class:ANSI>'
        from /home/unmanbearpig/.rubies/ruby-3.2.3/lib/ruby/3.2.0/reline/ansi.rb:6:in `<top (required)>'
        from <internal:/home/unmanbearpig/.rubies/ruby-3.2.3/lib/ruby/3.2.0/rubygems/core_ext/kernel_require.rb>:86:in `require'
        from <internal:/home/unmanbearpig/.rubies/ruby-3.2.3/lib/ruby/3.2.0/rubygems/core_ext/kernel_require.rb>:86:in `require'
        from /home/unmanbearpig/.rubies/ruby-3.2.3/lib/ruby/3.2.0/reline.rb:594:in `<top (required)>'
        from <internal:/home/unmanbearpig/.rubies/ruby-3.2.3/lib/ruby/3.2.0/rubygems/core_ext/kernel_require.rb>:86:in `require'
        from <internal:/home/unmanbearpig/.rubies/ruby-3.2.3/lib/ruby/3.2.0/rubygems/core_ext/kernel_require.rb>:86:in `require'
        from test_reline.rb:3:in `<main>'
```

- Aha! A different error, but still an error nonetheless!
  To me it seems like if it works without loading libncursesw.so, then it should work with it, right?

- What do we do from now? Ideally we should make sure it's compatible with `readline` library.
  But first, we can play with it a little bit.

  How about removing the exception?

  And it just works! I guess we need to dig into history to find out why it was added in the first place?

```
commit 74a7ffaa2fb0a48f5c790ac917489130fcf2bbde
Author: aycabta <aycabta@gmail.com>
Date:   Tue May 18 21:46:16 2021 +0900

    Add terminfo support
```
And it's a single large commit, oh well.
So we don't know why we need to crash here.
Let's google that new error first. But if we don't find anything then I guess
let's compare reline with readline and actually learn what they do.

Looks like the error was copy and pasted from curses function `setupterm` that the ruby code is actually calling.

man 3 setupterm:

> Initially, setupterm should be called. Note that setupterm is automatically called by initscr and newterm. This defines the set of terminal-dependent variables [listed in terminfo(5)]

bug in Reline: https://github.com/ruby/reline/issues/543

So curses wants us to call `setupterm` before doing anything else, but what happens if it fails, but we keep trying to use `curses` anyway?
And what should we do to maintain compatibility with `readline`?
I assume we definitely shouldn't fail because
 1. readline doesn't
 2. reline doesn't fail when there is no curses library!

 Let's try reline tests...

We need to first change the TERM that's being set in the helper and second is
remove the raise so it doesn't crash on `require`

And we get a bunch of 
```
Omission: can't find capability: knp [test_knp(Reline::ANSI::TestWithTerminfo)]
```

with different capabilities.

Does readline have tests?

