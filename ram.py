from collections import ChainMap
from enum import Enum, auto

class ram_var:
    def __init__(self, name: int) -> None:
        self.name: int = name
    def __str__(self) -> str:
        return f"[{self.name}]"

class reg_var:
    def __init__(self, name:int) -> None:
        self.name:int = name
    def __str__(self) -> str:
        return f"R_{self.name}"

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
        if self.value & 1 == self.JEQ.value & 1: # check if odd
            return Operand(self.value + 1)
        else:
            return Operand(self.value - 1)

    def check_jump(self):
        return Operand.JEQ.value <= self.value <= Operand.JC.value

    def check_arith(self):
        return Operand.ADD.value <= self.value <= Operand.ARI.value

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
    def negate_jump(self):
        self.op = self.op.negate()


class Ram:
    def __init__(self):
        self._ram: ChainMap[str, int] = ChainMap()
        self._lifetimes: dict[str, int] = dict()    # var_name, death

        # computed after ifetimes are computed
        self._lifetimes_stack: list[tuple[str, int]] = []

        self.temp_used: int = 0
        self.move_temp: int = 0

    def inner_start(self):
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
        if var_name is None or var_name == "" or isinstance(var_name, int):
            return

        self._lifetimes[var_name] =  instruction

    def _remove_dead_vars(self, instruction: int) -> None:
        while self._lifetimes_stack and self._lifetimes_stack[-1][1] < instruction:
            var, index = self._lifetimes_stack.pop()
            self._ram.pop(var, None)

    def compute_lifetimes(self, commands: list[Command]) -> None:
        for index, cmd in enumerate(commands):
                self._set_lifetime(cmd.source, index)
                self._set_lifetime(cmd.dest, index)

        self._lifetimes_stack = list(self._lifetimes.items())
        self._lifetimes_stack.sort(key=lambda item: item[1], reverse=True)

    def _get_min(self) -> int:
        values = sorted([key for key in self._ram.values()])
        expected_value = 0
        for value in values:
            if value > expected_value:
                return expected_value
            expected_value = value + 1
        return expected_value

    def allocate_command(self, cmd: Command, instruction: int) -> list[Command]:
        final_cmd: list[Command] = []
        self._remove_dead_vars(instruction)

        if cmd.op != Operand.MOV and isinstance(cmd.source, str) and isinstance(cmd.dest, str)\
                and cmd.source != "":
            self.move_temp += 1
            if self.move_temp >= 2:
                self.temp_used = 1
        if cmd.dest == "" or cmd.op == Operand.CMP:
            self.move_temp = 0
            self.temp_used = 0

        if cmd.op == Operand.CMP and cmd.source == "" and cmd.dest == "":
            cmd.source = reg_var(0)
            cmd.dest = reg_var(1)
            return [cmd]

        if cmd.source is not None and isinstance(cmd.source, str):
            var_location = self._get_var(cmd.source)
            if cmd.source == "":
                cmd.source = reg_var(self.temp_used)
            elif var_location is None:
                cmd.source = ram_var(self._set_var(cmd.source))
                if cmd.op != Operand.MOV:
                    raise ValueError("Initialise the variable before using it")
            else:
                cmd.source = ram_var(var_location)

        if cmd.dest is not None and isinstance(cmd.dest, str):
            var_location = self._get_var(cmd.dest)
            if cmd.dest == "":
                cmd.dest = reg_var(self.temp_used)
            elif var_location is None:
                cmd.dest = ram_var(self._set_var(cmd.dest))
                if cmd.op != Operand.MOV:
                    raise ValueError("Initialise the variable before using it")
            else:
                cmd.dest = ram_var(var_location)

        if isinstance(cmd.dest, ram_var) and isinstance(cmd.source, ram_var):

            if  cmd.op == Operand.MOV:
                final_cmd.append(Command(Operand.MOV, reg_var(self.temp_used), cmd.dest))
                cmd.dest = reg_var(self.temp_used)
            else:
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


