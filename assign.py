from collections import deque 
from location import Location
from temp_var import Temp, exists, MAX_REGISTERS


class Assign:
    def __init__(self):
        self.commands = [] # used to temporarily store commands while assigning variables
        self.max_variables = 0
        self.lifetimes = {}  # Maps variable names to their lifetimes
        self.location = Location() # maps variable name to Location register 0-11, RAM 12-...267
        self.global_vars = set() # variables that live on outside the block
        self.local_vars = set()
        self.true_local_vars = set()
        self.stack = deque() # for swapping variables to/from RAM

    def set_up(self, lifetimes: dict, max_variables: int, global_vars: set, local_vars: set, true_local_vars: set):
        self.global_vars = global_vars
        self.local_vars = local_vars
        self.true_local_vars = true_local_vars
        self.lifetimes = lifetimes
        self.max_variables = max_variables
    
    def assign_variables(self, var: str|int, index: int) -> str|int|None:
        if isinstance(var, list):
            raise Exception(f"Lists are not supported in assign_variables. {var} was given.")
        if isinstance(var, None.__class__):
            return None
        if isinstance(var, int):
            return var
        if exists(var):
            return Temp.get_temp(var)
        
        reg_location = self.location.get_index_register(var) # check if already in registers
        if reg_location != -1: # if in registers, return register
            return reg_location
        
        ram_location = self.location.get_index_ram(var) # check if already in RAM
        if ram_location != -1: # if in RAM, swap to the least used register
            free_reg = self.free_register(index) # get a free register
            self.location.move_variables(var, free_reg) # move variable from RAM to register
            return free_reg
        
        # the variables were not found in either registers or RAM, so we need to Assign them
        free_reg = self.free_register(index) # get a free register
        self.location.set_item(var, free_reg) # Assign variable to register
        
        
        return free_reg
    
    def prepare_allocation(self, func_ir, index:int, global_life) -> list[str]:
        to_be_put_back = {}
        var_to_stay = func_ir.locals

        # to do account for the amount in var_to_stay and max variables
        var_to_stay = sorted(var_to_stay, key=lambda x: global_life[x].get_next_use(index)) # sort by the next use first
        max_amount_to_move = min(MAX_REGISTERS, len(var_to_stay))
        var_to_stay, var_to_move = var_to_stay[:max_amount_to_move], var_to_stay[max_amount_to_move:]

        # moving all var_to_move to ram
        for name in var_to_move: # check if list is empty
            index = self.location.get_index_ram(name)
            if index == -1:
                index = self.location.move_variables_ram(name)
            to_be_put_back[name] = index

        # moving all var_to_stay to registers
        for i in range(MAX_REGISTERS):
            if len(var_to_stay) == 0:
                break
            name = self.location.get_var(i)
            if name is None: #register does not exist 
                var = var_to_stay.pop(0)
                to_be_put_back[var] = i
                self.location.move_variables(var,i) # move variable to empty register
            elif name not in var_to_stay: # register is occupied by a variable that is not needed
                var = var_to_stay.pop(0)
                to_be_put_back[var] = i
                self.location.move_variables_ram(name) # move the variable in the register to RAM
                self.location.move_variables(var,i) # move variable to register
            else: # register is occupied by a variable that is needed
                to_be_put_back[name] = i
                var_to_stay.remove(name) # remove it from the list, as it is already in a register


        for name in var_to_stay: # find the rest of the variables in RAM and put them in to_be_put_back{}
            pos = self.location.get_index_ram(name)
            if pos == -1:
                raise Exception(f"Variable {name} should be in RAM, but was not found. Location: {self.location} {self.location.rev_location}")
            to_be_put_back[name] = pos
        
        return to_be_put_back
    
    def finalize_allocation(self, func_ir, reg_list_rtrn: dict): # takes in list from block and puts them back in their place
        vars_to_remove = func_ir.true_locals

        self.location.check_delete_list(list(vars_to_remove)) # delete all local variables that are not global
        
        temp_var = Temp.TEMP_SWAP.reg # use Temp swap to help with swapping
        for name, pos in reg_list_rtrn.items():
            location_var = self.location.get_int(name)
            if location_var == -1:
                raise Exception(f"Variable {name} should be in register, but was not found. {self.location} {self.location.rev_location}")
            if pos == location_var: # the variable is already in the correct place
                continue

            to_put = self.location.get_var(pos)
            to_put_pos = self.location.get_int(pos)
            if to_put is None:
                self.location.move_variables(name, pos) # if the variable does not exist, move it to that position
                continue
            else: # move the to_put into Temp, then move name to to_put's position, then set Temp to pos
                self.location.move_variables(to_put, temp_var)
                self.location.move_variables(name, to_put_pos) # create move variable to Temp function
                temp_var = pos



    def get_commands(self):
        return self.location.get_commands()
    
    def free_register(self, inst_pointer) -> int: # account for the current register to be the one to swap
        # Check if registers are full first
        free_reg = self.location.get_lowest_register()
        if free_reg != -1: # if exists return it
            return free_reg
        
        furthest_next_use = -1
        var_to_swap = None

        for name, reg in self.location.get_registers().items(): # loops through all variables in registers
            next_use = self.lifetimes.get(name)
            if next_use is None:
                self.location.move_variables_ram(name)
                
                return reg
            next_use = next_use.get_next_use(inst_pointer)
            if next_use > furthest_next_use:
                furthest_next_use = next_use
                var_to_swap = reg
        if var_to_swap is None:
            raise Exception("No variable to swap found, this should never happen.")
        self.location.move_variables_ram(var_to_swap) # move the variable to RAM

        return var_to_swap
        
    def check_and_free(self, index: int):
        for var, lifetime in self.lifetimes.copy().items():
            if lifetime.check_if_dead(index):
                in_true_local = var in self.true_local_vars
                if not in_true_local:
                    self.location.move_variables_ram(var)

    
    
