import RPi.GPIO as GPIO
import time
import ephem
import Dogsitter


# Turn off the GPIO pins if they were left on for some reason after this script failed.
GPIO.cleanup()

# Pins get declared here.
downstairs_PIR_pin = 3
upstairs_PIR = 4
upstairs_relay_pin = 20
downstairs_relay_pin = 19
temp_sensor = 18
decibel_sensor = 23
initial_location_switch_pin = 26
power_LED_pin = 14
green_trigger_LED_pin = 15
blue_trigger_LED_pin = 16

# Set up GPIOs.
GPIO.setmode(GPIO.BCM)

GPIO.setup(downstairs_PIR_pin, GPIO.IN)
GPIO.setup(upstairs_PIR, GPIO.IN)
GPIO.setup(initial_location_switch_pin, GPIO.IN)
GPIO.setup(temp_sensor, GPIO.IN)
GPIO.setup(decibel_sensor, GPIO.IN)

GPIO.setup(downstairs_relay_pin, GPIO.OUT)
GPIO.setup(upstairs_relay_pin, GPIO.OUT)
GPIO.setup(power_LED_pin, GPIO.OUT)
GPIO.setup(blue_trigger_LED_pin, GPIO.OUT)
GPIO.setup(green_trigger_LED_pin, GPIO.OUT)

# Sound file name
sound_filename = "~/Music/whitenoise.mp3"

# This variable will control how many seconds we will wait for the second sensor to trigger once the first one detects movement.
time_delay = 10.0

# This variable determines how long we want to wait before the program starts running
startup_delay = 1.0

# Define city for aquisition of sunrise/sunset time. I don't live in SF, but it's the closest ephem can get.
where_am_I = ephem.city('San Francisco')

# Create objects and related variables
olive = Dogsitter.Dog()
initial_location_switch = Dogsitter.Initial_Location_Switch()
stereo = Dogsitter.Stereo(sound_filename)

power_LED = Dogsitter.Box.Power_LED()
trigger_LED = Dogsitter.Box.Trigger_LED(green_trigger_LED_pin, blue_trigger_LED_pin)

downstairs_PIR = Dogsitter.PIR_Sensor()
upstairs_PIR = Dogsitter.PIR_Sensor()

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
upstairs_light.register(lights)

downstairs_light.register(downstairs_light)
downstairs_light.register(downstairs_relay)
downstairs_light.register(lights)

downstairs_PIR.register(trigger_LED)
upstairs_PIR.register(trigger_LED)

# Easy vars for the dog's position, on and off
upstairs = "upstairs"
downstairs = "downstairs"
on = "On"
off = "Off"

# If the switch is up, set oliveLocation to upstairs.
if GPIO.input(initial_location_switch):
    olive.location_in_house = upstairs
    print("Olive was upstairs when you left")
else:
    olive.location_in_house = downstairs
    print("Olive was downstairs when you left")


def main():
    # Pause for some amount of time to give us a chance to leave without triggering downstairs_PIR.
    time.sleep(startup_delay)
    Dogsitter.print_time("Starting Dogsitter now")
    try:
        while True:
            # Check to see if the sun is up or not.
            sun = ephem.Sun(where_am_I)
            sun_is_up = where_am_I.previous_rising(sun) > where_am_I.previous_setting(sun)

            # Do things to the lights if the sun went up or down
            if sun_is_up:
                # Sun's up
                if lights.state == on:  # If the sun is up and the lights are on, turn the lights off.
                    upstairs_light.dispatch(off, upstairs_light_name)
                    downstairs_light.dispatch(off, downstairs_light_name)
            else:
                # Sun's down
                if lights.state == off: # If all the lights are off, check where olive is and turn a light on in her location.
                    if olive.location_in_house == upstairs:
                        downstairs_light.dispatch(on, downstairs_light_name)
                    else:
                        upstairs_light.dispatch(on, upstairs_light_name)
                else:   # If the lights are on, make sure the light that is on is in Olive's location
                    if olive.location_in_house == upstairs:
                        if downstairs_light.state == on:
                            print("Since Olive is upstairs, turning off light downstairs")
                            downstairs_light.dispatch(off, downstairs_light_name)
                    if olive.location_in_house == downstairs:
                        if upstairs_light.state == on:
                            print("Looks like olive moved downstairs. Turning upstairs light off.")
                            upstairs_light.dispatch(off, upstairs_light_name)

            # Check PIR sensors
            if GPIO.input(downstairs_PIR_pin):  # Check for motion at the downstairs sensor
                downstairs_PIR.dispatch("Downstairs sensor triggered", downstairs)
                trigger_time = time.time()  # This will be used to time the elapsed time between sensor trigger events
                while time.time() < trigger_time + time_delay and not GPIO.input(upstairs_PIR):     # Keep an eye on the upstairs PIR
                    if GPIO(upstairs_PIR):
                        olive.location_in_house = upstairs
                        olive.trips_through_house += 1

            if GPIO.input(upstairs_PIR):    # This block of code works the same as the one above
                upstairs_PIR.dispatch("Upstairs sensor triggered", upstairs)
                trigger_time = time.time()
                while time.time() < trigger_time + time_delay and not GPIO.input(downstairs_PIR_pin):
                    if GPIO(downstairs_PIR_pin):
                        olive.location_in_house = downstairs
                        olive.trips_through_house += 1

            # Check sound sensor
            if GPIO.input(decibel_sensor):
                stereo.play_audio()

            # Check temp sensor
            # Use I2C to communicate with Arduino and get temp info, maybe?

            # Publish info to webpage?


    except KeyboardInterrupt:
        Dogsitter.Print_Time("Dogsitter has been stopped by user")
        upstairs_light.unregister(upstairs_light)
        upstairs_light.unregister(upstairs_relay)
        downstairs_light.unregister(downstairs_light)
        downstairs_light.unregister(downstairs_relay)
        GPIO.cleanup()
        exit()

    except:
        Dogsitter.Print_Time("An error has occurred and Dogsitter needs to quit")
        upstairs_light.unregister(upstairs_light)
        upstairs_light.unregister(upstairs_relay)
        downstairs_light.unregister(downstairs_light)
        downstairs_light.unregister(downstairs_relay)
        GPIO.cleanup()
        exit()


if __name__ == '__main__':
    main()
