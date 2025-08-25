

## notes on latest iteration 7/2025

default frame rate will be 30 fps and effects and stuff can expect that

an effect will happen by invoking a method of an effect object to start it and then one repeatedly to step it foward, with the effect updating the frame and returning true if it is still active or false if it has finished

effect steps are invoked by a dispatcher

the dispatcher is responsible for clearing the WS2815 strip to black, invoking all of the active effects step routines, showing the resulting frame, and sleeping as needed

because we default to black every frame, the effects need not worry about turning off or setting back the LEDs that they change.

hmm instead of always setting them to black you could have a base set of values.  like the background values.  usually black but can be an array of colors and that's what the wipes and stuff could work on, things that expect what they write to stay and we don't want in a wipe to rewrite 300 values at 30 fps or whatever.

so there are foreground effects and background effects.  background effects change the background values.
foreground effects write new values into the frame on the fly.

so the dispatcher class of which there will be one instance will:
- be able to be handed an effect object which it will invoke its start function and then

every frame:
- invoke all the active background effects that update the background values
- reset the frame to the array of background values
- invoke all the active effects that update the frame
- show the frame

really since most background effects set all the pixels, having more than one running at the same time is a waste.  Only the last one in sequence will have its pixels seen.

is there a way for the effect to think it's doing a sleep and stuff so it doesn't have to get called as a callback, async or something?  Note - we added this.

## orchestrator

there needs to be an orchestrator that kicks off effects at points in time

it's a dispatcher that will execute code at points in time according to its schedule

it also shouild be able to do something like chain effects (the completion of one effect starts another) and wait for an effect to complete

(at least partially done - we have point-in-time actions)

------

## virtualization and multiple strings

Right now say you have one to several strings in series of 300 RGB pixels each, all the stuff expects the strings to be in a straight line.  if you're using multiple interfaces on the pi, you have to have multiple dispatchers because the dispatcher is tied to the string.

now let's say we because of the topology of the thing we're lighting, it's not so straightforward.  the first 200 pixels are a vertical, then the next 100 are a horizontal, then the next 200 are a vertical, then the next 100 are a horizontal.  one vertical might count up, the next down, and the horizontals might count left to right or right to left as a matter of the convenience of wiring.

We need to be able to virtualize the strings so that we in the case of four verticals and two long horizontals, that we create six conceptual strings that map over the actual strings.  So like the first vertical starts at the bottom and goes from physical pixel 1 to pixel 200, then 201 to 300 are horizontal, then the next vertical is 301 to 500, except the second vertical is "upside down" i.e. it counts down instead of up.  Then we cut the pixel strip and run wires back up to start the next horizontal run, etc.

But in the end we want the vertical strips to always be 0 at the top and N at the bottom, and the horizontal strips to always be 0 at the left and N at the right.

So, one, we need to think about the dispatcher.  We probably don't want two dispatchers.  We might want to decouple the dispatcher from the strings so that one dispatcher can handle multiple strings and maybe doesn't even know it is doing it.

Two, we need to think about the effects.  They need to be able to be applied to a virtual string, not a physical string.  So we need to have a way of mapping the virtual strings to the physical strings.  And virtual strings can span pixels of multiple physical strings, so each virtual pixel must be able to identify the corresponding interface and physical pixel number.

ok - turns out the dispatcher is already strip-agnostic.  it keeps track of all the strips it has seen as part of dispatching effects and invokes affected one's show method.  So we can just have one dispatcher and it will handle multiple strips.

The virtualization angle, we can do that by having a virtual strip class that maps the virtual pixel number to the physical interface and pixel number.  Is it necessary for an effect to be able to span strips?  Sure, imagine a bunch of verticals showing a spectrum analyzer or an ocean wave effect or something.  So effects need to be able to access and manipulate about multiple virtual strips.

A virtual strip will work a lot like a physical strip.  self.strip will be a virtual strip instead of a physical one.  self.width with be the number of pixels in the virtual strip, and self.pixels will be a list of pixel objects that are virtual pixels.  The virtual pixel object will have a reference to the physical interface and pixel number.


I kind of don't like every single pixel in a virtual strip identifying the physical strip.  It feels slow.  It probably doesn't much matter.  It kinda has to be that way but usually there will be long consecutive runs of pixels from the same strip.

## Moving to a mobile web UI

Right now all the demos are run from the command line.  

We need to move to a mobile web UI that can run on a phone or tablet and control the effects.  The UI should be able to:

- stop all effects and blackout the strips
- power off the computer
- Start and stop effects
- Queue effects
- Change effect parameters
- Show the current state of the effects
- Show the current state of the logical strips
- Show the current state of the dispatcher and orchestrator

please examine the gen2 directory of my lightymclightshow project at GitHub at https://github.com/lehenbauer/lightymclightshow/tree/async-alpha-gamma/gen2. It's in python and it uses the WS281x LED strips. Files with the name "steely" in them relate to an installation on our pontoon boat, Steely Glint. It has two strips of 470 RGB LEDs, one on the port side and one on the starboard side. The logical strip stuff allows us to call the frontmost pixels 0 even though 0 actually started at the back of the boat. The strips start at the center of the bow and proceed outward. Many effects are defined in dispatcher.py and steelydemo*.py are little driver programs to run the demos. I am about ready to take the next step. I'd like to create a mobile-friendly web UI to drive the lightshow. Something that will replace all the demo programs. I suppose the raspberry pi will offer a wifi connection for peoples' phones. I've done some flask apps. it's OK. but I'd like the website to be somewhat modern. please suggest what web technologies you think I should use, and how the demos can be run not as demo programs (currently I'm running them from the command line on my laptop) but instead from the web. Also I'm gonna want to do some stuff that aren't purely effects. like I might want a way to light all the pixels at the front of the boat white like as a dock light, and I might want to show red and green as port and starboard nav lights. so just cogitate and respond with your best suggestions for how I can take this technology to the next level. You might want to look at the README file and the like in the top level directory (one up from gen2) as well. Thanks!


