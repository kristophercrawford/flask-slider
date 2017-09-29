from flask import Flask, flash, render_template, request, redirect, jsonify, url_for
from time import sleep
import RPi.GPIO as GPIO

#These are global GPIO variables the PI uses to interface with the drv8825
DIR = 8  # Direction GPIO Pin
STEP = 7  # Step GPIO Pin
CW = 1  # Clockwise Rotation
CCW = 0  # Counterclockwise Rotation
SPR = 48  # Steps per Revolution (360 / 7.5)
dir_input = 0

#Function to move slider
def slider_move():
    global DIR, STEP, SPR, dir_input

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DIR, GPIO.OUT)
    GPIO.setup(STEP, GPIO.OUT)
    GPIO.output(DIR, dir_input)

    step_count = SPR
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
    print(dir_input)
    for x in range(step_count):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

    GPIO.cleanup()


app = Flask(__name__)
app.secret_key = 'some_secret'


@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == "POST":
        home_dict = request.form
        print(home_dict)
        #ImmutableMultiDict([('navbtn', 'nav1')])
        if home_dict['navbtn'] == "nav1":
            return redirect(url_for('linear'))
        elif home_dict['navbtn'] == "nav2":
            return redirect(url_for('pan'))
    return render_template('home.html')


@app.route('/linear', methods=['GET', 'POST'])
def linear():
    if request.method == "POST":
        linear_dict = request.form
        print(linear_dict)
        #flash(u'This is an error', 'error')
        #ImmutableMultiDict([('slider_speed', '1/16'), ('steps', '45'), ('direction', '0')])
        flash(u'Data has been submitted successfully', 'success')
        step_input = int(linear_dict['steps'])
        dir_input = int(linear_dict['direction'])
        for x in range(step_input):
            slider_move()
            sleep(1)

    return render_template("linear.html")


@app.route('/pan', methods=['GET', 'POST'])
def pan():
    if request.method == "POST":
        pan_dict = request.form
        print(pan_dict)
        #ImmutableMultiDict([('pan_direction', 'convex'), ('steps', '128'), ('direction', 'l2r'), ('slider_speed', '1/16')])

    return render_template('pan.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
