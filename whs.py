#!/usr/bin/env python3
import atexit
import signal
import sys
import time

import RPi.GPIO as GPIO
from max1238 import Max1238

# GPIO Pins
VALVE_PIN = 17

# MAX1238 channels
CH_HOT = 0
CH_COLD = 1
CH_FLOW = 2
CH_AMBIENT = 4

# ADC config
ADC_VREF = 4.096
ADC_MAX = (2**12) - 1


R_SHUNT_OHMS = 120.0

# Temperature transmitters C)
T_MAX_C = 150.0
T_MIN_C = -50.0

# Flow transmitter (GPM)
Q_MAX_GPM = 10.0
Q_MIN_GPM = 0.2

# Fail-safe configuration
MAX_RUN_MINUTES = 5.0
MIN_FLOW_GPM = 0.05
LOW_FLOW_TIMEOUT_S = 20.0
PRINT_PERIOD_S = 0.5

# Init
GPIO.setmode(GPIO.BCM)
GPIO.setup(VALVE_PIN, GPIO.OUT, initial=GPIO.LOW)

adc = Max1238()
adc.setup_adc()


def _fail_safe_close():
    try:
        GPIO.output(VALVE_PIN, GPIO.LOW)
    except Exception:
        pass


atexit.register(_fail_safe_close)


def _signal_handler(signum, frame):
    print(f"\n[!] Caught signal {signum}. Closing valve and exiting.")
    _fail_safe_close()
    sys.exit(1)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def _raw_to_voltage(raw: int) -> float:
    if raw is None:
        return float("nan")
    return (float(raw) / ADC_MAX) * ADC_VREF


def _volt_to_span(val_v: float, span_max: float, span_min: float) -> float:
    if val_v != val_v:
        return float("nan")

    i_loop = val_v / R_SHUNT_OHMS
    if i_loop < 0:
        i_loop = 0.0

    norm = (i_loop - 4e-3) / 16e-3
    return (norm * (span_max - span_min)) + span_min


def read_voltage(channel: int) -> float:
    raw = adc.read_single(channel)
    return _raw_to_voltage(raw)


def read_temps() -> dict:
    return {
        "Hot": _volt_to_span(read_voltage(CH_HOT), T_MAX_C, T_MIN_C),
        "Cold": _volt_to_span(read_voltage(CH_COLD), T_MAX_C, T_MIN_C),
        "Ambient": _volt_to_span(read_voltage(CH_AMBIENT), T_MAX_C, T_MIN_C),
    }


def read_flow_gpm() -> float:
    return _volt_to_span(read_voltage(CH_FLOW), Q_MAX_GPM, Q_MIN_GPM)


def draw_water(target_vol_gal: float) -> float:
    if target_vol_gal is None or target_vol_gal <= 0:
        print("Invalid target volume.")
        return 0.0

    print(f"Target: {target_vol_gal:.3f} gal")

    vol_gal = 0.0
    start = time.monotonic()
    last_log = start
    low_flow_start = None

    # Open valve
    GPIO.output(VALVE_PIN, GPIO.HIGH)

    try:
        t_prev = time.monotonic()
        while vol_gal < target_vol_gal:
            now = time.monotonic()
            dt = now - t_prev
            t_prev = now

            if (now - start) > (MAX_RUN_MINUTES * 60.0):
                print("[!] Timeout reached. Stopping.")
                break

            temps = read_temps()
            flow = read_flow_gpm()

            if any(v != v for v in temps.values()) or (flow != flow):
                print("[!] Sensor read error (NaN). Stopping.")
                break

            vol_gal += max(flow, 0.0) * (dt / 60.0)

            if flow < MIN_FLOW_GPM:
                if low_flow_start is None:
                    low_flow_start = now
                elif (now - low_flow_start) >= LOW_FLOW_TIMEOUT_S:
                    print("[!] Low flow persists. Stopping.")
                    break
            else:
                low_flow_start = None

            if (now - last_log) >= PRINT_PERIOD_S:
                print(
                    f"T_hot={temps['Hot']:.1f} C  "
                    f"T_cold={temps['Cold']:.1f} C  "
                    f"T_amb={temps['Ambient']:.1f} C  "
                    f"Flow={flow:.2f} gpm  "
                    f"Vol={vol_gal:.3f} gal"
                )
                last_log = now

            time.sleep(0.05)

    except Exception as e:
        print(f"[!] Exception: {e}")
    finally:
        _fail_safe_close()

    print(f"\u2713 Volume drawn: {vol_gal:.3f} gal")
    return vol_gal


if __name__ == "__main__":
    try:
        draw_water(1.25)
    except KeyboardInterrupt:
        print("\n[!] Aborted by user.")
