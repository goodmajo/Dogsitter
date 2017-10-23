import RPi.GPIO as GPIO
import pygame
import datetime
import time
import smtplib
from git import Repo

class Box(object):
    def __init__(self):
        print("Box is on")

    class Trigger_LED(object):
        def __init__(self, green_pin, blue_pin):
            print("We have a trigger LED")
            self.state = "Off"
            self.green_pin = green_pin
            self.blue_pin = blue_pin

        def update(self, message, sender):
            print(message)
            print("Trigger LED received update from", sender)
            if sender == "upstairs":
                print("Signal recieved from", sender)
                for i in range(1, 3):
                    GPIO.output(self.green_pin, GPIO.HIGH)
                    time.sleep(1.0)
                    GPIO.output(self.green_pin, GPIO.LOW)
                    time.sleep(1.0)
            if sender == "downstairs":
                print("Signal recieved from", sender)
                for i in range(1, 3):
                    GPIO.output(self.blue_pin, GPIO.HIGH)
                    time.sleep(1.0)
                    GPIO.output(self.blue_pin, GPIO.LOW)
                    time.sleep(1.0)

    class Power_LED(object):
        def __init__(self, pin):
            print("We have a power LED")
            self.state = "On"
            self.pin = pin
            GPIO.output(self.pin, GPIO.HIGH)


class Dog(object):
    def __init__(self):
        print("Creating a dog")

        self.location_in_house = "downstairs"
        self.trips_through_house = 0


class Lights(object):
    def __init__(self):
        print("Lights object exists now")
        self.state = "Off"
        self.on_location = ""
        self.upstairs_light = "Off"
        self.downstairs_light = "Off"

    def update(self, message, sender):
        print(message)
        print("Lights received update from", sender)
        if message == "On":
            if sender == "upstairs light":
                self.upstairs_light = "On"
                self.on_location = "upstairs"
            else:
                self.downstairs_light = "On"
                self.on_location = "downstairs"
        if message == "Off":
            if sender == "upstairs light":
                self.upstairs_light = "Off"
            else:
                self.downstairs_light = "Off"
        if self.downstairs_light == "On" or self.upstairs_light == "On":
            self.state = "On"
        if self.downstairs_light == "Off" and self.upstairs_light == "Off":
            self.state = "Off"
            self.on_location = ""


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
            GPIO.output(self.pin, GPIO.LOW)
        if message == "On":
            print("I just turned the light on")
            GPIO.output(self.pin, GPIO.HIGH)


class PIR_Sensor(object):
    def __init__(self, name="PIR"):
        self.name = name
        self.observers = set()

    def register(self, led):
        self.observers.add(led)

    def unregister(self, led):
        self.observers.discard(led)

    def dispatch(self, message, sender):
        for observer in self.observers:
            observer.update(message, sender)


class Initial_Location_Switch(object):
    def __init__(self):
        print("Checking state of Initial Position Switch")


class Stereo(object):
    def __init__(self, filename):
        print("Creating stereo object")
        self.state = "Off"
        self.filename = filename
        self.timer = time.time()

    def play_audio(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.filename)
        pygame.mixer.music.play()
        self.timer = time.time()
        self.state = "On"


def Print_Time(a_string):
    now = datetime.datetime.now()
    print(now, ":")
    print(a_string)


def Html_Author(temperature, a_dog, the_lights, a_stereo, off_message = "Spoiler: she's probably sleeping somewhere..."):
    # Make an html file with your variables nicely slipped into the body of the page.
    f = open('index.html', 'w')
    # Edit this HTML as you see fit. Make sure to change the picture filename.
    make_html = f"""
    <html>
    <head>
      <title>Where is My Dog Today?</title>
      <style>
      div.container {{
          width: 100%;
          border: 1px solid gray;
      }}

      header, footer {{
          padding: 1em;
          color: white;
          background-color: black;
          clear: left;
          text-align: center;
      }}

      nav {{
          float: left;
          max-width: 200px;
          margin: 0;
          padding: 1em;
      }}

      nav ul {{
          list-style-type: none;
          padding: 0;
      }}

      nav ul a {{
          text-decoration: none;
      }}

      article {{
          margin-left: 400px;
          border-left: 1px solid gray;
          padding: 1em;
          overflow: hidden;
      }}
      </style>
      </head>
      <body>

    <div class="flex-container">
    <header>
      <h1>Where is The Dog Today?</h1>
      <h9>{off_message}</h9>
    </header>

    <nav class="nav">
      <img src="DogPic.jpg" alt="Picture of the dog" width="337.5" height="450">
    </nav>

    <article class="article">
      <h1>Olive is:</h1>
        <p>{a_dog.location_in_house}</p>
      <h1>Trips up and down the stairs:</h1>
        <p>{a_dog.trips_through_house}</p>
      <h1>Temperature:</h1>
      <p>{temperature}° farenheit</p>

      <h1>White Noise Status:</h1>
      <p>{a_stereo.state}</p>

      <h1>Lights are:</h1>
      <p>{the_lights.state} {the_lights.on_location}</p>
    </article>
    </article>

    <footer>
    <a>Updated : {datetime.datetime.now()}</a>
    </footer>
    </div>
    </body>
    </html>
    """

    f.write(make_html)
    f.close()

    # Now do Git stuff to see the webpage update.
    # Remember, for this to work your page has to be hosted on github pages.
    repo_dir = ''
    repo = Repo(repo_dir)
    file_list = ['index.html']
    commit_message = 'Updating html'
    repo.index.add(file_list)
    repo.index.commit(commit_message)
    origin = repo.remote('origin')
    origin.push()


def Send_Mail(temperature, sound_level, a_stereo, the_lights, home_or_not = ""):
    mail_server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    mail_server.ehlo()

    email_sender = 'sender@gmail.com'
    email_password = 'p@ssword'
    email_receiver = 'receiver@gmail.com'
    email_subject = "Where is My Dog? - temperature is {} degrees.".format(temperature)

    if the_lights.state == "On":
        email_text = "Temperature = {0} degrees\nNoise level is {1} dB, Stereo is {2}.\nLights are on {3}.\nHave a " \
                     "good day!\n\nMessage sent:\n{4}.\n{5}\n".format(temperature, sound_level, a_stereo.state,
                                                                 the_lights.on_location, datetime.datetime.now(), home_or_not)
    else:
        email_text = "Temperature = {0} degrees\nNoise level is {1} dB, Stereo is {2}.\nLights are off.\nHave a " \
                     "good day!\n\nMessage sent:\n{3}.\n{4}".format(temperature, sound_level, a_stereo.state,
                                                                 datetime.datetime.now(), home_or_not)

    email_message = 'Subject: {}\n\n{}'.format(email_subject, email_text)

    mail_server.login(email_sender, email_password)
    mail_server.sendmail(email_sender, email_receiver, email_message)
    mail_server.close()

def Quit_Dogsitter(temperature, sound_level, a_dog, the_lights, a_stereo, message):
    Print_Time(message)
    email_message = message
    Html_Author(temperature, a_dog, the_lights, a_stereo, "OFFLINE")
    Send_Mail(temperature, sound_level, a_stereo, the_lights, email_message)
    GPIO.cleanup()
    return