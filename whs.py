import RPi.GPIO as GPIO
from max1238 import Max1238
from time import time
from threading import Thread

# GPIO Pin Mapping
VALVE_PIN = 17

# ADC Channel Mapping
CH_HOT = 0
CH_COLD = 1
CH_FLOW = 2
CH_AMBIENT = 4

# ADC stuff
ADC_VREF = 4.096
ADC_MAX = 2**12

# Temprature Transmitters Range in Celsius
T_max = 150
T_min = -50

# Flowmeter Transmitter Range in g/min
Q_max = 10
Q_min = 0.2

# Init Stuff Here
GPIO.setmode(GPIO.BCM)

GPIO.setup(VALVE_PIN, GPIO.OUT, initial=GPIO.LOW)

# TODO: Display Stuff gotta ask nawaf
# GPIO.setup(21, GPIO.OUT)
# GPIO.setup(25, GPIO.OUT)

adc = Max1238()
adc.setup_adc()


def voltage_to_val(V_meas, max, min) -> float:
    R_shunt = 120
    I_loop = V_meas / R_shunt
    return ((I_loop - 4e-3) / (16e-3)) * (max - min) + min


def read_voltage(channel: int) -> float:
    value = adc.read_single(channel)
    if value is None:
        return -1
    return (value / ADC_MAX) * ADC_VREF


def draw_water(target_vol: float) -> None:
    if target_vol <= 0:
        print("Invalid Volume")
        return

    print(f"Drawing {target_vol:.2f} gallon(s)")

    volume = 0
    start_time = time()
    GPIO.output(VALVE_PIN, GPIO.HIGH)

    while volume < target_vol:
        elapsed = time() - start_time

        hot = voltage_to_val(read_voltage(CH_HOT), T_max, T_min)
        cold = voltage_to_val(read_voltage(CH_COLD), T_max, T_min)
        amb = voltage_to_val(read_voltage(CH_AMBIENT), T_max, T_min)
        volume = voltage_to_val(read_voltage(CH_FLOW), Q_max, Q_min)

        print(f"{hot:.2f} {cold:.2f} {amb:.2f} {volume:.2f}")
        if elapsed > 180:
            print("Timeout Error")
            break

    GPIO.output(VALVE_PIN, GPIO.LOW)
    print(f"Volume drawn: {volume:.2f} gallon(s)")


thread_draw = Thread(target=draw_water, args=[20])
