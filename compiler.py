from typing import Any

from lark import Lark, Transformer
from enum import auto, IntEnum
from ram import Operand, Command, jm, Ram, ram_var, reg_var, base_pointer, stack_pointer
from functools import partial

code_parser = Lark(r"""
    ?start: function_definition+

    ?function_definition: ("def"i | "int"i) NAME "(" args ")" "{" inline_block+ "}"-> function_declaration

    ?inline_block: statements
        | block ";"

    ?statements: "for"i "(" assigns ";" compares ";" assigns ")" "{" inline_block+ "}" -> for_loop
        | "while"i "(" compares ")" "{" inline_block+ "}"          -> while_loop
        | "if"i "(" compares ")" "{" inline_block+ "}" elif_statement* else_statement? -> if_statement
        | "do"i "{" inline_block+ "}" "while"i "(" compares ");"-> do_while_loop

    ?elif_statement: "elif"i "(" compares ")" "{" inline_block+ "}" -> elif_statement

    ?else_statement: "else"i "{" inline_block+ "}" -> else_statement

    ?args: (NAME|NUMBER) ("," (NAME|NUMBER))* -> args
        |                  -> empty_args

    ?block: assigns 
        | "return"i return_args -> _return

    ?return_args: expr ("," expr)* -> return_args
                |                  -> empty_return_args


    ?assigns: NAME "=" expr -> assign_var
        | NAME "+=" expr -> add_assign_var
        | NAME "-=" expr -> sub_assign_var
        | NAME "*=" expr -> mul_assign_var
        | NAME "/=" expr -> div_assign_var
        | NAME "++" -> increment
        | NAME "--" -> decrement
        | (assignment_list "=")* function_call -> func_assign


    ?assignment_list: (NAME ",")*

    ?compares: expr "==" expr -> compare_equal
        | expr "!=" expr -> compare_not_equal
        | expr ">=" expr -> compare_greater_equal
        | expr "<=" expr -> compare_less_equal
        | expr ">" expr -> compare_greater
        | expr "<" expr -> compare_less
        | compares ("&&"|"and"i) compares -> and_compare
        | compares ("||"|"or"i) compares -> or_compare
        | "(" compares ")"

    ?expr: sum

    ?sum: product
        | sum "+" product -> add
        | sum "-" product -> sub
        | product "&" atom -> bit_and
        | product "|" atom -> bit_or
        | product "^" atom -> bit_xor

    ?product: atom
        | product "*" atom -> mult
        | product "/" atom -> div
        | product "%" atom -> quot

    ?atom: var
    | const
    | "(" expr ")"

    ?const: NUMBER -> number
        | HEX -> hex_number

    ?var: NAME -> var
        | "~" var -> nott

    ?function_call: NAME "(" args ")" -> function_call

    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE
    %import common.NEWLINE
    %import python.HEX_NUMBER -> HEX
    %ignore WS_INLINE
    %ignore NEWLINE
""", start='start', parser='lalr')


class Compare(IntEnum):
    COMP = auto()
    ANDS = auto()
    ORS = auto()


CommandLabel = partial(Command, Operand.LABEL, None, None)
CommandJump = partial(Command, Operand.JMP, None, None)
CommandInnerStart = partial(Command, Operand.INNER_START, None, None, None)
CommandInnerEnd = partial(Command, Operand.INNER_END, None, None, None)


class CodeTransformer(Transformer):
    def __init__(self):
        self.block = []
    def getblock(self):
        temp = self.block
        self.block = []
        return temp

       # --- var/number functions --------------------------
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

    def nop(self, items):
        return ('NOP',),
    # --- product functions --------------------------
    def product_helper(self, product1: int|str, product2: int|str, op: Operand, swap:bool = False) -> int|str:
        if swap and product2 == "":
            product1, product2 = product2, product1

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
                    raise ValueError(f"Cannot move an integer {product1} into an integer {product2}"
                                     f"for this operand {op}")

        # swap the variables right variable and left int
        if isint1 and not isint2 and op not in [Operand.DIV, Operand.QUOT]: # these operations are order dependent
            product1, product2 = product2, product1

        self.block.append(Command(op, product1, product2))
        return ""

    def add(self, items):
        return self.product_helper(items[0], items[1], Operand.ADD, True)
    def sub(self, items):
        return self.product_helper(items[0], items[1], Operand.SUB)
    def bit_and(self, items):
        return self.product_helper(items[0], items[1], Operand.AND)
    def bit_or(self, items):
        return self.product_helper(items[0], items[1], Operand.OR)
    def bit_xor(self, items):
        return self.product_helper(items[0], items[1], Operand.XOR)
    def mult(self, items):
        return self.product_helper(items[0], items[1], Operand.MULT, True)
    def div(self, items):
        return self.product_helper(items[0], items[1], Operand.DIV)
    def quot(self, items):
        return self.product_helper(items[0], items[1], Operand.QUOT)

    
    def increment(self, items) -> list[Command]:
        return [Command(Operand.ADD, items[0], 1)]
    
    def decrement(self, items) -> list[Command]:
        return [Command(Operand.SUB, items[0], 1)]
    
    # --- assignments functions --------------------------

    
    def assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.MOV)
        return self.getblock()
    
    def add_assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.ADD)
        return self.getblock()
    
    def sub_assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.SUB)
        return self.getblock()
    
    def mul_assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.MULT)
        return self.getblock()
    
    def div_assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.DIV)
        return self.getblock()
    
    # --- Comparison --------------------------

    def compare_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        self.product_helper(items[0], items[1], Operand.CMP)
        self.block.append(Command(Operand.JEQ))
        return self.getblock(), (None, None, Compare.COMP)
    
    def compare_not_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        self.product_helper(items[0], items[1], Operand.CMP)
        self.block.append(Command(Operand.JNE))
        return self.getblock(), (None, None, Compare.COMP)
    
    def compare_greater_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        self.product_helper(items[0], items[1], Operand.CMP)
        self.block.append(Command(Operand.JGE))
        return self.getblock(), (None, None, Compare.COMP)
    
    def compare_less_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        self.product_helper(items[0], items[1], Operand.CMP)
        self.block.append(Command(Operand.JLE))
        return self.getblock(), (None, None, Compare.COMP)
    
    def compare_greater(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        self.product_helper(items[0], items[1], Operand.CMP)
        self.block.append(Command(Operand.JG))
        return self.getblock(), (None, None, Compare.COMP)
    
    def compare_less(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        self.product_helper(items[0], items[1], Operand.CMP)
        self.block.append(Command(Operand.JL))
        return self.getblock(), (None, None, Compare.COMP)

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
        var_all: Ram = Ram()
        function_name: str = items[0]
        function_arguments: list[str] = items[1]
        var_all.set_arguments(function_arguments)
        main_block: list[Command] = self.list_in_list(items[2:])

        function_label = jm.get_function(function_name)
        final_block = [CommandLabel(function_label),
                       Command(Operand.MOV, ram_var(0), base_pointer()), # push the base_pointer
                       Command(Operand.MOV, base_pointer(), stack_pointer()), # starting function's frame
                       ]

        var_all.compute_lifetimes(main_block)

        for index, item in enumerate(main_block, start=0):
            if item.op == Operand.INNER_START:
                var_all.inner_start()
            elif item.op == Operand.INNER_END:
                var_all.inner_end()
            else:
                final_block.extend(var_all.allocate_command(item, index))

        final_block.extend([Command(Operand.MOV, stack_pointer(), base_pointer()), # cleaning function's frame
                            Command(Operand.MOV, ram_var(0), base_pointer()) # pop the base_pointer
                            ])

        if function_name == "main":
            final_block.extend([Command(Operand.HALT), CommandJump(function_label)])

        for cmd in final_block:
            cmd.compute_op()

        return final_block
    # --- function call --------------------------

    def assignment_list(self, items):
        return items
    
    def empty_args(self, items):
        return []
    
    def args(self, items):
        return items
    
    def function_call(self, items):
        return items[0], items[1]

    def func_assign(self, items):
        if len(items) == 2:
            assign_vars: list[str] = items[0]
            arguments: list[int|str] = items[1][1]
            function_name: str = items[1][0]
        else:
            assign_vars: list[str] = []
            arguments: list[int|str] = items[0][1]
            function_name: str = items[0][0]

        final_commands = [Command(Operand.SET_VARIABLE_MAX)]

        for i, arg in enumerate(arguments): # simulate move the arguments into correct position in reverse order
            # the -(i +1), is to append it to the front of all the vars, example -3 and the max index of variables is 4, it would be in index 7, so (3 + 4)
            final_commands.append(Command(Operand.MOV, -(i +1), arg))

        final_commands.append(Command(Operand.CALL,None, None, jm.get_function(function_name)))

        for i, arg in enumerate(assign_vars): # moves the return arguments back to their variable location
            final_commands.append(Command(Operand.MOV, arg, -(i +1)))

        return final_commands

    def empty_return_args(self, items):
        return []
    def return_args(self, items):
        return items
    def returnn(self, items):
        return_items = items[0] if items else []
        return [('RETURN', None, return_items)]


with open('program.txt', 'r') as file:
    program = file.read()


parse_tree = code_parser.parse(program)
print("Parse Token Tree:\n")
print(parse_tree)
print("\nPretty Print Parse Token Tree:\n")
print(parse_tree.pretty())

transformed = CodeTransformer().transform(parse_tree)

print("\nAssembly Code:\n")

index = 0
for cmd in transformed:
    if cmd.op == Operand.LABEL:
        jm.set_pos(cmd.location, index)
    else:
        index = index + 1
    print(cmd)

print("\nMachine Code:\n")
for cmd in transformed:
    print(cmd.get_binary(), end="")