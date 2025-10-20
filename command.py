from functools import partial

from type import Operand, RegVar, RamVar
from jump_manager import jump_manager

class Command:
    def __init__(self, op, dest=None, source=None, jump_label= None):
        """
        Forms of a command:
        Operand
        Operand, dest, source
        Operand, dest
        Operand, call_label
        Both dest, and source can be an int, str, register or memory
        """
        self.operand: Operand = op
        self.destination: int | str | RamVar | RegVar | list[int | str] | None = dest
        self.source: int | str | RamVar | RegVar | list[int | str] | None = source
        self.jump_label: int|None = jump_label
        self.call_label: str = ""

    def __str__(self) -> str:
        """
        returns string representation of command in assembly
        """
        match self.operand:
            case Operand.LABEL:
                return f"{jump_manager.get_name(self.jump_label)}:"
            case Operand.INNER_START:
                return "---\tInner Start ---"
            case Operand.INNER_END:
                return "---\tInner END   ---"
            case Operand.RETURN_HELPER:
                return ""

        output = f"\t{self.operand.name}"
        if self.destination is not None:
            output += f", {self.destination}"
        if self.source is not None:
            output += f", {self.source}"
        if self.jump_label is not None:
            output += f", {jump_manager.get_name(self.jump_label)}"
        return output

    def negate_jump(self) -> None:
        """
        Negates a jump, for example: JEQ -> JNE
        """
        self.operand = self.operand.negate()

    def compute_op(self) -> None:
        """
        Computes the right operand for the source/destination types
        For example MOV -> MOV_RR if both source and destination are RamVar
        """
        self.operand = self.operand.correct_op(self.destination, self.source)

    def num_instruct(self) -> int:
        if self.operand == Operand.LABEL:
            return 0
        inst = 1
        if isinstance(self.destination, RamVar) | isinstance(self.destination, int):
            inst += 1
        if isinstance(self.source, RamVar) | isinstance(self.source, int):
            inst += 1
        if isinstance(self.jump_label, int):
            inst = 2

        return inst

    def get_binary(self) -> str:
        """
        returns a binary string from the operand, destination, and destination and jump label
        the string can be either 16, 32, or 48 bits long
        the operand goes in the upper 8 bits of the first 16 bits: ex 1200
        instruction set is 16 bits in value
        the source goes in the lower 4 bits if it is a register: ex 000A
        the destination goes in the lower 4 bits if it is a register: ex 00A0
        if either destination or source is a ram variable or immediate then it gets a whole 16 bits
        """
        if self.operand == Operand.LABEL:
            return ""

        # get the binary of the operand
        binary_str: int = self.operand.value << 8
        if isinstance(self.destination, RegVar):
            binary_str += self.destination.val << 4
        if isinstance(self.source, RegVar):
            binary_str += self.source.val

        part1 = self.number_string(binary_str)

        part2_used: bool = False

        # get the binary of the destination
        binary_str2: int = 0
        if isinstance(self.destination, RamVar):
            part2_used = True
            binary_str2 = self.destination.val
        elif isinstance(self.destination, int):
            part2_used = True
            binary_str2 = self.format_signed_16bit_hex(self.destination)

        part2 = self.number_string(binary_str2)
        part3_used: bool = False

        # get the binary of the source
        binary_str3: int = 0
        if isinstance(self.source, RamVar):
            part3_used = True
            binary_str3 = self.source.val
        elif isinstance(self.source, int):
            part3_used = True
            binary_str3 = self.format_signed_16bit_hex(self.source)
        if isinstance(self.jump_label, int):
            part3_used = True
            binary_str3 = jump_manager.get_jump_location_index(self.jump_label)

        part3 = self.number_string(binary_str3)

        # put all the parts together
        full_str = part1
        if part2_used:
            full_str += part2
        if part3_used:
            full_str += part3

        return full_str

    @staticmethod
    def format_signed_16bit_hex(num) -> int:
        """
        Validates and returns a 16-bit signed number from -32768 and 32767
        if the number is less than zero then two's complement is performed
        """
        # Ensure the number fits within a 16-bit signed range
        if not (-32768 <= num <= 32767):
            raise ValueError("Number out of signed 16-bit range (-32768 to 32767)")

        if num < 0:
            # Convert negative number to its 16-bit two's complement equivalent
            num = 2 ** 16 + num
        return num

    @staticmethod
    def number_string(number) -> str:
        """
        Returns a hex string that is 16 bits wide
        Example: 28 -> "001C"
        """
        s = f"{number:X}"
        return s.zfill(4)


CommandLabel = partial(Command, Operand.LABEL, None, None)
CommandJump = partial(Command, Operand.JMP, None, None)
CommandInnerStart = partial(Command, Operand.INNER_START, None, None, None)
CommandInnerEnd = partial(Command, Operand.INNER_END, None, None, None)
CommandReturn = partial(Command, Operand.RETURN_HELPER)
