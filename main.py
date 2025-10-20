"""Compiler for 16-bit custom architecture for a computer in Logisim-evolution.

This module implements a compiler that transforms a high-level language into
assembly and binary code for a custom 16-bit architecture. The compiler handles:
- Variable allocation (registers and stack memory)
- Function calls and returns
- Control flow (if/else, loops)
- Arithmetic and logical operations

Main classes:
    CodeTransformer: Transforms parse tree into assembly commands
    Ram: Manages variable lifetime and memory allocation
    Command: Represents a single assembly instruction
    Operand: IntEnum of the instruction set
    Jump_Manager: Manages the function/statement jumps
"""

from lark import Lark
from pathlib import Path

from compiler import CodeTransformer
from jump_manager import jump_manager
from type import Operand


def main():
    # reads the program and grammar
    program_file = Path('program.txt')
    grammar_file = Path('grammar.txt')

    program = program_file.read_text()
    grammar = grammar_file.read_text()

    #loads the grammar into the parser
    code_parser = Lark(grammar, start='start', parser='lalr')

    # gets the parse-tree and writes it to program.tre
    parse_tree = code_parser.parse(program)
    Path('program.tre').write_text(parse_tree.pretty())

    # transform the parse tree into assembly
    transformed = CodeTransformer().transform(parse_tree)

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

    Path('program.asm').write_text(asm_str)

    # gets the binary string and writes it to program.hex
    binary_str = ""
    for cmd in transformed:
        cmd.compute_op()
        binary_str += cmd.get_binary()

    Path('program.bin').write_text(binary_str)

if __name__ == "__main__":
    #for op in Operand:
    #    print(f"{op.name}: {op.value :X}")
    main()