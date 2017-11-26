#!/usr/bin/python

# super-pi-cheerlights: super-pi-cheerlights.py: runs as a daemon acting as a sunset timer and
#                                                remote control for LED Tape and other lights.
# Copyright (C) 2017 Tugzrida (github.com/Tugzrida)
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from os import system, stat, path
from json import loads, dumps
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import timezone
from time import sleep
import RPi.GPIO as GPIO
from bottle import route, response, static_file, run
from thread import start_new_thread
from requests import get

# Variables
redVal = grnVal = bluVal = prevR = prevG = prevB = tapeMode = fairyMode = jsonMod = 0
# red/grn/bluVal - keeps track of current value during crossfade
# prevR/G/B - keeps track of last set colour for crossfade
# tape/fairyMode - see below
# jsonMod - keeps track of sunset.json modification time to detect changes

tapeColour = [0, 0, 0] # keeps track of currently set tape colour for web ui
fairyState = tapeLock = False
# fairyState - keeps track of current fairy lights state for web ui
# tapeLock - prevent tape colour from changing when displaying status signals

###################################
# Settings specific to each setup #
###################################
# See further settings in getsun.py(location, timezone, off time and manual overrides) and www/index.html(display led tape and/or fairy lights controls)

# Use Bottle's inbuilt server for static files
builtin_server=True # True or False

# Maximum RGB values out of 100. Use for calibrating white balance.
maxred = 100
maxgrn = 90
maxblu = 70

# Individual cheerlights colour definitions (RGB 0-100). Can be used for further calibration.
rgb_list = {
    "red": [100, 0, 0],
    "green": [0, 100, 0],
    "blue": [0, 0, 100],
    "cyan": [0, 100, 100],
    "purple": [43.1, 0, 50.2],
    "magenta": [100, 0, 58.8],
    "yellow": [100, 58.8, 0],
    "orange": [100, 7.8, 0],
    "warmwhite": [100, 33.3, 13.7],
    "pink": [100, 19.6, 19.6],
    "white": [100, 100, 100]
}
###################################

rgb_list["oldlace"] = rgb_list["warmwhite"] # Take care of warmwhite/oldlace duplication

# GPIO init
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)
GPIO.setup(12, GPIO.OUT)

red = GPIO.PWM(11, 100) #
grn = GPIO.PWM(13, 100) # PWM instances for R,G,B
blu = GPIO.PWM(15, 100) #

red.start(0)
grn.start(0)
blu.start(0)

# Modes(tapeMode and fairyMode):
#   | LED Tape                         | Fairy Lights
# 0 | full auto - cheerlights & timer  | full auto - timer
# 1 | semi auto - cheerlights no timer | 
# 2 | manual    - set colour no timer  | manual    - set state no timer

# Pins:
# 9:  - to LED Tape
# 11: + Red to LED Tape
# 13: + Green to LED Tape
# 15: + Blue to LED Tape
# 12: + to Fairy Lights
# 14: - to Fairy Lights

# Simple interpolation function for white balance
def interp(a, b, c, d, e):
    return float(d + float(e - d) * float(float(a - b) / float(c - b)))

# Fancy fader to fade red, green and blue simultaneously, adapted from https://www.arduino.cc/en/Tutorial/ColorCrossfader

# The program works like this:
# Imagine a crossfade that moves the red LED from 0-10, 
#   the green from 0-5, and the blue from 10-7, in
#   ten steps.
#   We'd want to count the 10 steps and increase or 
#   decrease colour values in evenly stepped increments.
#   Imagine a + indicates raising a value by 1, and a -
#   equals lowering it. Our 10 step fade would look like:
# 
#   1 2 3 4 5 6 7 8 9 10
# R + + + + + + + + + +
# G   +   +   +   +   +
# B     -     -     -
# 
# The red rises from 0 to 10 in ten steps, the green from 
# 0-5 in 5 steps, and the blue falls from 10 to 7 in three steps.
# 
# In the real program, the colour values are 
# 0-100 values, and there are 400 steps (100*4).

# To figure out how big a step there should be between one up- or
# down-tick of one of the LED values, we call calculateStep(), 
# which calculates the absolute gap between the start and end values, 
# and then divides that gap by 400 to determine the size of the step  
# between adjustments in the value.

def calculateStep(prevValue, endValue):
    step = endValue - prevValue
    if step: #If non-zero
        step = 400 / step
    return step

# The next function is calculateVal. When the loop value, i,
# reaches the step size appropriate for one of the
# colours, it increases or decreases the value of that colour by 1. 
# (R, G, and B are each calculated separately.)
def calculateVal(step, val, i):
    if (step) and ((i % step) == 0): # If step is non-zero and its time to change a value
        if step > 0:
            val += 1
        elif step < 0:
            val -= 1
    
    # Ensure value remains between 0 & 100
    if val > 100:
        val = 100
    elif val < 0:
        val = 0
    
    return val

# crossFade() loops 400 times, checking to see if  
# the value needs to be updated each time, then writing
# the colour values to the correct pins.
def crossFade(colour):
    if not tapeLock:
        global prevR, prevG, prevB, redVal, grnVal, bluVal
        R = colour[0]
        G = colour[1]
        B = colour[2]
        
        stepR = calculateStep(prevR, R)
        stepG = calculateStep(prevG, G)
        stepB = calculateStep(prevB, B)
        
        for i in range(0, 401):
            redVal = calculateVal(stepR, redVal, i)
            grnVal = calculateVal(stepG, grnVal, i)
            bluVal = calculateVal(stepB, bluVal, i)
            
            # write changes, taking into account white balance
            red.ChangeDutyCycle(interp(redVal, 0, 100, 0, maxred))
            grn.ChangeDutyCycle(interp(grnVal, 0, 100, 0, maxgrn))
            blu.ChangeDutyCycle(interp(bluVal, 0, 100, 0, maxblu))
            
            sleep(0.003)
            
        # Save final values for next time crossFade is called
        prevR = redVal
        prevG = grnVal
        prevB = bluVal

# Bottle web ui stuff
@route('/do/set/fairyMode/<n:int>') # for setting fairyMode
def callback(n):
    global fairyMode
    if (n == 0) or (n == 2):
        fairyMode = n
        response.status = 200
        return "fairyMode set"
    else:
        response.status = 400
        return "Bad Request: fairyMode must be 0 or 2"


@route('/do/set/tapeMode/<n:int>') # for setting tapeMode
def callback(n):
    global tapeMode
    if (n == 0) or (n == 1) or (n == 2):
        tapeMode = n
        response.status = 200
        return "tapeMode set"
    else:
        response.status = 400
        return "Bad Request: tapeMode must be 0, 1 or 2"
    
@route('/do/set/tapeColour/<r:int>/<g:int>/<b:int>') # for setting tapeColour
def callback(r, g, b):
    global tapeColour
    if tapeMode == 2:
        if (0 <= r <= 100) and (0 <= g <= 100) and (0 <= b <= 100):
            tapeColour = [r, g, b]
            start_new_thread(crossFade, ([r, g, b], )) # doing this in a new thread may be messyish, but means that the http request doesn't hang
            response.status = 200
            return "tapeColour set"
        else:
            response.status = 400
            return "Bad Request: tapeColour must be r/g/b values between 0-100"
    else:
        response.status = 409
        return "Conflict: tapeMode must be 2(manual) for colour to be manually set"

@route('/do/set/fairyState/<n>') # for setting fairyState
def callback(n):
    global fairyState
    if fairyMode == 2:
        if n == "True":
            fairyState = True
            GPIO.output(12, True)
            response.status = 200
            return "fairyState set"
        elif n == "False":
            fairyState = False
            GPIO.output(12, False)
            response.status = 200
            return "fairyState set"
        else:
            response.status = 400
            return "Bad Request: fairyState must be True or False"
    else:
        response.status = 409
        return "Conflict: fairyMode must be 2(manual) for state to be manually set"

@route('/do/shutdown') # for shutting down Pi
def callback():
    global tapeLock
    response.status = 200
    yield "Shutting down Pi..."
    tapeLock = True
    # show "shutdown" by flashing red twice
    red.ChangeDutyCycle(0)
    grn.ChangeDutyCycle(0)
    blu.ChangeDutyCycle(0)
    sleep(0.3)
    red.ChangeDutyCycle(75)
    sleep(0.3)
    red.ChangeDutyCycle(0)
    sleep(0.3)
    red.ChangeDutyCycle(75)
    system('sudo shutdown now') # this takes advantage of Pi's not needing a password for sudo by default. If you've changed this, shutdown from the web ui won't work

@route('/do/reloadsun') # for manually reloading sunset details from API
def callback():
    response.status = 200
    start_new_thread(system, (path.join(path.dirname(path.abspath(__file__)), 'getsun.py'), )) # again, doing this in a new thread may be messyish, but means that the http request doesn't hang
    return "Reloading sun times"

if builtin_server:
    @route('/do/get') # requested every few seconds to get state of system
    def callback():
        response.status = 200
        return {"tapeMode": tapeMode, "fairyMode": fairyMode, "tapeColour": tapeColour, "fairyState": fairyState}
    
    @route('/static/<filepath:path>') # handle static files
    def callback(filepath):
        response.status = 200
        return static_file(filepath, root=path.join(path.dirname(path.abspath(__file__)), 'www/'))
    
    @route('/') # handle landing page
    def callback():
        response.status = 200
        return static_file("index.html", root=path.join(path.dirname(path.abspath(__file__)), 'www/'))

def start_bottle():
    if builtin_server:
        run(host='0.0.0.0', port=80)
    else:
        run(host='127.0.0.1', port=8080)

start_new_thread(start_bottle, ()) # start bottle server

# show "ready" by fading up and down
crossFade([100, 100, 100])
print("Initialised")
crossFade([0, 0, 0])

# main loop
while True:

    # check if sunset.json modified
    if stat(path.join(path.dirname(path.abspath(__file__)), 'sunset.json')).st_mtime != jsonMod:
        print("sunset.json changed. Reloading...")
        f = open(path.join(path.dirname(path.abspath(__file__)), 'sunset.json'), 'r')
        sun = loads(f.read())
        f.close()
        sunset = parse(sun["sunset"]) # sunset time, earlier than twilight
        twilight = parse(sun["twilight"]) # end of civil twilight, sun is more than 6deg below horizon, later than sunset
        twilightd = timedelta(seconds=sun["twilightdur"]) # time from sunset - end of civil twilight
        off = parse(sun["off"]) # time for lights to turn off, change in getsun.py
        timeZone = sun["timezone"]
        jsonMod = stat(path.join(path.dirname(path.abspath(__file__)), 'sunset.json')).st_mtime
        # show "reloaded" by flashing green twice
        tapeLock = True
        red.ChangeDutyCycle(0)
        grn.ChangeDutyCycle(0)
        blu.ChangeDutyCycle(0)
        sleep(0.3)
        grn.ChangeDutyCycle(25)
        sleep(0.3)
        grn.ChangeDutyCycle(0)
        sleep(0.3)
        grn.ChangeDutyCycle(25)
        sleep(0.3)
        grn.ChangeDutyCycle(0)
        tapeLock = False
    
    now = datetime.now(timezone(timeZone))
    
    # True if lights should run in full automatic mode
    tapeRun = (tapeMode == 0 and now >= sunset and now <= off)
    fairyRun = (fairyMode == 0 and now >= twilight and now <= off)
    
    # LED tape to display cheerlights
    if (tapeRun) or (tapeMode == 1):
        try:
            clcolour = rgb_list[get("https://api.thingspeak.com/channels/1417/field/1/last.txt").text][:] # get colour
            
            # If between sunset and end of civil twilight, reduce brightness proportional to time between the two
            if tapeMode == 0 and now >= sunset and now <= twilight:
                ratio = float((now-sunset).seconds)/twilightd.seconds
                for i in range(0,3):
                    clcolour[i] = clcolour[i] * ratio
            
            tapeColour = clcolour # update web ui colour
            crossFade(clcolour) # fade to new colour
        except:
            print("Connection error. Leaving tape as is.")
    
    # LED tape to be off
    if (not tapeRun) and (tapeMode == 0):
        tapeColour = [0, 0, 0] # update web ui colour
        crossFade([0, 0, 0]) # fade to new colour
    
    # fairy lights to be on
    if fairyRun:
        fairyState = True # update web ui state
        GPIO.output(12, True) # turn on power switch tail
    
    # fairy lights to be off
    if (not fairyRun) and (fairyMode == 0):
        fairyState = False # update web ui state
        GPIO.output(12, False) # turn off power switch tail
    
    if not builtin_server:
        f = open(path.join(path.dirname(path.abspath(__file__)), 'www/get.json'), 'w')
        f.write(dumps({"tapeMode": tapeMode, "fairyMode": fairyMode, "tapeColour": tapeColour, "fairyState": fairyState}))
        f.close()
    
    sleep(3)
