from enum import Enum
from typing import Optional
from smbus2 import SMBus
import time


class InputMode(Enum):
    SingleEnded = 1
    Differential = 0


class ClockType(Enum):
    External = 0
    Internal = 1


class Polarity(Enum):
    Unipolar = 0
    Bipolar = 1


class ResetMode(Enum):
    Reset = 0
    NoAction = 1


class ScanMode(Enum):
    NoScan = 0b00
    ScanUpToChannel = 0b01
    ScanUpToAndWrap = 0b10
    ScanAll = 0b11


class RefrenceVoltage(Enum):
    VDD_Analog_input = 0b000
    ExternalReference = 0b010
    InternalReference_AlwaysOFF_AnalogInput = 0b100
    InternalReference_AlwaysON_AnalogInput = 0b101
    InternalReference_AlwaysOFF_ReferenceOutput = 0b110
    InternalReference_AlwaysON_ReferenceOutput = 0b111


class Max1238:
    def __init__(self, address: int = 0x35, bus_num: int = 1) -> None:
        self.address = address
        self.bus = SMBus(bus_num)

    def _build_setup_byte(
        self,
        referenceVoltage: RefrenceVoltage,
        clock: ClockType,
        polarity: Polarity,
        reset: ResetMode,
    ) -> int:
        return (
            (1 << 7)  # Setup command
            | (referenceVoltage.value << 6)
            | (clock.value << 3)
            | (polarity.value << 2)
            | (reset.value << 1)
            | 0
        )

    def _build_config_byte(
        self,
        scan: ScanMode,
        channel: int,
        mode: InputMode,
    ) -> int:
        if not 0 <= channel <= 11:
            raise ValueError("Channel must be between 0 and 11")

        return (0 << 7) | (scan.value << 6) | (channel << 4) | (mode.value)

    def setup_adc(
        self,
        referenceVoltage: RefrenceVoltage = RefrenceVoltage.InternalReference_AlwaysON_AnalogInput,
        clock: ClockType = ClockType.Internal,
        polarity: Polarity = Polarity.Unipolar,
        reset: ResetMode = ResetMode.NoAction,
    ) -> None:
        setup_byte = self._build_setup_byte(referenceVoltage, clock, polarity, reset)
        self.bus.write_byte(self.address, setup_byte)
        time.sleep(0.001)

    def read_single(
        self,
        channel: int,
        mode: InputMode = InputMode.SingleEnded,
    ) -> Optional[int]:
        try:
            config_byte = self._build_config_byte(ScanMode.NoScan, channel, mode)
            self.bus.write_byte(self.address, config_byte)
            time.sleep(0.001)
            data = self.bus.read_i2c_block_data(self.address, 0x00, 2)
            return (data[0] << 4) | (data[1] >> 4)
        except Exception as e:
            print(f"Read failed: {e}")
            return None

    def read_multiple(
        self,
        start_channel: int,
        count: int,
        mode: InputMode = InputMode.SingleEnded,
    ) -> list[int]:
        if not (0 <= start_channel <= 11) or not (1 <= count <= 12 - start_channel):
            raise ValueError("Invalid channel range")

        config_byte = self._build_config_byte(
            ScanMode.ScanUpToChannel, start_channel + count - 1, mode
        )
        self.bus.write_byte(self.address, config_byte)
        time.sleep(0.001)

        result = []
        for _ in range(count):
            data = self.bus.read_i2c_block_data(self.address, 0x00, 2)
            value = (data[0] << 4) | (data[1] >> 4)
            result.append(value)

        return result
