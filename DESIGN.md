

notes on latest iteration 7/2025

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

is there a way for the effect to think it's doing a sleep and stuff so it doesn't have to get called as a callback, async or something?



------

there needs to be an orchestrator that kicks off effects at points in time

it's a dispatcher that will execute code at points in time according to its schedule

it also shouild be able to do something like chain effects (the completion of one effect starts another) and wait for an effect to complete





