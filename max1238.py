from enum import Enum
from typing import Optional
from smbus2 import SMBus, i2c_msg
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
    VDD_AnalogIn = 0b000
    ExternalRef = 0b010
    InternalRef_AlwaysOFF_AnalogIn = 0b100
    InternalRef_AlwaysON_AnalogIn = 0b101
    InternalRef_AlwaysOFF_RefOut = 0b110
    InternalRef_AlwaysON_RefOut = 0b111


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
            | (referenceVoltage.value << 4)
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

        return (0 << 7) | (scan.value << 5) | (channel << 1) | (mode.value)

    def setup_adc(
        self,
        referenceVoltage: RefrenceVoltage = RefrenceVoltage.InternalRef_AlwaysON_AnalogIn,
        clock: ClockType = ClockType.Internal,
        polarity: Polarity = Polarity.Unipolar,
        reset: ResetMode = ResetMode.NoAction,
    ) -> None:
        setup_byte = self._build_setup_byte(referenceVoltage, clock, polarity, reset)
        self.bus.write_byte(self.address, setup_byte)

    def read_single(
        self,
        channel: int,
        mode: InputMode = InputMode.SingleEnded,
    ) -> Optional[int]:
        try:
            config_byte = self._build_config_byte(ScanMode.NoScan, channel, mode)
            self.bus.write_byte(self.address, config_byte)

            read = i2c_msg.read(self.address, 2)
            self.bus.i2c_rdwr(read)

            msb, lsb = list(read)

            return ((msb & 0x0F) << 8) | lsb
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

        result = []
        for _ in range(count):
            read = i2c_msg.read(self.address, 2)
            self.bus.i2c_rdwr(read)

            msb, lsb = list(read)

            value = ((msb << 0x0F) << 8) | lsb
            result.append(value)

        return result
