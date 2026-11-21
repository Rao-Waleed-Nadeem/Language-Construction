# 07 — Semantic Analysis Specification (Phase 4)

> Status: written by the implementation agent, needs group review
> Authority: follows `docs/00_PROJECT_MASTER_SPEC.md` and `docs/01_LANGUAGE_SPECIFICATION.md` §4–§9, §12, §16.3.

---

## 1. Overview and Requirements
The semantic analysis phase verifies the static semantics of a Vela Abstract Syntax Tree (AST). It performs:
1. **Type Representation and Inference** (`semantic/types.py`): Models primitive types, array types, void return, and error types.
2. **Symbol Table and Scope Management** (`semantic/symbols.py`): Models hierarchical lexical scoping, tracks symbol definitions, shadowing, offsets, uses, and emits an event log for the UI.
3. **Control-Flow Return Analysis** (`semantic/returns.py`): Performs structural all-paths-return analysis to detect `VL-SEM-010`.
4. **Type Checking and Validation** (`semantic/checker.py`): Validates variable usage, operator typing, assignment compatibility, array boundaries, implicit `int -> float` widening (inserting `ImplicitCast` nodes), and emits diagnostics `VL-SEM-001` through `VL-SEM-023` and `VL-WRN-001`.

---

## 2. Type System (`semantic/types.py`)

### 2.1 Types
- Primitive scalar types: `int`, `float`, `char`, `string`, `bool`.
- Non-value types:
  - `void`: only for functions returning no value. Cannot be used as variable type or expression value (`VL-SEM-023`).
  - `error`: poison/sentinel type to prevent error cascading after a primary type error.
- Array types: `T[N]` where `T` is a scalar base type and `N` is an integer $1 \le N \le 10\,000$ (or unconstrained `T[]` for function parameters).

### 2.2 Compatibility & Conversions
- **Implicit Widening:** Only `int -> float`. Allowed in:
  - Binary arithmetic/relational operators mixing `int` and `float`.
  - Assignment / initialization (`let f: float = 42;`).
  - Function argument passing (`func f(x: float); f(1);`).
  - Return statements (`func f(): float { return 1; }`).
  - Array initializers (`let a: float[2] = {1, 2.5};`).
- **Explicit Casts (`e as T`):**
  - Allowed:
    - `int as float`, `int as char` (checked at runtime: 0–255), `int as string`
    - `float as int` (truncated towards 0), `float as string`
    - `char as int`, `char as string`
    - `bool as int` (0 or 1), `bool as string` ("true" or "false")
  - All other combinations are disallowed (`VL-SEM-019`).

---

## 3. Symbol Table and Scopes (`semantic/symbols.py`)

### 3.1 Scope Kinds
1. `GLOBAL`: Top-level file scope. Contains global variables and all declared functions. Functions may be called before declaration.
2. `FUNCTION`: Encloses function parameters and the outermost function body block.
3. `BLOCK`: Enclosed in `{ ... }` (loops, if branches, bare blocks).
4. `FOR_HEADER`: Scopes the loop variable declared in `for (let i: int = 0; ...)`.
5. `CASE`: Scope of each `case` or `default` clause.

### 3.2 Symbol Representation
```python
@dataclass
class Symbol:
    name: str
    symbol_type: VelaType
    kind: str # "var", "param", "func"
    scope_id: int
    decl_span: Span
    param_types: list[VelaType] = field(default_factory=list) # For functions
    return_type: VelaType | None = None # For functions
    is_array: bool = False
    array_size: int | None = None
    offset: int = 0 # Stack offset or global data offset
    uses: list[Span] = field(default_factory=list)
```

### 3.3 Scope Tree & Event Logging
For the Vela Studio Semantic Explorer, every scope operation emits a `SymbolEvent`:
- `enter_scope(scope_id, kind, name)`
- `declare_symbol(symbol_name, symbol_type, kind)`
- `lookup_symbol(symbol_name, found, scope_id)`
- `shadow_symbol(symbol_name, outer_scope_id, inner_scope_id)`
- `exit_scope(scope_id)`

---

## 4. Return-Path Analysis (`semantic/returns.py`)

Every function with a return type must return a value on every possible control-flow execution path (`VL-SEM-010`).
Structural rules:
- `Block`: returns iff its last statement returns.
- `IfStmt`: returns iff `else_stmt` exists and both `then_block` and `else_stmt` return.
- `SwitchStmt`: returns iff `default_case` exists, every `CaseClause` returns, and no reachable `break` statement exists inside the clauses.
- Loops (`while`, `for`, `do-while`): **never** guarantee return (they might iterate 0 times or exit via `break`).
- `ReturnStmt`: unconditionally returns.

---

## 5. Diagnostic Catalog
- `VL-SEM-001`: undeclared variable
- `VL-SEM-002`: redeclaration in the same scope
- `VL-SEM-003`: type mismatch in initialization or assignment
- `VL-SEM-004`: invalid operand types for operator
- `VL-SEM-005`: condition is not `bool`
- `VL-SEM-006`: call to undeclared function / callee not a function
- `VL-SEM-007`: wrong number of arguments
- `VL-SEM-008`: argument type mismatch
- `VL-SEM-009`: return value/type mismatch
- `VL-SEM-010`: missing return on some path
- `VL-SEM-011`: `break` / `continue` outside a valid construct
- `VL-SEM-012`: duplicate case label
- `VL-SEM-013`: switch expression not `int`/`char` or label type mismatch
- `VL-SEM-014`: array index not `int`
- `VL-SEM-015`: indexing a non-array
- `VL-SEM-016`: too many array initializers
- `VL-SEM-017`: invalid array size (must be 1..10 000)
- `VL-SEM-018`: missing or ill-formed `main`
- `VL-SEM-019`: invalid `as` conversion
- `VL-SEM-020`: global initializer not a literal
- `VL-SEM-021`: whole array used as a value
- `VL-SEM-022`: constant index out of range
- `VL-SEM-023`: void function used as a value
- `VL-WRN-001`: unused local variable
