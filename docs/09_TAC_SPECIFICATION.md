# 09 — Three-Address Code (TAC) Specification (Phase 5 Intermediate Representation)

> Status: written by the implementation agent (ALLOW_SPEC_GAP_FILLING = true)
> Authority: follows `docs/00_PROJECT_MASTER_SPEC.md` (§5.8 TAC) and `docs/01_LANGUAGE_SPECIFICATION.md` §6–§11.

---

## 1. Overview and Architecture
Three-Address Code (TAC) is the compiler's linear, machine-independent intermediate representation (Phase 5).
Each TAC instruction is a quadruple `(opcode, arg1, arg2, result)` containing at most one operator and at most three addresses.

Every TAC instruction retains provenance:
- `src_span: Span`: Source code range in the input file (AP-7).
- `ast_id: int`: ID of the AST node from which the instruction was lowered.
- `rule_id: str`: The formal IR lowering rule (e.g., `TAC-ARITH`, `TAC-IF-THEN`, `TAC-SHORT-CIRCUIT-AND`).

---

## 2. Operands
Operands in TAC are strongly classified:
1. **Constant**: Literal values (`42`, `3.14`, `'c'`, `"str"`, `true`, `false`).
2. **Variable**: Named identifiers in scope (`x`, `a`, `total`).
3. **Temporary**: Compiler-generated temporaries (`t1`, `t2`, ...), unique within the compilation unit.
4. **Label**: Symbolic branch targets (`L1`, `L_main_entry`, `L_exit_2`, ...).

---

## 3. Instruction Set Architecture (Quadruples)

| Opcode | Quadruple Format | Text Representation | Meaning |
|---|---|---|---|
| `ASSIGN` | `ASSIGN arg1 None result` | `result = arg1` | Copy value of `arg1` to `result` |
| `ADD` | `ADD arg1 arg2 result` | `result = arg1 + arg2` | Arithmetic addition |
| `SUB` | `SUB arg1 arg2 result` | `result = arg1 - arg2` | Arithmetic subtraction |
| `MUL` | `MUL arg1 arg2 result` | `result = arg1 * arg2` | Arithmetic multiplication |
| `DIV` | `DIV arg1 arg2 result` | `result = arg1 / arg2` | Truncating int / float division |
| `MOD` | `MOD arg1 arg2 result` | `result = arg1 % arg2` | Modulo (sign of dividend) |
| `NEG` | `NEG arg1 None result` | `result = -arg1` | Unary negation |
| `NOT` | `NOT arg1 None result` | `result = !arg1` | Logical negation |
| `LT` | `LT arg1 arg2 result` | `result = arg1 < arg2` | Less than (yields boolean) |
| `LE` | `LE arg1 arg2 result` | `result = arg1 <= arg2` | Less than or equal |
| `GT` | `GT arg1 arg2 result` | `result = arg1 > arg2` | Greater than |
| `GE` | `GE arg1 arg2 result` | `result = arg1 >= arg2` | Greater than or equal |
| `EQ` | `EQ arg1 arg2 result` | `result = arg1 == arg2` | Equal |
| `NE` | `NE arg1 arg2 result` | `result = arg1 != arg2` | Not equal |
| `LABEL` | `LABEL None None result` | `label L` | Branch target definition |
| `JUMP` | `JUMP None None result` | `goto L` | Unconditional jump |
| `JUMP_IF` | `JUMP_IF arg1 None result` | `if arg1 goto L` | Jump if `arg1` is truthy |
| `JUMP_IF_FALSE` | `JUMP_IF_FALSE arg1 None result` | `ifFalse arg1 goto L` | Jump if `arg1` is falsy |
| `FUNC_BEGIN` | `FUNC_BEGIN None None result` | `func f:` | Function entry point |
| `FUNC_END` | `FUNC_END None None result` | `endfunc f` | Function exit marker |
| `PARAM` | `PARAM arg1 None None` | `param arg1` | Push argument for call |
| `CALL` | `CALL arg1 arg2 result` | `result = call f, n` | Call function `arg1` with `n` args |
| `RETURN` | `RETURN arg1 None None` | `return arg1` | Return value from function |
| `ARRAY_GET` | `ARRAY_GET arg1 arg2 result` | `result = arg1[arg2]` | Read from array `arg1` at index `arg2` |
| `ARRAY_SET` | `ARRAY_SET result arg2 arg1` | `arg1[arg2] = result` | Write `result` to array `arg1` at `arg2` |
| `CAST` | `CAST arg1 to_type result` | `result = cast(arg1, T)` | Type conversion (widening or explicit) |
| `SHOW` | `SHOW arg1 None None` | `show arg1` | Print operand value |
| `SHOW_NL` | `SHOW_NL None None None` | `show_nl` | Print newline terminator |
| `READ` | `READ None None result` | `read result` | Read token from stdin into `result` |

---

## 4. Translation Rules

### 4.1 Short-Circuit Booleans
As required by the assignment and Master Spec:
**No plain `and` or `or` TAC operator exists.**
- `a and b`:
  1. Evaluate `a` into `t1`.
  2. `ifFalse t1 goto L_false`
  3. Evaluate `b` into `t2`.
  4. `t_res = t2`
  5. `goto L_end`
  6. `label L_false`
  7. `t_res = false`
  8. `label L_end`
- `a or b`:
  1. Evaluate `a` into `t1`.
  2. `if t1 goto L_true`
  3. Evaluate `b` into `t2`.
  4. `t_res = t2`
  5. `goto L_end`
  6. `label L_true`
  7. `t_res = true`
  8. `label L_end`

### 4.2 Control-Flow Constructs
- **If-Then-Else**: Evaluates condition; `ifFalse cond goto L_else`; then body; `goto L_end`; `label L_else`; else body; `label L_end`.
- **Switch-Case**:
  Evaluates switch expr to temporary `t_sw`.
  Generates equality tests for each case label:
  `t_cmp = t_sw == case_val`
  `if t_cmp goto L_case_k`
  After all comparisons, `goto L_default` (or `L_exit`).
  Each case body ends with `goto L_exit` (no fall-through).
- **While Loop**:
  `label L_cond`
  Evaluate condition `t_c`
  `ifFalse t_c goto L_exit`
  Body (break targets `L_exit`, continue targets `L_cond`)
  `goto L_cond`
  `label L_exit`
- **Do-While Loop**:
  `label L_start`
  Body (break targets `L_exit`, continue targets `L_cond`)
  `label L_cond`
  Evaluate condition `t_c`
  `if t_c goto L_start`
  `label L_exit`
- **For Loop**:
  Execute init
  `label L_cond`
  If condition present: evaluate `t_c`; `ifFalse t_c goto L_exit`
  Body (break targets `L_exit`, continue targets `L_update`)
  `label L_update`
  Execute update statement
  `goto L_cond`
  `label L_exit`

### 4.3 Program Startup
Vela requires:
1. Global initializations execute in textual order.
2. `main()` is called.
The generator emits a `__init_globals` prologue or inlines global assignments before jumping to `main`.
