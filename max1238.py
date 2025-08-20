from enum import Enum
from typing import Optional, Sequence, Union
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
    ScanAIN0ToCS = 0b00
    RepeatSelect8x = 0b01
    ScanAIN6ToCS = 0b10
    ConvertSelected = 0b11


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
       ) -> list[int]:
        """
        Perform one atomic I²C transaction to this device:
        (optional) write_bytes  -> repeated START -> (optional) read_len bytes.

        Returns a list[int] of read bytes (0..255). If read_len == 0, returns [].

        Notes for MAX1238:
        - With internal clock, the READ triggers conversion; device may stretch SCL.
        - Use this for: config-write + read-2, multi-channel FIFO reads, setup writes, etc.
        """
        # Normalize write_bytes to a list of ints (0..255)
        if write_bytes is None:
            to_write: Optional[list[int]] = None
        elif isinstance(write_bytes, int):
            if not (0 <= write_bytes <= 255):
                raise ValueError("write byte out of range (0..255)")
            to_write = [write_bytes]
        else:
            to_write = list(write_bytes)
            if any((b < 0 or b > 255) for b in to_write):
                raise ValueError("one or more write bytes out of range (0..255)")

        if read_len < 0:
            raise ValueError("read_len must be >= 0")

        attempt = 0
        last_err = None
        while attempt <= retries:
            try:
                msgs = []
                if to_write is not None:
                    msgs.append(i2c_msg.write(self.address, to_write))
                if read_len:
                    msgs.append(i2c_msg.read(self.address, read_len))
                if not msgs:
                    return []

                self.bus.i2c_rdwr(*msgs)

                if read_len:
                    return list(msgs[-1])  # bytes from the read message
                return []
            except OSError as e:  # bus errors, NACK, etc.
                last_err = e
                if attempt == retries:
                    raise
                time.sleep(retry_delay_s)
                attempt += 1

        # Shouldn't reach here
        if last_err:
            raise last_err
        return []

    def setup_adc(
        self,
        referenceVoltage: RefrenceVoltage = RefrenceVoltage.InternalRef_AlwaysON_AnalogIn,
        clock: ClockType = ClockType.Internal,
        polarity: Polarity = Polarity.Unipolar,
        reset: ResetMode = ResetMode.NoAction,
    ) -> None:
        setup_byte = self._build_setup_byte(referenceVoltage, clock, polarity, reset)
               self._xfer(setup_byte, 0)

    def read_single(
        self,
        channel: int,
        mode: InputMode = InputMode.SingleEnded,
    ) -> Optional[int]:
            cfg = self._build_config_byte(ScanMode.ConvertSelected, channel, mode)

            msb, lsb = self._xfer(cfg, 2)
            return ((msb & 0x0F) << 8) | lsb

    def read_range(self, start_channel: int, end_channel: int, mode: InputMode = InputMode.SingleEnded) -> dict[int, int]:

        if not (0 <= start_channel <= end_channel <= 11):
            raise ValueError("Invalid channel range")

        if start_channel >= 6:
            scan = ScanMode.ScanAIN6ToCS  
            base = 6
        else:
            scan = ScanMode.ScanAIN0ToCS  
            base = 0

        cfg = self._build_config_byte(scan, end_channel, mode)

        n_res = (end_channel - base + 1)
        raw = self._xfer(cfg, 2 * n_res)

        words = [((raw[i] & 0x0F) << 8) | raw[i + 1] for i in range(0, len(raw), 2)]
        channels = list(range(base, end_channel + 1))
        results = dict(zip(channels, words))

        return {ch: results[ch] for ch in range(start_channel, end_channel + 1)}

    def read_multiple(
        self,
        start_channel: int,
        count: int,
        mode: InputMode = InputMode.SingleEnded,
    ) -> list[int]:

        if not (0 <= start_channel <= 11) or not (1 <= count <= 12 - start_channel):
            raise ValueError("Invalid channel range")

        end_ch = start_channel + count - 1
        if start_channel >= 6:
            scan, base = ScanMode.ScanAIN6ToCS, 6
        else:
            scan, base = ScanMode.ScanAIN0ToCS, 0

        cfg = self._build_config_byte(scan, end_ch, mode)
        n_results = (end_ch - base + 1)
        raw = self._xfer([cfg], 2 * n_results)

        words = [((raw[i] & 0x0F) << 8) | raw[i + 1] for i in range(0, len(raw), 2)]
        drop = start_channel - base
        return words[drop:drop + count]
