---
layout: post
title:  "KeyFortress - speedrunning to my first Firefox extension"
date:   2024-03-12 17:02:13 +0400
categories: misc
excerpt: "How little time can I spend to make a useful extension? - about 3hr"
---

If you're accustomed to using emacs-like (or mac-like) hotkeys in linux, such as ctrl-a, ctrl-e,
ctrl-a, ctrl-b, ctrl-k, etc., you might have noticed that Ctrl-k creates a
new chat in ChatGPT instead of deleting all characters from the cursor untill
the end of the line. I use it all the time, so it's really annoying.

The solution? Let's ask ChatGPT!

> can you write a minimalist firefox extension
that disables hotkeys that some websites override?

Which got me some `manifest.json` and `content.js`.
Having never written a browser extension that helped a lot, now I have something to start with.
I needed to ask things like how to test that extension, etc. but that was
easy enough.

It didn't work though. The code I got from the LLM was:
```js
// content.js
document.addEventListener("keydown", function(event) {
  // List of hotkeys you want to disable
  var blockedKeys = ["F5", "Ctrl+R", "Ctrl+U", "Ctrl+Shift+I"];
  
  // Check if the pressed key combination is in the blockedKeys list
  if (blockedKeys.includes(event.key) || blockedKeys.includes(getKeyCombination(event))) {
    event.preventDefault();
    event.stopPropagation();
  }
});

// Function to get the key combination
function getKeyCombination(event) {
  var keyCombination = "";
  if (event.ctrlKey) keyCombination += "Ctrl+";
  if (event.altKey) keyCombination += "Alt+";
  if (event.shiftKey) keyCombination += "Shift+";
  keyCombination += event.key;
  return keyCombination;
}
```

It seems like `preventDefault` and `stopPropagation` don't achieve what I intended.
Now I just have to figure out what to replace it with.

Shouldn't be hard, let's find some code that does it.
A quick search on addons.mozilla.org provided me with a bunch of extensions. Upon expecting the source code of the first one, I found:
```js
    event.stopImmediatePropagation();
```

And it worked! It was easier than I expected.

Next, I needed to add some configuration options so that I wouldn't have
to rebuild the extension every time I wanted to add more websites and shortcuts.
I didn't want to disable all overrides on all websites, as many of them are
actually useful. Creating a proper UI seemed like a lot of work, so I opted
for the simplest solution: a JSON config!

Chatting with ChatGPT provided me with prototypes for
options.html and options.js. However, they didn't work.
After some debugging, I discovered that you can't have callbacks when
blocking event propagation, which actually made the extension better,
in my opinion.
Instead of checking the configuration on every key event, we can load it on
page load and save it to a `window` variable.
Then, we can simply check the window variable. This method is likely faster,
as we don't need to use the browser.sync API very often.

![simplest possible config - the only UI this addon has](/blog_assets/key_fortress_config.png)

That might look terrible, but it works! And I don't need anything else, do you?
Having the config just as a text file, it's easy to copy and paste all of it, or parts of it,
it's easy to share it with other people or copy to your other browser, easy to back it up, etc. I actually love that solution! Why reinvent the wheel?

The rest of the process involved cleaning up some debug statements,
drawing an icon in 5 minutes, asking ChatGPT to come up with a name,
and submitting it to addons.mozilla.org.

We'll see if Mozilla accepts it. I'll update this blog post when I hear back from them.

The entire process took about 3 hours, including submitting to
addons.mozilla.org, drawing the icon, debugging, etc.
Actually, most of it was the boring stuff, like figuring out how to make an
icon and what else I needed to submit.

Surprisingly, it was easy overall. I didn't expect it to take only 3 hours,
considering I had almost zero knowledge of how browser extensions are made!

I'm not sure if anyone's going to use it, but hey,
why not spend an extra hour and publish it?
