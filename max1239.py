from dataclasses import dataclass
from enum import Enum

@dataclass
class Max1239:
    class InputMode(Enum):
        SingleMode = 1
        DifferentialMode = 2
     
    def create_config_binary(self, channel, InputMode:
        return 0

    def read_channel(channel):
        return 0

reg = 1
scan = 0b00
cs = 0b0000
sgl = 1

print(bin(reg << 7| scan << 6 | cs << 4 |sgl))
