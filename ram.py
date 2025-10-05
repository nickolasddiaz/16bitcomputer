from collections import ChainMap, OrderedDict
from enum import Enum, auto
from ram import Command

class Ram:
    def __init__(self):
        self._ram: ChainMap[str, int] = ChainMap()
        self._lifetimes: OrderedDict[str, int] = OrderedDict()    # var_name, death

        # computed after ifetimes are computed
        self._lifetimes_stack: list[tuple[str, int]] = []

    def inner_start(self):
        self._ram = self._ram.new_child(dict())

    def inner_end(self):
        self._ram = self._ram.parents

    def get_var(self, var_name: str) -> int|None:
        # Get the location if exists (int) else (None)
        return self._ram.get(var_name)

    def set_var(self, var_name: str) -> int:
        min_num = self.get_min()
        self._ram[var_name] = min_num
        return min_num

    def _set_lifetime(self, var_name: str, instruction: int) -> None:
        if var_name is None or var_name.isdigit():
            return

        self._lifetimes.setdefault(var_name, instruction)

    def _remove_dead_var(self, instruction: int) -> None:
        while self._lifetimes_stack and self._lifetimes_stack[0][1] > instruction:
            var, index = self._lifetimes_stack.pop()
            del self._ram[var]
            del self._lifetimes[var]

    def compute_lifetimes(self, commands: list[Command]) -> None:
        for index, cmd in enumerate(commands):
                self._set_lifetime(cmd.source, index)
                self._set_lifetime(cmd.dest, index)

        self._lifetimes_stack = list(self._lifetimes.items())

    def reset_lifetimes(self) -> None:
        self._ram: ChainMap[str, int] = ChainMap()
        self._lifetimes: OrderedDict[str, int] = OrderedDict()

    def get_min(self) -> int:
        values = sorted([key for key in self._ram.values()])
        expected_value = 1
        for value in values:
            if value > expected_value:
                return expected_value
            expected_value = value + 1
        return expected_value


class Operand(Enum):
    NOP = auto()
    HALT = auto()
    MOV = auto()
    MOVR = auto()
    MOVI = auto()
    ST  = auto()
    STR  = auto()
    STI  = auto()
    CMP = auto()
    CMPR = auto()
    CMPI = auto()
    VID = auto()
    ADD = auto()
    ADDR = auto()
    ADDI = auto()
    SUB = auto()
    SUBR = auto()
    SUBI = auto()
    MULT = auto()
    MULR = auto()
    MULTI = auto()
    DIV = auto()
    DIVR = auto()
    DIVI = auto()
    QUOT = auto()
    QUOTR = auto()
    QUOTI = auto()
    AND = auto()
    ANDR = auto()
    ANDI = auto()
    OR = auto()
    ORR = auto()
    ORI = auto()
    XOR = auto()
    XORR = auto()
    XORI = auto()
    SHL = auto()
    SHLR = auto()
    SHLI = auto()
    SHR = auto()
    SHRR = auto()
    SHRI = auto()
    RR = auto()
    RRR = auto()
    RRI = auto()
    RL = auto()
    RLR = auto()
    RLI = auto()
    AR = auto()
    ARR = auto()
    ARI = auto()
    NOT = auto()
    NOTR = auto()
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
    PUSH = auto()
    PUSHI = auto()
    PUSHR = auto()
    POP = auto()
    POPR = auto()
    LABEL = auto()
    INNER_START = auto()
    INNER_END = auto()

    def negate(self):
        if not self.check_jump():
            raise ValueError(f"this is not a jump: {self}")
        if self.value & 1 ^ self.JEQ.value & 1: # check if odd
            return Operand(self.value + 1)
        else:
            return Operand(self.value - 1)

    def check_jump(self):
        return Operand.JEQ.value <= self.value <= Operand.JC.value

    def check_arith(self):
        return Operand.ADD.value <= self.value <= Operand.ARI.value


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
        self.names[self.counters] = jump_name
        self.jumps[jump_name] = 0
        self.counters += 1
        return self.counters -1

    def get_name(self, id_: int) -> str:
        if self.names[id_].isdigit():
            return f".L{self.names[id_]}"
        else:
            return f".{self.names[id_]}"

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

class Command:
    def __init__(self, op: Operand, source: int|str = None, dest: int|str = None, location: int = None):
        self.op = op
        self.source = source
        self.dest = dest
        self.location = location

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
    def negate_jump(self):
        self.op = self.op.negate()


