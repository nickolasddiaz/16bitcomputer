# 8-bit CISC Processor Specification
*Logic-SIM Evolution Project*

## Architecture Overview

This is a Complex Instruction Set Computer (CISC) with microcode 8-bit opcodes designed and implemented in Logic-SIM Evolution.

## Instruction Formats
### R-type (Register Operations)
```
[ opcode(8) | reg(4) + reg(4) ]
```

### I-type (Immediate Operations)
```
[ opcode(8) | reg(4) | immediate(8) ]
```

### L-type (RAM Load Operations)
```
[ opcode(8) | reg(4) | RAM_addr(8) ]
```

### RI-type (RAM Immediate Operations)
```
[ opcode(8) | RAM_addr(8) | immediate(8) ]
```

### RR-type (RAM to RAM Operations)
```
[ opcode(8) | RAM_addr(8) | RAM_addr(8) ]
```

### J-type (Jumps and Calls)
```
[ opcode(8) | high(8) | low(8) ]
```

## System Specifications

| Component              | Specification                                  |
|------------------------|------------------------------------------------|
| **Instruction Memory** | 65,536 instructions - program counter 16-bit   |
| **Registers**          | 16 registers (0-15)                            |
| **RAM**                | 256 × 8-bit                                    |
| **Video Display**      | 16×16 RGB, XTerm256 color model (8-bit)        |
| **Status Register**    | Flags: Greater, Equal, Less, Zero, Carry       |
| **Program Counter**    | 16-bit                                         |
| **Variable Type**      | Only 8-bit unsigned integer 0 - 255/0x0 - 0xFF |
| **Number of Opcodes**  | 83 (0x00-0x52)                                 |

## Instruction Set

### System Instructions

| Opcode | Mnemonic | Format | Description   |
|--------|----------|--------|---------------|
| `0x00` | `NOP`    | -      | No Operation  |
| `0x01` | `HALT`   | -      | Halt Computer |

### Video Display Instructions

| Opcode | Mnemonic       | Format | Description             |
|--------|----------------|--------|-------------------------|
| `0x02` | `VID`          | -      | Update video display    |
| `0x03` | `VID_V [addr]` | -      | Set video value (color) |
| `0x04` | `VID_X [addr]` | -      | Set video X coordinate  |
| `0x05` | `VID_Y [addr]` | -      | Set video Y coordinate  |

### Data Movement Instructions

| Opcode | Mnemonic                | Format | Description                  |
|--------|-------------------------|--------|------------------------------|
| `0x06` | `MOV reg, reg`          | R      | Move register to register    |
| `0x07` | `MOV_R [addr], reg`     | R      | Move RAM to register         |
| `0x08` | `MOV_I reg, imm8`       | I      | Move immediate to register   |
| `0x09` | `MOV_L r, [addr]`       | L      | Move register to RAM address |
| `0x0A` | `MOV_RI [addr], imm8`   | RI     | Move immediate to RAM        |
| `0x0B` | `MOV_RR [addr], [addr]` | RR     | Move RAM to RAM              |

### Comparison Instructions

| Opcode | Mnemonic            | Format | Description                        |
|--------|---------------------|--------|------------------------------------|
| `0x0C` | `CMP reg, reg`      | R      | Compare two registers (sets flags) |
| `0x0D` | `CMP_R [addr], reg` | R      | Compare RAM with register          |
| `0x0E` | `CMP_I reg, imm8`   | I      | Compare register with immediate    |
| `0x0F` | `CMP_L reg, [addr]` | L      | Compare register with RAM          |

### Arithmetic Instructions

#### Addition
| Opcode | Mnemonic            | Format | Description              |
|--------|---------------------|--------|--------------------------|
| `0x10` | `ADD reg, reg`      | R      | input1 = input1 + input2 |
| `0x11` | `ADD_R reg, [addr]` | R      |                          |
| `0x12` | `ADD_I reg, imm8`   | I      |                          |
| `0x13` | `ADD_L [addr], reg` | L      |                          |

#### Subtraction
| Opcode | Mnemonic            | Format | Description              |
|--------|---------------------|--------|--------------------------|
| `0x14` | `SUB reg, reg`      | R      | input1 = input1 - input2 |
| `0x15` | `SUB_R reg, [addr]` | R      |                          |
| `0x16` | `SUB_I reg, imm8`   | I      |                          |
| `0x17` | `SUB_L [addr], reg` | L      |                          |

#### Multiplication
| Opcode | Mnemonic             | Format | Description              |
|--------|----------------------|--------|--------------------------|
| `0x18` | `MULT reg, reg`      | R      | input1 = input1 * input2 |
| `0x19` | `MUL_R reg, [addr]`  | R      |                          |
| `0x1A` | `MULT_I reg, imm8`   | I      |                          |
| `0x1B` | `MULT_L [addr], reg` | L      |                          |

#### Division
| Opcode | Mnemonic            | Format | Description              |
|--------|---------------------|--------|--------------------------|
| `0x1C` | `DIV reg, reg`      | R      | input1 = input1 / input2 |
| `0x1D` | `DIV_R reg, [addr]` | R      |                          |
| `0x1E` | `DIV_I reg, imm8`   | I      |                          |
| `0x1F` | `DIV_L [addr], reg` | L      |                          |

#### Modulo/Quotient
| Opcode | Mnemonic             | Format | Description                |
|--------|----------------------|--------|----------------------------|
| `0x20` | `QUOT reg, reg`      | R      | input1 = input1 mod input2 |
| `0x21` | `QUOT_R reg, [addr]` | R      |                            |
| `0x22` | `QUOT_I reg, imm8`   | I      |                            |
| `0x23` | `QUOT_L [addr], reg` | L      |                            |

### Bitwise Logic Instructions

#### AND Operations
| Opcode | Mnemonic            | Format | Description                    |
|--------|---------------------|--------|--------------------------------|
| `0x24` | `AND reg`           | R      | input1 = input1 bit and input2 |
| `0x25` | `AND_R reg, [addr]` | R      |                                |
| `0x26` | `AND_I reg, imm8`   | I      |                                |
| `0x27` | `AND_L [addr], reg` | L      |                                |

#### OR Operations
| Opcode | Mnemonic           | Format | Description                   |
|--------|--------------------|--------|-------------------------------|
| `0x28` | `OR reg, reg`      | R      | input1 = input1 bit or input2 |
| `0x29` | `OR_R reg, [addr]` | R      |                               |
| `0x2A` | `OR_I reg, imm8`   | I      |                               |
| `0x2B` | `OR_L [addr], reg` | L      |                               |

#### XOR Operations
| Opcode | Mnemonic            | Format | Description                    |
|--------|---------------------|--------|--------------------------------|
| `0x2C` | `XOR reg, reg`      | R      | input1 = input1 bit xor input2 |
| `0x2D` | `XOR_R reg, [addr]` | R      |                                |
| `0x2E` | `XOR_I reg, imm8`   | I      |                                |
| `0x2F` | `XOR_L [addr], reg` | L      |                                |

### Shift and Rotate Instructions

#### Shift Left
| Opcode | Mnemonic            | Format | Description                       |
|--------|---------------------|--------|-----------------------------------|
| `0x30` | `SHL reg, reg`      | R      | input1 = input1 shift left input2 |
| `0x31` | `SHL_R reg, [addr]` | R      |                                   |
| `0x32` | `SHL_I reg, imm8`   | I      |                                   |
| `0x33` | `SHL_L [addr], reg` | L      |                                   |

#### Shift Right
| Opcode | Mnemonic            | Format | Description                        |
|--------|---------------------|--------|------------------------------------|
| `0x34` | `SHR reg, reg`      | R      | input1 = input1 shift right input2 |
| `0x35` | `SHR_R reg, [addr]` | R      |                                    |
| `0x36` | `SHR_I reg, imm8`   | I      |                                    |
| `0x37` | `SHR_L [addr], reg` | L      |                                    |

#### Rotate Right
| Opcode | Mnemonic           | Format | Description                         |
|--------|--------------------|--------|-------------------------------------|
| `0x38` | `RR reg, reg`      | R      | input1 = input1 rotate right input2 |
| `0x39` | `RR_R reg, [addr]` | R      |                                     |
| `0x3A` | `RR_I reg, imm8`   | I      |                                     |
| `0x3B` | `RR_L [addr], reg` | L      |                                     |

#### Rotate Left
| Opcode | Mnemonic           | Format | Description                        |
|--------|--------------------|--------|------------------------------------|
| `0x3C` | `RL reg, reg`      | R      | input1 = input1 rotate left input2 |
| `0x3D` | `RL_R reg, [addr]` | R      |                                    |
| `0x3E` | `RL_I reg, imm8`   | I      |                                    |
| `0x3F` | `RL_L [addr], reg` | L      |                                    |

#### Arithmetic Right Shift
| Opcode | Mnemonic           | Format | Description                                   |
|--------|--------------------|--------|-----------------------------------------------|
| `0x40` | `AR reg, reg`      | R      | input1 = input1 arithmetic right shift input2 |
| `0x41` | `AR_R reg, [addr]` | R      |                                               |
| `0x42` | `AR_I reg, imm8`   | I      |                                               |
| `0x43` | `AR_L [addr], reg` | L      |                                               |

### NOT Operations
| Opcode | Mnemonic       | Format | Description            |
|--------|----------------|--------|------------------------|
| `0x44` | `NOT reg`      | R      | input1 = negate input2 |
| `0x45` | `NOT_R [addr]` | R      |                        |

### Control Flow Instructions

#### Jump Instructions
| Opcode | Mnemonic         | Format | Description                          |
|--------|------------------|--------|--------------------------------------|
| `0x46` | `JMP imm8, imm8` | J      | Unconditional jump to 16-bit address |
| `0x47` | `JEQ imm8, imm8` | J      | Jump if equal flag set               |
| `0x48` | `JNE imm8, imm8` | J      | Jump if not equal                    |
| `0x49` | `JG imm8, imm8`  | J      | Jump if greater                      |
| `0x4A` | `JLE imm8, imm8` | J      | Jump if less or equal                |
| `0x4B` | `JL imm8, imm8`  | J      | Jump if less                         |
| `0x4C` | `JGE imm8, imm8` | J      | Jump if greater or equal             |
| `0x4D` | `JNZ imm8, imm8` | J      | Jump if zero flag not set            |
| `0x4E` | `JZ imm8, imm8`  | J      | Jump if zero flag set                |
| `0x4F` | `JNC imm8, imm8` | J      | Jump if carry flag not set           |
| `0x50` | `JC imm8, imm8`  | J      | Jump if carry flag set               |

#### Subroutine Instructions
| Opcode | Mnemonic          | Format | Description                             |
|--------|-------------------|--------|-----------------------------------------|
| `0x51` | `CALL imm8, imm8` | J      | Push return address, jump to subroutine |
| `0x52` | `RTRN`            | -      | Pop return address into PC              |

## Register Conventions

| Register | Purpose         | Notes                                      |
|----------|-----------------|--------------------------------------------|
| R0-RF    | General Purpose | Available for computation and data storage |

## Status Flags

- **Greater (G)**: Set when first operand > second operand
- **Equal (E)**: Set when operands are equal
- **Less (L)**: Set when first operand < second operand  
- **Zero (Z)**: Set when result equals zero
- **Carry (C)**: Set when arithmetic operation produces carry

## Operand Format Suffixes

- **(none)**: Register-Register operations
- **_R**: RAM-Register operations
- **_I**: Register-Immediate operations
- **_L**: Register-RAM (Load) operations
- **_RI**: RAM-Immediate operations
- **_RR**: RAM-RAM operations