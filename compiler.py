from lark import Lark, Transformer
from Intermediate_form import IRform, BlockType, JumpManager, FunctionCall, Commands, Jumps
from temp_var import Temp


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
        | product "&" atom -> andd
        | product "|" atom -> orr
        | product "^" atom -> xor

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


jm = JumpManager() # Global Jump Manager instance

IRform = IRform()


class CodeTransformer(Transformer):
    # --- IRBuilder functions --------------------------

    def append_helper(self, list1, list2):
        if list1 is None and list2 is None:
            return []
        elif list1 is None:
            return list2
        elif list2 is None:
            return list1
        elif isinstance(list1, list) and isinstance(list2, list):
            return list1 + list2
        elif isinstance(list1, list):
            return list1 + [list2]
        elif isinstance(list2, list):
            return [list1] + list2
        else:
            return [list1, list2]
       
    # --- Transformer functions --------------------------
    # --- var/number functions --------------------------
    def number(self, n):
        return int(n[0])

    def hex_number(self, n):
        return int(n[0], 16)

    def var(self, name):
        return name[0]

    @staticmethod
    def const(value):
        return value[0]

    def NAME(self, name):
        return name.value

    def nop(self, items):
        return ('NOP',),
    # --- product functions --------------------------
    def product_helper(self, operand: str, left: str | int, right: str | int) -> int | tuple[str | Commands]:
        left_int = isinstance(left, int)
        right_int = isinstance(right, int)
        if left_int and not right_int: # swap left and right
            left, right = right, left

        if left_int and right_int:
            match operand:
                case 'MULT':
                    return int(left * right)
                case 'DIV':
                    return int(left / right)
                case 'QUOT':
                    return int(left % right)
                case 'ADD':
                    return int(left + right)
                case 'SUB':
                    return int(left - right)
                case 'AND':
                    return int(left & right)
                case 'OR':
                    return int(left | right)
                case 'XOR':
                    return int(left ^ right)
                case _:
                    raise Exception(f"Unknown operand: {operand}")
                
        else: 
            dest = ""
            if right_int ^ left_int: # left is a variable right is an int
                operand += 'I'  # immediate version of the command
                dest = left
            command = Commands(operand, left, right)
            if not right_int ^ left_int:
                dest = command.combine_operand()
            return dest, command
        
    def product_helper2(self, operand: str, items: list) -> tuple[str | int, list[Commands]]:
        # items can be ['a', 1] or ['a', 'a'], list of two items, either variable/int/Commands
        left = items[0]
        right = items[1]
        list_commands = []
        if len(items) == 3:
            list_commands = self.append_helper(list_commands, items[2])
        
        # Handle left operand
        if isinstance(items[0], tuple) and len(items[0]) == 2:
            left, left_commands = items[0]
            list_commands = self.append_helper(list_commands, left_commands)
        elif isinstance(items[0], Commands):
            left = items[0].get_destination()
            list_commands.append(items[0])
        
        # Handle right operand
        if isinstance(items[1], tuple) and len(items[1]) == 2:
            right, right_commands = items[1]
            list_commands = self.append_helper(list_commands, right_commands)
        elif isinstance(items[1], Commands):
            right = items[1].get_destination()
            list_commands.append(items[1])
        
        result = self.product_helper(operand, left, right)
        next_dest = None
        if isinstance(result, tuple):
            list_commands.append(result[1])
            next_dest = result[0]
        else:
            next_dest = result
        return next_dest, list_commands
        
    def add(self, items):
        return self.product_helper2('ADD', items)
    def sub(self, items):
        return self.product_helper2('SUB', items)
    def andd(self, items):
        return self.product_helper2('AND', items)
    def orr(self, items):
        return self.product_helper2('OR', items)
    def xor(self, items):
        return self.product_helper2('XOR', items)
    def mult(self, items):
        return self.product_helper2('MULT', items)
    def div(self, items):
        return self.product_helper2('DIV', items)
    def quot(self, items):
        return self.product_helper2('QUOT', items)
    
    def increment(self, items) -> tuple[str | int, list[Commands]]:
        var_name = items[0]
        return [Commands('INC', var_name, var_name),]
    
    def decrement(self, items) -> tuple[str | int, list[Commands]]:
        var_name = items[0]
        return [Commands('DEC', var_name, var_name),]
    
    # --- assignments functions --------------------------
    def assign_helper(self, operand_int: str, operand_var: str, items) -> list[Commands]:
        # items is a list[variable/int, int/tuple)]
        # tuple(variable, List[Commands])
        var_name = items[0]
        sub_item = items[1]
        command_lists = []
        if isinstance(sub_item, tuple):
            var_name_2 = sub_item[0]
            command_lists = sub_item[1] if len(sub_item) > 1 else []
        else:
            var_name_2 = sub_item
        
        operand = operand_int if isinstance(var_name_2, int) else operand_var # choose between immediate or variable version

        if len(command_lists) >= 1:
                var_name_2 = Temp.TEMP_SAVE.name
                command_lists = self.compare_dest_remover(command_lists, var_name_2)
        
        if isinstance(var_name_2, int) and isinstance(var_name, str):
            var_name, var_name_2 = var_name_2, var_name # swap to make var_name the int and var_name_2 the variable

        if operand == "MOV":
            
            command_lists.append(Commands(operand, var_name_2, var_name))
            command_lists[-1].var2 = var_name # set the last command's destination to the variable being assigned to
        else: # remove unnecessary moves
            command_lists.append(Commands(operand, var_name_2, var_name))

        return command_lists
    
    def assign_var(self, items):
        
        if isinstance(items[1], list): # handling edge case of items[1] may be an int
            if isinstance(items[1][0], FunctionCall): # handling edge case of FunctionCall
                func_call: FunctionCall = items[1][0]
                func_call.append_assignment(items[0])
                return [func_call]
            
        return self.assign_helper('LI', 'MOV', items)
    
    def add_assign_var(self, items):
        return self.assign_helper('ADDI', 'ADD', items)
    
    def sub_assign_var(self, items):
        return self.assign_helper('SUBI', 'SUB', items)
    
    def mul_assign_var(self, items):
        return self.assign_helper('MULTI', 'MULT', items)
    
    def div_assign_var(self, items):
        return self.assign_helper('DIVI', 'DIV', items)
    
    # --- Comparison --------------------------

    def compare_helper(self, items, operand: str) -> tuple[str, list[Commands]]:
        # items are list[var/int/tuple, var/int/tuple]
        # tuple(var/int, list[Commands])
        # first return is the jump, the seconds is the list of commands
        side1 = items[0]
        side2 = items[1]

        prev_commands = []
        if isinstance(side1, tuple):
            var1, commands1 = side1
            if len(commands1) >= 1:
                var1 = Temp.TEMP_SAVE.name
                commands1 = self.compare_dest_remover(commands1, var1)
                
            prev_commands = self.append_helper(prev_commands, commands1)
        else:
            var1 = side1

        if isinstance(side2, tuple):
            var2, commands2 = side2
            if len(commands2) >= 1:
                var2 = Temp.TEMP_RIGHT.name
                commands2 = self.compare_dest_remover(commands2, var2)
                
            prev_commands = self.append_helper(prev_commands, commands2)
        else:
            var2 = side2

        is_left_int = isinstance(var1, int)
        is_right_int = isinstance(var2, int)
        if is_left_int and is_right_int:
            raise ValueError("Cannot compare two immediate values.")
        if is_left_int and not is_right_int: # swap to make left always variable
            var1, var2 = var2, var1

        jump_label = jm.initiate_jump(Jumps.COMPARE) # jump if true
        compare_operand = "CMPI" if isinstance(var2, int) else "CMP"
        compare_cmd = Commands(compare_operand, var1, var2)
        prev_commands = self.append_helper(prev_commands, compare_cmd)

        compare_label = jm.initiate_jump(Jumps.COMPARE)
        IRform.add_builder(compare_label, BlockType.COMPARE_BLOCK)
        IRform.add_commands(compare_label, prev_commands)
        insert = Commands('INSERT', compare_label, None)
            
        return jump_label, [insert], Commands(operand, jump_label, None)

    def compare_dest_remover(self, items:list[Commands], temp_label: str) -> list[Commands]:
        temp1_var = ""
        temp2_var = ""

        prev_commands = []
        for cmd in items:
            operand_label = cmd.combine_operand()

            if cmd.get_var1() == temp1_var:
                cmd.set_var1(Temp.TEMP_RIGHT.name)
                if cmd.operand[-1] != 'I': # if immediate version change to variable version
                    temp1_var = ""
            if cmd.get_var2() == temp1_var:
                cmd.set_var2(Temp.TEMP_RIGHT.name)
                if cmd.operand[-1] != 'I':
                    temp1_var = ""

            if cmd.get_var1() == temp2_var:
                cmd.set_var1(Temp.TEMP_SAVE.name)
                if cmd.operand[-1] != 'I':
                    temp2_var = ""
            if cmd.get_var2() == temp2_var:
                cmd.set_var2(Temp.TEMP_SAVE.name)
                if cmd.operand[-1] != 'I':
                    temp2_var = ""
            
            if temp1_var == "":
                temp1_var = operand_label
                cmd.set_destination(Temp.TEMP_RIGHT.name)
            else:
                temp2_var = operand_label
                cmd.set_destination(Temp.TEMP_SAVE.name)

            
            prev_commands.append(cmd)


        prev_commands[-1].set_destination(temp_label) # set the last command's destination to the Temp label

        return prev_commands

    def compare_equal(self, items):
        return self.compare_helper(items, "JEQ")
    
    def compare_not_equal(self, items):
        return self.compare_helper(items,"JNE")
    
    def compare_greater_equal(self, items):
        return self.compare_helper(items,"JGE")
    
    def compare_less_equal(self, items):
        return self.compare_helper(items,"JLE")
    
    def compare_greater(self, items):
        return self.compare_helper(items,"JG")
    
    def compare_less(self, items):
        return self.compare_helper(items,"JL")

    def and_compare(self, items) -> tuple[str, list[Commands]]:
        # items are list[tuple[str, list[Commands], tuple[str, list[Commands]]
        # if it passes by it is false else it jumps it's true
        this_true = jm.initiate_jump(Jumps.COMPARE_AND)
        this_false = jm.initiate_jump(Jumps.COMPARE_AND_FALSE)
        left_true_1 = items[0][0]
        right_true_2 = items[1][0]
        this_true_command = Commands('JMP', this_true, None)
        left_true_command = Commands('NOP', None, None, left_true_1)
        right_true_command = Commands('NOP', None, None, right_true_2)
        this_false_label = Commands('NOP', None, None, this_false)
        this_false_command = Commands('JMP', this_false, None)

        left_side = items[0][1]
        left_side.append(items[0][2])
        left_side.append(this_false_command)
        right_side = items[1][1]
        right_side.append(items[1][2])
        right_side.insert(0, left_true_command)
        right_side.append(this_false_command)
        right_side.append(right_true_command)
        right_side.append(this_true_command)
        right_side.append(this_false_label)


        prev_commands = left_side + right_side
        return this_true, prev_commands

    def or_compare(self, items) -> tuple[str, list[Commands]]:
        # items are list[tuple[str, list[Commands], tuple[str, list[Commands]]
        left_true_1 = items[0][0]
        right_true_2 = items[1][0]
        true_label = left_true_1 + ',' + right_true_2

        left_side = items[0][1]
        right_side = items[1][1]
        prev_commands = left_side + right_side
        return true_label, prev_commands

    # --- loops declaration --------------------------

    def for_loop(self, items) -> list[Commands]:
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
        jump_command_label = Commands('NOP', None, None, jump_label)
        comparison_commands = items[1][1]
        if 0 <= 2 < len(items[1]): # there is a third item in to remove the jump from the insert
            comparison_commands.append(items[1][2]) # the register allocation needs to go before the jump

        increment_commands = items[2]
        body_commands = self.list_in_list(items[3:])
        for_jump = jm.initiate_jump(Jumps.FOR)
        end_jump = jm.initiate_jump(Jumps.END_FOR)
        jump_to_start = Commands('JMP', for_jump, None)
        jump_to_end = Commands('JMP', end_jump, None)
        end_label_command = Commands('NOP', None, None, end_jump)


        if not body_commands:
            raise ValueError("For loop must have a body.")
        if not comparison_commands:
            raise ValueError("While loop must have a condition.")
        
        comparison_commands.insert(0, Commands('NOP', None, None, for_jump)) # add the jump label command to the start of the comparison

        IRform.add_builder(for_jump, BlockType.FOR_BLOCK) # ensure jump label exists in IRform
        prev_commands = comparison_commands + [jump_to_end] + [jump_command_label] + increment_commands + body_commands
        IRform.add_commands(for_jump, prev_commands) # add the commands to the jump label builder
        insert = Commands('INSERT', for_jump, None) # placeholder to ensure jump label exists in IRform

        return init_commands + [insert] + [jump_to_start] + [end_label_command]

    def while_loop(self, items) -> list[Commands]:
        
        # items are list[tuple(label, list[Commands]), List[Commands]]
        # first variable label is the where it will jump to if true
        # second variable list[Commands] is the list of commands to reach the comparison
        # the third variable list[Commands] is the body of the while loop
        # Overall Structure: start_label, leading_Conditions, jump_to_end_label, true_label, comparison_jump, body, jump_to_start, end_label
        
        true_label = items[0][0] # the incomplete jump command
        jump_label = Commands('NOP', None, None, true_label)
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
        
        jump_to_end = Commands('JMP', end_jump, None)
        jump_to_start = Commands('JMP', while_jump, None)
        end_label_command = Commands('NOP', None, None, end_jump)
        
        jump_to_start_label = Commands('NOP', None, None, while_jump)

        IRform.add_builder(while_jump, BlockType.WHILE_BLOCK) # ensure jump label exists in IRform
        insert = Commands('INSERT', while_jump, None) # placeholder to ensure jump label exists in IRform
        prev_commands = [jump_to_start_label] + comparison_commands + [jump_to_end] + [jump_label] + body_commands

        IRform.add_commands(while_jump, prev_commands) # add the commands to the jump label builder

        return [insert] + [jump_to_start] + [end_label_command]
    
    def do_while_loop(self, items) -> list[Commands | FunctionCall]:
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
        
        start_jump = (Commands('NOP', None, None, jump_label)) # add the jump label command to the start of the body

        while_label = jm.initiate_jump(Jumps.DO_WHILE)
        IRform.add_builder(while_label, BlockType.DO_WHILE_BLOCK) # ensure jump label exists in IRform
        IRform.add_commands(while_label, [start_jump] + body_commands + comparison_commands[:-1]) # add the commands to the jump label builder
        insert = Commands('INSERT', while_label, None) # placeholder to ensure jump label exists in IRform
        return [insert, comparison_commands[-1]]
    # --- function declaration --------------------------
    def function_declaration(self, items):
        function_name = str(items[0])
        IRform.add_builder(function_name, BlockType.FUNCTION)
        args = items[1] if len(items) > 1 else []
        body = items[2:] if len(items) > 2 else []

        # Handle arguments - check if args is iterable
        if hasattr(args, '__iter__') and not isinstance(args, str):
            for i, arg in enumerate(args):
                if isinstance(arg, tuple): # if arg is a (var_name, commands) tuple
                    var_name, commands = arg
                    IRform.add_commands(function_name, commands)
                else:
                    var_name = arg
                self.add_command(function_name, ('mov', var_name, f'arg{i}'))
        
        # Handle body
        for statement in body:
            if isinstance(statement, list):
                for stmt in statement:
                    if isinstance(stmt, tuple): # if stmt is a (var_name, commands) tuple
                        var_name, commands = stmt
                        IRform.add_commands(function_name, commands)
                    else:
                        IRform.add_command(function_name, stmt)
            else:
                if isinstance(statement, tuple): # if statement is a (var_name, commands) tuple
                    var_name, commands = statement
                    IRform.add_commands(function_name, commands)
                else:
                    IRform.add_command(function_name, statement)
        
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

    def if_statement(self, items) -> list[Commands]:
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

        jump_end_if = Commands('JMP', end_if_jump_label, None)
        if not does_else_exist:
            if_body_commands.insert(0, jump_end_if)
        body_blocks = [Commands('NOP', None, None, if_jump_label)]

        comparison_blocks = if_condition_commands
        if_jump_build = jm.initiate_jump(Jumps.IF)
        IRform.add_builder(if_jump_build, BlockType.IF_BLOCK) # ensure jump label exists in IRform
        IRform.add_commands(if_jump_build, if_body_commands) # add the commands to the jump label builder
        body_blocks.append(Commands('INSERT', if_jump_build, None)) # placeholder to ensure jump label exists in IRform
        if does_else_exist:
            body_blocks.append(jump_end_if)
        

        for i in range(body_counter, len(items)-1): # Get elif statements
            elif_jump_label = items[i][1][0]
            elif_jump_command = Commands('NOP', None, None, elif_jump_label)

            elif_condition_commands = items[i][1][1]
            if 0 <= 2 < len(items[i][1]): # there is a third item in to remove the jump from the insert
                elif_condition_commands.append(items[i][1][2]) # the register allocation needs to go before the jump
            elif_body_commands = items[i][2]
            else_build_label = jm.initiate_jump(Jumps.ELIF)
            IRform.add_builder(else_build_label, BlockType.ELIF_BLOCK) # ensure jump label exists in IRform
            IRform.add_commands(else_build_label, self.list_in_list(elif_body_commands))
            elif_comparison_blocks = elif_condition_commands
            elif_body_blocks = [elif_jump_command] + [Commands("INSERT",else_build_label, None)] + [jump_end_if]
            comparison_blocks.extend(elif_comparison_blocks)
            body_blocks.extend(elif_body_blocks)

        if does_else_exist: # Get else statement      
            else_label = jm.initiate_jump(Jumps.ELSE)
            else_jump_command = Commands('JMP', else_label, None)
            comparison_blocks.append(else_jump_command)
            else_body_commands = items[-1][1]
            body_blocks.append(Commands('NOP', None, None, else_label))
            IRform.add_builder(else_label, BlockType.ELSE_BLOCK) # ensure jump label exists in IRform
            IRform.add_commands(else_label, self.list_in_list(else_body_commands)) # add the commands to the jump
            body_blocks.append(Commands('INSERT', else_label, None)) # placeholder to ensure jump label exists in IRform

        end_command = Commands('NOP', None, None, end_if_jump_label)
        prev_commands = comparison_blocks + body_blocks

        If_block_label = jm.initiate_jump(Jumps.IF_BLOCK)
        IRform.add_builder(If_block_label, BlockType.WHOLE_IF_BLOCK) # ensure jump label exists in IRform
        IRform.add_commands(If_block_label, self.list_in_list(prev_commands)) # add the commands to the jump label builder

        return [Commands('INSERT', If_block_label, None)] + [end_command]
    
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
        return [FunctionCall(items[0], items[1])]
    
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
        return [Commands('RETURN', None, return_items)]


with open('program.txt', 'r') as file:
    program = file.read()


parse_tree = code_parser.parse(program)
print("Parse Token Tree:\n")
print(parse_tree)
print("\nPretty Print Parse Token Tree:\n")
print(parse_tree.pretty())

transformed = CodeTransformer().transform(parse_tree)

# Print the Immediate 

print(IRform.__str__())
IRform.process_lifetimes()
IRform.print_lifetimes()
IRform.variable_assignment()

print("\nFinal Program:\n")
for s in IRform.get_final_program():
    print(s)

