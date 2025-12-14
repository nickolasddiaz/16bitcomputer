from enum import Enum, auto, IntEnum
from functools import partial

class Operand(Enum):
    def _generate_next_value_(name, start, count, last_values):
        """
        This method is called to determine the value for auto()
        'count' represents the number of members defined so far,
        effectively giving you a 0-indexed counter.
        """
        return count

    NOP = auto()
    HALT = auto()
    VID = auto()
    VID_RED = auto() #imm8
    VID_RED_R = auto() # register
    VID_RED_RR = auto() # ram
    VID_GREEN = auto()
    VID_GREEN_R = auto()
    VID_GREEN_RR = auto()
    VID_BLUE = auto()
    VID_BLUE_R = auto()
    VID_BLUE_RR = auto()
    VID_X = auto()  # set the x-axis 64 pixels wide
    VIDX_R = auto()
    VIDX_RR = auto()
    VID_Y = auto()  # set the y-axis 16 pixels tall
    VIDY_R = auto()
    VIDY_RR = auto()
    MOV = auto()  # move register, register
    MOV_R = auto()  # move ram, register
    MOV_I = auto()  # move register, immediate
    MOV_L = auto()  # move register, ram
    MOV_RI = auto()  # move ram, immediate
    MOV_RR = auto()  # move ram, ram
    CMP = auto()
    CMP_R = auto()
    CMP_I = auto()
    CMP_L = auto()
    CMP_RI = auto()
    CMP_RR = auto()
    ADD = auto()
    ADD_R = auto()
    ADD_I = auto()
    ADD_L = auto()
    ADD_RI = auto()
    ADD_RR = auto()
    SUB = auto()
    SUB_R = auto()
    SUB_I = auto()
    SUB_L = auto()
    SUB_RI = auto()
    SUB_RR = auto()
    MULT = auto()
    MUL_R = auto()
    MULT_I = auto()
    MULT_L = auto()
    MULT_RI = auto()
    MULT_RR = auto()
    DIV = auto()
    DIV_R = auto()
    DIV_I = auto()
    DIV_L = auto()
    DIV_RI = auto()
    DIV_RR = auto()
    QUOT = auto()
    QUOT_R = auto()
    QUOT_I = auto()
    QUOT_L = auto()
    QUOT_RI = auto()
    QUOT_RR = auto()
    AND = auto()
    AND_R = auto()
    AND_I = auto()
    AND_L = auto()
    AND_RI = auto()
    AND_RR = auto()
    OR = auto()
    OR_R = auto()
    OR_I = auto()
    OR_L = auto()
    OR_RI = auto()
    OR_RR = auto()
    XOR = auto()
    XOR_R = auto()
    XOR_I = auto()
    XOR_L = auto()
    XOR_RI = auto()
    XOR_RR = auto()
    SHL = auto()
    SHL_R = auto()
    SHL_I = auto()
    SHL_L = auto()
    SHL_RI = auto()
    SHL_RR = auto()
    SHR = auto()
    SHR_R = auto()
    SHR_I = auto()
    SHR_L = auto()
    SHR_RI = auto()
    SHR_RR = auto()
    NEG = auto() # imm8
    NEG_R = auto() # reg
    NEG_RR = auto() # ram
    NOT = auto()
    NOT_R = auto()
    NOT_RR = auto()
    JMP = auto()
    JEQ = auto()
    JNE = auto()
    JG = auto()
    JLE = auto()
    JL = auto()
    JGE = auto()
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
        # check if odd and if the original is odd
        # for example JEQ is odd and JNE is even or vice versa
        if self.value & 1 == self.JEQ.value & 1:
            return Operand(self.value + 1)
        else:
            return Operand(self.value - 1)

    def correct_op(self, source, dest):
        """
        Computes the right operand for the source/destination types
        For example MOV -> MOV_RR if both source and destination are RamVar
        MOV = auto()  # move register, register
        MOV_R = auto()  # move ram, register
        MOV_I = auto()  # move register, immediate
        MOV_L = auto()  # move register, ram
        MOV_RI = auto()  # move ram, immediate
        """
        if Operand.VID.value <= self.value <= Operand.VIDY_RR.value:
            match source:
                case int():
                    return self
                case RegVar():
                    return Operand(self.value + 1)
                case RamVar():
                    return Operand(self.value + 2)

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
        return Operand.JMP.value <= self.value <= Operand.CALL.value

    def check_arith(self):
        return Operand.ADD.value <= self.value <= Operand.NOT_R.value

class RamVar:
    def __init__(self, val: int) -> None:
        self.val: int = val

    def __str__(self) -> str:
        return f"[bp + {self.val}]"


class RegVar:
    def __init__(self, val: int) -> None:
        self.val: int = val

    def __str__(self) -> str:
        match self.val:
            case 14:
                return "bp"
            case 15:
                return "sp"
            case num if num > 16:
                raise ValueError(f"Cannot assign a register to more than 16 bits: {num}")
            case _:
                return f"R{self.val}"

base_pointer = partial(RegVar, 14)
stack_pointer = partial(RegVar, 15)


class Compare(IntEnum):
    SIMPLE = auto()
    LOGICAL_AND = auto()
    LOGICAL_OR = auto()

if __name__ == "__main__":
    print("let temp = [")
    for command in Operand:
        print(f"[this.{command.name}, DATA.RAM], ", end="")
    print("];")
