from enum import Enum


MAX_REGISTERS = 3 # 16 total - 4 reserved for temps - 1 control input
MAX_RAM = 256
MAX = MAX_REGISTERS + MAX_RAM

class Temp(Enum):
    CONTROL_INPUT   = ("TEMP+CONTROL+INPUT", MAX_REGISTERS) # 0xb
    TEMP_LEFT       = ("TEMP+LEFT", MAX_REGISTERS + 1) # 0xc
    TEMP_RIGHT      = ("TEMP+RIGHT", MAX_REGISTERS + 2) # 0xd
    TEMP_SAVE       = ("TEMP+SAVE", MAX_REGISTERS + 3) # 0xe
    TEMP_SWAP       = ("TEMP+SWAP", MAX_REGISTERS + 4) # 0xf

    def __init__(self, name, reg):
        self._name = name
        self._reg = ~reg # invert bits for input to Location class

    @property
    def name(self):
        return self._name

    @property
    def reg(self):
        return self._reg
    
    @property
    def true_value(self):
        return ~self._reg
    
    @staticmethod
    def get_temp(name: str) -> int:
        for t in Temp:
            if t.name == name:
                return ~t.reg
        raise Exception(f"Temp variable {name} not found.")
    
display_names = [Temp.TEMP_LEFT.name, Temp.TEMP_RIGHT.name, Temp.TEMP_SAVE.name, Temp.TEMP_SWAP.name]
def exists(var: str|list[str]) -> bool:
    if isinstance(var, list):
        return any(v in display_names for v in tuple(var))
    return var in display_names
