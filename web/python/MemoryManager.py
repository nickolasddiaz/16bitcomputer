from collections import ChainMap

from JumpManager import jump_manager
from Command import Command
from Type import Operand, RegVar, RamVar, stack_pointer, base_pointer
from SharedFunc import register_id, CompileHelper, SharedFunc


class MemoryManager:
    def __init__(self, function_name: str, compiler_helper: CompileHelper, shared_rtn: SharedFunc):
        self._ram: ChainMap[str, int] = ChainMap()
        self._lifetimes: dict[str, int] = dict()  # var_name, death
        self.compiler_helper = compiler_helper
        self.shared_rtn = shared_rtn

        # computed after ifetimes are computed
        self._lifetimes_stack: list[tuple[str, int]] = []

        self.stack_offset = 2

        self.return_offset: int = shared_rtn.return_count[function_name] + self.stack_offset

    def inner_start(self):
        """
        uses chain map to auto kill any variables that are out of scope
        creates a new child in the chain map
        """
        self._ram = self._ram.new_child(dict())

    def inner_end(self):
        """
        uses chain map to auto kill any variables that are out of scope
        pops the child in the chain map
        """
        self._ram = self._ram.parents

    def _get_var(self, var_name: str) -> int | None:
        """
        Get the jump_label if exists (int) else (None)
        """
        return self._ram.get(var_name)

    def _set_var(self, var_name: str) -> int:
        """
        allocates a variable into the ram
        """
        min_num = self._get_min()
        self._ram[var_name] = min_num
        return min_num

    def compute_lifetimes(self, var_name: str | list[str | int], instruction: int) -> None:
        """
        set the lifetime of when the variable is last used
        """
        if isinstance(var_name, list):
            for i in var_name:
                self.compute_lifetimes(i, instruction)
        if isinstance(var_name, tuple):
            for i in var_name[1]:
                self.compute_lifetimes(i.destination, instruction)
                self.compute_lifetimes(i.source, instruction)

        if var_name is None or (isinstance(var_name, str) and var_name.startswith(register_id)) or not isinstance(
                var_name, str):
            return

        self._lifetimes[var_name] = instruction

    def compute_lifetimes_list(self, commands: list[Command]) -> None:
        """
        Compute the lifetimes for a list of commands
        """
        for index, cmd in enumerate(commands):
            self.compute_lifetimes(cmd.destination, index)
            self.compute_lifetimes(cmd.source, index)

        # sort the stack where the closest vars are not used list[(var_name, num_when_they_die)]
        self._lifetimes_stack = list(self._lifetimes.items())
        self._lifetimes_stack.sort(key=lambda item: item[1], reverse=True)

    def _remove_dead_vars(self, instruction: int) -> None:
        """
        destroys all the variables that are not being used for the index of the instruction
        """
        while self._lifetimes_stack and self._lifetimes_stack[-1][1] < instruction:
            var, index = self._lifetimes_stack.pop()
            self._ram.pop(var, None)

    def set_arguments(self, args: list[str]) -> None:
        """
        Set the argument's variables for example def main (a, b) -> (a,1), (b,2)
        """
        for index, arg in enumerate(args):
            self._ram[arg] = index + self.return_offset

    def _get_min(self) -> int:
        """
        just gets the min of the key that is not used starting at 2
        """
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

    def allocate_helper(self, var, op: Operand | None = None):
        """
        manages the logic of converting strings into registers or memory
        """
        if var is not None and isinstance(var, str):
            var_location = self._get_var(var)
            if var.startswith(register_id):  # case where var is the temp variable
                return RegVar(int(var[1:]))
            elif var_location is None:  # case where var does not exist
                if op != Operand.MOV and not (
                        isinstance(var, str) and var.startswith("-")):  # only MOV can create variables
                    raise ValueError(f"Initialise the variable {var} before using it")
                return RamVar(self._set_var(var))
            else:
                return RamVar(var_location)  # case where var exists
        return var

    def complex_commands_helper(self, cmd: str | int, instruction: int, function_name: str) -> tuple[
        str | int, list[Command]]:
        """
        Allocates all the variables in commands such as RETURN_HELPER or CALL_HELPER
        it assigns all variables in the var_lists
        returns a tuple with a variable/integer, list of commands
        """
        variable, var_lists = self.compiler_helper.extract_variable_and_commands(cmd, [])
        for cmd in var_lists:
            self.allocate_command(cmd, instruction, function_name)
        temp_var = self.allocate_helper(variable, Operand.MOV)
        return temp_var, var_lists

    def allocate_command(self, cmd: Command, instruction: int, function_name: str) -> list[Command]:
        """
        Performs logic for command objects, it allocates the variables
        Performs logic for the RETURN_HELPER and CALL_HELPER
        Calling and returning function:

        base pointer for the current function starting at 0
        return for the current function starting at 1
        ####################
        reserved for returning for that function: example return a,b = 2-3
        ####################
        reserved the argument for that function: example current_func(a,b) = 4-5
        ####################
        reserved for functions locals and globals: example a = 8; b = 10; = 6-7
        ####################
        reserved on CALLING example a,b = CALL new_function(a,b)
        base pointer for the called function: = 8
        return for the called function: = 9
        ####################
        reserved for returns for call = 10-11
        ####################
        reserved for arguments for call = 12-13
        ####################
        reserved for future locals and globals on the call: 14-onwards
        """

        final_command: list[Command] = []

        self._remove_dead_vars(instruction)

        # logic for the returning
        if cmd.operand == Operand.RETURN_HELPER:
            # check if the return is consistent
            self.shared_rtn.validate_return(function_name, len(cmd.destination))

            # enumerate through all the returned arguments
            for index, arg in enumerate(cmd.destination):
                variable, var_lists = self.complex_commands_helper(arg, instruction, function_name)

                var_location = self.allocate_helper(variable)
                # gets the jump_label of the variable and put it in the right jump_label
                final_command.extend(var_lists + [Command(Operand.MOV, RamVar(index + self.stack_offset), var_location)])

            # clean up before returning
            final_command.extend([Command(Operand.MOV, stack_pointer(), base_pointer()),  # cleaning function's frame
                                  Command(Operand.MOV, base_pointer(), RamVar(0)),  # pop the base_pointer
                                  Command(Operand.RTRN)
                                  ])
            return final_command

        # logic for calling functions
        if cmd.operand == Operand.CALL_HELPER:
            # destination is returns and source is arguments, .call_label is the name of the function
            self.shared_rtn.validate_return(cmd.call_label, len(cmd.destination))
            self.shared_rtn.validate_arg(cmd.call_label, len(cmd.source))

            sp: int = self.get_stack_pointer()
            arg_offset: int = len(cmd.destination) + sp + self.stack_offset

            if cmd.call_label in ["VID"]:
                return [Command(Operand[cmd.call_label])]
            elif cmd.call_label in ["VID_RED","VID_GREEN","VID_BLUE", "VID_X", "VID_Y"]:
                variable, var_lists = self.complex_commands_helper(cmd.source[0], instruction, function_name)
                return var_lists + [Command(Operand[cmd.call_label], variable)]
            elif cmd.call_label == "VIDEO":
                variable, var_lists = self.complex_commands_helper(cmd.source[0], instruction, function_name)
                variable1, var_lists1 = self.complex_commands_helper(cmd.source[1], instruction, function_name)
                variable2, var_lists2 = self.complex_commands_helper(cmd.source[2], instruction, function_name)
                variable3, var_lists3 = self.complex_commands_helper(cmd.source[3], instruction, function_name)
                variable4, var_lists4 = self.complex_commands_helper(cmd.source[4], instruction, function_name)
                return (var_lists + [Command(Operand.VID_RED, variable)]
                        + var_lists1 + [Command(Operand.VID_GREEN, variable1)]
                        + var_lists2 + [Command(Operand.VID_BLUE, variable2)]
                        + var_lists3 + [Command(Operand.VID_X, variable1)]
                        + var_lists4 + [Command(Operand.VID_Y, variable2)]
                        + [Command(Operand.VID)])

            # compute the arguments
            for index, arg in enumerate(cmd.source):
                variable, var_lists = self.complex_commands_helper(arg, instruction, function_name)
                final_command.extend(var_lists + [Command(Operand.MOV, RamVar(arg_offset + index), variable)])

            # compute the returns if it does exist move it else let it be
            for index, arg in enumerate(cmd.destination):
                var_location = self._get_var(arg)
                return_offset = sp + index + 1
                if var_location is None:
                    self._ram[arg] = return_offset  # let it exist without moving it
                else:  # move it because it existed
                    final_command.append(Command(Operand.MOV, RamVar(var_location), RamVar(return_offset)))

            return final_command + [Command(Operand.ADD, stack_pointer(), sp),
                                    Command(Operand.CALL, None, None, jump_manager.get_function(cmd.call_label))]

        # logic assigning ram locations for var _names, handling cases of allocating new variables and the jump_label of old variables
        cmd.destination = self.allocate_helper(cmd.destination, cmd.operand)
        cmd.source = self.allocate_helper(cmd.source, cmd.operand)

        final_command.append(cmd)

        return final_command