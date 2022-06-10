---
layout: post
title:  "Overclocking mouse by patching Linux kernel"
date:   2022-06-09 17:02:13 +0400
categories: misc
---

So I have this old Logitech MX518 mouse that I love. I haven't played any
games in a while, but recently found Xonotic and got quite decent at it.
Me being a bit obsessed with latency and Xonotic being very fast game,
I've decided to improve the input latency as much as possible.

I remember that years and years ago I was able to increase the poll rate of
this exact mouse to 500 hz (default rate is 125 hz) in Windows.
Theoretically it should reduce the mouse latency and improve its smoothness
and accuracy when moving very fast.

I've tried looking for software for linux that would do that, but couldn't
find anything that works.
So I've decided to dig into it a bit more.

## Measure

We can't optimize anything unless we measure it.

In Linux each input device is a file in `/dev/input/`, for example by mouse
is at `/dev/input/by-id/usb-Logitech_USB-PS_2_Optical_Mouse-event-mouse`.

We can just read the data from it like so:

`> sudo cat /dev/input/by-id/usb-Logitech_USB-PS_2_Optical_Mouse-event-mouse | xxd`

```
00000000: 4e1a a362 0000 0000 5ea5 0400 0000 0000  N..b....^.......
00000010: 0200 0100 ffff ffff 4e1a a362 0000 0000  ........N..b....
00000020: 5ea5 0400 0000 0000 0000 0000 0000 0000  ^...............
00000030: 4e1a a362 0000 0000 d8bc 0400 0000 0000  N..b............
00000040: 0200 0100 ffff ffff 4e1a a362 0000 0000  ........N..b....
00000050: d8bc 0400 0000 0000 0000 0000 0000 0000  ................
00000060: 4e1a a362 0000 0000 33cc 0400 0000 0000  N..b....3.......
00000070: 0200 0000 0100 0000 4e1a a362 0000 0000  ........N..b....
00000080: 33cc 0400 0000 0000 0200 0100 ffff ffff  3...............
00000090: 4e1a a362 0000 0000 33cc 0400 0000 0000  N..b....3.......
000000a0: 0000 0000 0000 0000 4e1a a362 0000 0000  ........N..b....
000000b0: d6db 0400 0000 0000 0200 0100 ffff ffff  ................
```
As we move the mouse we get a bunch of data on the screen.

So we can measure the delays between the data batches and hopefully get
the actual mouse rate.

I've written a simple Rust program that performs a crude measurement
[here (unmanbearpig/hid_rate)][hid_rate]

here is a snippet from it:

```rust
loop {
    last_time = time::Instant::now();
    let bytes_read = file.read(&mut buf)?;
    let elapsed = last_time.elapsed();
    let secs = elapsed.as_secs_f64();
    let hz = 1.0 / secs;

    println!("{:14} ns, {:>14.3} us, {:10.5} hz, {:4} bytes read",
             elapsed.as_nanos(), secs * 1000_000.0, hz, bytes_read);
}
```

Here we just read some data in a loop and measure how each iteration took.
From the duration it's trivial to calculate the rate, so it's easier to read.

Let's run it on the device file of our mouse and move the mouse a bit.

`> hid_rate /dev/input/by-id/usb-Logitech_USB-PS_2_Optical_Mouse-event-mouse`
```
       7982385 ns,       7982.385 us,  125.27584 hz,   72 bytes read
       8002035 ns,       8002.035 us,  124.96821 hz,   72 bytes read
       7962256 ns,       7962.256 us,  125.59255 hz,   72 bytes read
       7988828 ns,       7988.828 us,  125.17481 hz,   72 bytes read
       8011032 ns,       8011.032 us,  124.82786 hz,   72 bytes read
       7966524 ns,       7966.524 us,  125.52526 hz,   72 bytes read
       7993312 ns,       7993.312 us,  125.10459 hz,   72 bytes read
       7986931 ns,       7986.931 us,  125.20454 hz,   48 bytes read
       7981237 ns,       7981.237 us,  125.29386 hz,   48 bytes read
```

Nice! we get 125 hz, which is the default poll rate and it's what we expect.

## USB configuration

I'm not an expert in USB, but as far as I know USB devices never send data to
host unannounced. They only respond to host's queries. The host polls the
device for new data at certain rate to check if device has any new data
to send.

Different devices have different rates they support, that supported rate is
sent by the device at configuration time in the `bInterval` field of the
descriptor. More specifically `bInterval` is the delay in milliseconds between
requests. It means slightly different things for different devices and speeds.

Universal Serial Bus Specification:

> Interval for polling endpoint for data transfers.
>
> Expressed in frames or microframes depending on the device operating speed
> (i.e., either 1 millisecond or 125 μs units).
>
> For full-/high-speed isochronous endpoints, this value
> must be in the range from 1 to 16. The _bInterval_ value
> is used as the exponent for a 2<sup>bInterval-1</sup> value; e.g., a
> _bInterval_ of 4 means a period of 8 (2<sup>4-1</sup>).
>
> For full-/low-speed interrupt endpoints, the value of
> this field may be from 1 to 255.
>
> For high-speed interrupt endpoints, the _bInterval_ value
> is used as the exponent for a 2<sup>4-1</sup>
> This value must be from 1 to 16.

We don't care about High-Speed, as mice are never High Speed.
So for our device a frame is just 1ms and `bInterval` is the number
of milliseconds.

We can find the device's configuration by `lsusb -v`

`> lsusb -v`

```
Bus 001 Device 007: ID 046d:c051 Logitech, Inc. G3 (MX518) Optical Mouse
Device Descriptor:
  bLength                18
  bDescriptorType         1
  bcdUSB               2.00
  bDeviceClass            0 
  bDeviceSubClass         0 
  bDeviceProtocol         0 
  bMaxPacketSize0         8
  idVendor           0x046d Logitech, Inc.
  idProduct          0xc051 G3 (MX518) Optical Mouse
  bcdDevice           30.00
  iManufacturer           1 Logitech
  iProduct                2 USB-PS/2 Optical Mouse
  iSerial                 0 
  bNumConfigurations      1
  Configuration Descriptor:
    bLength                 9
    bDescriptorType         2
    wTotalLength       0x0022
    bNumInterfaces          1
    bConfigurationValue     1
    iConfiguration          0 
    bmAttributes         0xa0
      (Bus Powered)
      Remote Wakeup
    MaxPower               98mA
    Interface Descriptor:
      bLength                 9
      bDescriptorType         4
      bInterfaceNumber        0
      bAlternateSetting       0
      bNumEndpoints           1
      bInterfaceClass         3 Human Interface Device
      bInterfaceSubClass      1 Boot Interface Subclass
      bInterfaceProtocol      2 Mouse
      iInterface              0 
        HID Device Descriptor:
          bLength                 9
          bDescriptorType        33
          bcdHID               1.10
          bCountryCode            0 Not supported
          bNumDescriptors         1
          bDescriptorType        34 Report
          wDescriptorLength      77
         Report Descriptors: 
           ** UNAVAILABLE **
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x81  EP 1 IN
        bmAttributes            3
          Transfer Type            Interrupt
          Synch Type               None
          Usage Type               Data
        wMaxPacketSize     0x0008  1x 8 bytes
        bInterval              10

```

So our mice's `bInterval` is 10 ms. Aparrently it's rounded to the nearest
power of 2 to 8 ms. So to get the polling rate we divide 1000ms (in a second)
by our `bInterval` which is 8 and get 125 hz.

To "overclock" our mouse we need somehow make Linux think that the device's
supported rate is 500hz, which means we need to set `bInterval` to 2 (ms).

## Patching the kernel

First, let's get the kernel source code, extract the archive and `cd` into it.
This step might be different for different distributions.
We should be able to build it and run it, which I do.

I'm using the latest stable kernel version which right now is 5.18.3.

Now let's make sure that there isn't a driver or a special case for this
specific mouse somewhere in the kernel. To do that I'll just grep for
something that might be a name or id if this mouse.

I use `ripgrep` instead of `grep`, but it's not important.

```
> cd drivers
> rg -i 'mx518'
```

Found nothing. How about MX followed by 3 numbers?

`> rg -i 'mx\d\d\d\b'`
```
...
input/mouse/logips2pp.c: { 61,	PS2PP_KIND_MX,					/* MX700 */
input/mouse/logips2pp.c: { 100,	PS2PP_KIND_MX,					/* MX510 */
input/mouse/logips2pp.c: { 111,  PS2PP_KIND_MX,	PS2PP_WHEEL | PS2PP_SIDE_BTN },	/* MX300 reports task button as side */
input/mouse/logips2pp.c: { 112,	PS2PP_KIND_MX,					/* MX500 */
input/mouse/logips2pp.c: { 114,	PS2PP_KIND_MX,					/* MX310 */
...
```

Looks interesting...

```c
// SPDX-License-Identifier: GPL-2.0-only
/*
 * Logitech PS/2++ mouse driver
 *
 * Copyright (c) 1999-2003 Vojtech Pavlik <vojtech@suse.cz>
 * Copyright (c) 2003 Eric Wong <eric@yhbt.net>
 */
```

It's a PS/2 not USB driver, so let's ignore that.

Now let's look for the `idProduct` of our mouse, which is `0xc051`:

`> rg 'c051'`

```
sound/pci/hda/patch_realtek.c
11238:	SND_PCI_QUIRK(0x144d, 0xc051, "Samsung R720", ALC662_FIXUP_IDEAPAD),

lib/crypto/chacha20poly1305-selftest.c
2980:static const u8 enc_assoc051[] __initconst = {
6033:	{ enc_input051, enc_output051, enc_assoc051, enc_nonce051, enc_key051,
6034:	  sizeof(enc_input051), sizeof(enc_assoc051), sizeof(enc_nonce051) },

drivers/gpu/drm/amd/include/asic_reg/gca/gfx_8_1_d.h
463:#define mmSCRATCH_ADDR                                                          0xc051

drivers/gpu/drm/amd/include/asic_reg/gca/gfx_8_0_d.h
463:#define mmSCRATCH_ADDR                                                          0xc051

drivers/gpu/drm/amd/include/asic_reg/gca/gfx_7_0_d.h
413:#define mmSCRATCH_ADDR                                                          0xc051

drivers/gpu/drm/amd/include/asic_reg/gca/gfx_7_2_d.h
425:#define mmSCRATCH_ADDR                                                          0xc051

drivers/gpu/drm/amd/pm/powerplay/inc/polaris10_pwrvirus.h
1117:	0x04200001, 0x7e2a0004, 0xce013084, 0x90000000, 0x28340001, 0x313c0bcc, 0x9bc00010, 0x393c051f,

drivers/gpu/drm/sun4i/sun8i_vi_scaler.c
210:	0x00fc051f, 0x00fc0521, 0x00fc0621, 0x00fc0721,

tools/testing/ktest/sample.conf
1031:#   IGNORE_WARNINGS = 42f9c6b69b54946ffc0515f57d01dc7f5c0e4712 0c17ca2c7187f431d8ffc79e81addc730f33d128
```

Nothing related to mice or Logitech.

Now that we are somewhat sure that there is no specific driver for our mouse
let's try to find where `bInterval` is being set for all devices.

Searching for `bInterval` resulted in the following interesting code in

`drivers/usb/core/config.c`:

```c
static int usb_parse_endpoint(struct device *ddev, int cfgno,
	struct usb_host_config *config, int inum, int asnum,
	struct usb_host_interface *ifp, int num_ep,
	unsigned char *buffer, int size)

...

/*
 * Fix up bInterval values outside the legal range.
 * Use 10 or 8 ms if no proper value can be guessed.
 */
i = 0;		/* i = min, j = max, n = default */
j = 255;
if (usb_endpoint_xfer_int(d)) {
	i = 1;
	switch (udev->speed) {
	case USB_SPEED_SUPER_PLUS:
	case USB_SPEED_SUPER:
	case USB_SPEED_HIGH:
		/*
		 * Many device manufacturers are using full-speed
		 * bInterval values in high-speed interrupt endpoint
		 * descriptors. Try to fix those and fall back to an
		 * 8-ms default value otherwise.
		 */
		n = fls(d->bInterval*8);
		if (n == 0)
			n = 7;	/* 8 ms = 2^(7-1) uframes */
		j = 16;

		/*
		 * Adjust bInterval for quirked devices.
		 */
		/*
		 * This quirk fixes bIntervals reported in ms.
		 */
		if (udev->quirks & USB_QUIRK_LINEAR_FRAME_INTR_BINTERVAL) {
			n = clamp(fls(d->bInterval) + 3, i, j);
			i = j = n;
		}
		/*
		 * This quirk fixes bIntervals reported in
		 * linear microframes.
		 */
		if (udev->quirks & USB_QUIRK_LINEAR_UFRAME_INTR_BINTERVAL) {
			n = clamp(fls(d->bInterval), i, j);
			i = j = n;
		}
		break;
	default:		/* USB_SPEED_FULL or _LOW */
		/*
		 * For low-speed, 10 ms is the official minimum.
		 * But some "overclocked" devices might want faster
		 * polling so we'll allow it.
		 */
		n = 10;
		break;
	}
} else if (usb_endpoint_xfer_isoc(d)) {
	i = 1;
	j = 16;
	switch (udev->speed) {
	case USB_SPEED_HIGH:
		n = 7;		/* 8 ms = 2^(7-1) uframes */
		break;
	default:		/* USB_SPEED_FULL */
		n = 4;		/* 8 ms = 2^(4-1) frames */
		break;
	}
}
if (d->bInterval < i || d->bInterval > j) {
	dev_warn(ddev, "config %d interface %d altsetting %d "
	    "endpoint 0x%X has an invalid bInterval %d, "
	    "changing to %d\n",
	    cfgno, inum, asnum,
	    d->bEndpointAddress, d->bInterval, n);
	endpoint->desc.bInterval = n;
}

/* Some buggy low-speed devices have Bulk endpoints, which is
 * explicitly forbidden by the USB spec.  In an attempt to make
 * them usable, we will try treating them as Interrupt endpoints.
 */
if (udev->speed == USB_SPEED_LOW && usb_endpoint_xfer_bulk(d)) {
	dev_warn(ddev, "config %d interface %d altsetting %d "
	    "endpoint 0x%X is Bulk; changing to Interrupt\n",
	    cfgno, inum, asnum, d->bEndpointAddress);
	endpoint->desc.bmAttributes = USB_ENDPOINT_XFER_INT;
	endpoint->desc.bInterval = 1;
	if (usb_endpoint_maxp(&endpoint->desc) > 8)
		endpoint->desc.wMaxPacketSize = cpu_to_le16(8);
}

/*
 * Validate the wMaxPacketSize field.
 * Some devices have isochronous endpoints in altsetting 0;
 * the USB-2 spec requires such endpoints to have wMaxPacketSize = 0
 * (see the end of section 5.6.3), so don't warn about them.
 */
maxp = le16_to_cpu(endpoint->desc.wMaxPacketSize);
if (maxp == 0 && !(usb_endpoint_xfer_isoc(d) && asnum == 0)) {

...

```

It looks like this code is setting `bInterval` based on device speed and
other things. Probably a decent place we can insert our code.

Judging by the comments the code here sets `endpoint->desc.bInterval`
to override it, so let's try doing the same.

```c
...

} else if (usb_endpoint_xfer_isoc(d)) {
	i = 1;
	j = 16;
	switch (udev->speed) {
	case USB_SPEED_HIGH:
		n = 7;		/* 8 ms = 2^(7-1) uframes */
		break;
	default:		/* USB_SPEED_FULL */
		n = 4;		/* 8 ms = 2^(4-1) frames */
		break;
	}
}

/* unmanbearpig: MX518 mouse hack */
/* The MX518 mouse supports 500 hz poll rate, but reports only 125 hz,
 * so we can override it to get the faster rate */
if (udev->descriptor.idVendor == 0x046d && udev->descriptor.idProduct == 0xc051) {
	dev_warn(ddev, "overriding MX518 bInterval to 2 (500hz); config %d interface %d\n",
	         cfgno, inum);
	n = 2;
	endpoint->desc.bInterval = n;
}
/* unmanbearpig end hack */

if (d->bInterval < i || d->bInterval > j) {
	dev_warn(ddev, "config %d interface %d altsetting %d "
	    "endpoint 0x%X has an invalid bInterval %d, "

...
```

We first match the `idVendor` and `idProduct` so we only affect our mouse.
Then we use `dev_warn` to print something into `dmesg` so we can check in
the logs that the code has actually ran, in case something goes wrong.
And finally we set the `n` value which is used in this function
and the `bInterval` to 2, which corresponds to 500 hz poll rate.

Now compile and install the kernel, then reboot and pray.

My kernel surprisingly worked the first time. Let's check if the patch worked:

`> dmesg | rg MX518`
```
[    2.940385] usb 1-1.4: overriding MX518 bInterval to 2 (500hz); config 1 interface 0
```

Looks good! Let's check if reported bInterval is changed to 2:

`> lsusb -v`
```
        bInterval              10
```

Huh, it's not changed and still is 10. Let's try measuring it anyway.

`> sudo hid_rate /dev/input/by-id/usb-Logitech_USB-PS_2_Optical_Mouse-event-mouse`
```
       1980669 ns,       1980.669 us,  504.87992 hz,   48 bytes read
       1993399 ns,       1993.399 us,  501.65571 hz,   48 bytes read
       1986994 ns,       1986.994 us,  503.27278 hz,   48 bytes read
       1975510 ns,       1975.510 us,  506.19840 hz,   48 bytes read
       1985570 ns,       1985.570 us,  503.63372 hz,   48 bytes read
       1980698 ns,       1980.698 us,  504.87252 hz,   48 bytes read
       1989573 ns,       1989.573 us,  502.62041 hz,   72 bytes read
       1972313 ns,       1972.313 us,  507.01892 hz,   48 bytes read
       1984499 ns,       1984.499 us,  503.90552 hz,   48 bytes read
       1983499 ns,       1983.499 us,  504.15957 hz,   72 bytes read
       1978091 ns,       1978.091 us,  505.53792 hz,   48 bytes read
       1983221 ns,       1983.221 us,  504.23024 hz,   48 bytes read
       1995423 ns,       1995.423 us,  501.14687 hz,   72 bytes read
       1978025 ns,       1978.025 us,  505.55478 hz,   48 bytes read
       1995992 ns,       1995.992 us,  501.00401 hz,   72 bytes read
       3980757 ns,       3980.757 us,  251.20850 hz,   72 bytes read
       3988748 ns,       3988.748 us,  250.70523 hz,   72 bytes read
       3977186 ns,       3977.186 us,  251.43405 hz,   72 bytes read
       3991401 ns,       3991.401 us,  250.53860 hz,   72 bytes read
       3987779 ns,       3987.779 us,  250.76615 hz,   72 bytes read
       3982110 ns,       3982.110 us,  251.12315 hz,   48 bytes read
       3979834 ns,       3979.834 us,  251.26676 hz,   48 bytes read
       1988891 ns,       1988.891 us,  502.79276 hz,   48 bytes read
       1984657 ns,       1984.657 us,  503.86540 hz,   48 bytes read
       1985271 ns,       1985.271 us,  503.70957 hz,   48 bytes read
       7988877 ns,       7988.877 us,  125.17404 hz,   48 bytes read
```

Yay! We got the 500 hz polling rate that we wanted! It means that `lsusb`
gets its data from the original USB descriptor, not the one that we've
written to, but the kernel actually uses our descriptor to poll the mouse.

Well, I'm not sure if it's good or bad that it still reports 10, but it works,
and it's good enough for me.

I suspect there might be a way to make a kernel module so that we don't have
to patch the kernel every time we update it, but I build my own kernel anyway,
so it's not a problem. I doubt many people would need this feature for that old
mouse, so as long as it works for me it's good enough.

Hope it inspires you to hack on the kernel and make your own first patch
for Linux!


Also take a look at 
[ArchWiki article on mouse polling rate][arch_wiki] for general
info on mouse polling rate in Linux.

[hid_rate]:    https://github.com/unmanbearpig/hid_rate
[arch_wiki]:   https://wiki.archlinux.org/title/Mouse_polling_rate
