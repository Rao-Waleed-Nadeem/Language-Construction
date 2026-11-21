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


---

## 3. Syntax-Directed Definition (SDD) and Translation (SDT) Engine

### 3.1 Overview and Safety
The SDD/SDT engine evaluates attribute grammars over parse trees without executing arbitrary code (`eval` or `exec` are strictly prohibited per AP-1 and academic safety guidelines). Rules are parsed using an AST-based safe expression evaluator restricted to arithmetic, string concatenation, comparisons, whitelisted functions, and attribute references.

### 3.2 Attribute Classification
- **Synthesized attributes**: Defined for the production head $A$ in $A \to X_1 \dots X_n$, depending on attributes of children $X_i$ or other attributes of $A$.
- **Inherited attributes**: Defined for a child symbol $X_i$ on the RHS, depending on parent $A$'s attributes or sibling attributes.
- **S-Attributed**: An SDD is S-attributed iff all attributes are synthesized.
- **L-Attributed**: An SDD is L-attributed iff every inherited attribute $X_i.a$ depends only on:
  1. Inherited attributes of the parent $A$.
  2. Attributes of symbols $X_1 \dots X_{i-1}$ strictly to the left of $X_i$ on the RHS.
  Any rule where $X_i.a$ depends on a right sibling $X_j$ ($j > i$) or a synthesized attribute of $A$ violates the L-attributed condition and is reported naming the exact violating rule.

### 3.3 Dependency Graph and Evaluation Order
- Nodes in the dependency graph represent pairs `(tree_node_id, attribute_name)`.
- Directed edges represent data dependencies: $u \to v$ if attribute $v$ requires attribute $u$.
- Evaluation order is computed via topological sort ($O(V + E)$). Cycles indicate circular definitions.

### 3.4 Presets
1. **Desk Calculator**: S-attributed arithmetic expression evaluation.
2. **Type Declarations**: L-attributed type propagation distributing type from $T$ to list $L$.
3. **Boolean Expression Labels**: Inherited and synthesized short-circuit flow labels.
4. **Vela Expression Typing**: Bottom-up type determination and widening.
