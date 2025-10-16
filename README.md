# 16-bit CISC Computer and Compiler

A complete 16-bit Complex Instruction Set Computer (CISC) architecture implemented in Logic-SIM Evolution, with a custom high-level language compiler written in Python.


## Overview

This project implements a fully functional 16-bit CISC processor with:
- Custom microcode architecture designed in Logic-SIM Evolution
- High-level programming language with C-style syntax
- Python-based compiler that generates assembly and binary code
- 126 instruction opcodes supporting arithmetic, logic, control flow, and I/O operations
- 16×16 RGB video display with 256-color support

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

| Component              | Specification                                   |
|------------------------|-------------------------------------------------|
| **Architecture**       | 16-bit CISC with microcode                      |
| **Instruction Memory** | 65,536 (0xFFFF) instructions                    |
| **Registers**          | 16 general-purpose (R0-R15)                     |
| **RAM**                | 65,535 (0xFFFF) × 16-bit words                  |
| **Video Display**      | 16×16 pixels, XTerm256 color model (8-bit)      |
| **Status Flags**       | Greater, Equal, Less, Zero, Carry               |
| **Data Type**          | 16-bit signed integer (-32,768 to 32,767)       |
| **Opcode Count**       | 126 instructions (0x00-0x7E)                    |

### Register Conventions

| Register | Mnemonic | Purpose                    |
|----------|----------|----------------------------|
| R0-R11   | -        | General purpose registers  |
| R12      | RC       | System timer               |
| R13      | RD       | User input/control         |
| R14      | RE (BP)  | Base pointer (stack frame) |
| R15      | RF (SP)  | Stack pointer              |

### Status Flags

- **Greater (G)**: Set when first operand > second operand
- **Equal (E)**: Set when operands are equal
- **Less (L)**: Set when first operand < second operand
- **Zero (Z)**: Set when result equals zero
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
VIDEO(value, x, y)  // Set pixel at (x, y) to color value
VID()               // Update video display
VID_V(value)        // Set color value
VID_X(x)            // Set X coordinate
VID_Y(y)            // Set Y coordinate
```

#### System Functions
```c
HALT()              // Halt the computer
```

### Built-in Variables

- `CONTROL` - User input register (R13)
- `TIME` - System timer register (R12)

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

| Opcode | Mnemonic    | Description             |
|--------|-------------|-------------------------|
| `0x02` | `VID`       | Update video display    |
| `0x03` | `VID_V reg` | Set video value (color) |
| `0x06` | `VID_X reg` | Set video X coordinate  |
| `0x09` | `VID_Y reg` | Set video Y coordinate  |

### Data Movement Instructions

| Opcode | Mnemonic       | Description               |
|--------|----------------|---------------------------|
| `0x0C` | `MOV reg, reg` | Move register to register |


### Comparison Instructions

| Opcode | Mnemonic       | Description                        |
|--------|----------------|------------------------------------|
| `0x12` | `CMP reg, reg` | Compare two registers (sets flags) |

### Arithmetic Instructions

#### Addition
| Opcode | Mnemonic        | Description                                   |
|--------|-----------------|-----------------------------------------------|
| `0x18` | `ADD reg, reg`  | input1 = input1 + input2                      |
| `0x1E` | `SUB reg, reg`  | input1 = input1 - input2                      |
| `0x24` | `MULT reg, reg` | input1 = input1 * input2                      |
| `0x2A` | `DIV reg, reg`  | input1 = input1 / input2                      |
| `0x30` | `QUOT reg, reg` | input1 = input1 mod input2                    |
| `0x36` | `AND reg`       | input1 = input1 bit and input2                |
| `0x3C` | `OR reg, reg`   | input1 = input1 bit or input2                 |
| `0x42` | `XOR reg, reg`  | input1 = input1 bit xor input2                |
| `0x48` | `SHL reg, reg`  | input1 = input1 shift left input2             |
| `0x4E` | `SHR reg, reg`  | input1 = input1 shift right input2            |
| `0x54` | `RR reg, reg`   | input1 = input1 rotate right input2           |
| `0x5A` | `RL reg, reg`   | input1 = input1 rotate left input2            |
| `0x60` | `AR reg, reg`   | input1 = input1 arithmetic right shift input2 |
| `0x66` | `NEG reg, reg`  | input1 = negate input2                        |
| `0x6C` | `NOT reg`       | input1 = not input2                           |

### Control Flow Instructions

#### Jump Instructions
| Opcode | Mnemonic         | Description                          |
|--------|------------------|--------------------------------------|
| `0x72` | `JMP imm8, imm8` | Unconditional jump to 16-bit address |
| `0x73` | `JEQ imm8, imm8` | Jump if equal flag set               |
| `0x74` | `JNE imm8, imm8` | Jump if not equal                    |
| `0x75` | `JG imm8, imm8`  | Jump if greater                      |
| `0x76` | `JLE imm8, imm8` | Jump if less or equal                |
| `0x77` | `JL imm8, imm8`  | Jump if less                         |
| `0x78` | `JGE imm8, imm8` | Jump if greater or equal             |
| `0x79` | `JNZ imm8, imm8` | Jump if zero flag not set            |
| `0x7A` | `JZ imm8, imm8`  | Jump if zero flag set                |
| `0x7B` | `JNC imm8, imm8` | Jump if carry flag not set           |
| `0x7C` | `JC imm8, imm8`  | Jump if carry flag set               |

#### Subroutine Instructions
| Opcode | Mnemonic          | Description                             |
|--------|-------------------|-----------------------------------------|
| `0x7D` | `CALL imm8, imm8` | Push return address, jump to subroutine |
| `0x7E` | `RTRN`            | Pop return address into PC              |

## Register Conventions

| Register | Purpose         |
|----------|-----------------|
| R0-RB    | General Purpose |
| RC       | Time            |
| RD       | User Input      |
| RE       | Base Pointer    |
| RF       | Stack Pointer   |
### Addressing Modes

Instructions support six addressing modes indicated by suffix:

| Suffix | Mode               | Example              | Description                               |
|--------|--------------------|----------------------|-------------------------------------------|
| (none) | Register-Register  | `ADD R1, R2`         | Both operands are registers               |
| _R     | Memory-Register    | `ADD [BP+5], R2`     | Dest is memory, source is register        |
| _I     | Register-Immediate | `ADD R1, 10`         | Dest is register, source is immediate     |
| _L     | Register-Memory    | `ADD R1, [BP+5]`     | Dest is register, source is memory (Load) |
| _RI    | Memory-Immediate   | `ADD [BP+5], 10`     | Dest is memory, source is immediate       |
| _RR    | Memory-Memory      | `ADD [BP+5], [BP+7]` | Both operands are memory                  |


```

The compiler generates three output files:
   - `program.tre` - Parse tree visualization
   - `program.asm` - Assembly code
   - `program.bin` - Binary machine code (hex)