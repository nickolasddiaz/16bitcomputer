from typing import Any

from lark import Lark, Transformer
from enum import auto, IntEnum
from operand import Operand

code_parser = Lark(r"""
    ?start: function_definition*

    ?function_definition:"def" NAME "(" args ")" "{" inline_block* "}"-> function_declaration

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
        self.jumps = dict()

    def get_jump(self, jump_name: None|str = None) -> str:
        self.counters += 1
        if isinstance(jump_name, str):
            name = jump_name
            self.jumps[name] = 0 # to be determined later
            return name
        else:
            name = "L"
            self.jumps[name] = 0 # to be determined later
            return f".{name}{self.counters}"


class Command:
    def __init__(self, op: "Operand", source: str = None, dest: int|str = None, location: str = None) -> None:
        self.op = op
        self.source = source
        self.dest = dest
        self.location = location

    def __str__(self) -> str:
        if self.op == Operand.LABEL:
            return f"{self.location}:"
        output = f"\t{self.op.name}"
        if self.source is not None:
            output += f", {self.source}"
        if self.dest is not None:
            output += f", {self.dest}"
        if self.location is not None:
            output += f", {self.location}"
        return output
    def negate_jump(self):
        self.op = self.op.negate()


class CodeTransformer(Transformer):
    def __init__(self):
        self.block = []
        self.jm = JumpManager()
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

    def and_compare(self, items: list[tuple[list[Command], tuple[str, str, Compare]]]) -> tuple[list[Command], tuple[str, str, Compare]]:
        block1 = items[0][0]
        block2 = items[1][0]
        fail_label1 = items[0][1][0]
        true_label1 = items[0][1][1]
        type1 = items[0][1][2]
        fail_label2 = items[1][1][0]
        true_label2 = items[1][1][1]
        type2 = items[1][1][2]

        final_fail = None
        final_true = None

        match (type1, type2):
            case Compare.COMP, Compare.COMP:
                final_fail = self.jm.get_jump()
                block1[-1].location = final_fail # set fail label
                block1[-1].negate_jump() # negate jump
                block2[-1].location = final_fail
                block2[-1].negate_jump()
            case Compare.COMP, Compare.ANDS:
                final_fail = fail_label2
                block1[-1].location = final_fail
                block1[-1].negate_jump()
            case Compare.ANDS, Compare.COMP:
                final_fail = fail_label1
                block2[-1].location = final_fail
                block2[-1].negate_jump()
            case Compare.ANDS, Compare.ANDS:
                final_fail = f"{fail_label1},{fail_label2}"
            case Compare.COMP, Compare.ORS:
                final_fail = fail_label2
                final_true = true_label2
                block1[-1].location = final_fail
                block1[-1].negate_jump()
            case Compare.ORS, Compare.COMP:
                final_fail = fail_label1
                block1.append(Command(Operand.LABEL, None, None, true_label1))
                block1[-1].location = final_fail
                block1[-1].negate_jump()
            case Compare.ORS, Compare.ORS:
                final_fail = f"{fail_label1},{fail_label2}"
                final_true = true_label2
                block1.append(Command(Operand.LABEL, None, None, true_label1))
            case Compare.ANDS, Compare.ORS:
                final_fail = f"{fail_label1},{fail_label2}"
                final_true = true_label2
            case Compare.ORS, Compare.ANDS:
                block1.append(Command(Operand.LABEL, None, None, true_label1))
                final_fail = f"{fail_label1},{fail_label2}"
            case _:
                raise ValueError(f"illegal comparison for {items}")

        return block1 + block2, (final_fail, final_true, Compare.ANDS)

    def or_compare(self, items: list[tuple[list[Command], tuple[str, str, Compare]]]) -> tuple[list[Command], tuple[str, str, Compare]]:
        block1 = items[0][0]
        block2 = items[1][0]
        fail_label1 = items[0][1][0]
        true_label1 = items[0][1][1]
        type1 = items[0][1][2]
        fail_label2 = items[1][1][0]
        true_label2 = items[1][1][1]
        type2 = items[1][1][2]

        final_fail = None
        final_true = None

        match (type1, type2):
            case Compare.COMP, Compare.COMP:
                final_fail = self.jm.get_jump()
                final_true = self.jm.get_jump()
                block1[-1].location = final_true  # set fail label
                block2[-1].location = final_fail
                block2[-1].negate_jump() # negate jump
            case Compare.COMP, Compare.ANDS:
                final_true = self.jm.get_jump()
                final_fail = fail_label2
                block1[-1].location = final_true
            case Compare.ANDS, Compare.COMP:
                final_true = self.jm.get_jump()
                final_fail = self.jm.get_jump()
                block1[-1].location = final_true
                block1[-1].negate_jump()
                block2[-1].location = final_true
                block2[-1].negate_jump()
                block1.append(Command(Operand.LABEL, None, None, fail_label1))
            case Compare.ANDS, Compare.ANDS:
                if true_label1 is not None:
                    final_true = true_label1
                else:
                    final_true = self.jm.get_jump()
                final_fail = fail_label2
                block1[-1].location = final_true
                block1[-1].negate_jump()
                block1.append(Command(Operand.LABEL, None, None, fail_label1))
            case Compare.COMP, Compare.ORS:
                final_true = true_label2
                final_fail = fail_label2
                block1[-1].location = final_true
            case Compare.ORS, Compare.COMP:
                final_true = true_label1
                final_fail = fail_label1
                block1[-1].location = final_true
                block1[-1].negate_jump()
                block2[-1].location = final_fail
                block2[-1].negate_jump()
            case Compare.ORS, Compare.ORS:
                final_true = f"{true_label1},{true_label2}"
                final_fail = f"{fail_label1},{fail_label2}"
                block1[-1].location = final_true
                block1[-1].negate_jump()
            case Compare.ANDS, Compare.ORS:
                final_true = f"{true_label1},{true_label2}"
                final_fail = fail_label2
                block1[-1].location = final_true
                block1[-1].negate_jump()
                block1.append(Command(Operand.LABEL, None, None, fail_label1))
            case Compare.ORS, Compare.ANDS:
                final_true = true_label1
                final_fail = fail_label2
                if fail_label1 is not None:
                    block2.insert(0, Command(Operand.LABEL, None, None, fail_label1))
                block1[-1].location = final_true
                block1[-1].negate_jump()
            case _:
                raise ValueError(f"illegal comparison for {items}")


        return block1 + block2, (final_fail, final_true, Compare.ORS)

    # --- loops declaration --------------------------

    def for_loop(self, items) -> list[str]:
        # items are list[list[Commands], Tuple(Label, list[Commands]), list[Commands], list[Commands]]
        # first variable list[Commands] is the init part
        # second variable label is the where it will jump to if true
        # third variable list[Commands] is the list of commands to reach the comparison
        # fourth variable list[Commands] is the increment part
        # fifth variable list[Commands] is the body of the for loop
        # Overall Structure: init, start_label, leading_Conditions, comparison_jump, Jump_to_end, jump_label, body, increment, jump_to_start, end_label
        if len(items) < 4:
            raise ValueError("For loop must have at least init, condition, increment, and body.")

        init_commands = items[0]
        jump_label = items[1][0] # the incomplete jump command
        jump_command_label = ('NOP', None, None, jump_label)
        comparison_commands = items[1][1]
        if 0 <= 2 < len(items[1]): # there is a third item in to remove the jump from the insert
            comparison_commands.append(items[1][2]) # the register allocation needs to go before the jump

        increment_commands = items[2]
        body_commands = self.list_in_list(items[3:])




        if not body_commands:
            raise ValueError("For loop must have a body.")
        if not comparison_commands:
            raise ValueError("While loop must have a condition.")
        
        comparison_commands.insert(0, ('NOP', None, None)) # add the jump label command to the start of the comparison




        return init_commands

    def while_loop(self, items) -> list[str]:

        return items
    
    def do_while_loop(self, items) -> list[str]:
        return items
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
         
    def else_statement(self, items):
        return items

    def elif_statement(self, items):
        return items

    def if_statement(self, items) -> list[str]:
        for i in items[0][0]:
            print(i)
        print(f"\nfail_label: {items[0][1][0]}")
        print(f"true_label: {items[0][1][1]}")
        raise ValueError(items)
        return items
    
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
