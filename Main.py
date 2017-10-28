import RPi.GPIO as GPIO
import Dogsitter
import time
import datetime
import ephem
import serial
import re


# Pins get declared here.
downstairs_PIR_pin = 19
upstairs_PIR = 26
upstairs_relay_pin = 20
downstairs_relay_pin = 21

initial_location_switch_pin = 23
off_button_pin = 24

power_LED_pin = 17
green_trigger_LED_pin = 27
blue_trigger_LED_pin = 22


# Set up GPIOs.
GPIO.setmode(GPIO.BCM)

GPIO.setup(downstairs_PIR_pin, GPIO.IN)
GPIO.setup(upstairs_PIR, GPIO.IN)
GPIO.setup(upstairs_relay_pin, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(downstairs_relay_pin, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)

GPIO.setup(initial_location_switch_pin, GPIO.IN)
GPIO.setup(off_button_pin, GPIO.IN)

GPIO.setup(power_LED_pin, GPIO.OUT)
GPIO.setup(green_trigger_LED_pin, GPIO.OUT)
GPIO.setup(blue_trigger_LED_pin, GPIO.OUT)

# Sound file name
sound_filename = "whitenoise.wav"

# This variable will control how many seconds we will wait for the second sensor to trigger once the first one
# detects movement.
time_delay = 10.0

# This variable determines how long we want to wait before the program starts running
startup_delay = 1.0

# Set acceptable sound level before stereo is switched on
sound_threshold = 100

# We need a temperature threshold, too
temp_threshold = 60

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

# When was the last email sent? This var will keep track of that
last_email = time.time()

# Serial stuff goes here
serial_port = "/dev/ttyACM0"
my_baud = 9600
arduino_serial = serial.Serial(serial_port, my_baud)

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
    Dogsitter.Print_Time("Starting Dogsitter now")
    temperature = 70
    sound_level = 50
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
                if lights.state == off:  # If all the lights are off, check where olive is and turn a light on in her location.
                    if olive.location_in_house == upstairs:
                        downstairs_light.dispatch(on, downstairs_light_name)
                    else:
                        upstairs_light.dispatch(on, upstairs_light_name)
                else:  # If the lights are on, make sure the light that is on is in Olive's location
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
                while time.time() < trigger_time + time_delay and not GPIO.input(
                        upstairs_PIR):  # Keep an eye on the upstairs PIR
                    if GPIO(upstairs_PIR):
                        olive.location_in_house = upstairs
                        olive.trips_through_house += 1

            if GPIO.input(upstairs_PIR):  # This conditional works the same as the one above
                upstairs_PIR.dispatch("Upstairs sensor triggered", upstairs)
                trigger_time = time.time()
                while time.time() < trigger_time + time_delay and not GPIO.input(downstairs_PIR_pin):
                    if GPIO(downstairs_PIR_pin):
                        olive.location_in_house = downstairs
                        olive.trips_through_house += 1

            # Check temp and sound info from Arduino serial The code below reads in the serial info, finds the
            # numbers, eliminates all other characters, and stores the numbers in a list.
            # Serial should look like this: "Temperature = nx.yz, Sound Level = ab.cd,"
            read_serial = arduino_serial.readline().decode('utf-8')
            split_serial = re.findall(r'\b\d+\b', read_serial)

            # This bit turns the list members back into floats, like we need.
            temperature = float(split_serial[0])
            sound_level = float(split_serial[2])

            if sound_level > sound_threshold and stereo.state is off:
                stereo.play_audio()

            # If an hour has gone by, the white noise has stopped.
            if stereo.state is on and time.time() > stereo.timer + 3600:
                stereo.state = off

            # If it's really cold, send an email letting us know. Only one email per hour, please!
            if temperature > temp_threshold and time.time() > last_email + 3600:
                Dogsitter.Send_Mail(temperature, sound_level, stereo, lights)
                last_email = time.time()

            time_right_now = datetime.datetime.now()
            if time_right_now.minute % 15 is 0:
                Dogsitter.Html_Author(temperature, olive, lights, stereo)

            if GPIO.input(off_button_pin):
                message = "This message is being sent because someone just turned off the Dogsitter"
                Dogsitter.Quit_Dogsitter(temperature, sound_level, olive, lights, stereo, message)
                exit()


    except KeyboardInterrupt:
        message = "Dogsitter has been stopped by user"
        Dogsitter.Quit_Dogsitter(temperature, sound_level, olive, lights, stereo, message)
        exit()

    except:
        message = "Dogsitter has encountered an error and needed to quit."
        Dogsitter.Quit_Dogsitter(temperature, sound_level, olive, lights, stereo, message)
        exit()


if __name__ == '__main__':
    main()
