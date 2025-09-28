from enum import Enum, auto
from assign import Assign
from temp_var import exists
from sys import maxsize

# https://www.youtube.com/watch?v=YmDoiA1_ri4

# ------------- Intermediate form builder -------------

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
    
class Commands:
    def __init__(self, operand: str, var1: str | None, var2: str | int | None, jump_label: str | None=None):
        self.operand = operand
        self.var1 = var1 # can be str or None
        self.var2 = var2 # can be int, str or None
        self.destination = None
        if jump_label is None:
            self.jump_label = None
        else:
            self.jump_label = '<'+ jump_label + '>'
        self.comparison_side = None

    def combine_operand(self):
        return f"{self.operand}+{self.var1}+{self.var2}"

    def get_var1(self):
        return self.var1
    def get_var2(self):
        return self.var2
    def set_var2(self, var2):
        self.var2 = var2
    def set_var1(self, var1):
        self.var1 = var1
    def get_other(self):
        return self.other
    def get_operand(self):
        return self.operand
    def get_jump_label(self):
        return self.jump_label
    def set_destination(self, destination):
        self.destination = destination
    def set_comparison_left(self):
        self.comparison_side = 'LEFT'
    def set_comparison_right(self):
            self.comparison_side = 'RIGHT'
    def set_jump_label(self, jump_label):
        self.jump_label = '<'+ jump_label + '>'
    def negate_jump(self):
        match self.operand:
            case 'JEQ':
                self.operand = 'JNE'
            case 'JNE':
                self.operand = 'JEQ'
            case 'JGE':
                self.operand = 'JL'
            case 'JLE':
                self.operand = 'JG'
            case 'JG':
                self.operand = 'JLE'
            case 'JL':
                self.operand = 'JGE'
            case _:
                raise Exception(f"Cannot negate unknown jump operand: {self.operand}")

    def __str__(self):
        parts = [self.operand]
        if self.var1 is not None:
            parts.append(str(self.var1))
        if self.var2 is not None:
            parts.append(str(self.var2))
        if self.comparison_side is not None:
            parts.append(f"TEMP_{self.comparison_side}")
        if self.jump_label is not None:
            parts.append(str(self.jump_label))
        if self.destination is not None:
            parts.append(f"{self.destination}")
        return ", ".join(parts)

class FunctionCall:
    def __init__(self, function_name: str, arguments: list[str|int]):
        self.function_name = function_name
        self.arguments = arguments
        self.assignment = [] # to be set later if needed
        self.jump_label = None

    def append_assignment(self, argument: str|int):
        self.assignment.extend(argument)

    def set_jump_label(self, jump_label):
        if self.jump_label is not None:
            self.jump_label += ',' + jump_label
        else:
            self.jump_label = jump_label

    def __str__(self):
        args_str = ", ".join(map(str, self.arguments))
        jump_str = f", JUMP: <{self.jump_label}>" if self.jump_label else ""

        return f"CALL: {self.function_name}, ARGs: [{args_str}], ASSIGN: {self.assignment}{jump_str}" 
    
# ------------- Variable Lifetime Management -------------

class BlockType(Enum):
    FUNCTION = "function"
    COMPARE_BLOCK = "compare"
    COMPARE_AND_BLOCK = "compare_and"
    COMPARE_OR_BLOCK = "compare_or"
    WHOLE_IF_BLOCK = "if_block"
    IF_BLOCK = "if"
    ELIF_BLOCK = "elif"
    ELSE_BLOCK = "else"
    WHILE_BLOCK = "while"
    DO_WHILE_BLOCK = "while"
    FOR_BLOCK = "for"

class IRform:
    def __init__(self):
        self.IR_BUILDER = dict()  # Maps function names to their IR representations
        self.assign = Assign()
        self.final_program = []
        global global_lifetimes
        global_lifetimes = dict()  # Global lifetimes across all functions

    def add_builder(self, function_name, block_type):
        if function_name not in self.IR_BUILDER:
            self.IR_BUILDER[function_name] = IRBuilder(block_type)
        else:
            raise Exception(f"Function {function_name} already defined.")
        
    def add_command(self, function_name, command):
        self.IR_BUILDER[function_name].add(command)

    def add_commands(self, function_name, commands):
        self.IR_BUILDER[function_name].add_all(commands)

    def __str__(self):
        print("\nIR Builder State:")
        for func_name, builder in self.IR_BUILDER.items():
            print(f"\nFunction: {func_name}")
            print(builder)

    def print_lifetimes(self):
        for func_name, builder in self.IR_BUILDER.items():
            print(f"\nFunction: {func_name} Lifetimes:")
            print(f"Max variables needed: {builder.max_variables}")
            print(f"True Locals: {sorted(builder.true_locals)}")
            print(f"Locals: {sorted(builder.locals)}")
            print(f"Globals: {sorted(builder.globals)}")
            print(f"Inserted functions: {sorted(builder.inserted)}")
            builder.print_lifetimes()

    def process_lifetimes(self):
        for func_name, builder in self.IR_BUILDER.items():
            if builder.block_type == BlockType.FUNCTION:
                self.process_variable_lifetimes(func_name, builder)

        for func_name in self.IR_BUILDER.keys():
            IR_BUILD = self.IR_BUILDER[func_name]
            lifetime_keys = set(IR_BUILD.lifetimes.keys())
            IR_BUILD.globals = lifetime_keys & IR_BUILD.globals
            IR_BUILD.locals = lifetime_keys
            IR_BUILD.true_locals = IR_BUILD.locals - IR_BUILD.globals
            IR_BUILD.max_variables = IR_BUILD.get_max_variables()
                
        for func_name, builder in self.IR_BUILDER.items():
            if builder.block_type == BlockType.FUNCTION:
                self.process_max_var_recursively(builder)

    def process_max_var_recursively(self, function: 'IRBuilder') -> int:
        if function.inserted is None:
            return function.max_variables
        for func_name in function.inserted:
            function.max_variables = max(function.max_variables, self.process_max_var_recursively(self.IR_BUILDER[func_name]))
        return function.max_variables
        
    
    def process_variable_lifetimes(self, function_name: str, builder: 'IRBuilder', index: int = 0) -> int:
        global_life = global_lifetimes.setdefault(function_name, dict())
        builder.parent_function = function_name
        for i, cmd in enumerate(builder.command_list):
            if isinstance(cmd, Commands) and cmd.operand == "INSERT":
                func_ir = self.IR_BUILDER[cmd.var1]
                func_ir.append_globals(builder.locals, builder.globals)
                index = self.process_variable_lifetimes(function_name, func_ir, index)
                self.set_used_lifetime(builder.lifetimes, func_ir.lifetimes, func_ir.globals)
                builder.inserted.add(cmd.var1)

            if check_to_skip(cmd):
                list_vars = cmd.get_var1(), cmd.get_var2()
                
                for var in list_vars:
                    if  isinstance(var, str) and not exists(var):
                        value = builder.lifetimes.setdefault(var, VariableLifetime())
                        value.add_use(index)
                        glob_value = global_life.setdefault(var, VariableLifetime())
                        glob_value.add_use(index)
                        builder.append_locals(var)
            if isinstance(cmd, FunctionCall):
                for var in cmd.assignment:
                    if isinstance(var, str) and not exists(var):
                        value = builder.lifetimes.setdefault(var, VariableLifetime())
                        value.add_use(index)
                        glob_value = global_life.setdefault(var, VariableLifetime())
                        glob_value.add_use(index)
                        builder.append_locals(var)
            index += 1
        return index

    def variable_assignment(self):
        start = self.IR_BUILDER.get("main")
        self.function_assignment(start)
        if start is None:
            raise Exception("No variable named 'main' found.")
        for func_name, builder in self.IR_BUILDER.items():
            if not builder.proceeded:
                continue
                #raise Exception(f"Function {func_name} was not reached from 'main'.")
        
    def function_assignment(self, function: 'IRBuilder', cmp_list_rtrn =None):
        if function.proceeded:
            return
        function.proceeded = True
        i = 0
        self.assign.set_up(function.lifetimes, function.max_variables, function.globals, function.locals, function.true_locals)
        for cmd in function.command_list:
            append_cmd = True
            if check_to_skip(cmd):
                cmd.var1 = self.assign.assign_variables(cmd.var1, i)
                cmd.var2 = self.assign.assign_variables(cmd.var2, i)
                cmd.destination = self.assign.assign_variables(cmd.destination, i)
            if isinstance(cmd, Commands) and cmd.operand == "INSERT":
                append_cmd = False
                func_IR = self.IR_BUILDER[cmd.var1]
                
                if func_IR.block_type == BlockType.COMPARE_BLOCK:
                    self.function_assignment(func_IR) # recursively call the function
                    print(self.assign.location)
                    self.assign.finalize_allocation(func_IR, cmp_list_rtrn) # put back the variables in the compare block
                else:
                    reg_list_rtrn = self.assign.prepare_allocation(func_IR, i, global_lifetimes[func_IR.parent_function]) # prepare the allocation for the function
                    self.final_program.extend(self.assign.get_commands()) # add the commands to the final program
                    self.function_assignment(func_IR, reg_list_rtrn) # recursively call the function
                    self.assign.finalize_allocation(func_IR, reg_list_rtrn) # put back the variables in the function


            i += 1
            self.final_program.extend(self.assign.get_commands())
            if append_cmd: # not to append INSERT commands
                self.final_program.append(cmd.__str__())

    def get_final_program(self):
        return self.final_program
    
    def set_used_lifetime(self, parent_lifetime, child_lifetime, add_list):
        for var in add_list:
            live = child_lifetime.get(var)
            if live is not None:
                parent_live = parent_lifetime.setdefault(var, VariableLifetime())
                parent_live.append_use_list(live.use_list)


class VariableLifetime:
    def __init__(self):
        self.first_use = None
        self.last_use = None
        self.use_list = []
        self.use_count = 0

    def append_use_list(self, use_list):
        self.use_list.extend(use_list)
        self.use_list.sort()
        self.last_use = self.use_list[-1] if self.use_list else None
    
    def add_use(self, instruction_index: int):
        
        if self.first_use is None:
            self.first_use = instruction_index

        if self.last_use != instruction_index:
            self.use_list.append(instruction_index)
            self.use_count += 1



        self.last_use = instruction_index
        
    def check_if_dead(self, instruction_index: int) -> bool:
        return instruction_index > self.last_use
    
    def get_next_use(self, instruction_index: int) -> int:
        # Find the next use after instruction_index
        next_uses = [use for use in self.use_list if use > instruction_index]
        if next_uses:
            next_use = min(next_uses)
            # Remove all uses up to and including instruction_index
            self.use_list = [use for use in self.use_list if use > instruction_index]
            return next_use
        return maxsize
 
    def __str__(self):
        return (f"First Use: {self.first_use}, Last Use: {self.last_use}, "
                f"Use Count: {self.use_count}, Use List: {self.use_list}")

class IRBuilder:
    def __init__(self, block_type):
        self.command_list = []
        self.amount_returned = 0
        self.amount_input = 0
        self.block_type = block_type
        self.parent_function = "" 
        self.block_id = None  # Unique identifier
        self.lifetimes = {}  # Maps variable names to VariableLifetime instances
        self.max_variables = 0
        self.proceeded = False
        self.locals = set() # variables that are used in this block
        self.globals = set()
        self.true_locals = set() # local that are not globals_
        self.inserted = set() # functions that have been inserted into this block

        
        # Lifetime tracking at function level
        if block_type == BlockType.FUNCTION:
            self.lifetime = {}  # Only functions track lifetimes
            self.child_blocks = []  # List of child blocks
        else:
            self.lifetime = None  # Child blocks don't track independently
    def append_locals(self, var: str):
        self.locals.add(var)

    def append_globals(self, local, globals_):
        self.globals = self.globals | local | globals_


    def get_root_function(self):
        """Get the root function that owns lifetime tracking"""
        current = self
        while current.parent is not None:
            current = current.parent
        return current
    
    def add(self, command):
        self.command_list.append(command)

    def add_all(self, commands):
        self.command_list.extend(commands)

    def __str__(self):
        result = [f"Block Type: {self.block_type.value}", f"Returned: {self.amount_returned}",
                  f"Input: {self.amount_input}", "Commands:"]
        for i, command in enumerate(self.command_list):
            result.append(f"  {i}: {command}")
        return "\n".join(result)
    
    def print_lifetimes(self):
        for var, lifetime in self.lifetimes.items():
            print(f"Variable: {var}, Lifetime: {lifetime}")

    def get_max_variables(self) -> int:
        # Count how many times each variable appears in use_list
        true_local_lifetime = {key: self.lifetimes[key] for key in self.true_locals if key in self.lifetimes}
        # get a new dictionary with only the true local
        intervals = []
        for lifetime in true_local_lifetime.values():
            intervals.append((lifetime.first_use, lifetime.last_use))

        overlap = self.find_max_overlap_events(intervals)

        return overlap + min(len(self.globals), len(self.locals))

    @staticmethod
    def find_max_overlap_events(intervals):
        # Given a list of (start, end) tuples, find the maximum number of overlapping intervals
        if not intervals:
            return 0

        events = []
        for start, end in intervals:
            # A start event increases overlap
            events.append((start, 1))
            # An end event decreases overlap
            events.append((end, -1))

        # Sort by time, then by event type (starts before ends)
        events.sort()

        max_overlap = 0
        current_overlap = 0
        for time, event_type in events:
            current_overlap += event_type
            if current_overlap > max_overlap:
                max_overlap = current_overlap

        return max_overlap


def check_to_skip(cmd):
    return not (not isinstance(cmd, Commands) or cmd.operand in ["INSERT", "NOP", "JMP", "JEQ", "JNE", "JGE", "JLE", "JG", "JL", "CALL", "RETURN"])
    