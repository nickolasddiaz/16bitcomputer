from typing import Any

from lark import Lark, Transformer
from enum import auto, IntEnum
from ram import Operand, Command, jm, Ram, Ram_Var, reg_var, base_pointer, stack_pointer, shared_rtn
from functools import partial
import heapq


code_parser = Lark(r"""
    ?start: function_definition+

    ?function_definition: ("def"i | "int"i) NAME "(" args ")" "{" inline_block+ "}" -> function_declaration
    
    ?inline_block: statements
        | block ";"
    
    ?statements: "for"i "(" assigns ";" compares ";" assigns ")" "{" inline_block+ "}" -> for_loop
        | "while"i "(" compares ")" "{" inline_block+ "}" -> while_loop
        | "if"i "(" compares ")" "{" inline_block+ "}" elif_statement* else_statement? -> if_statement
        | "do"i "{" inline_block+ "}" "while"i "(" compares ")" ";" -> do_while_loop
    
    ?elif_statement: "elif"i "(" compares ")" "{" inline_block+ "}" -> elif_statement
    
    ?else_statement: "else"i "{" inline_block+ "}" -> else_statement
    
    ?args: (NAME|NUMBER) ("," (NAME|NUMBER))* -> args
        | -> empty_args
    
    ?block: assigns 
        | "return"i return_args -> _return
    
    ?return_args: sum ("," sum)* -> return_args
        | -> empty_return_args
    
    ?assigns: NAME "=" sum -> assign_var
        | NAME "+=" sum -> add_assign_var
        | NAME "-=" sum -> sub_assign_var
        | NAME "*=" sum -> mul_assign_var
        | NAME "/=" sum -> div_assign_var
        | NAME "++" -> increment
        | NAME "--" -> decrement
        | list_assign "=" sum (","sum)* -> multi_assign_var
        | function_call
    
    ?list_assign: NAME (","NAME)+
    
    ?compares: sum "==" sum -> compare_equal
        | sum "!=" sum -> compare_not_equal
        | sum ">=" sum -> compare_greater_equal
        | sum "<=" sum -> compare_less_equal
        | sum ">" sum -> compare_greater
        | sum "<" sum -> compare_less
        | compares ("&&"|"and"i) compares -> and_compare
        | compares ("||"|"or"i) compares -> or_compare
        | "(" compares ")"
    
    ?sum: product
        | sum "+" product -> add
        | sum "-" product -> sub
    
    ?product: atom
        | product "*" atom -> mult
        | product "/" atom -> div
        | product "%" atom -> quot
        | product "&" atom -> bit_and
        | product "|" atom -> bit_or
        | product "^" atom -> bit_xor
    
    ?atom: NUMBER -> number
        | HEX -> hex_number
        | NAME -> var
        | function_call
        | "~" atom -> bit_not
        | "(" sum ")"
    
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
CommandReturn = partial(Command, Operand.RETURN_HELPER)


class temp_helper:
    def __init__(self):
        self._dead_temp: list[int] = [0]
        heapq.heapify(self._dead_temp)

    def del_var(self, var: int):
        heapq.heappush(self._dead_temp, var)

    def app_var(self) -> str:
        temp = heapq.heappop(self._dead_temp)
        if not self._dead_temp:
            heapq.heappush(self._dead_temp, temp + 1)
        return f"#{temp}"

temp_help = temp_helper()

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
        return f"{name.value}_"

    def nop(self, items):
        return ('NOP',),

    def bit_not(self, items):
        return items[0],[Command(Operand.NOT, items[0])]

    # --- product functions --------------------------
    def product_helper(self, input1: int|str|tuple[str,list[Command]], input2: int|str|tuple[str,list[Command]], op: Operand) -> int|str|tuple[int | str, list[Command]]:
        final_commands = []
        if isinstance(input1, tuple):
            final_commands.extend(input1[1])
            product1 = input1[0]
        else:
            product1 = input1

        if isinstance(input2, tuple):
            final_commands.extend(input2[1])
            product2 = input2[0]
        else:
            product2 = input2

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

        is_temp1 = isinstance(product1, str) and product1[0] == "#"
        is_temp2 = isinstance(product2, str) and product2[0] == "#"
        return_var = ""

        match (is_temp1, is_temp2):
            case True, True:
                temp_help.del_var(int(product2[1:]))
                final_commands.append(Command(op, product1, product2))
                return_var = product1
            case False, True:
                temp_help.del_var(int(product2[1:]))
                final_commands.append(Command(op, product2, product1))
                return_var = product2
            case True, False:
                final_commands.append(Command(op, product1, product2))
                return_var = product1
            case False, False:
                temp_var = temp_help.app_var()
                final_commands.append(Command(Operand.MOV, temp_var, product1))
                final_commands.append(Command(op, temp_var, product2))
                return_var = temp_var


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
        return [Command(Operand.ADD, items[0], 1)]
    
    def decrement(self, items) -> list[Command]:
        return [Command(Operand.SUB, items[0], 1)]
    
    # --- assignments functions --------------------------

    
    def assign_var(self, items):
        temp = self.product_helper(items[0], items[1], Operand.MOV)
        for i in temp[1]:
            print(i)
        raise ValueError(temp)
        return temp[1] + [Command(Operand.MOV, temp[0], temp[1])]
    
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
        function_name: str = items[0]
        function_arguments: list[str] = items[1]
        var_all: Ram = Ram(function_name)
        var_all.set_arguments(function_arguments)
        main_block: list[Command] = self.list_in_list(items[2:])

        function_label = jm.get_function(function_name)
        final_block = [CommandLabel(function_label),
                       Command(Operand.MOV, Ram_Var(0), base_pointer()),  # push the base_pointer
                       Command(Operand.MOV, base_pointer(), stack_pointer()),  # starting function's frame
                       ]

        var_all.compute_lifetimes(main_block)

        for i, item in enumerate(main_block, start=0):
            if item.op == Operand.INNER_START:
                var_all.inner_start()
            elif item.op == Operand.INNER_END:
                var_all.inner_end()
            else:
                final_block.extend(var_all.allocate_command(item, i, function_name))

        if function_name == "main":
            final_block.extend([Command(Operand.HALT), CommandJump(function_label)])

        for command in final_block:
            command.compute_op()

        return final_block
    # --- function call --------------------------

    def list_assign(self, items):
        return items
    
    def empty_args(self, items):
        return []
    
    def args(self, items):
        return items
    
    def function_call(self, items):
        temp = Command(Operand.CALL_HELPER, [], items[1])
        temp.other = items[0] # the name of the function
        return temp

    def empty_return_args(self, items):
        return []
    def return_args(self, items):
        return items
    def _return(self, items):
        return_items: list[str|int] = items[0] if items else []
        return [CommandReturn(return_items)]

    def multi_assign_var(self, items) -> list[Command]:
        to_assign: list[str] = items[0]
        from_assign: list[int|str|tuple|Command] = items[1:]
        if len(to_assign) < len(from_assign):
            raise SyntaxError(f"Too few arguments: {to_assign}")
        size_function: int = len(to_assign) - len(from_assign) +1

        final_commands = []
        to_offset = 0
        for index, assign in enumerate(from_assign):
            match(assign):
                case int()| str():
                    final_commands.append(Command(Operand.MOV, to_assign[index + to_offset], assign))
                case tuple():
                    final_commands.extend(assign[1])
                    final_commands.append(Command(Operand.MOV, to_assign[index + to_offset], assign[0]))
                case Command():
                    assign.source = to_assign[index + to_offset: index + to_offset + size_function]
                    if size_function != 1:
                        to_offset = size_function -1
                        size_function = 1
                    final_commands.append(assign)

        return final_commands
    def start(self, items):
        return self.list_in_list(items)


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