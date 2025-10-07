from collections import ChainMap
from enum import Enum, auto
from functools import partial


class ram_var:
    def __init__(self, val: int) -> None:
        self.val: int = val
    def __str__(self) -> str:
        return f"[bp + {self.val}]"

class reg_var:
    def __init__(self, val:int) -> None:
        self.val:int = val
    def __str__(self) -> str:
        match self.val:
            case 0:
                return "ax"
            case 1:
                return "dx"
            case 3:
                return "bp"
            case 4:
                return "sp"
            case _:
                return f"R{self.val}"

base_pointer = partial(reg_var, 3)
stack_pointer = partial(reg_var, 4)


class Operand(Enum):
    NOP = auto()
    HALT = auto()
    VID = auto() # color the video
    VID_V = auto() # set XTerm256 color model (8-bit)
    VID_X = auto() # set the x-axis 16 pixels wide
    VID_Y = auto() # set the y-axis 16 pixels tall
    MOV = auto() # move register, register
    MOV_R = auto()  # move ram, register
    MOV_I = auto() # move register, immediate
    MOV_L = auto()  # move register, ram
    MOV_RI = auto()  # move ram, immediate
    MOV_RR = auto() # move ram, ram
    CMP = auto()
    CMP_R = auto()
    CMP_I = auto()
    CMP_L = auto()
    ADD = auto()
    ADD_R = auto()
    ADD_I = auto()
    ADD_L = auto()
    SUB = auto()
    SUB_R = auto()
    SUB_I = auto()
    SUB_L = auto()
    MULT = auto()
    MUL_R = auto()
    MULT_I = auto()
    MULT_L = auto()
    DIV = auto()
    DIV_R = auto()
    DIV_I = auto()
    DIV_L = auto()
    QUOT = auto()
    QUOT_R = auto()
    QUOT_I = auto()
    QUOT_L = auto()
    AND = auto()
    AND_R = auto()
    AND_I = auto()
    AND_L = auto()
    OR = auto()
    OR_R = auto()
    OR_I = auto()
    OR_L = auto()
    XOR = auto()
    XOR_R = auto()
    XOR_I = auto()
    XOR_L = auto()
    SHL = auto()
    SHL_R = auto()
    SHL_I = auto()
    SHL_L = auto()
    SHR = auto()
    SHR_R = auto()
    SHR_I = auto()
    SHR_L = auto()
    RR = auto()
    RR_R = auto()
    RR_I = auto()
    RR_L = auto()
    RL = auto()
    RL_R = auto()
    RL_I = auto()
    RL_L = auto()
    AR = auto()
    AR_R = auto()
    AR_I = auto()
    AR_L = auto()
    NOT = auto()
    NOT_R = auto()
    JMP = auto()
    JEQ = auto()
    JNE = auto()
    JG = auto()
    JLE = auto()
    JL = auto()
    JGE = auto()
    JNZ = auto()
    JZ = auto()
    JNC = auto()
    JC = auto()
    CALL = auto()
    RTRN = auto()
    LABEL = auto()
    INNER_START = auto()
    INNER_END = auto()
    # this used for the CALL operand where arguments are push and returns are pop
    SET_VARIABLE_MAX = auto()

    def negate(self):
        if not self.check_jump():
            raise ValueError(f"this is not a jump: {self}")
        if self.value & 1 == self.JEQ.value & 1: # check if odd
            return Operand(self.value + 1)
        else:
            return Operand(self.value - 1)

    def correct_op(self, source, dest):
        # MOV = auto()  # move register, register
        # MOV_R = auto()  # move ram, register
        # MOV_I = auto()  # move register, immediate
        # MOV_L = auto()  # move register, ram
        # MOV_RI = auto()  # move ram, immediate
        if not Operand.MOV.value <= self.value <= Operand.NOT_R.value:
            return self

        match (source, dest):
            case reg_var(), reg_var():
                return self
            case ram_var(), reg_var():
                return Operand(self.value + 1)
            case reg_var(), int():
                return Operand(self.value + 2)
            case reg_var(), ram_var():
                return Operand(self.value + 3)
            case ram_var(), int():
                return Operand(self.value + 4)
            case ram_var(), ram_var():
                return Operand(self.value + 5)

    def check_jump(self):
        return Operand.JEQ.value <= self.value <= Operand.JC.value

    def check_arith(self):
        return Operand.ADD.value <= self.value <= Operand.NOT_R.value


class Command:
    def __init__(self, op: Operand, source: int|str|ram_var|reg_var|None = None, dest: int|str|ram_var|reg_var|None = None, location: int = None):
        self.op: Operand = op
        self.source: int|str|ram_var|reg_var|None = source
        self.dest: int|str|ram_var|reg_var|None = dest
        self.location: int = location

    def __str__(self) -> str:
        match self.op:
            case Operand.LABEL:
                return f"{jm.get_name(self.location)}:"
            case Operand.INNER_START:
                return "---\tInner Start ---"
            case Operand.INNER_END:
                return "---\tInner END   ---"

        output = f"\t{self.op.name}"
        if self.source is not None:
            output += f", {self.source}"
        if self.dest is not None:
            output += f", {self.dest}"
        if self.location is not None:
            output += f", {jm.get_name(self.location)}"
        return output

    def negate_jump(self) -> None:
        self.op = self.op.negate()

    def compute_op(self) -> None:
        self.op = self.op.correct_op(self.source, self.dest)

    def get_binary(self) -> str:
        if self.op == Operand.LABEL:
            return ""

        temp = ""
        binary: str = f"{self.op.value:02x}"
        if isinstance(self.source, reg_var) and isinstance(self.dest, reg_var):
            binary += f"{self.source.val:01x}{self.source.val:01x}"
        else:
            if isinstance(self.source, ram_var):
                temp = self.number_hex(self.source.val)
            elif isinstance(self.source, int):
                temp = self.number_hex(self.source)
            if temp is not None:
                binary += temp
            if isinstance(self.dest, ram_var):
                temp = self.number_hex(self.dest.val)
            elif isinstance(self.dest, int):
                temp = self.number_hex(self.dest)
            if temp is not None:
                binary += temp

        if self.location is not None:
            id = jm.get_index(self.location)
            binary += self.number_hex(id >> 4)
            binary += self.number_hex(id & 0x0F)

        return binary

    @staticmethod
    def number_hex(num: int) -> str:
        return f"{num:02x}"


class Ram:
    def __init__(self):
        self._ram: ChainMap[str, int] = ChainMap()
        self._lifetimes: dict[str, int] = dict()    # var_name, death

        # computed after ifetimes are computed
        self._lifetimes_stack: list[tuple[str, int]] = []

        # how many times source is a string and operand is not MOV
        self.temp_used: int = 0
        # move temp is what temp register to use 0 = ax, 1 = bx
        self.move_temp: int = 0

        # this used for the CALL operand where arguments are push and returns are pop
        self.variable_max = 0

    def inner_start(self):
        # this uses chainmap to auto kill any variables that are out of scope
        self._ram = self._ram.new_child(dict())

    def inner_end(self):
        self._ram = self._ram.parents

    def _get_var(self, var_name: str) -> int | None:
        # Get the location if exists (int) else (None)
        return self._ram.get(var_name)

    def _set_var(self, var_name: str) -> int:
        min_num = self._get_min()
        self._ram[var_name] = min_num
        return min_num

    def _set_lifetime(self, var_name: str, instruction: int) -> None:
        if var_name is None or var_name == "" or not isinstance(var_name, str):
            return

        self._lifetimes[var_name] =  instruction

    def _remove_dead_vars(self, instruction: int) -> None:
        # if the var is dead it destroys it
        while self._lifetimes_stack and self._lifetimes_stack[-1][1] < instruction:
            var, index = self._lifetimes_stack.pop()
            self._ram.pop(var, None)

    def set_arguments(self, args: list[str]) -> None:
        # Set the argument's spots for example def main (a, b) -> (a,1), (b,2)
        for index, arg in enumerate(args):
            self._ram[arg] = index + 1

    def compute_lifetimes(self, commands: list[Command]) -> None:
        # loop through each command and sets the number of the last used variable
        for index, cmd in enumerate(commands):
            self._set_lifetime(cmd.source, index)
            self._set_lifetime(cmd.dest, index)

        # sort the stack where the closest vars are not used list[(var_name, num_when_they_die)]
        self._lifetimes_stack = list(self._lifetimes.items())
        self._lifetimes_stack.sort(key=lambda item: item[1], reverse=True)

    def _get_min(self) -> int:
        # just gets the min of the key that is not used starting at 1
        values = sorted([key for key in self._ram.values()])
        expected_value = 1
        for value in values:
            if value > expected_value:
                return expected_value
            expected_value = value + 1
        return expected_value

    def allocate_helper(self, op: Operand, var):
        # assigning ram from strings, if it does not exist create it
        if var is not None and isinstance(var, str):
            var_location = self._get_var(var)
            if var == "": # case where var is the temp variable
                return reg_var(self.temp_used)
            elif var_location is None: # case where var does not exist
                if op != Operand.MOV: # only MOV can create variables
                    raise ValueError("Initialise the variable before using it")
                return ram_var(self._set_var(var))
            else:
                return ram_var(var_location) # case where var exists
        elif isinstance(var, int) and var < 0: # case where var is int and is negative
            # the -(i +1), is to append it to the front of all the vars, example -3 and the max index of variables is 4, it would be in index 7, so (3 + 4)
            return ram_var(self.variable_max + (var * -1))
        return None

    def allocate_command(self, cmd: Command, instruction: int) -> list[Command]:
        final_cmd: list[Command] = []
        self._remove_dead_vars(instruction)

        if cmd.op == Operand.SET_VARIABLE_MAX:
            self.variable_max = max(self._ram.values()) + 1
            return []

        # logic in order to manage the temp variables, when the first temp is used the second one steps in
        if (cmd.op != Operand.MOV and isinstance(cmd.source, str)
                and isinstance(cmd.dest, str) and cmd.source != ""):
            self.move_temp += 1
            if self.move_temp >= 2:
                self.temp_used = 1
        if cmd.dest == "" or cmd.op == Operand.CMP:
            self.move_temp = 0
            self.temp_used = 0

        # logic when the op is compare and both source and destination are temps
        # set the source to ax, dest to bx
        if cmd.op == Operand.CMP and cmd.source == "" and cmd.dest == "":
            cmd.source = reg_var(0)
            cmd.dest = reg_var(1)
            return [cmd]

        # logic assigning ram locations for var names, handling cases of allocating new variables and the location of old variables
        temp = self.allocate_helper(cmd.op, cmd.source)
        if temp is not None:
            cmd.source = temp
        temp = self.allocate_helper(cmd.op, cmd.dest)
        if temp is not None:
            cmd.dest = temp

        # logic for chain arithmetic forcing using temp, ax or bx
        # example:
        # a = 6 / b, oder of operations is enforced for / and %
        # MOV, ax, 6
        # DIV, ax, b
        # MOV, a, ax
        if  ((isinstance(cmd.source, ram_var) or isinstance(cmd.source, int)) and
                (isinstance(cmd.dest, ram_var) or isinstance(cmd.dest, int)) and
                cmd.op != Operand.MOV):

            final_cmd.append(Command(Operand.MOV, reg_var(self.temp_used), cmd.source))
            cmd.source = reg_var(self.temp_used)

        final_cmd.append(cmd)

        return final_cmd


class JumpManager:
    def __init__(self):
        self.counters = 0
        self.names = dict() # key: id, value: name
        self.jumps = dict() # key: name, value: position

    def get_jump(self) -> int:
        self.names[self.counters] = str(self.counters)
        self.jumps[str(self.counters)] = 0
        self.counters += 1
        return self.counters - 1

    def get_function(self, jump_name: str) -> int:
        key_found = next((key for key, val in self.names.items() if val == key), None)
        if key_found is not None:
            return key_found

        self.names[self.counters] = jump_name
        self.jumps[jump_name] = 0
        self.counters += 1
        return self.counters -1

    def get_name(self, id_: int) -> str:
        if self.names[id_].isdigit():
            return f".L{self.names[id_]}"
        else:
            return f".{self.names[id_]}"

    def get_index(self, id_: int) -> int:
        return self.jumps[self.names[id_]]

    def remove_duplicate(self, id1: int|None, id2: int|None = None) -> int:
        match (id1 is None, id2 is None):
            case (True, True):
                return self.get_jump()
            case (False, True):
                return id1
            case(True, False):
                return id2
            case _:
                num_change = self.names[id1]
                num_to_change = self.names[id2]
                del self.jumps[self.names[id2]]
                for key, value in self.names.items():
                    if value == num_to_change:
                        self.names[key] = num_change
                return id1

    def set_pos(self, id_: int, pos: int):
        if self.jumps[self.names[id_]] == 0:
            self.jumps[self.names[id_]] = pos
        else:
            raise ValueError(f"Jump label has already been set: {self.names[id_]}")

jm = JumpManager()


