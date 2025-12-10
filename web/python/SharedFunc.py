import heapq

from Command import Command
from Type import Operand

# any string that starts off with # will be a register
register_id = "#"

class SharedFunc:
    """
    Manages the arguments and return values of every function
    It verifies the arguments and returns are consistent
    Raises error if it doesn't
    """
    def __init__(self):
        self.return_count: dict[str, int] = {"main": 0, "VID": 0, "VID_V": 0, "VID_X": 0, "VID_Y": 0, "VIDEO": 0, "HALT": 0}
        self.arg_count: dict[str, int] = {"main": 0, "VID": 0, "VID_V": 1, "VID_X": 1, "VID_Y": 1, "VIDEO": 3, "HALT": 0}

    def validate_return(self, func_name: str, amount_returned):
        """
        function validates if all uses of the function returns the same amount
        """

        if func_name not in self.return_count:
            self.return_count[func_name] = amount_returned
            return

        if self.return_count[func_name] != amount_returned:
            raise ValueError(f"{func_name} returned {amount_returned} instead of {self.return_count[func_name]}")

    def validate_arg(self, func_name: str, amount_argument):
        """
        function validates if all uses of the function argument the same amount
        """

        if func_name not in self.arg_count:
            self.arg_count[func_name] = amount_argument
            return

        if self.arg_count[func_name] != amount_argument:
            raise ValueError(
                f"{func_name} had this many {amount_argument} arguments instead of {self.arg_count[func_name]}")

class CompileHelper:
    """
    Performs extra logic for the compiler
    Manages the registers, such as assigning, and removing them
    """
    def __init__(self):
        self._dead_temp: list[int] = [0]
        heapq.heapify(self._dead_temp)
        # just a number to store a temp when calling a function
        self.call_temp: int = 0

    def free_reg(self, var: int):
        heapq.heappush(self._dead_temp, var)

    def get_reg(self) -> str:
        temp = heapq.heappop(self._dead_temp)
        if not self._dead_temp:
            heapq.heappush(self._dead_temp, temp + 1)
        return f"{register_id}{temp}"

    def get_temp_ram(self) -> str:
        """
        returns a temporary memory that will be deleted as soon as it is not used
        """
        self.call_temp += 1
        return f"-{self.call_temp}-call temp"

    def free_all_reg(self):
        self.call_temp = 0

    def reset(self):
        self._dead_temp: list[int] = [0]
        heapq.heapify(self._dead_temp)
        self.call_temp: int = 0

    def extract_variable_and_commands(self, input1: int | str | tuple[str, list[Command]], commands: list[Command]) -> tuple[str | int, list[Command]]:
        """
        takes in two inputs of either integer, string or tuple of string and list commands
        combines the two inputs and returns a tuple of string and list commands
        """
        if isinstance(input1, Command):
            raise ValueError("Command object cannot be used as input")
        if isinstance(input1, tuple):
            if input1[1][-1].operand == Operand.CALL_HELPER:
                temp_name = self.get_temp_ram()
                input1 = (temp_name, input1[1])
                input1[1][-1].destination = [temp_name]
                commands = input1[1] + commands
            else:
                commands.extend(input1[1])
            return input1[0], commands
        else:
            return input1, commands
