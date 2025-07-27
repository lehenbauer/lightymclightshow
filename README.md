

# lightymclightshow

This is python software to control as many WS2812B RGB LED strips or equivalent as you can reasonably put on a Raspberry Pi.

It uses the rpi_ws281x library to control the LEDs and gpsd to get GPS data for speed-aware lighting effects, etc.

It has a dispatcher class that an run many effects simultaneously.  

## Effects

effects are python objects that have a start and a step method and do things to the lights.  they have a duration in seconds and are thus frame rate independent.  when the dispatcher calls the step method, it passes the elapsed time in seconds since the start of the effect.  the effect can then calculate what pixels it needs to set based on that time.

for example a fill effect that fills over 5 seconds would set half the pixels to the fill color at 2.5 seconds, all at 5 seconds.

background effects operate on a background array of pixels that is the size of the strip, and they can set pixels to a color or leave them unchanged.  The dispatcher then takes the background array and sets the actual strip pixels to it when it calls the show method.

foreground effects operate directly on the strip pixels and can set them to a color or leave them unchanged.  The dispatcher calls the show method on the strip after all foreground effects have been stepped.

The step function returns True if there are more steps to follow and False if it has finished.


Currently the action is in the gen2 directory.  Directories named "attic" contain old stuff and are unimportant.

The code and effects are in gen2/dispatcher.py.


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

pwm0 is pin 32, the fifth one up from the bottom right if facing the board with the connector on the upper right -- is this right, better confirm

pin 1 top left is 3.3 volts, pin 2 top right is 5V as is pin 4 just below it, the third pin on the right from the top is ground, also the bottom left pin is ground

also 9 down on the left is 3.3v

bottom left is also ground

GPIO 18 is the sixth one down from the top right and that's the goodie for now

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

