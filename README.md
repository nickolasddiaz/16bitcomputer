# 8-bit CISC Processor Specification
*Logic-SIM Evolution Project*

## Architecture Overview

This is a Complex Instruction Set Computer (CISC) with microcoded 8-bit opcodes designed and implementation in Logic-SIM.

## Instruction Formats

### R-type (Register Operations)
```
[ opcode(8) | reg1(4) + reg2(4) | dest(4) ]
```

### I-type (Immediate/Memory Operations)
```
[ opcode(8) | reg(4) | immediate/address(8) ]
```

### J-type (Jumps and Calls)
```
[ opcode(8) | high(8) | low(8) ]
```

## System Specifications

| Component | Specification |
|-----------|---------------|
| **Instruction Memory** | 65,536 instructions |
| **Registers** | 16 registers (0-15) |
| **RAM** | 256 × 8-bit |
| **Video Display** | 256×256 RGB, XTerm256 color model (8-bit) |
| **Status Register** | Flags: Greater, Equal, Less, Zero, Carry|
| **Program Counter** | 16-bit |
| **Call Stack Counter** | 4-bit |
| **Push/Pop Stack Counter** | 8-bit |
| **Variable Type** | 8-bit unsigned integer |

## Instruction Set

### Data Movement Instructions

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| `0x00` | `NOP` | - | No Operation |
| `0x01` | `HALT` | - | Halt Computer |
| `0x02` | `LD rd, [addr]` | I | Load byte from RAM into register |
| `0x03` | `ST rs, [addr]` | I | Store byte from register into RAM |
| `0x04` | `MOV rd, rs` | R | Copy register to register rs moves into rd|
| `0x05` | `LI rd, imm8` | I | Load immediate value to register |
| `0x06` | `VID` | - | Load RGB video  x cord RF, y cord RE, and value XTERM 256 from RD|

### Arithmetic and Logic Instructions

#### Register-Register Operations
| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| `0x07` | `ADD rd, rs, rt` | R | Addition: rd = rs + rt |
| `0x08` | `SUB rd, rs, rt` | R | Subtraction: rd = rs - rt |
| `0x09` | `MULT rd, rs, rt` | R | Multiplication: rd = rs × rt |
| `0x0A` | `DIV rd, rs, rt` | R | Division: rd = rs ÷ rt |
| `0x0B` | `QUOT rd, rs, rt` | R | Quotient: rd = rs mod rt |
| `0x0C` | `AND rd, rs, rt` | R | Bitwise AND: rd = rs & rt |
| `0x0D` | `OR rd, rs, rt` | R | Bitwise OR: rd = rs \| rt |
| `0x0E` | `XOR rd, rs, rt` | R | Bitwise XOR: rd = rs ^ rt |
| `0x0F` | `NOT rd, rs` | R | Bitwise NOT: rd = ~rs |
| `0x10` | `SHL rd, rs, rt` | R | Logical shift left: rd = rs << rt |
| `0x11` | `SHR rd, rs, rt` | R | Logical shift right: rd = rs >> rt |
| `0x12` | `RR rd, rs, rt` | R | Rotate right: rd = ror(rs, rt) |
| `0x13` | `RL rd, rs, rt` | R | Rotate left: rd = rol(rs, rt) |
| `0x14` | `AR rd, rs, rt` | R | Arithmetic right shift: rd = ars(rs, rt) |

#### Immediate Operations
| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| `0x15` | `ADDI rd, rt, imm8` | I | Add immediate: rd = rs + imm8 |
| `0x16` | `SUBI rd, rt, imm8` | I | Subtract immediate: rd = rs - imm8 |
| `0x17` | `MULTI rd, rt, imm8` | I | Multiply immediate: rd = rs × imm8 |
| `0x18` | `DIVI rd, rt, imm8` | I | Divide immediate: rd = rs ÷ imm8 |
| `0x19` | `QUOTI rd, rt, imm8` | I | Quotient immediate: rd = rs mod imm8 |
| `0x1A` | `ANDI rd, rt, imm8` | I | AND immediate: rd = rs & imm8 |
| `0x1B` | `ORI rd, rt, imm8` | I | OR immediate: rd = rs \| imm8 |
| `0x1C` | `XORI rd, rt, imm8` | I | XOR immediate: rd = rs ^ imm8 |
| `0x1D` | `NOTI rd, imm8` | I | NOT immediate: rd = ~imm8 |
| `0x1E` | `SHLI rd, rt, imm8` | I | Shift left immediate: rd = rs << imm8 |
| `0x1F` | `SHRI rd, rt, imm8` | I | Shift right immediate: rd = rs >> imm8 |
| `0x20` | `RRI rd, rt, imm8` | I | Rotate right immediate: rd = ror(rt, imm8) |
| `0x21` | `RLI rd, rt, imm8` | I | Rotate left immediate: rd = rol(rt, imm8) |
| `0x22` | `ARI rd, rt, imm8` | I | Arithmetic right immediate: rd = ars(rt, imm8) |
| `0x23` | `INC rd, rt` | - | Increment a register: rd++ |
| `0x24` | `DEC rd, rt` | - | Decrement a register: rd-- |

### Control Flow Instructions

| Opcode | Mnemonic | Format | Description |
|--------|----------|--------|-------------|
| `0x25` | `JMP addr` | J | Unconditional jump to 16-bit address |
| `0x26` | `JEQ addr` | J | Jump if equal flag set |
| `0x27` | `JNE addr` | J | Jump if not equal |
| `0x28` | `JG addr` | J | Jump if greater |
| `0x29` | `JL addr` | J | Jump if less |
| `0x2A` | `JGE addr` | J | Jump if greater or equal |
| `0x2B` | `JLE addr` | J | Jump if less or equal |
| `0x2C` | `JNZ addr` | J | Jump if zero flag not set |
| `0x2D` | `JZ addr` | J | Jump if zero flag set |
| `0x2E` | `JNC addr` | J | Jump if carry flag not set |
| `0x2F` | `JC addr` | J | Jump if carry flag set |
| `0x30` | `CALL addr` | J | Push return address, jump to subroutine |
| `0x31` | `RTRN` | - | Pop return address into PC |
| `0x32` | `PUSH rd` | - | Push the stack |
| `0x33` | `POP rd` | - | Pop the stack |
| `0x34` | `CMP rs, rt` | R | Compare registers (sets flags) |
| `0x35` | `CMPI rs, imm8` | I | Compare immediate (sets flags) |

## Register Conventions

| Register | Purpose | Notes |
|----------|---------|-------|
| R0-RC | General Purpose | Available for computation and data storage |
| RD | Special | Used by VID instruction for XTerm256 color model (8-bit) |
| RE | Special | Used by VID instruction for video y axis |
| RF | Special | Used by VID instruction for video x axis |

## Status Flags

- **Greater (G)**: Set when first operand > second operand
- **Equal (E)**: Set when operands are equal
- **Less (L)**: Set when first operand < second operand  
- **Zero (Z)**: Set when result equals zero
- **Carry (C)**: Set when arithmetic operation produces carry