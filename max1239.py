from enum import Enum
from typing import Optional
from smbus2 import SMBus
import time


class InputMode(Enum):
    SingalMode = 1
    DifferentialMode = 0


class ClockType(Enum):
    ExternalClock = 0
    InternalClock = 1


class Polarity(Enum):
    Unipolar = 0
    Bipolar = 1


class Reset(Enum):
    ResetConfig = 0
    NoAction = 1


class Max1239:
    def __init__(self, address=0x35) -> None:
        self.address = address
        self.bus = SMBus(0)

    def create_config_binary(
        self,
        scan: int,
        channel: int,
        inputMode: InputMode,
    ) -> int:
        if scan > 3 or scan < 0:
            raise ValueError("Invalid Scan value should be 0 to 3")
        if channel > 11 or channel < 0:
            raise ValueError("Invalid Channel value should be 0 to 11")
        return 0 << 7 | scan << 6 | channel << 4 | inputMode.value

    def create_setup_binary(
        self, select: int, clockType: ClockType, polarity: Polarity, reset: Reset
    ) -> int:
        return (
            1 << 7
            | select << 6
            | clockType.value << 3
            | polarity.value << 2
            | reset.value << 1
            | 0
        )

    def read_channel(
        self,
        scan: int = 0,
        channel: int = 0,
        inputMode: InputMode = InputMode.SingalMode,
    ) -> Optional[int]:
        try:
            config = self.create_config_binary(scan, channel, inputMode)
            self.bus.write_byte(self.address, config)

        except ValueError as e:
            print(e)
            return None

        time.sleep(0.001)

        res = self.bus.read_i2c_block_data(self.address, 0x00, 2)
        return (res[0] << 4) | (res[1] >> 4)

    def setup_adc(
        self,
        select: int = 0,
        clockType: ClockType = ClockType.InternalClock,
        polarity: Polarity = Polarity.Unipolar,
        reset: Reset = Reset.NoAction,
    ) -> Optional[int]:
        try:
            setup = self.create_setup_binary(select, clockType, polarity, reset)
            self.bus.write_byte(self.address, setup)
        except ValueError as e:
            print(e)
            return None
