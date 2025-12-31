from typing import Any

from lark import Transformer

from Command import Command, CommandJump, CommandLabel, CommandReturn, CommandInnerStart, CommandInnerEnd
from JumpManager import jump_manager
from MemoryManager import MemoryManager
from SharedFunc import register_id, CompileHelper, SharedFunc
from Type import Operand, RamVar, base_pointer, stack_pointer, Compare


class Parser(Transformer):
    def __init__(self):
        super().__init__()
        self.compiler_helper = CompileHelper()
        self.shared_rtn = SharedFunc()
       # --- var/number functions --------------------------
    def NUMBER(self, n):
        return int(n)

    def number(self, n):
        return int(n[0])

    def hex_number(self, n):
        return int(n[0], 16)

    def var(self, name):
        return name[0]

    def const(self, value):
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
        product, final_commands = self.compiler_helper.extract_variable_and_commands(items[0], [])
        temp_name = self.compiler_helper.get_temp_ram() # gets new temp variable
        return temp_name, final_commands + [Command(Operand.NOT, temp_name, product)]

    def negative(self, items):
        """
        Takes previous variable performs NEG and returns the new temp variable
        :return: tuple[new variable, the previous Commands along as its own]
        """
        if isinstance(items[0], int):
            return ~items[0] + 1 # returns the 2's compliment on integer
        # easily separates the input into the variable and commands
        product, final_commands = self.compiler_helper.extract_variable_and_commands(items[0], [])
        temp_name = self.compiler_helper.get_temp_ram() # gets new temp variable
        return temp_name, final_commands + [Command(Operand.NEG, temp_name, product)]

    # --- product functions --------------------------

    def process_binary_operation(self, input1: int | str | tuple[str,list[Command]], input2: int | str | tuple[str,list[Command]], op: Operand) -> int | str | tuple[int | str, list[Command]]:
        """
        Takes two inputs performs the necessary product like +-*/%.
        Processes cases like the inputs being integers, registers or memory.
        Combines the input's list of commands into a single command.
        returns a tuple of variable, and list of commands
        """

        # separating the variables from the list of commands
        product2,final_commands = self.compiler_helper.extract_variable_and_commands(input2, [])
        product1,final_commands = self.compiler_helper.extract_variable_and_commands(input1, final_commands)

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
                case Operand.SHL:
                    return product1 << product2
                case Operand.SHR:
                    return product1 >> product2
                case _:
                    raise ValueError(f"Cannot move an integer {product1} into an integer {product2} for this operand {op}")

        # getting if the variable is a register
        is_reg1 = isinstance(product1, str) and product1.startswith(register_id)
        is_reg2 = isinstance(product2, str) and product2.startswith(register_id)
        return_var = ""

        match (is_reg1, is_reg2):
            case True, True: # both are registers
                # free the unused register coming from the destination
                self.compiler_helper.free_reg(int(product2[1:]))
                final_commands.append(Command(op, product1, product2))
                return_var = product1
            case False, True: # right is register
                # free the unused register coming from the destination
                self.compiler_helper.free_reg(int(product2[1:]))
                final_commands.append(Command(op, product2, product1))
                return_var = product2
            case True, False: # left is register
                final_commands.append(Command(op, product1, product2))
                return_var = product1
            case False, False: # none is a register
                # first get a temp register
                # move the first product into the register
                # then perform the operation on the second product
                temp_reg = self.compiler_helper.get_reg()
                final_commands.append(Command(Operand.MOV, temp_reg, product1))
                final_commands.append(Command(op, temp_reg, product2))
                return_var = temp_reg

        return return_var, final_commands

    def add(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.ADD)
    def sub(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.SUB)
    def bit_and(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.AND)
    def bit_or(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.OR)
    def bit_xor(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.XOR)
    def mult(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.MULT)
    def div(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.DIV)
    def quot(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.QUOT)
    def left_shift(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.SHL)
    def right_shift(self, items):
        return self.process_binary_operation(items[0], items[1], Operand.SHR)

    
    def increment(self, items) -> list[Command]:
        """ processes examples like var++"""
        return [Command(Operand.ADD, items[0], 1)]
    
    def decrement(self, items) -> list[Command]:
        """ processes examples like var--"""
        return [Command(Operand.SUB, items[0], 1)]

    
    # --- assignments functions --------------------------

    def process_assignment_operation(self, input1: str | int | tuple[str,list[Command]], input2: str | int | tuple[str,list[Command]], op: Operand) -> list[Command]:
        """
        Helps performs an operand on two inputs.
        Returns the list of commands plus the operand
        """
        # separates the variable with the commands
        product2, final_commands = self.compiler_helper.extract_variable_and_commands(input2, [])
        product1, final_commands = self.compiler_helper.extract_variable_and_commands(input1, final_commands)
        self.compiler_helper.free_all_reg()

        return final_commands + [Command(op, product1, product2)]
    
    def assign_var(self, items) -> list[Command]: # a = b
        return self.process_assignment_operation(items[0], items[1], Operand.MOV)
    
    def add_assign_var(self, items) -> list[Command]: # a += b
        return self.process_assignment_operation(items[0], items[1], Operand.ADD)
    
    def sub_assign_var(self, items) -> list[Command]: # a-= b
        return self.process_assignment_operation(items[0], items[1], Operand.SUB)
    
    def mul_assign_var(self, items) -> list[Command]: # a*= b
        return self.process_assignment_operation(items[0], items[1], Operand.MULT)
    
    def div_assign_var(self, items) -> list[Command]: # a /= b
        return self.process_assignment_operation(items[0], items[1], Operand.DIV)
    
    # --- Comparison --------------------------

    def compare_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        """
        Takes in two list of operands and compares them with compare and equal.
        Returns a tuple with the list of commands, tuple success label, fail label, and the compare type
        There are three compare types:
        SIMPLE for things like a == b
        AND for things like a == b && a == b
        OR for things like a == b && a == b
        """
        return self.process_assignment_operation(items[0], items[1], Operand.CMP) + [Command(Operand.JEQ)], (None, None, Compare.SIMPLE)
    
    def compare_not_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.process_assignment_operation(items[0], items[1], Operand.CMP) + [Command(Operand.JNE)], (None, None, Compare.SIMPLE)
    
    def compare_greater_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.process_assignment_operation(items[0], items[1], Operand.CMP) + [Command(Operand.JGE)], (None, None, Compare.SIMPLE)
    
    def compare_less_equal(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.process_assignment_operation(items[0], items[1], Operand.CMP) + [Command(Operand.JLE)], (None, None, Compare.SIMPLE)
    
    def compare_greater(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.process_assignment_operation(items[0], items[1], Operand.CMP) + [Command(Operand.JG)], (None, None, Compare.SIMPLE)
    
    def compare_less(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        return self.process_assignment_operation(items[0], items[1], Operand.CMP) + [Command(Operand.JL)], (None, None, Compare.SIMPLE)

    def zero_compare(self, items) -> tuple[list[Any], tuple[None, None, Compare]]:
        """
        Computes the compare for a single operand. For example if (a + 5)
        """
        return self.process_assignment_operation(items[0], 0, Operand.CMP) + [Command(Operand.JNE)], (None, None, Compare.SIMPLE)

    def and_compare(self, items: list[tuple[list[Command], tuple[int, int, Compare]]]) -> tuple[list[Command], tuple[int, int, Compare]]:
        """
        Takes two inputs from a previous compare, and computes a single compare simulating the AND operator
        """
        # splits the variables from items each side has the blocks, success label, fail label and the comparison type
        block1 = items[0][0]
        block2 = items[1][0]
        fail_label1 = items[0][1][0]
        true_label1 = items[0][1][1]
        type1 = items[0][1][2]
        fail_label2 = items[1][1][0]
        true_label2 = items[1][1][1]
        type2 = items[1][1][2]

        final_true = None
        # merges the two fail labels together
        final_fail = jump_manager.remove_duplicate(fail_label2, fail_label1)

        # if operand is Compare negate it and set its jump_label to fail
        if type1 == Compare.SIMPLE:
            block1[-1].jump_label = final_fail
            block1[-1].negate_jump()
        if type2 == Compare.SIMPLE:
            block2[-1].jump_label = final_fail
            block2[-1].negate_jump()

        # append the true label from the left side if exists
        if true_label1 is not None:
            block1.append(CommandLabel(true_label1))

        if type1 != Compare.SIMPLE and type2 != Compare.SIMPLE:
            final_true = true_label2

        return block1 + block2, (final_fail, final_true, Compare.LOGICAL_AND)

    def or_compare(self, items: list[tuple[list[Command], tuple[int, int, Compare]]]) -> tuple[list[Command], tuple[int, int, Compare]]:
        """
                Takes two inputs from a previous compare, and computes a single compare simulating the OR operator
                """
        # splits the variables from items each side has the blocks, success label, fail label and the comparison type
        block1 = items[0][0]
        block2 = items[1][0]
        fail_label1 = items[0][1][0]
        true_label1 = items[0][1][1]
        type1 = items[0][1][2]
        fail_label2 = items[1][1][0]
        true_label2 = items[1][1][1]
        type2 = items[1][1][2]

        # merges the two fail labels together
        final_true = jump_manager.remove_duplicate(true_label1, true_label2)
        # if fail label is none them create a new label
        final_fail = jump_manager.remove_duplicate(fail_label2)

        # sets the left compare to the true label
        block1[-1].jump_label = final_true
        if type1 is not Compare.SIMPLE:
            # revert the compare to its original, both && and || negate the last item to jump to it's failed jump_label
            block1[-1].negate_jump()

        if type2 == Compare.SIMPLE:
            block2[-1].jump_label = final_fail
            block2[-1].negate_jump()

        if fail_label1 is not None:
            block1.append(CommandLabel(fail_label1))

        return block1 + block2, (final_fail, final_true, Compare.LOGICAL_OR)

    # --- loops declaration --------------------------

    def loop_helper(self, true_label, fail_label, condition_block, compare_type):
        """
        Performs logic for the three loop types
        It manages the true_label and fail_label
        """
        # if the true_label does not exist create it, used for the SIMPLE type
        if true_label is None:
            true_label = jump_manager.get_jump()

        condition_block[-1].jump_label = true_label
        if compare_type != Compare.SIMPLE:
            # last compare _jumps if fail and rolls down if true, this is negating that
            # rolls down if false
            condition_block[-1].negate_jump()

        # sets the fail label after the condition block
        if fail_label is not None:
            condition_block.append(CommandLabel(fail_label))

        return true_label

    def for_loop(self, items) -> list[Command]:
        """
        Manages the logic in the for loop
        Overall structure:
        initialization, jump to condition, if condition is true label, main block, increment, jump to condition label, condition block, fail label
        """
        initialization = items[0]
        condition = items[1]
        increment = items[2]
        main_block = self.flatten_command_list(items[3:])
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]

        start_loop_label = jump_manager.get_jump()

        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = (initialization + [CommandJump(start_loop_label), CommandLabel(true_label)] +
                          main_block + increment + [CommandLabel(start_loop_label)] + condition_block)

        return [CommandInnerStart()] + final_commands + [CommandInnerEnd()]

    def while_loop(self, items) -> list[Command]:
        """
        Manages the logic in the while loop
        Overall structure:
        jump to condition, if condition is true label, main block, jump to condition label, condition block, fail label
        """
        condition = items[0]
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]
        main_block = self.flatten_command_list(items[1:])

        start_loop_label = jump_manager.get_jump()

        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = ([CommandJump(start_loop_label), CommandLabel(true_label)] + main_block  +
                          [CommandLabel(start_loop_label)] + condition_block)

        return [CommandInnerStart()] + final_commands + [CommandInnerEnd()]
    
    def do_while_loop(self, items) -> list[Command]:
        """
        Manages the logic in the do while loop
        Overall structure:
        if condition is true label, main block, condition block, fail label
        """
        condition = items[-1]
        fail_label = condition[1][0]
        true_label = condition[1][1]
        compare_type = condition[1][2]
        condition_block = condition[0]
        main_block = self.flatten_command_list(items[:-1])
        true_label = self.loop_helper(true_label, fail_label, condition_block, compare_type)

        final_commands = [CommandLabel(true_label)] + main_block + condition_block

        return [CommandInnerStart()] + final_commands + [CommandInnerEnd()]

    # --- if-else declaration --------------------------
    def if_helper(self, compare_type:int, fail_label: int, true_label:int, compare_block: list[Command], main_block: list[Command]) -> list[Command]:
        """
        Performs shared logic in the if and elif statements
        Manages the true and fail labels and appends them to the compare/main block
        returns a single list combining the comparison, main block, and labels
        """
        # the compare types does not have a label
        if compare_type == Compare.SIMPLE:
            compare_block[-1].negate_jump()
            fail_label = jump_manager.get_jump()
            compare_block[-1].jump_label = fail_label

        main_block.append(CommandLabel(fail_label))

        if true_label is not None:
            compare_block.append(CommandLabel(true_label))

        return [CommandInnerStart()] + compare_block + main_block + [CommandInnerEnd()]

    def else_statement(self, items: list[list[Command]]) -> tuple[list[Command]]:
        # else statement does not have any comparison, just return the main block
        # returning a tuple to differentiate between the if and else statement later
        return ([CommandInnerStart()] + self.flatten_command_list(items) + [CommandInnerEnd()],)

    def elif_statement(self, items) -> tuple[list[Command]]:
        """
        Logic for the elif statement returns a tuple of list of commands
        """
        elif_compare = items[0][0]
        elif_fail_label = items[0][1][0]
        elif_true_label = items[0][1][1]
        elif_compare_type = items[0][1][2]
        elif_block = self.flatten_command_list(items[1:])

        # returning a tuple to differentiate between the if and else statement later
        return (self.if_helper(elif_compare_type, elif_fail_label, elif_true_label, elif_compare, elif_block),)

    def if_statement(self, items) -> list[Command]:
        """
        Takes input from the if statement and an optional amount of elif/else statements
        """
        # gathers if items
        if_compare = items[0][0]
        if_fail_label = items[0][1][0]
        if_true_label = items[0][1][1]
        if_compare_type = items[0][1][2]

        # gathers info about when the if block ends, when it sees a tuple it stops
        if_block_ends = 2
        for item in items[2:]:
            if isinstance(item, list):
                if_block_ends += 1
            else:
                break

        # flattens the if statement
        if_block = self.flatten_command_list(items[1:if_block_ends])

        final_commands = self.if_helper(if_compare_type, if_fail_label, if_true_label, if_compare, if_block)

        final_jump_label = jump_manager.get_jump()
        final_jump = CommandJump(final_jump_label)

        # computes the rest of the elif and else statements
        for item in items[if_block_ends:]:
            final_commands.insert(-1, final_jump)
            final_commands.extend(item[0])

        # appends the final jump label
        if final_commands[-1].operand != Operand.LABEL:
            final_commands.append(CommandLabel(final_jump_label))
        else:
            # merges the duplicate labels into one
            jump_manager.remove_duplicate(final_jump_label, final_commands[-1].jump_label)

        return final_commands

    def flatten_command_list(self, list_of_lists):
        """
        Flattens out a list
        """
        result = []
        for item in list_of_lists:
            if isinstance(item, list):
                result.extend(self.flatten_command_list(item))
            else:
                result.append(item)
        return result

    # --- function declaration --------------------------
    def function_declaration(self, items) -> list[Command]:
        """
        Takes in the function name, arguments and main block and returns a list of commands
        """
        # splits the items into useful variables
        function_name: str = items[0]
        function_arguments: list[str] = items[1]
        main_block: list[Command] = self.flatten_command_list(items[2:])

        # validates the amount of variables it will return is consistent
        found_none:bool = True
        for block in main_block:
            if isinstance(block, Command) and block.operand == Operand.RETURN_HELPER:
                self.shared_rtn.validate_return(function_name, len(block.destination))
                found_none = False

        # if no returns are found then the default is zero
        if found_none:
            self.shared_rtn.validate_return(function_name, 0)

        # validates the amount of arguments is consistent
        self.shared_rtn.validate_arg(function_name, len(function_arguments))
        # creates a class to process the commands
        variable_process: MemoryManager = MemoryManager(function_name, self.compiler_helper, self.shared_rtn)
        # sets the arguments into ram
        variable_process.set_arguments(function_arguments)

        # logic for reserving functions
        if function_name in ["VID", "VID_RED", "VID_GREEN", "VID_BLUE", "VID_X", "VID_Y", "HALT"]:
            raise ValueError(f"{function_name} is a reserved function")

        # sets the label for the function
        function_label = jump_manager.get_function(function_name)
        # starts off every block with setting up the base and stack pointer
        final_block = [CommandLabel(function_label),
                       Command(Operand.PUSH, base_pointer()),  # push the base_pointer
                       Command(Operand.MOV, base_pointer(), stack_pointer()),  # starting function's frame
                       ]

        if len(function_arguments) != 0:
            final_block.append(Command(Operand.ADD, stack_pointer(), len(function_arguments)))

        # processing the data to ensure it is correct removing the tuples
        for i, arg in enumerate(main_block):
            if isinstance(arg, tuple):
                main_block[i] = arg[1][0]

        # computing the life and deaths of every variable in the function
        variable_process.compute_lifetimes_list(main_block)

        # sets the lifetime for each argument variable
        # if the variable is not used it will die
        for arg in function_arguments:
            variable_process.compute_lifetimes(arg, -1)

        # computing the variable to register/memory conversion
        # in addition to the return and calling functionality
        for i, item in enumerate(main_block, start=0):
            if item.operand == Operand.INNER_START:
                variable_process.inner_start()
            elif item.operand == Operand.INNER_END:
                variable_process.inner_end()
            else:
                final_block.extend(variable_process.allocate_command(item, i, function_name))

        # after the main function is called halt
        if function_name == "main":
            final_block.append(Command(Operand.HALT))


        return final_block
    # --- function call --------------------------

    def list_assign(self, items):
        return items
    
    def empty_args(self, items):
        return []
    
    def args(self, items):
        return items
    
    def function_call(self, items) -> tuple[str,list[Command]]:
        # destination is returns and source is arguments, .call_label is the name of the function
        temp = Command(Operand.CALL_HELPER, [], items[1])
        temp.call_label = items[0] # the name of the function
        return "", [temp]

    def empty_return_args(self, items):
        return []
    def return_args(self, items):
        return items
    def _return(self, items):
        return_items: list[str|int] = items[0] if items else []
        return [CommandReturn(return_items)]

    def multi_assign_var(self, items) -> list[Command]:
        """
        Process multiple function assignment for example:
        a, b, c, d = 6, new_function(a,b), d
        case: functions returning multiple variables
        case: integers and variables
        """
        to_assign: list[str] = items[0]
        from_assign: list[int|str|tuple[str,list[Command]]] = items[1:]

        # validates that there are enough arguments to go around
        if len(to_assign) < len(from_assign):
            raise SyntaxError(f"Too few arguments: {to_assign}")
        size_function: int = len(to_assign) - len(from_assign) +1

        final_commands = []
        var_offset = 0
        # index of the variable to assign

        # loops through the assignments
        for i, assign in enumerate(from_assign):
            match assign:
                case int()| str(): # case for variables and integers
                    final_commands.append(Command(Operand.MOV, to_assign[i + var_offset], assign))
                case tuple():
                    if assign[0] == "": # case for functions
                        assign[1][-1].destination = to_assign[i + var_offset: i + var_offset + size_function]
                        # the first function will fill in the amount of arguments, the rest will take in one variable
                        if size_function != 1:
                            var_offset = size_function - 1
                            size_function = 1
                        final_commands.extend(assign[1])
                    else: # case for variables with a list of commands
                        final_commands.extend(assign[1])
                        final_commands.append(Command(Operand.MOV, to_assign[i + var_offset], assign[0]))


        return final_commands

    def block(self, items):
        self.compiler_helper.reset()
        return items

    def start(self, items):
        return [Command(Operand.JMP, None, None, jump_manager.get_function("main"))] + self.flatten_command_list(items)