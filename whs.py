import RPi.GPIO as GPIO
from max1239 import Max1239

# Init Stuff Here

GPIO.setmode(GPIO.BCM)

# Valve Control
GPIO.setup(17, GPIO.OUT)

# TODO
# Display Stuff gotta ask nawaf
GPIO.setup(21, GPIO.OUT)
GPIO.setup(25, GPIO.OUT)

adc = Max1239()

# TODO
# write the control and logging logic here
