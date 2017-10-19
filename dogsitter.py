import RPi.GPIO as GPIO
import subprocess
import time
import datetime
import ephem


class Box(object):
    def __init__(self):
        print("Box is on")

    class Trigger_LED(object):
        def __init__(self):
            print("We have a trigger LED")
            self.state = "Off"

    class Power_LED(object):
        def __init__(self):
            print("We have a power LED")
            self.state = "On"


class Dog(object):
    def __init__(self):
        print("Creating a dog")

        self.location_in_house = "downstairs"
        self.trips_through_house = 0


class Lights(object):
    def __init__(self):
        print("Lights object exists now")
        self.state = "Off"


class Light(object):
    def __init__(self, name):
        print("Making light object called", name)
        self.name = name
        self.state = "Off"
        self.observers = set()

    def register(self, relay):
        self.observers.add(relay)

    def unregister(self, relay):
        self.observers.discard(relay)

    def dispatch(self, message, sender):
        for observer in self.observers:
            observer.update(message, sender)

    def update(self, message, sender):
        if sender == self.name:
            if message == "Off":
                self.state = "Off"
            if message == "On":
                self.state = "On"
        else:
            if message == "Off":
                self.state = "On"
            if message == "On":
                self.state = "Off"


class Relay(object):
    def __init__(self, name, pin):
        self.name = name
        self.pin = pin
        print("Relay initialized with name", self.name)

    def update(self, message, sender):
        print("relay received update from", sender)
        if message == "Off":
            print("I just turned the light off")
            GPIO.output(pin, GPIO.LOW)
        if message == "On":
            print("I just turned the light on")
            GPIO.output(pin, GPIO.HIGH)


class Initial_Location_Switch(object):
    def __init__(self):
        print("Checking state of Initial Position Switch")


class Stereo(object):
    def __init__(self, filename):
        print("Making stereo object")
        self.state = "Off"
        self.filename = filename

    def play_audio(self):
        subprocess.call(['xdg-open', self.filename])


def PrintTime(aString):
    now = datetime.datetime.now()
    print(now, ":")
    print(aString)
