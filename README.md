

define segments

number the lights from 0 within a segment

the dock segment might have a horizontal that's 100 wide and four verticals that are 40 high.

so we might have horiz and vert1 through vert4

-----


apt install git cmake
apt install pytho0n3-dev


https://github.com/jgarff/rpi_ws281x?tab=readme-ov-file

for pwm0

/etc/modprobe.d/snd-blacklist.conf
blacklist snd_bcm2835

pwm0 is pin 32, the fifth one up from the bottom right if facing the board with the connector on the upper right

pin 1 top left is 3.3 volts, pin 2 top right is 5V as is pin 4 just below it, the third pin on the right from the top is ground, also the bottom left pin is ground

also 9 down on the left is 3.3v

bottom left is also ground

GPIO 18 is the sixth one down from the top right

https://images.theengineeringprojects.com/image/webp/2021/03/raspberry-pi-4.png.webp?ssl=1

sudo ./test --width 300 --height 1 --gpio 18

is putting something on the scope

https://www.amazon.com/dp/B07L3QD1LF?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1

python

Rpython3 -m venv venv
. venv/bin/activate

on pi 4 add to /boot/config.txt
core_freq=500
core_freq_min=500

to avoid the idle CPU scaling changing the SPI frequency and breaking the timings


it's flickering

https://x.com/MarioNawfal/status/1847149819632013750

says 249 ohm resistor

660 worked.

the level converter probably isn't fast enough.

i'm getting faster ones.



888-477-3701

total due is 4824.66
account number is 4790-03-002-0150-901


