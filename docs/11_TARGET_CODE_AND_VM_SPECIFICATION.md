# 11 — Target Code Generation and Virtual Machine Specification (Phase 7)

> Status: written by the implementation agent (ALLOW_SPEC_GAP_FILLING = true)
> Authority: follows `docs/00_PROJECT_MASTER_SPEC.md` (§4.8, §5.10, §5.11), `docs/01_LANGUAGE_SPECIFICATION.md` §11, and `docs/03_UI_UX_SPECIFICATION.md` §5.10, §5.11.

---

## 1. Overview and Architecture

Phase 7 lowers optimized Three-Address Code (TAC) into an executable target register-machine assembly language and simulates it on an architectural Virtual Machine (VM).

The subsystem consists of:
1. **Instruction Set Architecture (ISA) & Cost Model** (`vela.codegen.isa`, `cost`): Register-machine ISA with 8 general-purpose registers ($R0$–$R7$), stack pointer ($SP$), frame pointer ($FP$), program counter ($PC$), condition flags, and standardized instruction costs.
2. **Instruction Selection** (`vela.codegen.selector`): Pattern-matching selection rules mapping TAC quadruples to target instructions with provenance (`tac_index`, selection rule).
3. **Register Allocation & Descriptors** (`vela.codegen.regalloc`): Dragon Book Algorithm 8.7 `getReg` implementation with register and address descriptors, next-use distance tracking, and spilling to stack slots `[FP - offset]`.
4. **DAG-Based Code Generation** (`vela.codegen.dag_codegen`): Ershov / topological ordering over Expression DAGs to minimize register pressure and spill operations.
5. **Machine-Dependent Peephole Optimization** (`vela.codegen.peephole`): Sliding-window peephole optimizer removing redundant loads/stores, jumps to next instructions, and dead instructions.
6. **Virtual Machine** (`vela.vm.machine`, `memory`, `cpu`): Complete register-machine execution engine with segmented memory (code, globals, stack, heap), instruction budgets, reversible step snapshots (cap 5,000), and identical runtime semantics to the TAC interpreter oracle.
7. **End-to-End Pipeline & CLI** (`vela.codegen.pipeline`, `vela.cli`): Unified compilation and execution driver.

---

## 2. Target Instruction Set Architecture (ISA)

### 2.1 Registers and State
- **General-Purpose Registers**: `R0`, `R1`, `R2`, `R3`, `R4`, `R5`, `R6`, `R7` (32-bit signed integers or floating-point values).
- **Special Registers**:
  - `SP`: Stack Pointer (points to top of stack).
  - `FP`: Frame Pointer (points to current function call frame).
  - `PC`: Program Counter (index of next instruction to execute).
- **Condition Flags**:
  - `ZF`: Zero Flag (set if comparison yielded equality).
  - `SF`: Sign/Less-Than Flag (set if comparison yielded less-than).

### 2.2 Addressing Modes
1. **Register**: `R_k` (value in register $k$).
2. **Immediate**: `#imm` (literal integer, float, string, or boolean constant).
3. **Memory Direct (Global)**: `[symbol]` (direct address of global variable in data segment).
4. **Base Displacement (Stack / Heap)**: `[FP + offset]`, `[FP - offset]`, `[R_base + R_offset]`.

### 2.3 Opcode Table and Cost Model

| Opcode | Operands | Description | Base Cost |
|---|---|---|---|
| `MOV` | `dst, src` | Move register to register or immediate to register | 1 |
| `LOAD` | `dst, [addr]` | Load word from memory into register | 2 |
| `STORE` | `[addr], src` | Store word from register into memory | 2 |
| `ADD` | `dst, src1, src2` | Signed addition: `dst = src1 + src2` (32-bit wrap) | 1 |
| `SUB` | `dst, src1, src2` | Signed subtraction: `dst = src1 - src2` (32-bit wrap) | 1 |
| `MUL` | `dst, src1, src2` | Signed multiplication: `dst = src1 * src2` (32-bit wrap) | 3 |
| `DIV` | `dst, src1, src2` | Integer division truncating toward zero | 5 |
| `MOD` | `dst, src1, src2` | Modulo with dividend sign | 5 |
| `NEG` | `dst, src` | Arithmetic negation | 1 |
| `NOT` | `dst, src` | Boolean negation | 1 |
| `CMP` | `src1, src2` | Compare operands and set `ZF`, `SF` flags | 1 |
| `JMP` | `label` | Unconditional jump | 1 |
| `JE` | `label` | Jump if equal (`ZF == 1`) | 1 |
| `JNE` | `label` | Jump if not equal (`ZF == 0`) | 1 |
| `JL` | `label` | Jump if less than (`SF == 1` and `ZF == 0`) | 1 |
| `JLE` | `label` | Jump if less than or equal (`SF == 1` or `ZF == 1`) | 1 |
| `JG` | `label` | Jump if greater than (`SF == 0` and `ZF == 0`) | 1 |
| `JGE` | `label` | Jump if greater than or equal (`SF == 0`) | 1 |
| `CALL` | `func_label` | Push return address, jump to function | 2 |
| `RET` | | Pop return address, return to caller | 2 |
| `PUSH` | `src` | Push register or constant onto stack (`SP -= 1`) | 1 |
| `POP` | `dst` | Pop word from stack into register (`SP += 1`) | 1 |
| `SYS_SHOW` | `src` | Print value to stdout | 1 |
| `SYS_SHOW_NL` | | Print newline to stdout | 1 |
| `SYS_READ` | `dst, type` | Read formatted value from stdin | 1 |
| `SYS_ALLOC` | `dst, size, fill` | Allocate array buffer on heap | 3 |
| `HLT` | | Halt machine execution | 0 |

---

## 3. Register Allocation (Algorithm 8.7)

### 3.1 Descriptors
- **Register Descriptor ($R$)**: For each register $R_i$, tracks the set of variables currently stored in $R_i$.
- **Address Descriptor ($A$)**: For each variable $x$, tracks the locations where the current value of $x$ can be found (registers, stack slot, memory).

### 3.2 Spilling Strategy (`getReg`)
When selecting a register for computation $x = y \text{ op } z$:
1. If $y$ is already in a register $R_y$ and has no subsequent uses, reuse $R_y$ for $x$.
2. Otherwise, pick any completely empty register.
3. If all 8 registers are occupied, find the register holding a value whose next use is farthest in the future (or not used again).
4. If the spilled variable's only copy is in that register, emit `STORE [FP - offset], R_spill` and update its address descriptor.

---

## 4. Virtual Machine Architecture

### 4.1 Memory Model
- **Code Segment**: Read-only sequence of target `TargetInstruction` objects indexed by integer $PC$.
- **Data Segment**: Global variables indexed by symbol name.
- **Stack Segment**: Call frames containing local variables, saved return addresses, and saved frame pointers.
- **Heap Segment**: Dynamically allocated arrays created by `ALLOC_ARRAY`.

### 4.2 Step Reversibility and Diagnostics
- The VM records a historical trace of state snapshots: `VMSnapshot(step, pc, registers, stack_top, flags, last_output)`.
- Snapshot capacity is bounded at `MAX_VM_SNAPSHOTS = 5000` to prevent memory bloat on long executions.
- Stepping backward in the UI simply rolls back the VM state to the previous snapshot.
