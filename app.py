from flask import Flask, flash, render_template, request, redirect, jsonify, url_for
from time import sleep
import RPi.GPIO as GPIO
import threading
import _thread

# These are GPIO variables the PI uses to interface with the drv8825
dir_pin = 8  # Direction GPIO Pin
step_pin = 7  # Step GPIO Pin

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

# Function to move slider
def slider_move(u_input):

    # print(u_input)
    # ImmutableMultiDict([('slider_speed', '1/16'), ('direction', '0'), ('steps', '10')])

    # Break passed json data into seperate variables
    slider_speed = u_input['slider_speed']
    step_input = int(u_input['steps'])
    dir_input = int(u_input['direction'])

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(dir_pin, GPIO.OUT)
    GPIO.setup(step_pin, GPIO.OUT)
    GPIO.output(dir_pin, dir_input)

    step_count = 48 # Steps per Revolution (360 / 7.5)
    delay = .0005

    MODE = (14, 15, 18)
    GPIO.setup(MODE, GPIO.OUT)
    RESOLUTION = {'full': (0, 0, 0),
                  'half': (1, 0, 0),
                  '1/4': (0, 1, 0),
                  '1/8': (1, 1, 0),
                  '1/16': (0, 0, 1),
                  '1/32': (1, 0, 1)}
    GPIO.output(MODE, RESOLUTION[slider_speed])
    for x in range(step_input):
        for x in range(step_count):
            GPIO.output(step_pin, GPIO.HIGH)
            sleep(delay)
            GPIO.output(step_pin, GPIO.LOW)
            sleep(delay)

    GPIO.cleanup()


def take_picture():

    # sleeve = ground red
    expose = 21 # black
    focus = 20 # white

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(expose, GPIO.OUT)
    GPIO.setup(focus, GPIO.OUT)
    GPIO.output(focus, 1)
    GPIO.output(expose, 1)
    sleep(5)
    GPIO.cleanup()


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


@app.route('/linear')
def linear():
    if request.method == "GET":
        return render_template("linear.html")

@app.route('/postdata', methods=['POST'])
def postdata():
    u_input = request.form
    _thread.start_new_thread(slider_move, (u_input,))
    return url_for('homepage')

@app.route('/pan', methods=['GET', 'POST'])
def pan():
    if request.method == "POST":
        pan_dict = request.form
        # print(pan_dict)
        # ImmutableMultiDict([('pan_direction', 'convex'), ('steps', '128'), ('direction', 'l2r'), ('slider_speed', '1/16')])
        take_picture()

    return render_template('pan.html')


if __name__ == '__main__':
    app.run(debug=True, threaded=True, host='0.0.0.0')
