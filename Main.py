import RPi.GPIO as GPIO
import time
import subprocess
import ephem
import Dogsitter

# Turn off the GPIO pins if they were left on for some reason.
GPIO.cleanup()

# Pins get declared here.
downstairs_PIR = 3
upstairs_PIR = 3
upstairs_relay_pin = 20
downstairs_relay_pin = 19
temp_sensor = 18
decibel_sensor = 23
initial_location_switch_pin = 26
power_LED_pin = 14
trigger_LED_pin = 15

# Set up GPIOs.
GPIO.setmode(GPIO.BCM)
GPIO.setup(downstairs_PIR, GPIO.IN)
GPIO.setup(upstairs_PIR, GPIO.IN)
GPIO.setup(initial_location_switch_pin, GPIO.IN)
GPIO.setup(downstairs_relay_pin, GPIO.OUT)
GPIO.setup(upstairs_relay_pin, GPIO.OUT)
GPIO.setup(power_LED_pin, GPIO.OUT)
GPIO.setup(trigger_LED_pin, GPIO.OUT)

# This variable will control how many seconds we will wait for the second sensor to trigger once the first one detects movement.
time_delay = 10.0

# This variable determines how long we want to wait before the program starts running
startup_delay = 1.0

# Define city for aquisition of sunrise/sunset time.
where_am_I = ephem.city('San Francisco')

# Create objects and related variables
olive = Dogsitter.Dog()
initial_location_switch = Dogsitter.Initial_Location_Switch()
stereo = Dogsitter.Stereo
power_LED = Dogsitter.Box.Power_LED()
trigger_LED = Dogsitter.Box.Trigger_LED()

lights = Dogsitter.Lights()

upstairs_light_name = "upstairs light"
upstairs_light = Dogsitter.Light(upstairs_light_name)

downstairs_light_name = "downstairs light"
downstairs_light = Dogsitter.Light(downstairs_light_name)

upstairs_relay = Dogsitter.Relay("upstairs relay", upstairs_relay_pin)
downstairs_relay = Dogsitter.Relay("downstairs relay", downstairs_relay_pin)

# Set up observers
upstairs_light.register(upstairs_light)
upstairs_light.register(upstairs_relay)

downstairs_light.register(downstairs_light)
downstairs_light.register(downstairs_relay)

# Easy vars for the dog's position
upstairs = "upstairs"
downstairs = "downstairs"

# Sound file name
sound_filename = "~/Music/whitenoise.mp3"

# If the switch is up, set oliveLocation to upstairs.
if GPIO.input(initial_location_switch):
    olive.location_in_house = upstairs
    print("Olive was upstairs when you left")
else:
    olive.location_in_house = downstairs
    print("Olive was downstairs when you left")


def main():
    # Pause for 10 seconds to give us a chance to leave without triggering downstairsSensor.
    time.sleep(startup_delay)
    Dogsitter.PrintTime("Starting Dogsitter now")
    try:
        while True:
            # Check to see if the sun is up or not.
            sun = ephem.Sun(where_am_I)
            sun_is_up = where_am_I.previous_rising(sun) > where_am_I.previous_setting(sun)

            # Do things to the lights if the sun went up or down
            if sun_is_up:
                # Sun's up
                if lights.state == "On":
                    upstairs_light.dispatch("Off", upstairs_light_name)
                    downstairs_light.dispatch("Off", downstairs_light_name)
            else:
                # Sun's down
                if lights.state == "Off":
                    if olive.location_in_house == upstairs:
                        downstairs_light.dispatch("On", downstairs_light_name)
                    else:
                        upstairs_light.dispatch("On", upstairs_light_name)
                    lights.state = "On"
                else:
                    if olive.location_in_house == upstairs:
                        if downstairs_light.state == "On":
                            print("Since Olive is upstairs, turning off light downstairs")
                            downstairs_light.dispatch("Off", downstairs_light_name)
                    if olive.location_in_house == downstairs:
                        if upstairs_light.state == "On":
                            print("Looks like olive moved downstairs. Turning upstairs light off.")
                            upstairs_light.dispatch("Off", upstairs_light_name)


            # Check PIR sensors
            if GPIO.input(downstairs_PIR):
                print("Downstairs sensor triggered")
                trigger_time = time.time()
                while time.time() < trigger_time + time_delay and GPIO.input(upstairs_PIR) == False:
                    if GPIO(upstairs_PIR):
                        olive.location_in_house = upstairs
                        olive.trips_through_house += 1

            if GPIO.input(upstairs_PIR):
                print("Upstairs sensor triggered")
                trigger_time = time.time()
                while time.time() < trigger_time + time_delay and GPIO.input(downstairs_PIR) == False:
                    if GPIO(downstairs_PIR):
                        olive.location_in_house = downstairs
                        olive.trips_through_house += 1

            # Check sound sensor
            if GPIO.input(decibel_sensor):
                subprocess.call(['xdg-open', sound_filename])

            # Check temp sensor
            # Use I2C to communicate with Arduino and get temp info, maybe?

            # Publish info to webpage?


    except KeyboardInterrupt:
        Dogsitter.Print_Time("Dogsitter has been stopped by user")
        GPIO.cleanup()
        upstairs_light.unregister(upstairs_light)
        upstairs_light.unregister(upstairs_relay)
        downstairs_light.unregister(downstairs_light)
        downstairs_light.unregister(downstairs_relay)
        exit()

    except:
        Dogsitter.Print_Time("An error has occurred and Dogsitter needs to quit")
        GPIO.cleanup()
        upstairs_light.unregister(upstairs_light)
        upstairs_light.unregister(upstairs_relay)
        downstairs_light.unregister(downstairs_light)
        downstairs_light.unregister(downstairs_relay)
        exit()









if __name__ == '__main__':
    main()