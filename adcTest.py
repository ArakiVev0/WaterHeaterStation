from time import sleep
from max1238 import Max1238, InputMode

Vref = 4.096

def to_volts(raw: int) -> float:
    return (raw / 4096.0) * Vref


adc = Max1238()
adc.setup_adc()  
print("=== Single channel reads ===")
for i in range(12):
    raw = adc.read_single(channel=i, mode=InputMode.SingleEnded)
    print(f"CH{i}: {to_volts(raw):.3f} V")
print()

print("=== Read multiple (contiguous block) ===")
# Example: read channels 0..3 in one transaction
raws = adc.read_multiple(start_channel=0, count=4, mode=InputMode.SingleEnded)
for i, raw in enumerate(raws, start=0):
    print(f"CH{i}: {to_volts(raw):.3f} V")
print()

print("=== Read range (dict) ===")
# Example: read channels 6..9 efficiently
vals = adc.read_range(6, 9, mode=InputMode.SingleEnded)
for ch, raw in vals.items():
    print(f"CH{ch}: {to_volts(raw):.3f} V")
print()
