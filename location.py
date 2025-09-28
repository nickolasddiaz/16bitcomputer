from functools import singledispatch
from temp_var import Temp, MAX, MAX_REGISTERS

class Location:
    def __init__(self): # maps variable name to Location register 0-11, RAM 12-...267
        self.location = dict() # key is str, value is int
        self.rev_location = dict() # key is int, value is str
        self.commands = [] # used to temporarily store commands while assigning variables

    def __str__(self):
        return f"Location: {self.location}\n"
    
    def __sizeof__(self):
        return len(self.location)
    
    def get_registers(self) -> dict[str, int]:
        return {name: loc for loc, name in self.rev_location.items() if loc < MAX_REGISTERS}
    
    def get_ram(self) -> dict[str, int]:
        return {name: loc for loc, name in self.rev_location.items() if loc >= MAX_REGISTERS}

    @singledispatch # gets item from Location
    def get_item(self, key) -> int|str:
        raise TypeError(f"Unsupported key type: {type(key)}")
    @get_item.register
    def _(self, key: str) -> int:
        return self.location[key]
    @get_item.register  
    def _(self, key: int) -> str:
        return self.rev_location[key]
    
    def get_int(self, key: str|int) -> int:
        if isinstance(key, int):
            return key
        if key not in self.location:
            return -1
        return self.location[key]

    def get_var(self, key: str|int) -> str|None:
        if isinstance(key, str):
            return key
        if key not in self.rev_location:
            return None
        return self.rev_location[key]
        
    def set_item(self, key: str|int, value: int|str) -> None: # there is no multidispatch for setting items
        if isinstance(key, str) and isinstance(value, int):
            if key == "":
                raise ValueError("Key cannot be None")
            self.location[key] = value
            self.rev_location[value] = key
        elif isinstance(key, int) and isinstance(value, str):
            if value == "":
                raise ValueError("Key cannot be None")
            self.rev_location[key] = value
            self.location[value] = key
        else:
            raise TypeError(f"Unsupported key type: {type(key)}, {type(value)}")

    def contains(self, key: str|int) -> bool:
        if isinstance(key, int):
            return key in self.rev_location
        elif isinstance(key, str):
            return key in self.location
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")
    
    def del_item(self, key: str|int) -> None:
        if isinstance(key, str):
            value = self.location[key]
            del self.location[key]
            del self.rev_location[value]
        elif isinstance(key, int):
            value = self.rev_location[key]
            del self.rev_location[key]
            del self.location[value]
        else:
            raise TypeError(f"Unsupported key type: {type(key)}")

    def check_delete(self, key: str|int) -> None: # deletes item if it exists and deletes it
        if self.contains(key):
            self.del_item(key)

    def check_delete_list(self, keys: list[str|int]) -> None: # deletes items if they exist
        for key in keys:
            self.check_delete(key)

    def get_lowest(self, start_at: int = 0, end_at: int = MAX) -> int:
        for i in range(start_at, end_at):
            if i not in self.rev_location:
                return i
        return -1 # all locations full
    
    def get_lowest_ram(self) -> int:
        return self.get_lowest(MAX_REGISTERS, MAX)
    
    def get_lowest_register(self) -> int:
        return self.get_lowest(0, MAX_REGISTERS)
    

    def assign_lowest(self, key: str, start_at: int = 0, end_at: int = MAX) -> int:
        lowest = self.get_lowest(start_at, end_at)
        self.set_item(key, lowest)
        return lowest
    
    def assign_lowest_ram(self, key: str) -> int:
        return self.assign_lowest(key, MAX_REGISTERS, MAX)
    
    def assign_lowest_register(self, key: str) -> int:
        return self.assign_lowest(key, 0, MAX_REGISTERS)

    def get_or_create(self, key: str) -> int:
        if self.contains(key):
            return self.location[key]
        else:
            return self.assignlowest(key)
        
    def check_if_register(self, key: str|int) -> bool:
        loc = self.get_int(key)
        return loc < MAX_REGISTERS
    
    def get_index(self, key: str|int ) -> int: # if in Location, then return index, else -1
        return self.get_int(key) if (self.contains(key)) else -1
    
    def get_index_register(self, key: str|int ) -> int: # if in register, then return register index, else -1
        return self.get_int(key) if (self.check_if_register(key)) else -1
    
    def get_index_ram(self, key: str|int ) -> int: # if in RAM, then return RAM index, else -1
        return -1 if (self.check_if_register(key)) else self.get_int(key)
       
    def move_variables(self, location_1: str|int, location_2: str|int|None = None) -> int:
        var1 = self.get_var(location_1)
        loc1 = self.get_int(location_1)
        if location_2 is None:
            loc2 = self.get_lowest() # get lowest available Location
        else:
            loc2 = self.get_int(location_2)
        self.check_delete(loc1) # 2 hours to figure out that check_delete before set_item as it overwrites the Location
        self.set_item(var1, loc2)
        match (self.check_if_register(loc1), self.check_if_register(loc2)):
            case (True, True):
                self._reg_to_reg(loc1, loc2)
            case (True, False):
                self._reg_to_ram(loc1, loc2)
            case (False, True):
                self._ram_to_reg(loc1, loc2)
            case _: # (False, False)
                self._ram_to_ram(loc1, loc2)

        return loc2
    
    def move_variables_ram(self, location_1: str) -> int:
        if location_1 == "":
            raise ValueError("Key cannot be None")
        return self.move_variables(location_1, self.get_lowest_ram())
    
    def move_variables_register(self, location_1: str|int) -> int:
        return self.move_variables(location_1, self.get_lowest_register())

    # ---------------------------------- Helper functions for moving data --------------------------------- #
    
    def _reg_to_reg(self, reg1: int, reg2: int) -> None:
        self.commands.append(f"MV, {self._encap_reg(reg1)}, {self._encap_reg(reg2)}")
    def _reg_to_ram(self, reg: int, ram: int) -> None:
        self.commands.append(f"ST, {self._encap_reg(reg)}, {self._encap_ram(ram)}")
    def _ram_to_reg(self, ram: int, reg: int) -> None:
        self.commands.append(f"LD, {self._encap_ram(ram)}, {self._encap_reg(reg)}")
    def _ram_to_ram(self, ram1: int, ram2: int) -> None:
        temp_reg = Temp.TEMP_SWAP.reg
        self._ram_to_reg(ram1, temp_reg)
        self._reg_to_ram(temp_reg, ram2)

    def _encap_ram(self, reg: int) -> str:
        return f"[{reg - MAX_REGISTERS}]"
    
    def _encap_reg(self, reg: int) -> int:
        return abs(reg)
    
    def get_commands(self):
        cmds = self.commands[:]
        self.commands.clear()
        return cmds
