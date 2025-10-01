from lark import Lark, Transformer
from enum import Enum, auto
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


class Jumps(Enum):
    FOR = auto()
    END_FOR = auto()
    IF_BLOCK = auto()
    IF = auto()
    END_IF = auto()
    ELIF = auto()
    ELSE = auto()
    WHILE = auto()
    DO_WHILE = auto()
    END_WHILE = auto()
    COMPARE = auto()
    COMPARE_AND = auto()
    COMPARE_OR = auto()
    COMPARE_AND_FALSE = auto()

class JumpManager:
    def __init__(self):
        self.counters = {jump: 0 for jump in Jumps}
        self.closest_jump = ""

    def initiate_jump(self, jump_enum: Jumps) -> str:
        self.counters[jump_enum] += 1
        self.closest_jump = f"{jump_enum.name.upper()}_{self.counters[jump_enum]}"
        return f"{self.closest_jump}"

    def get_closest_jump(self) -> str:
        return self.closest_jump

jm = JumpManager() # Global Jump Manager instance

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
        self.op.value = self.op.negate()


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
        return value[0]

    def NAME(self, name):
        return name.value

    def nop(self, items):
        return ('NOP',),
    # --- product functions --------------------------
    def product_helper(self, product1: int|str, product2: int|str, op: "Operand") -> int|str:
        isint1 = isinstance(product1, int)
        isint2 = isinstance(product2, int)
        if isint1 and isint2: # if both are int then return the operation
            match(op):
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

    def compare_equal(self, items):
        self.product_helper(items[0], items[1], Operand.CMP)
        return Operand.JEQ
    
    def compare_not_equal(self, items):
        self.product_helper(items[0], items[1], Operand.CMP)
        return Operand.JNE
    
    def compare_greater_equal(self, items):
        self.product_helper(items[0], items[1], Operand.CMP)
        return Operand.JGE
    
    def compare_less_equal(self, items):
        self.product_helper(items[0], items[1], Operand.CMP)
        return Operand.JLE
    
    def compare_greater(self, items):
        self.product_helper(items[0], items[1], Operand.CMP)
        return Operand.JG
    
    def compare_less(self, items):
        self.product_helper(items[0], items[1], Operand.CMP)
        return Operand.JL

    def and_compare(self, items) -> tuple[str, list[str]]:
        # case 1 Input [Block1, Block2] both are came from non and/or compare
        # case 2 right is [Block1, Block2, fail_label, success_label]

        return items

    def or_compare(self, items) -> tuple[str, list[str]]:

        return items

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
        for_jump = jm.initiate_jump(Jumps.FOR)
        end_jump = jm.initiate_jump(Jumps.END_FOR)
        jump_to_start = ('JMP', for_jump, None)
        jump_to_end = ('JMP', end_jump, None)
        end_label_command = ('NOP', None, None, end_jump)


        if not body_commands:
            raise ValueError("For loop must have a body.")
        if not comparison_commands:
            raise ValueError("While loop must have a condition.")
        
        comparison_commands.insert(0, ('NOP', None, None, for_jump)) # add the jump label command to the start of the comparison


        prev_commands = comparison_commands + [jump_to_end] + [jump_command_label] + increment_commands + body_commands


        return init_commands + [jump_to_start] + [end_label_command]

    def while_loop(self, items) -> list[str]:
        
        # items are list[tuple(label, list[Commands]), List[Commands]]
        # first variable label is the where it will jump to if true
        # second variable list[Commands] is the list of commands to reach the comparison
        # the third variable list[Commands] is the body of the while loop
        # Overall Structure: start_label, leading_Conditions, jump_to_end_label, true_label, comparison_jump, body, jump_to_start, end_label
        
        true_label = items[0][0] # the incomplete jump command
        jump_label = ('NOP', None, None, true_label)
        while_jump = jm.initiate_jump(Jumps.WHILE)
        end_jump = jm.initiate_jump(Jumps.END_WHILE)

        comparison_commands = items[0][1]
        if 0 <= 2 < len(items[0]): # there is a third item in to remove the jump from the insert
            comparison_commands.append(items[0][2]) # the register allocation needs to go before the jump
        body_commands = self.list_in_list(items[1:])
        if not body_commands:
            raise ValueError("While loop must have a body.")
        
        if not comparison_commands:
            raise ValueError("While loop must have a condition.")
        
        jump_to_end = ('JMP', end_jump, None)
        jump_to_start = ('JMP', while_jump, None)
        end_label_command = ('NOP', None, None, end_jump)
        
        jump_to_start_label = ('NOP', None, None, while_jump)


        prev_commands = [jump_to_start_label] + comparison_commands + [jump_to_end] + [jump_label] + body_commands



        return [jump_to_start] + [end_label_command]
    
    def do_while_loop(self, items) -> list[str]:
        # items are list[list[Commands], Tuple(label, list[Commands])]
        # first variable list[Commands] is the body of the do-while loop
        # second variable label is the where it will jump to if true
        # third variable list[Commands] is the list of commands to reach the comparison
        # Overall Structure: start_label, body, leading_Conditions, comparison_jump
        if len(items) < 2:
            raise ValueError("Do-While loop must have at least body and condition.")
        
        body_commands = self.list_in_list(items[:-1])
        

        jump_label = items[-1][0]
        comparison_commands = items[-1][1]
        if 0 <= 2 < len(items[-1]): # there is a third item in to remove the jump from the insert
            comparison_commands.append(items[-1][2]) # the register allocation needs to go before the jump
        
        

        if not body_commands:
            raise ValueError("For loop must have a body.")
        if not comparison_commands:
            raise ValueError("While loop must have a condition.")
        
        start_jump = (('NOP', None, None, jump_label)) # add the jump label command to the start of the body

        while_label = jm.initiate_jump(Jumps.DO_WHILE)

        insert = ('INSERT', while_label, None) # placeholder to ensure jump label exists in IRform
        return [insert, comparison_commands[-1]]
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
        if len(items) < 1:
            raise ValueError("Else statement must have at least body.")

        return "ELSE", items # just the body statement returned

    def elif_statement(self, items):
        condition = items[0] if items[0] is not None else None
        if len(items) <= 1:
            raise ValueError("Elif statement must have at least condition and body.")
        body = items[1:]
        
        return "ELIF", condition, body

    def if_statement(self, items) -> list[str]:
        # items are list[tuple(label, list[Commands]), list[Commands](one per block), ("ELIF", tuple(label, list[Commands]), list[Commands]), ("ELSE", list[Commands])]
        if_condition_commands = items[0][1]
        if 0 <= 2 < len(items[0]): # there is a third item in to remove the jump from the insert
                if_condition_commands.append(items[0][2]) # the register allocation needs to go before the jump
        if_body_commands = []
        body_counter = -1

        for index, value in enumerate(items): # Get if body 
            body_counter += 1
            if index == 0:
                continue
            if isinstance(value, list):
                if_body_commands.extend(value)
                continue
            break
        does_else_exist = (items[-1][0] == "ELSE")
        end_if_jump_label = jm.initiate_jump(Jumps.END_IF)
        if_jump_label = items[0][0]

        jump_end_if = ('JMP', end_if_jump_label, None)
        if not does_else_exist:
            if_body_commands.insert(0, jump_end_if)
        body_blocks = [('NOP', None, None, if_jump_label)]

        comparison_blocks = if_condition_commands
        if_jump_build = jm.initiate_jump(Jumps.IF)

        body_blocks.append(('INSERT', if_jump_build, None)) # placeholder to ensure jump label exists in IRform
        if does_else_exist:
            body_blocks.append(jump_end_if)
        

        for i in range(body_counter, len(items)-1): # Get elif statements
            elif_jump_label = items[i][1][0]


            elif_condition_commands = items[i][1][1]
            if 0 <= 2 < len(items[i][1]): # there is a third item in to remove the jump from the insert
                elif_condition_commands.append(items[i][1][2]) # the register allocation needs to go before the jump
            elif_body_commands = items[i][2]
            else_build_label = jm.initiate_jump(Jumps.ELIF)

            elif_comparison_blocks = elif_condition_commands
            elif_body_blocks = [("INSERT",else_build_label, None)] + [jump_end_if]
            comparison_blocks.extend(elif_comparison_blocks)
            body_blocks.extend(elif_body_blocks)

        if does_else_exist: # Get else statement      
            else_label = jm.initiate_jump(Jumps.ELSE)
            else_jump_command = ('JMP', else_label, None)
            comparison_blocks.append(else_jump_command)
            else_body_commands = items[-1][1]
            body_blocks.append(('NOP', None, None, else_label))

            body_blocks.append(('INSERT', else_label, None)) # placeholder to ensure jump label exists in IRform

        end_command = ('NOP', None, None, end_if_jump_label)
        prev_commands = comparison_blocks + body_blocks

        If_block_label = jm.initiate_jump(Jumps.IF_BLOCK)

        return [('INSERT', If_block_label, None)] + [end_command]
    
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
