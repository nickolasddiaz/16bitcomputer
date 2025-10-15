from typing import Any

from lark import Lark, Transformer
from enum import auto, IntEnum
from ram import Operand, Command, jm, Ram, RamVar, base_pointer, stack_pointer, shared_rtn, register_id, CompilerHelp
from functools import partial

with open('grammar.txt', 'r') as file:
    grammar = file.read()

#loads the grammar into the parser
code_parser = Lark(grammar, start='start', parser='lalr')


class Compare(IntEnum):
    COMP = auto()
    ANDS = auto()
    ORS = auto()


CommandLabel = partial(Command, Operand.LABEL, None, None)
CommandJump = partial(Command, Operand.JMP, None, None)
CommandInnerStart = partial(Command, Operand.INNER_START, None, None, None)
CommandInnerEnd = partial(Command, Operand.INNER_END, None, None, None)
CommandReturn = partial(Command, Operand.RETURN_HELPER)

class CodeTransformer(Transformer):
       # --- var/number functions --------------------------
    def NUMBER(self, n):
        return int(n)

    def number(self, n):
        return int(n[0])

    def hex_number(self, n):
        return int(n[0], 16)

    def var(self, name):
        return name[0]

    def const(value):
        return value

    def NAME(self, name):
        return name.value

    def bit_not(self, items):
        """
        Takes previous variable performs NOT and returns the new temp variable
        :return: tuple[new variable, the previous Commands along as its own]
        """
        if isinstance(items[0], int):
            return ~items[0] # returns the negate integer
        # easily separates the input into the variable and commands
        product, final_commands = CompilerHelp.input_helper(items[0], [])
        temp_name = CompilerHelp.get_temp_ram() # gets new temp variable
        return temp_name, final_commands + [Command(Operand.NOT, temp_name, product)]

    def negative(self, items):
        """
        Takes previous variable performs NEG and returns the new temp variable
        :return: tuple[new variable, the previous Commands along as its own]
        """
        if isinstance(items[0], int):
            return ~items[0] + 1 # returns the 2's compliment on integer
        # easily separates the input into the variable and commands
        product, final_commands = CompilerHelp.input_helper(items[0], [])
        temp_name = CompilerHelp.get_temp_ram() # gets new temp variable
        return temp_name, final_commands + [Command(Operand.NEG, temp_name, product)]

    # --- product functions --------------------------

    def product_helper(self, input1: int|str|tuple[str,list[Command]], input2: int|str|tuple[str,list[Command]], op: Operand) -> int|str|tuple[int | str, list[Command]]:
        """
        Takes two inputs performs the necessary product like +-*/%.
        Processes cases like the inputs being integers, registers or memory.
        Combines the input's list of commands into a single command.
        returns a tuple of variable, and list of commands
        """

        # separating the variables from the list of commands
        product2,final_commands = CompilerHelp.input_helper(input2, [])
        product1,final_commands = CompilerHelp.input_helper(input1, final_commands)

        isint1 = isinstance(product1, int)
        isint2 = isinstance(product2, int)
        if isint1 and isint2: # if both are int then return the operation
            match op:
                case Operand.ADD:
                    return product1 + product2
                case Operand.SUB:
                    return product1 - product2
                case Operand.MULT:
                    return product1 * product2
                case Operand.DIV:
                    return int(product1 / product2)
                case Operand.QUOT:
                    return product1 % product2
                case Operand.AND:
                    return product1 & product2
                case Operand.OR:
                    return product1 | product2
                case Operand.XOR:
                    return product1 ^ product2
                case _:
                    raise ValueError(f"Cannot move an integer {product1} into an integer {product2} for this operand {op}")

        # getting if the variable is a register
        is_reg1 = isinstance(product1, str) and product1.startswith(register_id)
        is_reg2 = isinstance(product2, str) and product2.startswith(register_id)
        return_var = ""

        match (is_reg1, is_reg2):
            case True, True: # both are registers
                # free the unused register coming from the destination
                CompilerHelp.free_reg(int(product2[1:]))
                final_commands.append(Command(op, product1, product2))
                return_var = product1
            case False, True: # right is register
                # free the unused register coming from the destination
                CompilerHelp.free_reg(int(product2[1:]))
                final_commands.append(Command(op, product2, product1))
                return_var = product2
            case True, False: # left is register
                final_commands.append(Command(op, product1, product2))
                return_var = product1
            case False, False: # none is a register
                # first get a temp register
                # move the first product into the register
                # then perform the operation on the second product
                temp_reg = CompilerHelp.get_reg()
                final_commands.append(Command(Operand.MOV, temp_reg, product1))
                final_commands.append(Command(op, temp_reg, product2))
                return_var = temp_reg

        return return_var, final_commands

    def add(self, items):
        return self.product_helper(items[0], items[1], Operand.ADD)
    def sub(self, items):
        return self.product_helper(items[0], items[1], Operand.SUB)
    def bit_and(self, items):
        return self.product_helper(items[0], items[1], Operand.AND)
    def bit_or(self, items):
        return self.product_helper(items[0], items[1], Operand.OR)
    def bit_xor(self, items):
        return self.product_helper(items[0], items[1], Operand.XOR)
    def mult(self, items):
        return self.product_helper(items[0], items[1], Operand.MULT)
    def div(self, items):
        return self.product_helper(items[0], items[1], Operand.DIV)
    def quot(self, items):
        return self.product_helper(items[0], items[1], Operand.QUOT)

    
    def increment(self, items) -> list[Command]:
        """ processes examples like var++"""
        return [Command(Operand.ADD, items[0], 1)]
    
    def decrement(self, items) -> list[Command]:
        """ processes examples like var--"""
        return [Command(Operand.SUB, items[0], 1)]

    def block(self, items):
        CompilerHelp.reset()
        return items
    
    # --- assignments functions --------------------------

    def move_helper(self, input1: str|int|tuple[str,list[Command]], input2:str|int|tuple[str,list[Command]], op: Operand) -> list[Command]:
        """
        Helps performs an operand on two inputs.
        Returns the list of commands plus the operand
        """
        # separates the variable with the commands
        product2, final_commands = CompilerHelp.input_helper(input2, [])
        product1, final_commands = CompilerHelp.input_helper(input1, final_commands)
        CompilerHelp.free_all_reg()

        return final_commands + [Command(op, product1, product2)]
    
    def assign_var(self, items) -> list[Command]:
        return self.move_helper(items[0], items[1], Operand.MOV)
    
    def add_assign_var(self, items) -> list[Command]:
        return self.move_helper(items[0], items[1], Operand.ADD)
    
    def sub_assign_var(self, items) -> list[Command]:
        return self.move_helper(items[0], items[1], Operand.SUB)
    
    def mul_assign_var(self, items) -> list[Command]:
        return self.move_helper(items[0], items[1], Operand.MULT)
    
    def div_assign_var(self, items) -> list[Command]:
        return self.move_helper(items[0], items[1], Operand.DIV)
    
    # --- Comparison --------------------------

    def compare_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.move_helper(items[0], items[1], Operand.CMP) + [Command(Operand.JEQ)], (None, None, Compare.COMP)
    
    def compare_not_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.move_helper(items[0], items[1], Operand.CMP) + [Command(Operand.JNE)], (None, None, Compare.COMP)
    
    def compare_greater_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.move_helper(items[0], items[1], Operand.CMP) + [Command(Operand.JGE)], (None, None, Compare.COMP)
    
    def compare_less_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.move_helper(items[0], items[1], Operand.CMP) + [Command(Operand.JLE)], (None, None, Compare.COMP)
    
    def compare_greater(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.move_helper(items[0], items[1], Operand.CMP) + [Command(Operand.JG)], (None, None, Compare.COMP)
    
    def compare_less(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.move_helper(items[0], items[1], Operand.CMP) + [Command(Operand.JL)], (None, None, Compare.COMP)

    def zero_compare(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.move_helper(items[0], 0, Operand.CMP) + [Command(Operand.JNE)], (None, None, Compare.COMP)

    def and_compare(self, items: list[tuple[list[Command], tuple[int, int, Compare]]]) -> tuple[list[Command], tuple[int, int, Compare]]:
        block1 = items[0][0]
        block2 = items[1][0]
        fail_label1 = items[0][1][0]
        true_label1 = items[0][1][1]
        type1 = items[0][1][2]
        fail_label2 = items[1][1][0]
        true_label2 = items[1][1][1]
        type2 = items[1][1][2]

        final_true = None
        final_fail = jm.remove_duplicate(fail_label2, fail_label1)

        if type1 == Compare.COMP:
            block1[-1].location = final_fail
            block1[-1].negate_jump()
        if type2 == Compare.COMP:
            block2[-1].location = final_fail
            block2[-1].negate_jump()

        if true_label1 is not None:
            block1.append(CommandLabel(true_label1))

        if type1 != Compare.COMP and type2 != Compare.COMP:
            final_true = true_label2

        return block1 + block2, (final_fail, final_true, Compare.ANDS)

    def or_compare(self, items: list[tuple[list[Command], tuple[int, int, Compare]]]) -> tuple[list[Command], tuple[int, int, Compare]]:
        block1 = items[0][0]
        block2 = items[1][0]
        fail_label1 = items[0][1][0]
        true_label1 = items[0][1][1]
        type1 = items[0][1][2]
        fail_label2 = items[1][1][0]
        true_label2 = items[1][1][1]
        type2 = items[1][1][2]

        final_true = jm.remove_duplicate(true_label1, true_label2)
        final_fail = jm.remove_duplicate(fail_label2)

        block1[-1].location = final_true
        if type1 is not Compare.COMP:
            block1[-1].negate_jump()

        if type2 == Compare.COMP:
            block2[-1].location = final_fail
            block2[-1].negate_jump()

        if fail_label1 is not None:
            block1.append(CommandLabel(fail_label1))

        return block1 + block2, (final_fail, final_true, Compare.ORS)

    # --- loops declaration --------------------------

    @staticmethod
    def loop_helper(true_label, fail_label, condition_block, compare_type):

        if true_label is None:
            true_label = jm.get_jump()

        condition_block[-1].location = true_label
        if compare_type != Compare.COMP:
            condition_block[-1].negate_jump()

        if fail_label is not None:
            condition_block.append(CommandLabel(fail_label))

        return true_label

    def for_loop(self, items) -> list[Command]:
        initialization = items[0]
        condition = items[1]
        increment = items[2]
        main_block = self.list_in_list(items[3:])
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]

        start_loop_label = jm.get_jump()

        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = (initialization + [CommandJump(start_loop_label), CommandLabel(true_label)] +
                          main_block + increment + [CommandLabel(start_loop_label)] + condition_block)

        return [CommandInnerStart()] + final_commands + [CommandInnerEnd()]

    def while_loop(self, items) -> list[Command]:
        condition = items[0]
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]
        main_block = self.list_in_list(items[1:])

        start_loop_label = jm.get_jump()

        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = ([CommandJump(start_loop_label), CommandLabel(true_label)] + main_block  +
                          [CommandLabel(start_loop_label)] + condition_block)

        return [CommandInnerStart()] + final_commands + [CommandInnerEnd()]
    
    def do_while_loop(self, items) -> list[Command]:
        condition = items[-1]
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]
        main_block = self.list_in_list(items[:-1])
        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = [CommandLabel(true_label)] + main_block + condition_block

        return [CommandInnerStart()] + final_commands + [CommandInnerEnd()]

    # --- if-else declaration --------------------------
    @staticmethod
    def if_helper(compare_type:int, fail_label: int, true_label:int, compare_block: list[Command], main_block: list[Command]) -> list[Command]:
        if compare_type == Compare.COMP:
            compare_block[-1].negate_jump()
            fail_label = jm.get_jump()
            compare_block[-1].location = fail_label

        if fail_label is None:
            raise ValueError("if statement must have a fail condition")
        else:
            main_block.append(CommandLabel(fail_label))

        if true_label is not None:
            compare_block.append(CommandLabel(true_label))

        return [CommandInnerStart()] + compare_block + main_block + [CommandInnerEnd()]

    def else_statement(self, items: list[list[Command]]) -> tuple[list[Command]]:
        return ([CommandInnerStart()] + self.list_in_list(items) + [CommandInnerEnd()],)

    def elif_statement(self, items) -> tuple[list[Command]]:
        elif_compare = items[0][0]
        elif_fail_label = items[0][1][0]
        elif_true_label = items[0][1][1]
        elif_compare_type = items[0][1][2]
        elif_block = self.list_in_list(items[1:])

        return (self.if_helper(elif_compare_type, elif_fail_label, elif_true_label, elif_compare, elif_block),)

    def if_statement(self, items) -> list[Command]:
        if_compare = items[0][0]
        if_fail_label = items[0][1][0]
        if_true_label = items[0][1][1]
        if_compare_type = items[0][1][2]

        if_block_ends = 2
        for item in items[2:]:
            if isinstance(item, list):
                if_block_ends += 1
            else:
                break

        if_block = self.list_in_list(items[1:if_block_ends])

        final_commands = self.if_helper(if_compare_type, if_fail_label, if_true_label, if_compare, if_block)

        final_jump_label = jm.get_jump()
        final_jump = CommandJump(final_jump_label)


        for item in items[if_block_ends:]:
            final_commands.insert(-1, final_jump)
            final_commands.extend(item[0])

        if final_commands[-1].op != Operand.LABEL:
            final_commands.append(CommandLabel(final_jump_label))
        else:
            jm.remove_duplicate(final_jump_label, final_commands[-1].location)

        return final_commands

    def list_in_list(self,list_of_lists): # the body of the elif/else statements are in nested lists
        result = []
        for item in list_of_lists:
            if isinstance(item, list):
                result.extend(self.list_in_list(item))
            else:
                result.append(item)
        return result

    # --- function declaration --------------------------
    def function_declaration(self, items) -> list[Command]:
        function_name: str = items[0]
        function_arguments: list[str] = items[1]
        main_block: list[Command] = self.list_in_list(items[2:])

        found_none:bool = True
        for block in main_block:
            if isinstance(block, Command) and block.op == Operand.RETURN_HELPER:
                shared_rtn.validate_return(function_name, len(block.source))
                found_none = False

        if found_none:
            shared_rtn.validate_return(function_name, 0)

        shared_rtn.validate_arg(function_name, len(function_arguments))
        var_all: Ram = Ram(function_name)
        var_all.set_arguments(function_arguments)

        if function_name in ["VID", "VID_V", "VID_X", "VID_Y", "VIDEO", "HALT"]:
            raise ValueError(f"{function_name} is a reserved function")

        function_label = jm.get_function(function_name)
        final_block = [CommandLabel(function_label),
                       Command(Operand.MOV, RamVar(0), base_pointer()),  # push the base_pointer
                       Command(Operand.MOV, base_pointer(), stack_pointer()),  # starting function's frame
                       ]

        for i, arg in enumerate(main_block):
            if isinstance(arg, tuple):
                main_block[i] = arg[1][0]

        var_all.compute_lifetimes(main_block)

        for arg in function_arguments:
            var_all.set_lifetime(arg, -1)

        for i, item in enumerate(main_block, start=0):
            if item.op == Operand.INNER_START:
                var_all.inner_start()
            elif item.op == Operand.INNER_END:
                var_all.inner_end()
            else:
                final_block.extend(var_all.allocate_command(item, i, function_name))

        if function_name == "main":
            final_block.extend([Command(Operand.HALT), CommandJump(function_label)])


        return final_block
    # --- function call --------------------------

    def list_assign(self, items):
        return items
    
    def empty_args(self, items):
        return []
    
    def args(self, items):
        return items
    
    def function_call(self, items) -> tuple[str,list[Command]]:
        # source is returns and dest is arguments, .other is the name of the function
        temp = Command(Operand.CALL_HELPER, [], items[1])
        temp.other = items[0] # the name of the function
        return "", [temp]

    def empty_return_args(self, items):
        return []
    def return_args(self, items):
        return items
    def _return(self, items):
        return_items: list[str|int] = items[0] if items else []
        return [CommandReturn(return_items)]

    def multi_assign_var(self, items) -> list[Command]:
        to_assign: list[str] = items[0]
        from_assign: list[int|str|tuple[str,list[Command]]] = items[1:]
        if len(to_assign) < len(from_assign):
            raise SyntaxError(f"Too few arguments: {to_assign}")
        size_function: int = len(to_assign) - len(from_assign) +1

        final_commands = []
        to_offset = 0
        for i, assign in enumerate(from_assign):
            match assign:
                case int()| str():
                    final_commands.append(Command(Operand.MOV, to_assign[i + to_offset], assign))
                case tuple():
                    if assign[0] == "":
                        assign[1][-1].source = to_assign[i + to_offset: i + to_offset + size_function]
                        if size_function != 1:
                            to_offset = size_function - 1
                            size_function = 1
                        final_commands.extend(assign[1])
                    else:
                        final_commands.extend(assign[1])
                        final_commands.append(Command(Operand.MOV, to_assign[i + to_offset], assign[0]))


        return final_commands

    def start(self, items):
        return self.list_in_list(items)

# reads the program
with open('program.txt', 'r') as file:
    program = file.read()

# gets the parse-tree and writes it to program.tre
parse_tree = code_parser.parse(program)
with open('program.tre', 'w') as f:
    f.write(parse_tree.pretty())

transformed = CodeTransformer().transform(parse_tree)

# gets the assembly string and writes it to program.asm
index = 0
asm_str:str = ""
for cmd in transformed:
    if cmd.op == Operand.LABEL:
        jm.set_pos(cmd.location, index)
    else:
        index += cmd.num_instruct()
    asm_str += str(cmd) + "\n"

with open('program.asm', 'w') as f:
    f.write(asm_str)

# gets the binary string and writes it to program.hex
binary_str = ""
for cmd in transformed:
    cmd.compute_op()
    binary_str += cmd.get_binary()

with open('program.hex', 'w') as f:
    f.write(binary_str)