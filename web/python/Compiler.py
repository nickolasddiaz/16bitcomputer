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

from lark import Lark, Transformer, v_args

from JumpManager import jump_manager
from Parser import Parser
from Type import Operand

@v_args(meta=True)
class HtmlDetailsTransformer(Transformer):
    """
    Transforms a Lark Tree into an HTML string using <details> and <summary> tags.
    """

    def __default__(self, data, children, meta):
        # This method handles all rules not explicitly defined in the Transformer.
        # 'data' is the name of the rule (e.g., 'start', 'expression').
        # 'children' is a list of the transformed children (strings in this case).

        summary_content = f"<summary>{data}</summary>"
        details_content = "".join(children)

        return f"<details open>{summary_content}{details_content}</details>"

    def __default_token__(self, token):
        return f"<div>{token.value}</div>"


class Compiler(ABC):
    def __init__(self, grammar: str):
        self.grammar: str = grammar

    def _main(self, program: str) -> tuple[str, str, str, str, float, list[int], list[int]]:
        try:
            start_time = time.perf_counter()

            #loads the grammar into the parser
            code_parser = Lark(self.grammar, start='start', parser='lalr', propagate_positions=True)

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
            binary_to_assembly_mappings: list[int] = []
            code_mappings: list[int] = []
            total: int = 0
            code_line: int = 1
            for cmd in transformed:
                cmd.compute_op()
                temp = cmd.get_binary()
                total += len(temp)//4
                if cmd.line_num != -1:
                    code_line = max(cmd.line_num, code_line)
                binary_to_assembly_mappings.append(total)
                code_mappings.append(code_line)

                binary_str += temp

            end_time = time.perf_counter()


            return HtmlDetailsTransformer().transform(parse_tree), asm_str, binary_str, "", end_time - start_time, binary_to_assembly_mappings, code_mappings

        except Exception as e:
            import traceback
            return "", "", "", str(traceback.print_exc()), 0, [], []
