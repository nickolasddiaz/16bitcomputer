# 16-bit CISC Computer and Compiler

A complete 16-bit Complex Instruction Set Computer (CISC) architecture implemented in Logic-SIM Evolution, with a custom high-level language compiler written in Python.

✅ Compiler is finished

❌ 16 bit logic-sim computer is not finished


The compiler generates three output files:
   - `program.tre` - Parse tree visualization
   - `program.asm` - Assembly code
   - `program.bin` - Binary machine code (hex)


## Overview

This project implements a fully functional 16-bit CISC processor with:
- Custom microcode architecture designed in Logic-SIM Evolution
- High-level programming language with C/python-style syntax
- Python-based compiler that generates assembly and binary code
- 114 instruction opcodes supporting arithmetic, logic, control flow, and I/O operations
- 64×64 RGB video display

## Features

- **Complete compiler toolchain**: Source → Parse Tree → Assembly → Binary
- **Register allocation**: Intelligent register and memory management
- **Function support**: User-defined functions with multiple return values
- **Control structures**: if/elif/else, for, while, do-while loops
- **Arithmetic operations**: Addition, subtraction, multiplication, division, modulo
- **Bitwise operations**: AND, OR, XOR, NOT, shifts, rotates
- **Video output**: Built-in functions for pixel manipulation

## System Architecture

### Hardware Specifications

| Component              | Specification                             |
|------------------------|-------------------------------------------|
| **Architecture**       | 16-bit CISC with microcode                |
| **Instruction Memory** | 65,536 (0xFFFF) instructions              |
| **Registers**          | 16 general-purpose (R0-R15)               |
| **RAM**                | 65,535 (0xFFFF) × 16-bit words            |
| **Video Display**      | 16×16 pixels, RGB 555 (15-bit)            |
| **Status Flags**       | Greater, Equal, Less, Carry               |
| **Data Type**          | 16-bit signed integer (-32,768 to 32,767) |
| **Opcode Count**       | 114 instructions                          |

### Register Conventions

| Register | Mnemonic | Purpose                    |
|----------|----------|----------------------------|
| R0-R13   | -        | General purpose registers  |
| R14      | RE (BP)  | Base pointer (stack frame) |
| R15      | RF (SP)  | Stack pointer              |

### Status Flags

- **Greater (G)**: Set when first operand > second operand
- **Equal (E)**: Set when operands are equal
- **Less (L)**: Set when first operand < second operand
- **Carry (C)**: Set when arithmetic operation produces carry/borrow

## Language Specification

### Data Types

The language supports a single data type:
- **Integer**: 16-bit signed integer (-32,768 to 32,767)

### Control Structures

#### If Statement
```c
if (condition) {
    // code block
} elif (condition) {  // optional
    // code block
} else {              // optional
    // code block
}
```

#### Loops

**While Loop**
```c
while (condition) {
    // code block
}
```

**Do-While Loop**
```c
do {
    // code block
} while (condition);
```

**For Loop**
```c
for (i = 0; i < 10; i++) {
    // code block
}
```

### Functions

All programs must contain a `main()` function as the entry point.

**Function Definition**
```c
def function_name(param1, param2) {
    // code block
    return value1, value2;  // Multiple return values supported
}
```

**Function Call**
```c
// Single return value
result = function_name(arg1, arg2);

// Multiple return values
a, b, c = function_name(x, y);

// Mixed assignment
a, b, c, d, e = a, 2, function_name(a, b);
```

### Operators

#### Arithmetic Operators
- `+` Addition
- `-` Subtraction
- `*` Multiplication
- `/` Division (integer)
- `%` Modulo

#### Bitwise Operators
- `&` Bitwise AND
- `|` Bitwise OR
- `^` Bitwise XOR
- `~` Bitwise NOT (one's complement)
- `<<`Left shift
- `>>`Right shift

#### Comparison Operators
- `==` Equal to
- `!=` Not equal to
- `>` Greater than
- `<` Less than
- `>=` Greater than or equal to
- `<=` Less than or equal to

#### Logical Operators
- `&&` or `and` Logical AND
- `||` or `or` Logical OR

#### Assignment Operators
- `=` Assignment
- `+=` Add and assign
- `-=` Subtract and assign
- `*=` Multiply and assign
- `/=` Divide and assign
- `++` Increment
- `--` Decrement

### Built-in Functions

#### Video Functions
```c
VIDEO(r,g,b, x, y)  // Set pixel at (x, y) to color value
VID()               // Update video display
VID_RED(value)        // Set color value
VID_GREEN(value)        // Set color value
VID_BLUE(value)        // Set color value
VID_X(x)            // Set X coordinate
VID_Y(y)            // Set Y coordinate
```

#### System Functions
```c
HALT()              // Halt the computer
```

### Syntax Examples

**Variable Assignment**
```c
a = 3;
a += b;
a -= b;
a *= b;
a /= b;
```

**Negation**
```c
a = -(100 ^ b | function_call());  // Arithmetic negation
a = ~(100 ^ b | function_call());  // Bitwise NOT
```

**Conditional Expressions**
```c
if (a + 6) {          // Non-zero evaluation
    // code
}

if (a == b + 6 && c) {  // Logical AND
    // code
}

if (a == b + 6 || function_call() != 21) {  // Logical OR
    // code
}
```

## Instruction Set

### System Instructions

| Opcode | Mnemonic | Description   |
|--------|----------|---------------|
| `0x00` | `NOP`    | No Operation  |
| `0x01` | `HALT`   | Halt Computer |

### Video Display Instructions

| Opcode | Mnemonic        | Description                    |
|--------|-----------------|--------------------------------|
| `0x01` | `VID`           | Updates the pixel with a color |
| `0x03` | `VID_RED reg`   | Set video Red  0-31            |
| `0x06` | `VID_GREEN reg` | Set video Blue  0-31           |
| `0x09` | `VID_BLUE reg`  | Set video Green  0-31          |
| `0x0C` | `VID_X reg`     | Set video X coordinate 0-63    |
| `0x0F` | `VID_Y reg`     | Set video Y coordinate 0-63    |

### Data Movement Instructions

| Opcode | Mnemonic       | Description               |
|--------|----------------|---------------------------|
| `0x12` | `MOV reg, reg` | Move register to register |


### Comparison Instructions

| Opcode | Mnemonic       | Description                        |
|--------|----------------|------------------------------------|
| `0x18` | `CMP reg, reg` | Compare two registers (sets flags) |

### Arithmetic Instructions

#### Addition
| Opcode | Mnemonic        | Description                                   |
|--------|-----------------|-----------------------------------------------|
| `0x1E` | `ADD reg, reg`  | input1 = input1 + input2                      |
| `0x24` | `SUB reg, reg`  | input1 = input1 - input2                      |
| `0x2A` | `MULT reg, reg` | input1 = input1 * input2                      |
| `0x30` | `DIV reg, reg`  | input1 = input1 / input2                      |
| `0x36` | `QUOT reg, reg` | input1 = input1 mod input2                    |
| `0x3C` | `AND reg`       | input1 = input1 bit and input2                |
| `0x42` | `OR reg, reg`   | input1 = input1 bit or input2                 |
| `0x48` | `XOR reg, reg`  | input1 = input1 bit xor input2                |
| `0x4E` | `SHL reg, reg`  | input1 = input1 shift left input2             |
| `0x54` | `SHR reg, reg`  | input1 = input1 shift right input2            |
| `0x5A` | `NEG reg, reg`  | input1 = negate input2                        |
| `0x60` | `NOT reg, reg`  | input1 = not input2                           |

### Control Flow Instructions

#### Jump Instructions
| Opcode | Mnemonic         | Description                          |
|--------|------------------|--------------------------------------|
| `0x66` | `JMP imm8`       | Unconditional jump to 16-bit address |
| `0x67` | `JEQ imm8`       | Jump if equal flag set               |
| `0x68` | `JNE imm8`       | Jump if not equal                    |
| `0x69` | `JG imm8`        | Jump if greater                      |
| `0x6A` | `JLE imm8`       | Jump if less or equal                |
| `0x6B` | `JL imm8`        | Jump if less                         |
| `0x6C` | `JGE imm8`       | Jump if greater or equal             |
| `0x6D` | `JNZ imm8`       | Jump if zero flag not set            |
| `0x6E` | `JZ imm8`        | Jump if zero flag set                |
| `0x6F` | `JNC imm8`       | Jump if carry flag not set           |
| `0x70` | `JC imm8`        | Jump if carry flag set               |

#### Subroutine Instructions
| Opcode | Mnemonic          | Description                             |
|--------|-------------------|-----------------------------------------|
| `0x71` | `CALL imm8       `| Push return address, jump to subroutine |
| `0x72` | `RTRN`            | Pop return address into PC              |

## Register Conventions

| Register | Purpose         |
|----------|-----------------|
| R0-RC    | General Purpose |
| RD       | User Input      |
| RE       | Base Pointer    |
| RF       | Stack Pointer   |
### Addressing Modes

Instructions support six addressing modes indicated by suffix:

| Suffix | Mode               | Example              | Description                               |
|--------|--------------------|----------------------|-------------------------------------------|
| (none) | Register-Register  | `ADD R1, R2`         | Both operands are registers               |
| _MR     | Memory-Register    | `ADD [BP+5], R2`     | Dest is memory, source is register        |
| _IM     | Register-Immediate | `ADD R1, 10`         | Dest is register, source is immediate     |
| _RM     | Register-Memory    | `ADD R1, [BP+5]`     | Dest is register, source is memory (Load) |
| _MI    | Memory-Immediate   | `ADD [BP+5], 10`     | Dest is memory, source is immediate       |
| _MM    | Memory-Memory      | `ADD [BP+5], [BP+7]` | Both operands are memory                  |

