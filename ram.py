import heapq
from collections import ChainMap
from enum import Enum, auto
from functools import partial



temp_identifier = "#"

class SharedFunc:
    def __init__(self):
        self.return_count: dict[str, int] = {"main": 0, "VID": 0, "VID_V": 0, "VID_X": 0, "VID_Y": 0, "VIDEO": 0, "HALT": 0}
        self.arg_count: dict[str, int] =    {"main": 0, "VID": 0, "VID_V": 1, "VID_X": 1, "VID_Y": 1, "VIDEO": 3, "HALT": 0}

    def validate_return(self, func_name: str, amount_returned):
        # function validates if all uses of the function returns the same amount

        if func_name not in self.return_count:
            self.return_count[func_name] = amount_returned
            return

        if self.return_count[func_name] != amount_returned:
            raise ValueError(f"{func_name} returned {amount_returned} instead of {self.return_count[func_name]}")

    def validate_arg(self, func_name: str, amount_argument):
        # function validates if all uses of the function argument the same amount

        if func_name not in self.arg_count:
            self.arg_count[func_name] = amount_argument
            return

        if self.arg_count[func_name] != amount_argument:
            raise ValueError(f"{func_name} had this many {amount_argument} arguments instead of {self.arg_count[func_name]}")

shared_rtn = SharedFunc()

class RamVar:
    def __init__(self, val: int) -> None:
        self.val: int = val
    def __str__(self) -> str:
        return f"[bp + {self.val}]"

class RegVar:
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

base_pointer = partial(RegVar, 3)
stack_pointer = partial(RegVar, 4)


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
    NOT_I = auto()
    NOT_L = auto()
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
    # below Operands are helpers
    LABEL = auto()
    INNER_START = auto()
    INNER_END = auto()
    RETURN_HELPER = auto()
    CALL_HELPER = auto()

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
            case RegVar(), RegVar():
                return self
            case RamVar(), RegVar():
                return Operand(self.value + 1)
            case RegVar(), int():
                return Operand(self.value + 2)
            case RegVar(), RamVar():
                return Operand(self.value + 3)
            case RamVar(), int():
                return Operand(self.value + 4)
            case RamVar(), RamVar():
                return Operand(self.value + 5)

    def check_jump(self):
        return Operand.JEQ.value <= self.value <= Operand.JC.value

    def check_arith(self):
        return Operand.ADD.value <= self.value <= Operand.NOT_R.value


class Command:
    def __init__(self, op: Operand, source: int | str | RamVar | RegVar | list[int | str] | None = None, dest: int | str | RamVar | RegVar | None = None, location: int = None):
        self.op: Operand = op
        self.source: int | str | RamVar | RegVar | list[int | str] | None = source
        self.dest: int | str | RamVar | RegVar | list[int | str] | None = dest
        self.location: int = location
        self.other: str = ""

    def __str__(self) -> str:
        match self.op:
            case Operand.LABEL:
                return f"{jm.get_name(self.location)}:"
            case Operand.INNER_START:
                return "---\tInner Start ---"
            case Operand.INNER_END:
                return "---\tInner END   ---"
            case Operand.RETURN_HELPER:
                return ""

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
        if self.op in [Operand.LABEL, Operand.RETURN_HELPER]:
            return ""

        temp = ""
        binary: str = f"{self.op.value:02x}"
        if isinstance(self.source, RegVar) and isinstance(self.dest, RegVar):
            binary += f"{self.source.val:01x}{self.source.val:01x}"
        else:
            if isinstance(self.source, RamVar):
                temp = self.number_hex(self.source.val)
            elif isinstance(self.source, int):
                temp = self.number_hex(self.source)
            if temp is not None:
                binary += temp
            if isinstance(self.dest, RamVar):
                temp = self.number_hex(self.dest.val)
            elif isinstance(self.dest, int):
                temp = self.number_hex(self.dest)
            if temp is not None:
                binary += temp

        if self.location is not None:
            _id = jm.get_index(self.location)
            binary += self.number_hex(_id >> 4)
            binary += self.number_hex(_id & 0x0F)

        return binary

    @staticmethod
    def number_hex(num: int) -> str:
        if 0 <= num >= 0xFF:  # check if input1 is between 0-255
            raise ValueError(f"Number {num} out of range, valid range is 0 - 255")
        return f"{num:02x}"


class Ram:
    def __init__(self, function_name:str):
        self._ram: ChainMap[str, int] = ChainMap()
        self._lifetimes: dict[str, int] = dict()    # var_name, death

        # computed after ifetimes are computed
        self._lifetimes_stack: list[tuple[str, int]] = []

        self.return_offset: int = shared_rtn.return_count[function_name] + 1


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

    def set_lifetime(self, var_name: str | list[str | int], instruction: int) -> None:
        if isinstance(var_name, list):
            for i in var_name:
                self.set_lifetime(i, instruction)
        if isinstance(var_name, tuple):
            for i in var_name[1]:
                self.set_lifetime(i.source, instruction)
                self.set_lifetime(i.dest, instruction)

        if var_name is None or (isinstance(var_name, str) and var_name.startswith(temp_identifier)) or not isinstance(var_name, str):
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
            self._ram[arg] = index + self.return_offset

    def compute_lifetimes(self, commands: list[Command]) -> None:
        # loop through each command and sets the number of the last used variable
        for index, cmd in enumerate(commands):
            self.set_lifetime(cmd.source, index)
            self.set_lifetime(cmd.dest, index)

        # sort the stack where the closest vars are not used list[(var_name, num_when_they_die)]
        self._lifetimes_stack = list(self._lifetimes.items())
        self._lifetimes_stack.sort(key=lambda item: item[1], reverse=True)

    def _get_min(self) -> int:
        # just gets the min of the key that is not used starting at 1
        values = sorted([key for key in self._ram.values()])
        expected_value = self.return_offset
        for value in values:
            if value > expected_value:
                return expected_value
            expected_value = value + 1
        return expected_value

    def get_stack_pointer(self) -> int:
        # 1 represents the base pointer that exists at [bp + 0]
        return max(self._ram.values(), default=0) + 1

    def allocate_helper(self, var, op: Operand|None = None):
        # assigning ram from strings, if it does not exist create it
        if var is not None and isinstance(var, str):
            var_location = self._get_var(var)
            if var.startswith(temp_identifier): # case where var is the temp variable
                return RegVar(int(var[1:]))
            elif var_location is None: # case where var does not exist
                if op != Operand.MOV and not (isinstance(var, str) and var.startswith("-")): # only MOV can create variables
                    raise ValueError(f"Initialise the variable {var} before using it")
                return RamVar(self._set_var(var))
            else:
                return RamVar(var_location) # case where var exists
        return var

    def complex_commands_helper(self, cmd: str|int, instruction: int, function_name:str) -> tuple[str | int, list[Command]]:
        variable, var_lists = CompilerHelp.input_helper(cmd, [])
        for cmd in var_lists:
            self.allocate_command(cmd, instruction, function_name)
        temp_var = self.allocate_helper(variable, Operand.MOV)
        return temp_var, var_lists

    def allocate_command(self, cmd: Command, instruction: int, function_name:str) -> list[Command]:
        final_command: list[Command] = []

        """
        Calling and returning function
        
        base pointer for the current function starting at 0
        ####################
        reserved for returning for that function: example return a,b = 1-2
        ####################
        reserved the argument for that function: example current_func(a,b) = 3-4
        ####################
        reserved for functions locals and globals: example a = 8; b = 10; = 5-6
        ####################
        reserved on CALLING example a,b = CALL new_function(a,b)
        base pointer for the called function: = 7
        ####################
        reserved for returns for call = 8-9
        ####################
        reserved for arguments for call = 10-11
        ####################
        reserved for future locals and globals on the call: 12-onwards
        """
        self._remove_dead_vars(instruction)

        # logic for the returning
        if cmd.op == Operand.RETURN_HELPER:
            # check if the return is consistent
            shared_rtn.validate_return(function_name, len(cmd.source))

            # enumerate through all the returned arguments
            for index, arg in enumerate(cmd.source):
                variable, var_lists = self.complex_commands_helper(arg, instruction, function_name)

                var_location = self.allocate_helper(variable)
                # gets the location of the variable and put it in the right location
                final_command.extend(var_lists + [Command(Operand.MOV, RamVar(index + 1), var_location)])

            # clean up before returning
            final_command.extend([Command(Operand.MOV, stack_pointer(), base_pointer()),  # cleaning function's frame
                              Command(Operand.MOV, base_pointer(), RamVar(0)),  # pop the base_pointer
                              Command(Operand.RTRN)
                              ])
            return final_command

        # logic for calling functions
        if cmd.op == Operand.CALL_HELPER:
            # source is returns and dest is arguments, .other is the name of the function
            shared_rtn.validate_return(cmd.other, len(cmd.source))
            shared_rtn.validate_arg(cmd.other, len(cmd.dest))

            sp: int = self.get_stack_pointer()
            arg_offset: int = len(cmd.source) + sp + 1

            if cmd.other in ["VID_V", "VID_X", "VID_Y", "VID_VXY"]:
                variable, var_lists = self.complex_commands_helper(cmd.dest[0], instruction, function_name)
                return var_lists + [Command(Operand[cmd.other], variable)]
            elif cmd.other == "VIDEO":
                variable, var_lists = self.complex_commands_helper(cmd.dest[0], instruction, function_name)
                variable1, var_lists1 = self.complex_commands_helper(cmd.dest[1], instruction, function_name)
                variable2, var_lists2 = self.complex_commands_helper(cmd.dest[2], instruction, function_name)
                return (var_lists + [Command(Operand.VID_V, variable)]
                        + var_lists1 + [Command(Operand.VID_X, variable1)]
                        + var_lists2 + [Command(Operand.VID_Y, variable2)]
                        + [Command(Operand.VID)])


            # compute the arguments
            for index, arg in enumerate(cmd.dest):
                variable, var_lists = self.complex_commands_helper(arg, instruction, function_name)
                final_command.extend(var_lists + [Command(Operand.MOV, RamVar(arg_offset + index), variable)])

            # compute the returns if it does exist move it else let it be
            for index, arg in enumerate(cmd.source):
                var_location = self._get_var(arg)
                return_offset = sp + index + 1
                if var_location is None:
                    self._ram[arg] = return_offset # let it exist without moving it
                else: # move it because it existed
                    final_command.append(Command(Operand.MOV, RamVar(var_location), RamVar(return_offset)))

            return final_command + [Command(Operand.ADD, stack_pointer(), sp), Command(Operand.CALL, None, None, jm.get_function(cmd.other))]

        # logic assigning ram locations for var names, handling cases of allocating new variables and the location of old variables
        cmd.source = self.allocate_helper(cmd.source, cmd.op)
        cmd.dest = self.allocate_helper(cmd.dest, cmd.op)

        final_command.append(cmd)

        return final_command


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


class CompileHelper:
    def __init__(self):
        self._dead_temp: list[int] = [0]
        heapq.heapify(self._dead_temp)
        # just a number to store a temp when calling a function
        self.call_temp: int = 0

    def del_var(self, var: int):
        heapq.heappush(self._dead_temp, var)

    def app_var(self) -> str:
        temp = heapq.heappop(self._dead_temp)
        if not self._dead_temp:
            heapq.heappush(self._dead_temp, temp + 1)
        return f"{temp_identifier}{temp}"

    def get_temp_var(self) -> str:
        self.call_temp += 1
        return f"-{self.call_temp}-call temp"

    def reset_temp(self):
        self.call_temp = 0

    def input_helper(self, input1: int | str | tuple[str,list[Command]], commands: list[Command]) -> tuple[str | int,list[Command]] :
        if isinstance(input1, Command):
            raise ValueError("Command cannot be used as input")
        if isinstance(input1, tuple):
            if input1[1][-1].op == Operand.CALL_HELPER:
                temp_name = self.get_temp_var()
                input1 = (temp_name, input1[1])
                input1[1][-1].source = [temp_name]
                commands = input1[1] + commands
            else:
                commands.extend(input1[1])
            return input1[0], commands
        else:
            return input1, commands

CompilerHelp = CompileHelper()


