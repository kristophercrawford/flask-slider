from flask import Flask, flash, render_template, request, redirect, jsonify, url_for
from time import sleep
import RPi.GPIO as GPIO
import threading
import _thread
import os

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
    # ImmutableMultiDict([('direction', '0'), ('shots', '10'), ('time_delay', '10')])

    # Break passed json data into seperate variables
    dir_input = int(u_input['direction'])
    shot_input = int(u_input['shots'])
    time_input = int(u_input['time_delay'])

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(dir_pin, GPIO.OUT)
    GPIO.setup(step_pin, GPIO.OUT)
    GPIO.output(dir_pin, dir_input)

    step_count = int(48 * (800 / int(shot_input)))
    delay = .0005

    MODE = (14, 15, 18)
    GPIO.setup(MODE, GPIO.OUT)
    RESOLUTION = {'Full': (0, 0, 0),
                  'Half': (1, 0, 0),
                  '1/4': (0, 1, 0),
                  '1/8': (1, 1, 0),
                  '1/16': (0, 0, 1),
                  '1/32': (1, 0, 1)}
    GPIO.output(MODE, RESOLUTION['1/16'])


    for x in range(shot_input):
        for y in range(step_count):
            GPIO.output(step_pin, GPIO.HIGH)
            sleep(delay)
            GPIO.output(step_pin, GPIO.LOW)
            sleep(delay)
        sleep(time_input)

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
    print(u_input)
    _thread.start_new_thread(slider_move, (u_input,))
    return url_for('homepage')

@app.route('/status')
def status():
    return render_template('status.html')

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
