# 08 — AST, DAG, SDD, and SDT Specification (Phase 4 Theory & Production)

> Status: written by the implementation agent, needs group review
> Authority: follows `docs/00_PROJECT_MASTER_SPEC.md` and `docs/01_LANGUAGE_SPECIFICATION.md` §6–§9.

---

## 1. Abstract Syntax Tree (AST) Hierarchy
The AST discards concrete syntax details (delimiters, parentheses) and captures semantic structure. Every node carries:
- `id: int`: unique integer identifier within the compilation unit.
- `span: Span`: source code coordinate range (AP-7).

### 1.1 Node Classes
- **Program**: `items: list[TopItem]` (VarDecl or FuncDecl).
- **VarDecl**: `name: str`, `type_name: str`, `array_size: int | None`, `init: Expr | None`, `array_inits: list[Expr]`.
- **FuncDecl**: `name: str`, `params: list[Param]`, `return_type: str | None`, `body: Block`.
- **Param**: `name: str`, `type_name: str`, `is_array: bool`.
- **Block**: `statements: list[Stmt]`.
- **Statements**:
  - `AssignStmt`: `target: VarRefExpr | ArrayAccessExpr`, `op: str` (`=, +=, -=, *=, /=, %=`), `value: Expr | None` (None for ++/--).
  - `CallStmt`: `expr: CallExpr`.
  - `IfStmt`: `condition: Expr`, `then_block: Block`, `else_stmt: Block | IfStmt | None`.
  - `SwitchStmt`: `expr: Expr`, `cases: list[CaseClause]`, `default_case: Block | None`.
  - `CaseClause`: `labels: list[int | str]`, `body: list[Stmt]`.
  - `WhileStmt`: `condition: Expr`, `body: Block`.
  - `DoWhileStmt`: `body: Block`, `condition: Expr`.
  - `ForStmt`: `init: VarDecl | AssignStmt | None`, `condition: Expr | None`, `update: AssignStmt | None`, `body: Block`.
  - `ReturnStmt`: `value: Expr | None`.
  - `BreakStmt`, `ContinueStmt`.
  - `ShowStmt`: `expressions: list[Expr]`.
  - `ReadStmt`: `target: VarRefExpr | ArrayAccessExpr`.
- **Expressions**:
  - `BinaryExpr`: `left: Expr`, `op: str`, `right: Expr`.
  - `UnaryExpr`: `op: str`, `operand: Expr`.
  - `CastExpr`: `expr: Expr`, `target_type: str`.
  - `ImplicitCast`: `expr: Expr`, `from_type: str`, `to_type: str`.
  - `LiteralExpr`: `literal_type: str`, `value: int | float | str | bool`.
  - `VarRefExpr`: `name: str`.
  - `ArrayAccessExpr`: `name: str`, `index: Expr`.
  - `CallExpr`: `callee: str`, `args: list[Expr]`.

---

## 2. AST Serialization & Pretty-Printing
- S-expression format: e.g. `(Program (FuncDecl main () (Block ...)))`.
- JSON-ready dictionary representation for frontend visualization.
