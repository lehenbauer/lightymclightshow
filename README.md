

# lightymclightshow

LightyMcLightShow can do things with RGB LED strips pretty much beyond anything you've seen before.

It comes with a library of interesting and, in some cases, dramatic effects.  New effects can be coded in dead simple python by you and your favorite reasonably high-end AI.

Something else cool that you never see, multiple effects can run at the same time.  For example you might have two independent chases, the sparkle effect, and the pulsator effect play simultaneously.

RGBW (RGB + white)?  No problem.

LML can respond to its environment.  With a $20 USB GPS, LML effects' behavior can change according to latitude and longitude, speed, altitude, bearing, etc.  Add a $30 9DOF intertial unit and also sense acceleration, turn rate, magnetic heading (allowing you to detect the vehicle is going forward or backwards), etc.  Write something responsive to music by using fourier transforms on data read from a microphone or audio playback.

One pretty cool LML effect is the ability to read an image file such as a png, jpeg, webp, etc, and play successive rows of the image to the light strips.  Like a piano roll.  This allows you to create subpixel-accurate maps of animations to play in your favorite image editor such as Photoshop.  Geometric 2D images with lots of black can produce some really stunning strip animations.


This is python software to control as many WS2812B RGB LED strips or equivalent as you can reasonably put on a Raspberry Pi.

It uses the rpi_ws281x library to control the LEDs and gpsd to get GPS data for speed-aware lighting effects, etc.

It has a dispatcher class that an run many effects simultaneously.  

### Frame rate independent

LightyMcLightShow is frame rate independent.  Effects are time based, not frame based.  So for example if you get faster hardware and go from 30 fps to 60 or 100 fps, or free running at the maximum possible update rate, you don't have to change any of your effects; they will just be updated more frequently, usually resulting in a more fluid animation.

### String size independent

Most LightyMcLightShow effects specify the percentage of a string that is to be lit, rather than a number of pixels.  An installation running LightyMcLightShow that doubled their pixel density from 30 RGB pixels per meter to 60 will not have to change their effects, since width specifications are in percentages of string width. 

### Update Rate

* ~110 Hz max for a 300-LED RGB strip
* ~80–85 Hz max for the same length if each LED is RGBW

There is a ~50 μs “reset” low‐pulse between frames, so real-world max refresh will be just slightly under these values

So to go to 600 LEDs on one interface, you'd be halving the frame rate.  Still pretty good, though.


## Effects

Effects are python objects that have a start and a step method and do things to the lights.  When the dispatcher calls the step method, it passes the elapsed time in seconds since the start of the effect.  the effect can then calculate what pixels it needs to set based on that time.

for example a fill effect that fills over 5 seconds would set half the pixels to the fill color at 2.5 seconds, all at 5 seconds.

There are two effects types, background effects and foreground effects.   You code them almost exactly the same but they are treated a little differently by LML.

Background effects operate on a background array of pixels that is the size of the strip, and they can set pixels to a color or leave them unchanged.  After stepping all the background effects (usually only one is running) the dispatcher then takes the background array and sets the actual strip pixels to it when it calls the show method.

Examples of background effects are doing a fill where you slowly change from one color to another from one end or another.  It eventually effects all the pixels.

foreground effects operate directly on the strip pixels and can set them to a color or leave them unchanged.  The dispatcher calls the show method on the strip after all foreground effects have been stepped.

The step function returns True if there are more steps to follow and False if it has finished.


Currently the action is in the gen2 directory.  Directories named "attic" contain old stuff and are unimportant.

The code and effects are in gen2/dispatcher.py.

## Aesthetics

You want to create your effects according to the purpose of the installation.  The lobby of a nice hotel calls for subtle, unintrusive lighting that doesn't call attention to itself.  So you'd install the strips so the LEDs are only indirectly visible and go for slow fills of near-adjacent colors, probably from a relatively limited, muted color palette, developed in coordination with the designer, slow color wheels to different shades at a rate that's nearly imperceptible.

Since each RGB LED can be individually set to one of about four million colors, this stuff kicks the crap out of cheesy 8-color RGB strips and especially when the pixels aren't individually addressable.







## prerequisites

apt install git cmake
apt install python3-dev


https://github.com/jgarff/rpi_ws281x?tab=readme-ov-file

if using PWM0, you need to blacklist snd_bcm2835

for pwm0

add to /etc/modprobe.d/snd-blacklist.conf

```
blacklist snd_bcm2835
```

## notes on raspberry pi pins

We're using the Adafruit pixel shifter https://learn.adafruit.com/adafruit-pixel-shifter/pinouts although an appropriately fast 3.3V to 5V level converter will do.

+---------------+          +-------------------+          +-------------------+          +-------------+
| Raspberry Pi 4|          | Adafruit Pixel    |          | 12V Power Supply  |          | WS2815 Strip|
| GPIO Header   |          | Shifter           |          | (e.g., 12V/5A+)   |          |             |
|               |          |                   |          |             +12V  +--------->| +12V        |
| Pin 1/17: 3V3 +--------->| V (3-5V power)    |          |              GND  +--------->| GND         |
| Pin 2/4:  5V  |          |                   |          +-------------------+          |             |
| Pin 32:  PWM0 +--------->| DAT (3.3V input)  |                                         |             |
| Pin 6: GND    +--------->| G (ground)        +---------------------------------------->| GND         |
|               |          |                   |                                         |             |
|               |          | D5 (5V output)    +---------------------------------------->| DIN         |
|               |          |                   |                                         |             |
|               |          |                   |                                         |             |
+---------------+          +-------------------+                                         +-------------+

pin 1 on the big connector is the top inside pin with the USB and ethernet at the bottom.  pin 2 is the top outside pin.

pin 1 is 3V3 power and pin 2 is 5V power.  alternate 5V power on pin 4 and alternate 3V3 power on pin 17 (9th pin down on the inside), useful if you have a dorky fan hogging pin 1.

pwm0 aka GPIO18 aka PWM0 is pin 12, the sixth one down from the top right if facing the board with the GPIO connector on the upper right

pin 1 top left is 3.3 volts, pin 2 top right is 5V as is pin 4 just below it, the third pin on the right from the top is ground, also the bottom left pin is ground

also 9 down on the left is 3.3v

bottom left is also ground


ground is on pins 6, 9, 14, 20, 25, 30, 34, and 39.

you'll need 3V3 and 5V for your level converter.

on the breadboard, make the bottom power rail 3V3 and the top one 5V.

pwm0 is pin 32, the fifth one up from the bottom right if facing the board with the connector on the upper right

pwm0 needs to be connected to your low voltage in on one of your level converters.

you need to run 3V3, 5V and ground to appropriate pins on your level converter.

high voltage out on your level converter needs to go to your data line on your strip.

everything needs to be grounded together.

possibly old or wrong stuff:

GPIO 18 is the sixth one down from the top right and that's the goodie for now

^ or does PWM0 appear on multiple pins or does it need to be configured or what

https://images.theengineeringprojects.com/image/webp/2021/03/raspberry-pi-4.png.webp?ssl=1

## if using SPI on Pi 4

on pi 4 add to /boot/config.txt

```
core_freq=500
core_freq_min=500
```

to avoid the idle CPU scaling changing the SPI frequency and breaking the timings
sudo ./test --width 300 --height 1 --gpio 18

is putting something on the scope

https://www.amazon.com/dp/B07L3QD1LF?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1

python

you need to be root to have permission to access /dev/mem or something for PWM0

## python virtual environment

```
python3 -m venv venv
. venv/bin/activate
```
or 
```
sudo venv/bin/python demo2.py
```


## flickering

if it flickers when a lot of LEDs are on then your power supply is probably not sufficient.

We are using a level converter to raise the 3.3V GPIO signal to 5V for the LED data channel.

We are using WS2815 LEDs which are 12V.

Found somewhere someone says add a 249 ohm resistor.  playing around, 660 worked.  but the problem probably was power supply weakness anyway.

the level converter probably should be faster.  it looks a little soft on the scope.

i'm getting faster ones.

however i the main problem was just not having enough power

## playing images a row at a time to the LEDs

i wrote some stuff that can play lines of an image successively to the LEDs.  It's OK and should be revisited in light of how gen2 works.


play images, play2.py

## Audio

We use python-sounddevice to read audio from a microphone or audio playback device.  This allows us to do things like react to music, or use the audio as a source for effects.

We use pyFFTW to do fast fourier transforms on the audio data to get frequency and amplitude data.

```
sudo apt install libportaudio2 libasound2-dev python3-cffi libatlas-base-dev portaudio19-dev
pip install sounddevice
pip install pyFFTW
```

## GPS

We are going to have effects that are GPS-aware.

USB GPS based on the ublox 7 chipset, $20 on Amazon.

https://www.amazon.com/dp/B01EROIUEW

sudo apt install gpsd gpsd-clients python3-gps

edit /etc/default/gpsd

```
START_DAEMON="true"

# gpsd will listen even if no client is connected (-n) and won’t try to change
# the receiver configuration (-b).  Add -s <rate> only if you have a true UART.
GPSD_OPTIONS="-n -b"

DEVICES="/dev/ttyACM0"
GPSD_SOCKET="/var/run/gpsd.sock"

# Turn off udev hot‑plug because we are specifying the device explicitly.
USBAUTO="false"
```


### to serve GPS to other machines using gpsd,

edit /etc/systemd/system/sockets.target.wants/gpsd.socket

comment out the localhost ListenStream and comment in the ListenStream for the 0.0.0.0
and [::1] addresses and put a -G in there in the above defaults
```

### reload systemd and enable the socket

```
sudo systemctl daemon-reload
sudo systemctl enable gpsd.socket   # start on boot
sudo systemctl restart gpsd.socket  # activate now
```

test with "cgps -s", "gpspipe -r", etc

## slice notation and other python niceties

the pixel strip supports slice notation for setting and that's so cool but you wouldn't know it because it's undocumented since there is basically zero documentation plus none of the examples show it i don't think

so like strip[0:300] = Color(255, 0, 0) will set the first 300 pixels to red
(don't forget strip.show() to actually display the changes)

you can also say strip[0] = Color(255, 0, 0) to set the first pixel to red

it supports len(strip) to get the number of elements/RGB LEDs in the strip

you can also read the color values of a pixel using strip[0] which will return a Color object with the RGB values or a slice like strip[0:300] will return a list of colors for those pixels

## ideas

define segments

number the lights from 0 within a segment

the dock segment might have a horizontal that's 100 wide and four verticals that are 40 high.

so we might have horiz and vert1 through vert4


