## GPIO
- GPIO 17 Flow meter control (Output)
- GPIO 21 Display A0
- GPIO 25 Display Reset

GPIO 18 and 26 are just used as mosi and cs for spi

## ADC (MAX1239KEEE+) using i2c
- CH 0  🔥 Temperature Transmitter Hot
- CH 1  🧊 Temperature Transmitter Cold
- CH 2  ⚙️ Flow Meter
- CH 3  ⏳ Future Use
- CH 4  🌡️ Ambient Temperature
- CH 5  ⏳ Future Use
- CH 6  ⏳ Future Use
- CH 7  ⏳ Future Use
- CH 8  ⏳ Future Use
- CH 9  ❌ Not Used
- CH 10 ❌ Not Used
- CH 11 ❌ Not Used

[max1239](https://www.analog.com/media/en/technical-documentation/data-sheets/max1236-max1239m.pdf)

ADC is using a i2c

## ADC config table
| BIT 7 | BIT 6 | BIT 5 | BIT 4 | BIT 3 | BIT 2 | BIT 1 | BIT 0 | 
| --------------- | --------------- | --------------- | --------------- | --------------- |
| REG | SCAN1 | SCAN0 | CS3 | CS2 | CS1 | CS0 | SGL/^DIF |

for CH0 with single ended mode the config byte would be 0x1 00 0000 1
for CH1 with single ended mode the config byte would be 0x1 00 0001 1
for CH1 with single ended mode the config byte would be 0x1 00 0010 1
