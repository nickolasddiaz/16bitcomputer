import os
import re
import string
from dataclasses import dataclass
from enum import Enum
'''
8-bit assembler for an instruction set for my 8-bit computer project.
It generates a binary file 16bitcode.hex from 8bitcode.txt that contains assembly code
Loaded though the instruction register ROM 4k x16bit through version 2.0 raw from logic sim evolution
'''
class DataType(Enum):
    Reg = 0
    Imm8 = 1
    Func = 2
    Adr = 3
    Double_Reg = 4

triple_reg = (DataType.Double_Reg, DataType.Reg) # 3 cycles
Imm8s = (DataType.Double_Reg, DataType.Imm8) # 3 cycles
one_reg = DataType.Reg  # 2 cycles
Calls = DataType.Func  # 3 cycles
No_types = None # 1 cycles
Register_Address = (DataType.Reg, DataType.Adr) # 3 cycles
two_reg = DataType.Double_Reg  # 2 cycles
reg_imm = (DataType.Reg, DataType.Imm8) # 3 cycles

def get_cycles_from_parse(cycles):
    if cycles is Calls:
        return 3
    elif cycles is No_types:
        return 1
    elif isinstance(cycles, tuple):
        return len(cycles) + 1
    else:
        return 2


@dataclass(frozen=True)
class Instruction:
    code: int
    parse: DataType

OPCODES = {
    "NOP":   Instruction(0x0, No_types),   # No Operation ex NOP
    "HALT":  Instruction(0x1, No_types),   # Halt Computer ex HALT
    "LD":    Instruction(0x2, Register_Address),   # Load byte from RAM into register: ex LD rd, [addr]
    "ST":    Instruction(0x3, Register_Address),   # Store byte from register into RAM: ex ST rs, [addr]
    "MOV":   Instruction(0x4, two_reg),   # Copy register to register: ex MOV rd, rs
    "LI":    Instruction(0x5, reg_imm),   # Load immediate value to register: ex LI rd, imm8
    "VID":   Instruction(0x6, No_types),   # Load RGB video  x cord RF, y cord RE, and value XTERM 256 from RD: ex VID
    "ADD":   Instruction(0x7, triple_reg),   # Addition: ex ADD rd, rs, rt
    "SUB":   Instruction(0x8, triple_reg),   # Subtraction: ex SUB rd, rs, rt
    "MULT":  Instruction(0x9, triple_reg),   # Multiplication: ex MULT rd, rs, rt
    "DIV":   Instruction(0xA, triple_reg),   # Division: ex DIV rd, rs, rt
    "QUOT":  Instruction(0xB, triple_reg),   # Quotient: ex QUOT rd, rs, rt
    "AND":   Instruction(0xC, triple_reg),   # Bitwise AND: ex AND rd, rs, rt
    "OR":    Instruction(0xD, triple_reg),   # Bitwise OR: ex OR rd, rs, rt
    "XOR":   Instruction(0xE, triple_reg),   # Bitwise XOR: ex XOR rd, rs, rt
    "NOT":   Instruction(0xF, two_reg),   # Bitwise NOT: ex NOT rd, rs
    "SHL":   Instruction(0x10, triple_reg),  # Shift Left: ex SHL rd, rs, rt
    "SHR":   Instruction(0x11, triple_reg),  # Shift Right: ex SHR rd, rs, rt
    "RR":    Instruction(0x12, triple_reg),  # Rotate Right: ex RR rd, rs
    "RL":    Instruction(0x13, triple_reg),  # Rotate Left: ex RL rd, rs
    "AR":    Instruction(0x14, triple_reg),  # Arithmetic Right: ex AR rd, rs
    "ADDI":  Instruction(0x15, Imm8s),  # Add Immediate: ex ADDI rd, rt, imm8
    "SUBI":  Instruction(0x16, Imm8s),  # Subtract Immediate: ex SUBI rd, rt, imm8
    "MULTI": Instruction(0x17, Imm8s),  # Multiply Immediate: ex MULTI rd, rt, imm8
    "DIVI":  Instruction(0x18, Imm8s),  # Divide Immediate: ex DIVI rd, rt, imm8
    "QUOTI": Instruction(0x19, Imm8s),  # Quotient Immediate: ex QUOTI rd, rt, imm8
    "ANDI":  Instruction(0x1A, Imm8s),  # Bitwise AND Immediate: ex ANDI rd, rt, imm8
    "ORI":   Instruction(0x1B, Imm8s),  # Bitwise OR Immediate: ex ORI rd, rt, imm8
    "XORI":  Instruction(0x1C, Imm8s),  # Bitwise XOR Immediate: ex XORI rd, rt, imm8
    "NOTI":  Instruction(0x1D, reg_imm),  # Bitwise NOT Immediate: ex NOTI rd, imm8
    "SHLI":  Instruction(0x1E, Imm8s),  # Shift Left Immediate: ex SHLI rd, rt, imm8
    "SHRI":  Instruction(0x1F, Imm8s),  # Shift Right Immediate: ex SHRI rd, rt, imm8
    "RRI":   Instruction(0x20, Imm8s),  # Rotate Right Immediate: ex RRI rd, rt, imm8
    "RLI":   Instruction(0x21, Imm8s),  # Rotate Left Immediate: ex RLI rd, rt, imm8
    "ARI":   Instruction(0x22, Imm8s),  # Arithmetic Right Immediate: ex ARI rd, rt, imm8
    "INC":   Instruction(0x23, two_reg),  # Increment: ex INC rd, rt
    "DEC":   Instruction(0x24, two_reg),  # Decrement: ex DEC rd, rt
    "JMP":   Instruction(0x25, Calls),  # Jump to address: ex JMP addr or JMP <function_name>
    "JEQ":   Instruction(0x26, Calls),  # Jump if Equal: ex JEQ addr
    "JNE":   Instruction(0x27, Calls),  # Jump if Not Equal: ex JNE addr
    "JGT":   Instruction(0x28, Calls),  # Jump if Greater Than: ex JGT addr
    "JLT":   Instruction(0x29, Calls),  # Jump if Less Than: ex JLT addr
    "JGE":   Instruction(0x2A, Calls),  # Jump if Greater Than or Equal: ex JGE addr
    "JLE":   Instruction(0x2B, Calls),  # Jump if Less Than or Equal: ex JLE addr
    "JNZ":   Instruction(0x2C, Calls),  # Jump if NOT Zero: ex JNZ addr
    "JZ":    Instruction(0x2D, Calls),  # Jump if Zero: ex JZ addr
    "JNC":   Instruction(0x2E, Calls),  # Jump if No Carry: ex JNC addr
    "JC":    Instruction(0x2F, Calls),  # Jump if Carry: ex JC addr
    "CALL":  Instruction(0x30, Calls),  # Call subroutine: ex CALL addr or CALL <function_name>
    "RTRN":  Instruction(0x31, No_types),  # Return from subroutine: ex RTRN
    "PUSH":  Instruction(0x32, one_reg),  # Push to stack: ex PUSH rs
    "POP":   Instruction(0x33, one_reg),  # Pop from stack: ex POP rs
    "CMP":   Instruction(0x34, two_reg),  # Compare two registers: ex CMP rs, rt
    "CMPI":  Instruction(0x35, reg_imm),  # Compare register with immediate: ex CMPI rs, imm8
}

functions = {}  # Dictionary to hold function names and their line numbers


def assemble_instruction(instr: str, linecount: int) -> str:
    parts = instr.strip().replace(',', '').split()
    op = parts[0].upper()
    if op not in OPCODES:
        raise ValueError(f"instruction not found on line {linecount}, Opcode: {op}")

    instruction = OPCODES[op]
    opcode = instruction.code
    formats = instruction.parse

    i = 0
    code = [opcode]
    if not instruction.parse:
        # If parse is empty, just return the opcode
        return code
    if isinstance(instruction.parse, tuple) and len(parts) - 1 < len(instruction.parse):
        raise ValueError(f"Not enough arguments for instruction '{op}' on line {linecount}")
    
    formats_tuple = formats if isinstance(formats, tuple) else (formats,)
    index = 0
    while index < len(formats_tuple):
        i += 1
        assemble_format = formats_tuple[index]
        match assemble_format:
            case DataType.Reg: # Extracting 4 bits for register and append it
                    code.append(int(parts[i], 16) << 0x04 & 0xFF)
                    index += 1

            case DataType.Double_Reg:
                    code.append((int(parts[i], 16) << 0x04 & 0xFF) | (int(parts[i+1], 16) & 0xF))
                    index += 1
                    i += 1

            case DataType.Imm8: # Extracting 8 bits for immediate value and append it
                code.append(int(parts[i], 16) & 0xFF)
                index += 1

            case DataType.Func: # getting a jump address (16 bits)
                if all(c in string.hexdigits for c in parts[1]): # if the jump address is not a number use the number as the address
                    immediate = int(parts[i], 16) & 0xFFFF
                else:
                    function_name = parts[i]
                    if function_name not in functions:
                        raise ValueError(f"Function '{function_name}' not defined on line {linecount}, Opcode: {op}, Number: {i}")
                    immediate = functions[function_name] & 0xFFFF # point to the address number of the defined function name
                code.append((immediate >> 8) & 0xFF) # split it and append the address into two higher (8 bits) and lower (8 bits)
                code.append(immediate & 0xFF)
                index += 1

            case DataType.Adr:
                if i < len(parts):
                    
                    if parts[i].startswith('[') and parts[i].endswith(']'):
                        immediate = int(parts[i].replace("[", "").replace("]", ""), 16) & 0xFF
                        code.append(immediate)
                    else:
                        raise ValueError(f"Address must be enclosed in brackets [] on line {linecount} , Opcode: {op}, Number: {i}")
                index += 1
                
    return code




def assemble_file(input_path: str, output_: str):
    input_path = os.path.join(os.path.dirname(__file__), input_path)
    with open(input_path, 'r') as infile:
        lines = infile.readlines()

    hex_linecount = 0
    for line in lines: # Strip whitespace and ignore empty lines or comments while looping through the lines
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Search for things encased in <>
        matches = re.findall(r'<(.*?)>', line)
        for match in matches:
            functions[match] = hex_linecount -1

        hex_linecount += get_cycles_from_parse(OPCODES[line.split(maxsplit=1)[0].upper()].parse)

    linecount = 0
    output_lines = []
    for line in lines: # Strip whitespace and ignore empty lines or comments while looping through the lines
        line = line.strip()
        linecount += 1
        if hex_linecount > 65535:
            raise ValueError("Program exceeds maximum line count of 65535.")
        if not line or line.startswith('#'):
            continue
        encoded = assemble_instruction(re.sub(r'<(.*?)>', '', line), linecount)
        if isinstance(encoded, list):
            for code in encoded:
                if code is not None:
                    output_lines.append(f"{(code & 0xFF):02X}")

    with open(output_, 'w') as outfile:
        for code in output_lines:
            if code is not None:
                outfile.write(code + '\n')
    print(f"Assembly complete. Output written to {output_}. Total lines: {hex_linecount}")

output_path = os.path.join(os.path.dirname(__file__), '8bitcode.hex') # Output file path
assemble_file('8bitcode.txt', output_path)