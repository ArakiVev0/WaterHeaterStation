from max1238 import Max1238
from time import sleep

Vref = 4.096
ch = 0

adc = Max1238()
adc.setup_adc()

while True:
    raw_val = adc.read_single(channel=ch)
    val = Vref * (raw_val / 4096)
    print(f"votage at channel {ch}: {val}")
    sleep(0.5)
