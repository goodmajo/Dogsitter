# Dogsitter
This is a work in progress and is, as of right now, pretty much pseudocode as it has not yet been tested yet at all. Do not clone this repo and expect it to work.
## What it is
This program controls an Arduino, an RPi, 2 relays, and a number of sensors. The Arduino acts as a signal processor for the analog sensors, and the RPi handles the system's output.
## What it does
It tracks whether my dog is upstairs or downstairs, and turns a light on in her location if it's after sunset. It also tracks the noise level in the house, and if there is nearby construction or a garbage truck outside, it plays white noise over the stereo. Finally, it logs the temperature in the house over the day.
## How it works
The Arduino reads in data from the temperature sensor and the sound detection module. It calculates the exact temperature and decible level from these values, and prints them to serial. The Arduino code is not yet written.
