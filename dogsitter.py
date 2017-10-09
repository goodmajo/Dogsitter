import RPi.GPIO as GPIO
import time
import datetime
import ephem

# This function gets used right away, outside of the main loop. Thus, it needs to be up here.
def PrintTime(aString):
    now = datetime.datetime.now()
    print(now, ":")
    print(aString)

# Turn off the GPIO pins if they were left on for some reason.
GPIO.cleanup()

# Pins get declared here.
downstairsSensor = 3
upstairsSensor = 3
upstairsRelay = 20
downstairsRelay = 21
initialLocationSwitch = 26
powerLED = 14
triggerLED = 15

# Set up GPIOs.
GPIO.setmode(GPIO.BCM)
GPIO.setup(downstairsSensor, GPIO.IN)
GPIO.setup(upstairsSensor, GPIO.IN)
GPIO.setup(initialLocationSwitch, GPIO.IN)
GPIO.setup(downstairsRelay, GPIO.OUT)
GPIO.setup(upstairsRelay, GPIO.OUT)
GPIO.setup(powerLED, GPIO.OUT)
GPIO.setup(triggerLED, GPIO.OUT)

# Make a boolean to say whether or not the light is activated. Assume we're turning this on during the day.
isALightOn = 0

# This variable will control how many seconds we will wait for the second sensor to trigger once the first one detects movement.
timeDelay = 12

# This variable determines how long we want to wait before the program starts running
startupDelay = 1

# This will tell us *which* light is on.
theLightIsOn = "upstairs"

# Define city for aquisition of sunrise/sunset time.
whereAmI = ephem.city('San Francisco')

# Pause for 10 seconds to give us a chance to leave without triggering downstairsSensor.
time.sleep(startupDelay)
PrintTime("Starting Dogsitter now")

# If the switch is up, set oliveLocation to upstairs.
if GPIO.input(initialLocationSwitch) == 1:
    oliveLocation = "upstairs"
    print("Olive was upstairs when you left")
else:
    oliveLocation = "downstairs"
    print("Olive was downstairs when you left")

def main():
    try:
        while True:
            # Check time
            sun = ephem.Sun(whereAmI)
            sunIsUp = whereAmI.previous_rising(sun) > whereAmI.previous_setting(sun)
            print("sunIsUp defined")
            
            print("startup delay == ", startupDelay)
            print("downstairs == ", downstairsSensor)
            print("is a light on == ", isALightOn)

            # Do things to the lights if the sun went up or down
            if sunIsUp == False:
                print("We need to turn on a light")
                theLightIsOn = LightOn()
            if sunIsUp == True:
                print("We need to turn the light off")
                if theLightIsOn == "downstairs":
                    GPIO.output(downstairsRelay, GPIO.LOW)
                    #isALightOn = 1
                else:
                    GPIO.output(upstairsRelay, GPIO.LOW)
                    #isALightOn = 1
                PrintTime("Lights are now off")

            # Check sensors
            if GPIO.input(downstairsSensor) == 1:
                print("Downstairs sensor triggered")
                oliveLocation = DownstairsSensorTriggered(sunIsUp)
                if len(oliveLocation) == 2:
                    theLightIsOn = oliveLocation[1]
                    oliveLocation = oliveLocation[0]

            if GPIO.input(upstairsSensor) == 1:
                print("Upstairs sensor triggered")
                oliveLocation = UpstairsSensorTriggered(sunIsUp)
                if len(oliveLocation) == 2:
                    theLightIsOn = oliveLocation[1]
                    oliveLocation = oliveLocation[0]

    except KeyboardInterrupt:
        PrintTime("Dogsitter has been stopped by user")
        GPIO.cleanup()
        exit()
    
    #except:
    #    PrintTime("An error has occurred and Dogsitter needs to quit")
    #    GPIO.cleanup()
    #    exit()


def LightOn():
    if oliveLocation == "upstairs":
        GPIO.output(upstairsRelay, GPIO.HIGH)
        theLightIsOn = "upstairs"
        PrintTime("Turned a light on upstairs")
    else:
        GPIO.output(downstairsRelay, GPIO.HIGH)
        theLightIsOn = "downstairs"
        PrintTime("Turned a light on downstairs")
    return(theLightIsOn)


def DownstairsSensorTriggered(sunIsUp):
    triggerTime = time.time()
    lightChanged = False
    PrintTime("Downstairs sensor has been triggered")
    # Now wait and see if the second sensor was triggered
    while time.time() < triggerTime + timeDelay and lightChanged == False:
        if GPIO.input(upstairsSensor) == 1:
            oliveLocation = "upstairs"
            if sunIsUp == False and isALightOn == 1 and theLightIsOn == "downstairs":
                PrintTime("Olive is moving downstairs. Turning on light downstairs.")
                theLightIsOn = LightOn()
                lightChanged = True
                continue
    if lightChanged == True:
        return(oliveLocation, theLightIsOn)
    else:
        return(oliveLocation)


def UpstairsSensorTriggered(sunIsUp):
    triggerTime = time.time()
    lightChanged = False
    PrintTime("Upstairs sensor has been triggered")
    # Now wait and see if the second sensor was triggered
    while time.time() < triggerTime + timeDelay and lightChanged == False:
        if GPIO.input(downstairsSensor) == 1:
            oliveLocation = "downstairs"
            if sunIsUp == False and isALightOn == 1 and theLightIsOn == "upstairs":
                PrintTime("Olive is moving upstairs. Turning on light upstairs.")
                theLightIsOn = LightOn()
                lightChanged = True
                continue
    if lightChanged == True:
        return(oliveLocation, theLightIsOn)
    else:
        return(oliveLocation)


if __name__ == '__main__':
    main()
