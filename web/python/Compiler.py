"""Compiler for 16-bit custom architecture for a computer in Logisim-evolution.

This module implements a compiler that transforms a high-level language into
assembly and binary code for a custom 16-bit architecture. The compiler handles:
- Variable allocation (registers and stack memory)
- Function calls and returns
- Control flow (if/else, loops)
- Arithmetic and logical operations

Main classes:
    Parser: Transforms parse tree into assembly commands
    MemoryManager: Manages variable lifetime and memory allocation
    Command: Represents a single assembly instruction
    Operand: IntEnum of the instruction set
    Jump_Manager: Manages the function/statement jumps
"""
import time
from abc import ABC

from lark import Lark

from JumpManager import jump_manager
from Parser import Parser
from Type import Operand


class Compiler(ABC):
    def __init__(self, grammar: str):
        self.grammar: str = grammar

    def _main(self, program: str) -> tuple[str, str, str, str, float]:
        try:
            start_time = time.perf_counter()

            #loads the grammar into the parser
            code_parser = Lark(self.grammar, start='start', parser='lalr')

            # gets the parse-tree and writes it to program.tre
            parse_tree = code_parser.parse(program)

            # transform the parse tree into assembly
            transformed = Parser().transform(parse_tree)

            # process what index set the labels
            index = 0
            for cmd in transformed:
                if cmd.operand == Operand.LABEL:
                    jump_manager.set_pos(cmd.jump_label, index)
                elif Operand.check_jump(cmd.operand):
                    jump_manager.set_verify_jump(cmd.jump_label)
                    index += cmd.num_instruct()
                else:
                    index += cmd.num_instruct()

            # gets the assembly string and writes it to program.asm
            index = 0
            asm_str:str = ""
            for cmd in transformed:
                if cmd.operand != Operand.LABEL or jump_manager.verify_jump(cmd.jump_label):
                    index += cmd.num_instruct()
                    asm_str += str(cmd) + "\n"

            # gets the binary string and writes it to program.hex
            binary_str = ""
            for cmd in transformed:
                cmd.compute_op()
                binary_str += cmd.get_binary()

            end_time = time.perf_counter()

            return parse_tree.pretty(), asm_str, binary_str, "", end_time - start_time

        except Exception as e:
            return "", "", "", str(e), 0
