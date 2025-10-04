from typing import Any

from lark import Lark, Transformer
from enum import auto, IntEnum
from operand import Operand
from functools import partialmethod, partial

code_parser = Lark(r"""
    ?start: function_definition*

    ?function_definition: ("def"i | "int"i) NAME "(" args ")" "{" inline_block* "}"-> function_declaration

    ?inline_block: statements
        | block ";"

    ?statements: "for"i "(" assigns? ";" compares? ";" assigns? ")" "{" inline_block* "}" -> for_loop
        | "while"i "(" compares ")" "{" inline_block* "}"          -> while_loop
        | "if"i "(" compares ")" "{" inline_block* "}" elif_statement* else_statement? -> if_statement
        | "do"i "{" inline_block* "}" "while"i "(" compares ");"-> do_while_loop

    ?elif_statement: "elif"i "(" compares ")" "{" inline_block* "}" -> elif_statement

    ?else_statement: "else"i "{" inline_block* "}" -> else_statement

    ?args: (NAME|NUMBER) ("," (NAME|NUMBER))* -> args
        |                  -> empty_args

    ?block: assigns 
        | function_call -> function_call_statement
        | "return"i return_args -> returnn

    ?return_args: expr ("," expr)* -> return_args
                |                  -> empty_return_args

    ?assigns: single_assign | multiple_assign

    ?single_assign: NAME "=" expr -> assign_var
        | NAME "+=" expr -> add_assign_var
        | NAME "-=" expr -> sub_assign_var
        | NAME "*=" expr -> mul_assign_var
        | NAME "/=" expr -> div_assign_var
        | NAME "++" -> increment
        | NAME "--" -> decrement

    ?multiple_assign: assignment_list "=" expr -> multiple_assign

    ?assignment_list: NAME ("," NAME)+

    ?compares: expr "==" expr -> compare_equal
        | expr "!=" expr -> compare_not_equal
        | expr ">=" expr -> compare_greater_equal
        | expr "<=" expr -> compare_less_equal
        | expr ">" expr -> compare_greater
        | expr "<" expr -> compare_less
        | compares "and" compares -> and_compare
        | compares "&&" compares -> and_compare
        | compares "or" compares -> or_compare
        | compares "||" compares -> or_compare
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
    | function_call
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


class JumpManager:
    def __init__(self):
        self.counters = 0
        self.names = dict() # key: id, value: name
        self.jumps = dict() # key: name, value: position

    def get_jump(self) -> int:
        self.names[self.counters] = str(self.counters)
        self.jumps[str(self.counters)] = 0
        self.counters += 1
        return self.counters - 1

    def get_function(self, jump_name: str) -> int:
        self.names[self.counters] = jump_name
        self.jumps[jump_name] = 0
        self.counters += 1
        return self.counters -1

    def get_name(self, id_: int) -> str:
        if self.names[id_].isdigit():
            return f".L{self.names[id_]}"
        else:
            return f".{self.names[id_]}"

    def remove_duplicate(self, id1: int|None, id2: int|None = None) -> int:
        match (id1 is None, id2 is None):
            case (True, True):
                return self.get_jump()
            case (False, True):
                return id1
            case(True, False):
                return id2
            case _:
                num_change = self.names[id1]
                num_to_change = self.names[id2]
                del self.jumps[self.names[id2]]
                for key, value in self.names.items():
                    if value == num_to_change:
                        self.names[key] = num_change
                return id1

    def set_pos(self, id_: int, pos: int):
        if self.jumps[self.names[id_]] == 0:
            self.jumps[self.names[id_]] = pos
        else:
            raise ValueError(f"Jump label has already been set: {self.names[id_]}")


class Command:
    def __init__(self, op: "Operand", source: str = None, dest: int|str = None, location: int = None):
        self.op = op
        self.source = source
        self.dest = dest
        self.location = location

    def __str__(self) -> str:
        if self.op == Operand.LABEL:
            return f"{jm.get_name(self.location)}:"
        output = f"\t{self.op.name}"
        if self.source is not None:
            output += f", {self.source}"
        if self.dest is not None:
            output += f", {self.dest}"
        if self.location is not None:
            output += f", {jm.get_name(self.location)}"
        return output
    def negate_jump(self):
        self.op = self.op.negate()

CommandLabel = partial(Command, Operand.LABEL, None, None)
CommandJump = partial(Command, Operand.JMP, None, None)


jm = JumpManager()
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
    def product_helper(self, product1: int|str, product2: int|str, op: "Operand") -> int|str:
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

        if isint1 and not isint2: # swap the variables right variable and left int
            product1, product2 = product2, product1

        if isint1 ^ isint2: # if either is int then have it be immediate
            op = Operand(op.value + 1) # example if add then it turns into addi

        self.block.append(Command(op, product1, product2))
        return product1

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

    
    def increment(self, items) -> tuple[str | int, list[str]]:
        self.block.append(Command(Operand.INC, items[0]))
        return None
    
    def decrement(self, items) -> tuple[str | int, list[str]]:
        self.block.append(Command(Operand.DEC, items[0]))
        return None
    
    # --- assignments functions --------------------------

    
    def assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.MOV)
        return self.getblock()
    
    def add_assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.ADD)
        self.product_helper(items[0], items[1], Operand.MOV)
        return self.getblock()
    
    def sub_assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.SUB)
        self.product_helper(items[0], items[1], Operand.MOV)
        return self.getblock()
    
    def mul_assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.MULT)
        self.product_helper(items[0], items[1], Operand.MOV)
        return self.getblock()
    
    def div_assign_var(self, items):
        self.product_helper(items[0], items[1], Operand.DIV)
        self.product_helper(items[0], items[1], Operand.MOV)
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
        main_block = items[3]
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]

        start_loop_label = jm.get_jump()

        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = (initialization + [CommandJump(start_loop_label), CommandLabel(true_label)] +
                          main_block + increment + [CommandLabel(start_loop_label)] + condition_block)

        return final_commands

    def while_loop(self, items) -> list[Command]:
        condition = items[0]
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]
        main_block = items[1]

        start_loop_label = jm.get_jump()

        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = ([CommandJump(start_loop_label), CommandLabel(true_label)] + main_block  +
                          [CommandLabel(start_loop_label)] + condition_block)

        return final_commands
    
    def do_while_loop(self, items) -> list[Command]:
        condition = items[1]
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]
        main_block = items[0]

        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = [CommandLabel(true_label)] + main_block + condition_block

        return final_commands
    # --- function declaration --------------------------
    def function_declaration(self, items):
        function_name = str(items[0])

        args = items[1] if len(items) > 1 else []
        body = items[2:] if len(items) > 2 else []

        # Handle arguments - check if args is iterable
        if hasattr(args, '__iter__') and not isinstance(args, str):
            for i, arg in enumerate(args):
                if isinstance(arg, tuple): # if arg is a (var_name, commands) tuple
                    var_name, commands = arg

                else:
                    var_name = arg
                self.add_command(function_name, ('mov', var_name, f'arg{i}'))
        
        # Handle body
        for statement in body:
            if isinstance(statement, list):
                for stmt in statement:
                    if isinstance(stmt, tuple): # if stmt is a (var_name, commands) tuple
                        var_name, commands = stmt

            else:
                if isinstance(statement, tuple): # if statement is a (var_name, commands) tuple
                    var_name, commands = statement

        return function_name

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

        return compare_block + main_block

    def else_statement(self, items: list[list[Command]]) -> list[Command]:
        return items[0]

    def elif_statement(self, items) -> list[Command]:
        elif_compare = items[0][0]
        elif_fail_label = items[0][1][0]
        elif_true_label = items[0][1][1]
        elif_compare_type = items[0][1][2]
        elif_block = items[1]

        return self.if_helper(elif_compare_type, elif_fail_label, elif_true_label, elif_compare, elif_block)

    def if_statement(self, items) -> list[Command]:
        if_compare = items[0][0]
        if_fail_label = items[0][1][0]
        if_true_label = items[0][1][1]
        if_compare_type = items[0][1][2]
        if_block = items[1]

        final_commands = self.if_helper(if_compare_type, if_fail_label, if_true_label, if_compare, if_block)

        final_jump_label = jm.get_jump()
        final_jump = CommandJump(final_jump_label)


        for item in items[2:]:
            final_commands.insert(-1, final_jump)
            final_commands.extend(item)

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

    # --- function call --------------------------
    def assignment_list(self, items):
        return items
    
    def empty_args(self, items):
        return []
    
    def args(self, items):
        return items
    
    def function_call(self, items):
        return [(items[0], items[1])]
    
    def multiple_assign(self,items):
        items[1][0].append_assignment(items[0])
        return [items[1][0]]
    
    def function_call_statement(self, items):
        return items[0]

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
print(transformed)
