from flask import Flask, flash, render_template, request, redirect, jsonify, url_for
from time import sleep
import RPi.GPIO as GPIO
import threading
import _thread
import os

# These are GPIO variables the PI uses to interface with the drv8825
dir_pin = 5  # Direction GPIO Pin
step_pin = 6  # Step GPIO Pin
sleep_pin = 11 # Enable/disable controller
# These are used to interact with the camera
expose_pin = 17  # red / green
focus_pin = 27  # orage / white
# These are used to check the micro switches
sw1 = 3 # Pin used for limit switch
sw2 = 4 # Pin used for limit switch
garbage = 0


app = Flask(__name__)
app.secret_key = 'some_secret'

# Class to enable threading
class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)

    def run(self):
        self._target(*self._args)

# Function to calibrate slider position left to right
def start_calibration(garbage):
    GPIO.setmode(GPIO.BCM) # Set board mode to Broadcom standard
    GPIO.setup(dir_pin, GPIO.OUT) # Setup direction pin for drv8825 as output
    GPIO.setup(step_pin, GPIO.OUT) # Setup step pin for drv8825 as output
    GPIO.setup(sleep_pin, GPIO.OUT) # Setup sleep pin for drv8825 as output
    GPIO.setup(sw1, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Read limit switch status
    GPIO.setup(sw2, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Read limit switch status
    GPIO.output(sleep_pin, True) # Set to high to turn on controller

    left_counter = 0 # Number of steps needed to move from current position to left switch
    flag = False
    global track_len
    track_len = 0 # Number of steps needed to fully traverse the track
    delay = .0005 # Short time delay between on/off cycles of the stepper driver
    MODE = (13, 19, 26) # Set resolution of the stepper driver through these three pins
    GPIO.setup(MODE, GPIO.OUT)
    RESOLUTION = {'Full': (0, 0, 0),
                  'Half': (1, 0, 0),
                  '1/4': (0, 1, 0),
                  '1/8': (1, 1, 0),
                  '1/16': (0, 0, 1),
                  '1/32': (1, 0, 1)} # Various step modes pulled from https://www.pololu.com/product/2133
    GPIO.output(MODE, RESOLUTION['1/4']) # Hard-code a resolution of 1/16 speed.


    while True:
        sw1_state = GPIO.input(sw1)  # Define variable to hold state of left limit switch
        sw2_state = GPIO.input(sw2)  # Define variable to hold state of right limit switch
        if (sw1_state and sw2_state) and not flag: # Switch defaults to True
            GPIO.output(dir_pin, 1)
            GPIO.output(step_pin, GPIO.HIGH)
            sleep(delay)
            GPIO.output(step_pin, GPIO.LOW)
            sleep(delay)
            left_counter += 1
            continue
        elif not sw1_state and not flag:
            print('Left switch triggered')
            flag = True
            continue
        elif sw2_state and flag:
            GPIO.output(dir_pin, 0)
            GPIO.output(step_pin, GPIO.HIGH)
            sleep(delay)
            GPIO.output(step_pin, GPIO.LOW)
            sleep(delay)
            track_len += 1
        elif not sw2_state:
            print('Right switch triggered, move to start position')
            GPIO.output(dir_pin, 1)
            for x in range(track_len - 100):
                GPIO.output(step_pin, GPIO.HIGH)
                sleep(delay)
                GPIO.output(step_pin, GPIO.LOW)
                sleep(delay)
            GPIO.cleanup()
            break


# Function to move slider
def slider_move(u_input):

    # print(u_input)
    # ImmutableMultiDict([('direction', '0'), ('shots', '10'), ('time_delay', '10')])

    # Break passed json data into seperate variables
    dir_input = int(u_input['direction'])
    shot_input = int(u_input['shots'])
    time_input = int(u_input['time_delay'])

    GPIO.setmode(GPIO.BCM) # Set board mode to Broadcom standard
    GPIO.setup(dir_pin, GPIO.OUT) # Setup direction pin for drv8825 as output
    GPIO.setup(step_pin, GPIO.OUT) # Setup step pin for drv8825 as output
    GPIO.setup(sleep_pin, GPIO.OUT) # Setup sleep pin for drv8825 as output
    GPIO.output(dir_pin, dir_input) # Set motor output direction
    GPIO.output(sleep_pin, True) # Set to high to turn on controller

    step_count = int((track_len - 200) / int(shot_input))
    delay = .0005 # Short time delay between on/off cycles of the stepper driver
    MODE = (13, 19, 26) # Set resolution of the stepper driver through these three pins
    GPIO.setup(MODE, GPIO.OUT)
    RESOLUTION = {'Full': (0, 0, 0),
                  'Half': (1, 0, 0),
                  '1/4': (0, 1, 0),
                  '1/8': (1, 1, 0),
                  '1/16': (0, 0, 1),
                  '1/32': (1, 0, 1)} # Various step modes pulled from https://www.pololu.com/product/2133
    GPIO.output(MODE, RESOLUTION['1/4']) # Hard-code a resolution of 1/16 speed.


    for x in range(shot_input):
        for y in range(step_count):
            GPIO.output(step_pin, GPIO.HIGH)
            sleep(delay)
            GPIO.output(step_pin, GPIO.LOW)
            sleep(delay)
        sleep(time_input)

    GPIO.cleanup() # cleanup in-use pins


def take_picture():
    # sub function to fire remote shutter
    # connect 2N2222 transistor base to expose and focus pins defined below through a 10k resistor
    # connect emitter pin to board ground and common from remote shutter
    # connect collector pin to expose/focus wires on remote shutter
    # brown = common

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(expose, GPIO.OUT)
    GPIO.setup(focus, GPIO.OUT)

    GPIO.output(focus_pin, True) # set focus pin to to high to focus and start light metering
    sleep(3) # wait three seconds for camera to come out of sleep
    GPIO.output(expose_pin, True) # set expose pin to high to fire shutter
    sleep(.1) # delay time between setting pins to low
    GPIO.output(expose_pin, False) # set expose pin to low
    GPIO.output(focus_pin, False) # set focus pin to low
    GPIO.cleanup() # cleanup in-use pins


@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == "POST":
        home_dict = request.form
        # print(home_dict)
        # ImmutableMultiDict([('navbtn', 'nav1')])
        if home_dict['navbtn'] == "nav1":
            return redirect(url_for('linear'))
        elif home_dict['navbtn'] == "nav2":
            return redirect(url_for('pan'))
    return render_template('home.html')


@app.route('/calibrate', methods=['GET', 'POST'])
def calibrate():
    if request.method == "POST":
        print(request.form)
        # ImmutableMultiDict([('id', 'begin')])
        calibrate_dict = request.form
        if calibrate_dict['id'] == "begin":
            _thread.start_new_thread(start_calibration, (garbage,))

    return render_template('calibrate.html')


@app.route('/linear')
def linear():
    if request.method == "GET":
        return render_template("linear.html")


@app.route('/postdata', methods=['POST'])
def postdata():
    u_input = request.form
    print(u_input)
    _thread.start_new_thread(slider_move, (u_input,))
    return url_for('homepage')


@app.route('/status')
def status():
    return render_template('status.html', track_len_var=track_len)


@app.route('/pan', methods=['GET', 'POST'])
def pan():
    if request.method == "POST":
        pan_dict = request.form
        # print(pan_dict)
        # ImmutableMultiDict([('pan_direction', 'convex'), ('steps', '128'), ('direction', 'l2r'), ('slider_speed', '1/16')])
        take_picture()

    return render_template('pan.html')


@app.route('/shutdown_pi', methods=['GET','POST'])
def shutdown():
    os.system("sudo shutdown +1")
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0')
