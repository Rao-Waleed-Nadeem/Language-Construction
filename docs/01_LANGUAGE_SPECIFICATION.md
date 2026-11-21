# 01 — Vela Language Specification

> **Status:** Batch 1 draft for group review. Authoritative for syntax, types and semantics once approved.
> **Name:** *Vela* (compiler `velac`, IDE *Vela Studio*, extension `.vela`). The name is a placeholder the group may change; if renamed, change it everywhere in one pass (docs, UI title, file extension, `backend/vela/` package name).
> **Related:** grammar files `docs/grammar/vela.bnf` (authoritative) and `vela_ll1.bnf` (derived); examples `examples/*.vela`; lexer details in `04_LEXER_SPECIFICATION.md` (Batch 2); semantic rules in `07_SEMANTIC_ANALYSIS_SPECIFICATION.md` (Batch 2).

---

## 1. Identity and design principles

Vela is a small statically typed, imperative, block-structured language with a C-like control-flow vocabulary but its own declaration, I/O and operator style.

| # | Principle | Consequence |
|---|---|---|
| P1 | Explicit types | Every variable and parameter is declared `name: type`. No type inference. |
| P2 | Braces are mandatory | `if`, `else`, `for`, `while`, `do` bodies are always `{ ... }`. Removes the dangling-else ambiguity from the language itself and keeps the grammar LL(1). |
| P3 | Words for logic | `and`, `or`, `not` (the assignment says AND/OR/NOT). |
| P4 | No silent narrowing | The only implicit conversion is `int → float`. Everything else needs `as`. |
| P5 | Assignment is a statement | `=`, `+=`, `++` … cannot appear inside expressions. Keeps expression grammar and TAC simple. |
| P6 | No fall-through | A `case` body ends the `switch` when it finishes. Optional `break` exits early. |
| P7 | Deterministic runtime | 32-bit wrapping integers, defined division rules, no undefined behaviour. All errors are reported with codes. |

Look and feel:

```vela
let total: int = 0;

func main() {
    for (let i: int = 1; i <= 3; i++) {
        total += i * i;
    }
    show "sum of squares = ", total;
}
```

---

## 2. Lexical structure

### 2.1 Source text
- UTF-8 text file. `\r\n` and `\r` are normalized to `\n` before scanning.
- Positions are 1-based `line:column`; a column counts one Unicode code point (a tab counts as 1).
- Whitespace (space, tab, newline) separates tokens and is otherwise ignored.
- Limits: source ≤ 100 000 characters; identifier ≤ 64 characters.

### 2.2 Comments
- Line comment: `//` to end of line.
- Block comment: `/* ... */`, **not nested**. An unclosed block comment is lexical error `VL-LEX-007`.

### 2.3 Identifiers
`[A-Za-z_][A-Za-z0-9_]*`, ASCII only, case-sensitive. Reserved words (2.4) are not identifiers. Convention (not enforced): `snake_case` for variables and functions. Longer than 64 characters → `VL-LEX-010`.

### 2.4 Keywords (26, all reserved, all lowercase)

| Group | Keywords |
|---|---|
| Declarations | `let` `func` |
| Types | `int` `float` `char` `string` `bool` |
| Literals | `true` `false` |
| Selection | `if` `else` `switch` `case` `default` |
| Loops / jumps | `for` `while` `do` `break` `continue` `return` |
| I/O | `show` `read` |
| Operators | `and` `or` `not` `as` |

There are no other reserved words; `void` does not exist (a function without a return type is void).

### 2.5 Literals

| Kind | Regular expression | Notes |
|---|---|---|
| Integer | `[0-9]+` | Value 0 … 2 147 483 647. Larger → `VL-LEX-009`. Negative numbers are unary minus applied to a literal. No leading `+`, no hex, no underscores. |
| Float | `[0-9]+\.[0-9]+` | Digits required on both sides of the dot. No exponent form. `12.` or `.5` are lexical errors (`VL-LEX-008` / `VL-LEX-001`). |
| Char | `'([^'\\\n]\|\\[ntr0\\'"])'` | Exactly one character with code ≤ 255, or an escape. `''` → `VL-LEX-004`; two characters → `VL-LEX-005`; unterminated → `VL-LEX-003`; code > 255 → `VL-LEX-011`. |
| String | `"([^"\\\n]\|\\[ntr0\\'"])*"` | May contain any Unicode except raw newline. Unterminated → `VL-LEX-002`. Bad escape → `VL-LEX-006`. |
| Boolean | `true` \| `false` | Keywords. |

Escapes: `\n` newline, `\t` tab, `\r` carriage return, `\0` code 0, `\\`, `\'`, `\"`.
A number immediately followed by a letter or `_` (e.g. `12abc`) is `VL-LEX-008` (malformed number), reported once for the whole run of characters.

### 2.6 Operators and delimiters

| Class | Lexemes |
|---|---|
| Arithmetic | `+` `-` `*` `/` `%` |
| Relational | `<` `<=` `>` `>=` `==` `!=` |
| Logical | `and` `or` `not` (keywords) |
| Assignment | `=` `+=` `-=` `*=` `/=` `%=` |
| Increment / decrement | `++` `--` (statement-level only) |
| Conversion | `as` (keyword) |
| Delimiters | `(` `)` `{` `}` `[` `]` `;` `,` `:` |

The scanner always takes the **longest match** (`<=` before `<`, `++` before `+`, `==` before `=`). Any other character is `VL-LEX-001`.

### 2.7 Token model (summary; full structure in `04_LEXER_SPECIFICATION.md` and `12_API_AND_DATA_CONTRACTS.md`)

Every token carries: `category`, `symbol`, `lexeme`, `value`, `span`.
`symbol` is the **grammar terminal** the parser sees: keywords/operators/delimiters use their lexeme (`let`, `<=`, `;`), literals use `INT_LIT`, `FLOAT_LIT`, `CHAR_LIT`, `STRING_LIT`, identifiers use `ID`, end of input uses `$`.
`category` ∈ `KEYWORD, IDENTIFIER, INT_LITERAL, FLOAT_LITERAL, CHAR_LITERAL, STRING_LITERAL, OPERATOR, DELIMITER, EOF, ERROR`.

---

## 3. Program structure

A program is a sequence of top-level items in any order: global variable declarations and function declarations. Execution begins at the function `main`.

```
Program  →  { VarDecl | FuncDecl }
```

- Exactly one `func main()` with no parameters and no return type is required (`VL-SEM-018` otherwise).
- Global variables are initialized, in textual order, before `main` starts.
- No header, no imports, no modules.

---

## 4. Types

| Type | Values | Size / representation | Default value |
|---|---|---|---|
| `int` | whole numbers | 32-bit two's complement, **wrapping** on overflow | `0` |
| `float` | real numbers | IEEE-754 double | `0.0` |
| `char` | one character | 8-bit code 0–255 | `'\0'` |
| `string` | text | immutable sequence of Unicode characters | `""` |
| `bool` | `true`, `false` | — | `false` |
| `T[N]` | array of `N` elements of base type `T` | fixed size, 0-indexed | every element default |

Rules:
- Every variable has a default value, so reading an uninitialized variable is never an error and never undefined.
- Array types exist only on variables and parameters. Arrays are **not** values: they cannot be assigned, compared, printed or returned. They may be passed to functions by name (by reference).
- One dimension only; element type is any of the five base types; size is an integer literal from 1 to 10 000.
- **Type equivalence:** scalar types are equal iff they are the same base type. An array argument matches an array parameter iff the element types are equal (size is ignored; a parameter is written `name: T[]`).
- There is no `void` type. A function with no `: T` returns nothing and cannot be used in an expression.

---

## 5. Declarations, initialization, scope

### 5.1 Syntax

```vela
let x: int;                        // default-initialized
let y: float = 2.5;                // initialized
let c: char = 'z';
let s: string = "text";
let ok: bool = x > 0;
let a: int[5];                     // five zeros
let b: int[5] = {1, 2, 3};         // 1 2 3 0 0   (fewer initializers → rest default)
let n: string[2] = {"a", "b"};
```

- An initializer must be assignable to the declared type (Section 6.4). An array may have at most `N` initializers (`VL-SEM-016`).
- Array declarations require the size; `let a: int[] = ...` is a syntax error.
- **Global** initializers must be a literal, optionally preceded by unary `-` (`VL-SEM-020` otherwise). Arrays globally follow the same rule element by element.

### 5.2 Scopes

| Scope | Created by | Contains |
|---|---|---|
| Global | the file | global variables and all functions |
| Function | `func` | parameters **and** the outermost body block (same scope: a local cannot reuse a parameter's name) |
| Block | `{ ... }` including bodies of `if/else/while/do/for` and bare blocks | locals declared inside |
| For-header | `for (...)` | the loop variable declared in the init clause; visible in condition, update and body |
| Case | each `case` / `default` clause body | locals declared in that clause |

Rules:
- A name may be declared once per scope (`VL-SEM-002`). An inner scope may **shadow** an outer name.
- Variables must be declared textually **before** use (`VL-SEM-001`). Functions may be called before their declaration (including mutual recursion).
- Functions and global variables share one global namespace.
- Name lookup walks from the innermost scope outward.

---

## 6. Expressions

### 6.1 Precedence and associativity (highest first)

| Level | Operator(s) | Kind | Associativity | Grammar nonterminal |
|---|---|---|---|---|
| 1 | `f(args)`  `a[i]`  `( e )` | postfix / grouping | left | `Primary` |
| 2 | `e as T` | conversion | left | `CastExpr` |
| 3 | `-e` | unary prefix | right | `UnaryExpr` |
| 4 | `*` `/` `%` | multiplicative | left | `MulExpr` |
| 5 | `+` `-` | additive | left | `AddExpr` |
| 6 | `<` `<=` `>` `>=` | relational | left | `RelExpr` |
| 7 | `==` `!=` | equality | left | `EqExpr` |
| 8 | `not e` | logical not (prefix) | right | `NotExpr` |
| 9 | `and` | logical and | left | `AndExpr` |
| 10 | `or` | logical or | left | `OrExpr` |

Notes: `not` binds **looser** than `==`, so `not a == b` means `not (a == b)`. Chained comparisons like `a < b < c` parse as `(a < b) < c` and are rejected by the type checker (`bool < int`).

### 6.2 Operator typing and overloading

`+` is overloaded; the checker selects the operation from the operand types (this is the language's operator-overloading / polymorphism demonstration).

| Operator | Operand types → result |
|---|---|
| `+` | `int,int → int` · `float,float → float` · mixed `int/float → float` (int widened) · `string,string → string` (concatenation) |
| `-` `*` `/` | `int,int → int` · any `float` involved → `float` |
| `%` | `int,int → int` only |
| unary `-` | `int → int` · `float → float` |
| `<` `<=` `>` `>=` | `int/float` (mixed → float comparison) · `char,char` → `bool`. Strings and bools are not ordered. |
| `==` `!=` | both operands the same type after widening: `int/float` mixed, `char`, `string` (value comparison), `bool` → `bool`. Arrays not comparable. |
| `and` `or` `not` | `bool` operands → `bool` |
| `as T` | see 6.3 |

Anything else is `VL-SEM-004` (invalid operand types).

### 6.3 Conversions

**Implicit:** only `int → float`, applied in: mixed arithmetic/comparison, initialization, assignment, argument passing, `return`, array initializers. The checker inserts an explicit *ImplicitCast* node in the AST, which becomes an `i2f` instruction in TAC.

**Explicit (`as`):**

| from \ to | `int` | `float` | `char` | `string` | `bool` |
|---|---|---|---|---|---|
| `int` | — | ✔ | ✔ runtime error if outside 0–255 (`VL-RUN-005`) | ✔ decimal text | ✘ |
| `float` | ✔ truncates toward zero; runtime error if outside int range (`VL-RUN-005`) | — | ✘ | ✔ | ✘ |
| `char` | ✔ code | ✘ | — | ✔ 1-character string | ✘ |
| `string` | ✘ | ✘ | ✘ | — | ✘ |
| `bool` | ✔ 0 / 1 | ✘ | ✘ | ✔ `"true"` / `"false"` | — |

✘ is `VL-SEM-019` at compile time. (`int → bool` is deliberately absent; write `x != 0`.)

### 6.4 Assignment compatibility
A value of type `S` may be stored into a target of type `T` iff `S == T`, or `S = int` and `T = float`. Otherwise `VL-SEM-003`.

### 6.5 Evaluation order and short-circuit
- Operands and call arguments are evaluated left to right.
- `a and b`: `b` is evaluated only if `a` is `true`. `a or b`: `b` only if `a` is `false`.
- For `a[i] = e` and `a[i] op= e`, the index is evaluated before `e`.

---

## 7. Statements

| Statement | Syntax | Semantics |
|---|---|---|
| Declaration | `let x: T [= e];` | Section 5 |
| Assignment | `x = e;`  `a[i] = e;` | store; Section 6.4 |
| Compound assignment | `x += e;` (`-=` `*=` `/=` `%=`) | `x = x op e`, typed as that operator (`string += string` concatenates; `int += float` is an error) |
| Increment | `x++;`  `a[i]--;` | operand must be `int` or `float`; adds / subtracts 1 |
| Call | `f(args);` | evaluate, discard any result |
| If | `if (c) { } [else if (c) { }]* [else { }]` | `c` must be `bool` (`VL-SEM-005`) |
| Switch | `switch (e) { case L1, L2: ... default: ... }` | `e` is `int` or `char`; labels are literals of that type (optionally `-` on ints), unique (`VL-SEM-012`, `VL-SEM-013`); the matching clause runs and the switch **ends** (no fall-through); `break;` exits early; `default` optional |
| While | `while (c) { }` | test before each iteration |
| Do-while | `do { } while (c);` | body first, test after; `continue` jumps to the test |
| For | `for (init; cond; update) { }` | `init` = `let` declaration or assignment/increment or empty; `cond` optional (empty = true); `update` = assignment/increment or empty. `continue` jumps to `update` |
| Return | `return [e];` | see Section 8 |
| Break / continue | `break;` `continue;` | `break` inside a loop or switch; `continue` inside a loop (also when nested inside a switch inside a loop). Otherwise `VL-SEM-011` |
| Show | `show e1, e2, ...;` | print each value in order with no separator, then a newline |
| Read | `read x;`  `read a[i];` | Section 10 |
| Block | `{ ... }` | new scope |

---

## 8. Functions

```vela
func name(p1: T1, p2: T2[]): R { ... }     // returns R
func name(p: T) { ... }                    // returns nothing
```

- Parameters: scalars are passed **by value**; arrays are passed **by reference** (`p: int[]`; the argument must be a plain array name with the same element type).
- Return type is optional; omitted means “returns nothing”. Return type can be any base type but never an array.
- `return e;` — `e` assignable to the return type (`VL-SEM-009`); `return;` only in a function without return type; falling off the end of a function with a return type on **some path** is `VL-SEM-010`. “All paths return” is a structural check: a block returns if its last reachable statement returns; `if/else` returns if both branches do; a `switch` returns if it has `default`, every clause returns and no `break` targets it; loops never count as returning.
- Calls: argument count must match (`VL-SEM-007`), each argument assignable to its parameter (`VL-SEM-008`); calling an unknown name is `VL-SEM-006`. A void function in an expression is `VL-SEM-023`.
- Recursion is allowed; a call depth above 1000 is the runtime error `VL-RUN-006` (Section 11).
- No function overloading in Vela (one function per name). Operator overloading (`+`) and implicit widening are the polymorphism features. This is a documented scope decision.
- No built-in functions: all I/O is by the `show` and `read` statements.

---

## 9. Arrays

- Declaration and initialization: Section 5.1. Indexing `a[i]` requires `i` of type `int` (`VL-SEM-014`) and `a` to be an array (`VL-SEM-015`).
- A literal index outside `0..N-1` is a compile-time error `VL-SEM-022`; any other bad index is the runtime error `VL-RUN-002` (bounds are always checked).
- Array elements are used like variables: `a[i] = e;`, `a[i] += e;`, `a[i]++;`, `read a[i];`, `show a[i];`.
- A whole array cannot be used as a value: `x = a;`, `show a;`, `return a;` → `VL-SEM-021`. As an argument it must be the bare name.
- Local arrays live in the function's stack frame; global arrays in static data.

---

## 10. Input and output

**`show e1, e2, ...;`** prints the values in order, no separators, then `\n`.
Formatting: `int` decimal; `float` shortest text that round-trips (`2.5`, `3.0`, `1e+16`; identical to Python `repr`); `char` the character; `string` raw text; `bool` `true`/`false`.

**`read target;`** reads from standard input (a text box in the IDE, supplied before the run). Input is a stream of whitespace-separated tokens.

| Target type | Consumes | Error |
|---|---|---|
| `int` | next token, optional sign + digits, must fit 32-bit | `VL-RUN-004` |
| `float` | next token matching `-?[0-9]+(\.[0-9]+)?` | `VL-RUN-004` |
| `bool` | next token exactly `true` or `false` | `VL-RUN-004` |
| `string` | next token (no spaces) | — |
| `char` | next **non-whitespace character** | — |

Nothing left to read → `VL-RUN-003`.

---

## 11. Runtime semantics

| Topic | Rule |
|---|---|
| `int` arithmetic | 32-bit two's complement; results wrap (`2147483647 + 1 == -2147483648`). Constant folding must use the same wrap. |
| `int` division, `%` | truncate toward zero; remainder has the sign of the dividend (`-7 / 2 == -3`, `-7 % 2 == -1`). Divisor 0 → `VL-RUN-001`. |
| `float` | IEEE double. Division by `0.0` → `VL-RUN-001` (no infinities or NaN are ever produced). |
| Comparisons | `int` vs `float` compare as floats. Strings compare by value. |
| Limits | call depth 1000 → `VL-RUN-006`; instruction budget 1 000 000 → `VL-RUN-007`; output ≤ 100 000 characters → `VL-RUN-008`. |
| Startup | global initializers in textual order, then `main()`. |

---

## 12. Error model

Message format: `line:col: error[CODE]: message` plus optional `hint`. Every diagnostic has `code`, `severity` (`error`/`warning`), `phase` (`lexical`, `syntax`, `semantic`, `runtime`), `message`, `span` (`start`/`end` line+col).
`VL-LIM-001` is reported in phase `lexical`. **Phase gating:** lexical errors stop the pipeline after the lexer (tokens are still shown); syntax errors stop after the parser; semantic errors stop after semantic analysis. Within a phase *all* errors are collected (lexer continues past bad characters; parser uses panic-mode recovery to `;` / `}` ; semantic analysis continues after an error using an `error` type that suppresses follow-on errors).

| Code | Meaning | Reported at |
|---|---|---|
| VL-LEX-001 | invalid character | the character |
| VL-LEX-002 | unterminated string literal | opening quote |
| VL-LEX-003 | unterminated char literal | opening quote |
| VL-LEX-004 | empty char literal | the `''` |
| VL-LEX-005 | char literal has more than one character | opening quote |
| VL-LEX-006 | invalid escape sequence | the backslash |
| VL-LEX-007 | unterminated block comment | the `/*` |
| VL-LEX-008 | malformed number | start of the number |
| VL-LEX-009 | integer literal out of range | the literal |
| VL-LEX-010 | identifier longer than 64 characters | the identifier |
| VL-LEX-011 | char literal outside Latin-1 (code > 255) | the literal |
| VL-SYN-001 | unexpected token (message names what was expected) | the unexpected token |
| VL-SYN-002 | unexpected end of file | the EOF position |
| VL-SYN-003 | nesting too deep (> 200) | the token that exceeded it |
| VL-LIM-001 | more than 50 000 tokens (compiler limit; the scan stops) | the first token over the limit |
| VL-SEM-001 | undeclared variable | the identifier |
| VL-SEM-002 | redeclaration in the same scope | the new name |
| VL-SEM-003 | type mismatch in initialization/assignment | the value expression |
| VL-SEM-004 | invalid operand types for operator | the operator |
| VL-SEM-005 | condition is not `bool` | the condition expression |
| VL-SEM-006 | call to undeclared function / name is not a function | the callee name |
| VL-SEM-007 | wrong number of arguments | the callee name |
| VL-SEM-008 | argument type mismatch | the argument |
| VL-SEM-009 | return value/type mismatch | the returned expression (or `return`) |
| VL-SEM-010 | missing return on some path | the function name |
| VL-SEM-011 | `break`/`continue` outside a valid construct | the keyword |
| VL-SEM-012 | duplicate case label | the duplicate label |
| VL-SEM-013 | switch expression not `int`/`char`, or label type mismatch | the switch expression / the label |
| VL-SEM-014 | array index not `int` | the index |
| VL-SEM-015 | indexing a non-array | the identifier |
| VL-SEM-016 | too many array initializers | first extra initializer |
| VL-SEM-017 | invalid array size (not 1..10 000) | the size literal |
| VL-SEM-018 | missing/ill-formed `main` | 1:1 (or the `main` name) |
| VL-SEM-019 | invalid `as` conversion | the `as` keyword |
| VL-SEM-020 | global initializer not a literal | the initializer |
| VL-SEM-021 | array used as a value | the array name |
| VL-SEM-022 | constant index out of range | the index |
| VL-SEM-023 | void function used as a value | the callee name |
| VL-RUN-001 | division or modulo by zero | the operator |
| VL-RUN-002 | array index out of bounds | the indexing expression |
| VL-RUN-003 | input exhausted | the `read` |
| VL-RUN-004 | invalid input format | the `read` |
| VL-RUN-005 | conversion out of range | the `as` |
| VL-RUN-006 | call stack overflow (depth > 1000) | the call |
| VL-RUN-007 | instruction budget exceeded | current statement |
| VL-RUN-008 | output limit exceeded | the `show` |
| VL-WRN-001 | unused local variable (warning, P2) | the declaration |

---

## 13. Formal grammar

### 13.1 Authoritative grammar `G` (`docs/grammar/vela.bnf`)

Plain BNF, `ε` = empty. Terminals are lexemes (keywords/punctuation) or `ID INT_LIT FLOAT_LIT CHAR_LIT STRING_LIT`. Start symbol `Program`. **Left-recursive and unfactored on purpose** (natural form, used for all LR work).

```
Program      -> TopList
TopList      -> TopList TopItem | ε
TopItem      -> FuncDecl | VarDecl

FuncDecl     -> func ID ( ParamsOpt ) RetType Block
RetType      -> : BaseType | ε
ParamsOpt    -> ParamList | ε
ParamList    -> ParamList , Param | Param
Param        -> ID : BaseType | ID : BaseType [ ]

BaseType     -> int | float | char | string | bool
VarDecl      -> let ID : BaseType ;
             | let ID : BaseType = Expr ;
             | let ID : BaseType [ INT_LIT ] ;
             | let ID : BaseType [ INT_LIT ] = { ExprListOpt } ;
ExprListOpt  -> ExprList | ε
ExprList     -> ExprList , Expr | Expr

Block        -> { StmtList }
StmtList     -> StmtList Stmt | ε
Stmt         -> VarDecl
             | SimpleAssign ;
             | ID ( ArgsOpt ) ;
             | IfStmt | SwitchStmt | WhileStmt | DoWhileStmt | ForStmt
             | return ExprOpt ;
             | break ;
             | continue ;
             | show ExprList ;
             | read ID IndexOpt ;
             | Block
SimpleAssign -> ID IndexOpt AssignOp Expr
             | ID IndexOpt ++
             | ID IndexOpt --
IndexOpt     -> [ Expr ] | ε
AssignOp     -> = | += | -= | *= | /= | %=
ArgsOpt      -> ExprList | ε
ExprOpt      -> Expr | ε

IfStmt       -> if ( Expr ) Block
             | if ( Expr ) Block else Block
             | if ( Expr ) Block else IfStmt
SwitchStmt   -> switch ( Expr ) { CaseList DefaultOpt }
CaseList     -> CaseList CaseClause | ε
CaseClause   -> case CaseLabels : StmtList
CaseLabels   -> CaseLabels , CaseConst | CaseConst
CaseConst    -> INT_LIT | CHAR_LIT | - INT_LIT
DefaultOpt   -> default : StmtList | ε
WhileStmt    -> while ( Expr ) Block
DoWhileStmt  -> do Block while ( Expr ) ;
ForStmt      -> for ( ForInit ; ExprOpt ; ForUpdate ) Block
ForInit      -> let ID : BaseType = Expr | SimpleAssign | ε
ForUpdate    -> SimpleAssign | ε

Expr         -> OrExpr
OrExpr       -> OrExpr or AndExpr | AndExpr
AndExpr      -> AndExpr and NotExpr | NotExpr
NotExpr      -> not NotExpr | EqExpr
EqExpr       -> EqExpr EqOp RelExpr | RelExpr
EqOp         -> == | !=
RelExpr      -> RelExpr RelOp AddExpr | AddExpr
RelOp        -> < | <= | > | >=
AddExpr      -> AddExpr AddOp MulExpr | MulExpr
AddOp        -> + | -
MulExpr      -> MulExpr MulOp UnaryExpr | UnaryExpr
MulOp        -> * | / | %
UnaryExpr    -> - UnaryExpr | CastExpr
CastExpr     -> CastExpr as BaseType | Primary
Primary      -> INT_LIT | FLOAT_LIT | CHAR_LIT | STRING_LIT | true | false
             | ( Expr ) | ID | ID [ Expr ] | ID ( ArgsOpt )
```

Syntax-only restrictions enforced by semantic analysis, not by the grammar: global initializers are literals; `read` target must be a scalar variable or array element; `case` labels match the switch type.

### 13.2 Ambiguity analysis and resolution

| Source of ambiguity | Resolution in Vela |
|---|---|
| Operator precedence / associativity | One nonterminal per precedence level (Section 6.1); left-recursive for left-associative operators, right-recursive (`NotExpr`, `UnaryExpr`) for prefix operators. |
| Dangling `else` | `if` bodies must be `Block`s, so an `else` always belongs to the nearest enclosing `if` **by construction**. The grammar has no `else` in `FOLLOW(IfStmt)`. |
| Unary vs binary `-` | Different grammar positions (`UnaryExpr` vs `AddOp`), distinguished by the parser state, not by the token. |
| Statement starting with `ID` | `SimpleAssign` vs call share a prefix; resolved by left factoring for LL(1) and by the LR automaton for LR. |

Proof of unambiguity: `G` is SLR(1) (13.4). Every LR(k) grammar is unambiguous.
The classical dangling-else problem and its three standard resolutions (prefer shift, matched/unmatched rewrite, mandatory delimiters — the one Vela uses) are demonstrated live in the Grammar Lab with presets `dangling_else.bnf` and `dangling_else_unambiguous.bnf`.

### 13.3 Transformations (`G → G′`, file `docs/grammar/vela_ll1.bnf`)

| Technique | Applied to | Result |
|---|---|---|
| Immediate left-recursion elimination `A → Aα \| β ⇒ A → βA′, A′ → αA′ \| ε` | `TopList` `ParamList` `ExprList` `StmtList` `CaseList` `CaseLabels`; all binary levels `OrExpr … MulExpr`, `CastExpr` | tail nonterminals `OrTail AndTail EqTail RelTail AddTail MulTail CastTail ParamTail ExprTail LabelTail`; list rules become right-recursive (`TopList -> TopItem TopList`) |
| Left factoring `A → αβ₁ \| αβ₂ ⇒ A → αA′, A′ → β₁ \| β₂` | `VarDecl` (4 alternatives share `let ID : BaseType`) → `DeclRest` `ArrInit` `ScalarInit`; `Stmt` (`SimpleAssign` and call share `ID`) → `IdStmtTail` `AssignTail`; `IfStmt` (3 alternatives share `if ( Expr ) Block`) → `ElsePart` `ElseBody`; `Primary` (`ID`, `ID[..]`, `ID(..)`) → `PrimaryTail`; `Param` → `ArrayMark`; `SimpleAssign` | factored alternatives |
| Indirect left recursion | none in `G` (demonstrated on preset `left_recursion_indirect.bnf`) | — |

The recursive-descent parser in `backend/vela/parser/` follows `G′` exactly (one method per nonterminal; `*Tail` nonterminals are written as loops).

### 13.4 Machine-verified properties (reference values the implementation's own grammar engine must reproduce)

Computed at specification time with an independent throw-away checker (not part of the deliverable); these are golden values for the grammar tests in `13_TESTING_AND_ACCEPTANCE.md`.

| Property | Value |
|---|---|
| `G`: productions (ε alternatives counted, augmented production excluded) | 121 |
| `G`: nonterminals / terminals | 47 / 59 (26 keywords + 5 token classes + 9 delimiters + 19 operators) |
| `G` is LL(1) | **No** — 19 nonterminals have table conflicts (left recursion, common prefixes) |
| `G` LR(0) automaton | 214 states; 33 states have shift/reduce conflicts ⇒ **not LR(0)** |
| `G` SLR(1) | **conflict-free** |
| `G` LALR(1) | **conflict-free**, 214 states (same cores as LR(0)) |
| `G` CLR(1) | **conflict-free**, 609 states |
| `G′`: productions / nonterminals | 138 / 65, same 59 terminals |
| `G′` is LL(1) | **Yes** — no table conflicts |
| Equivalence check | 1 500 random sentences generated from `G`, plus 1 500 single-token mutations: the LL(1) parser for `G′` and the SLR(1) parser for `G` gave the same accept/reject result in 100 % of cases |
| `FOLLOW(IfStmt)` | `ID break case continue default do for if let read return show switch while { }` — no `else` |

### 13.5 Chomsky classification (with justification)

- **Lexical syntax** (tokens) is **Type 3 / regular**: every token class has a regular expression and is recognized by a DFA (see lexer spec).
- **Syntactic grammar `G`** is **Type 2 / context-free**: every production has a single nonterminal on the left. It is not regular because balanced `( )`, `{ }`, `[ ]` and nested statements need a stack (pumping-lemma argument: `{ⁿ }ⁿ`). It is a deterministic CFL (it is LR(1)).
- **The full language** (declare-before-use, type compatibility, argument-count checks) is **not context-free**; these context-sensitive constraints are checked in semantic analysis with a symbol table, which is why the compiler has a separate semantic phase.
- The Grammar Lab includes an automatic classifier that labels any loaded grammar Type 3 (all productions right- or left-linear) or Type 2.

---

## 14. Coverage of the assignment's mandatory constructs

| Assignment feature | Required functionality | Vela construct |
|---|---|---|
| Data types | Integer, Float, Character, String, Boolean | `int float char string bool` |
| Variables | declaration, initialization, assignment | `let x: T;` `let x: T = e;` `x = e;` |
| Arithmetic | `+ - * / %` | same symbols |
| Relational | `> < >= <= == !=` | same symbols |
| Logical | AND, OR, NOT | `and` `or` `not` |
| Conditional | IF, IF-ELSE, nested IF | `if (c) { } else { }`, `else if`, nesting |
| Selection | SWITCH-CASE, DEFAULT | `switch (e) { case L: ... default: ... }` |
| Loops | FOR, WHILE, DO-WHILE | `for`, `while`, `do { } while (c);` |
| Functions | declaration, parameters, return | `func f(p: T): R { return e; }` |
| Arrays | declaration, initialization, indexing | `let a: T[N] = {...};` `a[i]` |
| Input/output | Read/Input and Print/Output | `read x;` `show e;` |
| Also required by language-design list | assignment operators, comments, delimiters, keywords, identifiers | Sections 2.2–2.6 |

---

## 15. Valid example programs

Files live in `examples/` and are the golden end-to-end tests. Each was checked to parse under both `G′` (LL(1)) and `G` (SLR(1)). **Expected output** below is derived by hand from the semantics above and must be reproduced by the compiler's VM, by the TAC interpreter, and by the optimized pipeline.

| File | Demonstrates | stdin | Expected output |
|---|---|---|---|
| `01_hello_types.vela` | global/local variables, five types, `show`, int→float | — | `Hello, Vela!` / `answer=42 ratio=2.5` / `grade=A ready=true` / `total=44.5` |
| `02_conditions.vela` | if / else if / else, nested if, return on every path | — | `negative` / `zero` / `positive odd` / `positive even` |
| `03_switch.vela` | multi-label cases, no fall-through, `break`, `default`, char switch | — | `one` / `two-or-three!` / `three` / `other` / `true false` |
| `04_loops.vela` | for, while, do-while, `break`, `continue`, `++`, `+=` | — | `sum 1..5 = 15` / `collatz steps = 6` / `k=3` / `k=9` / `k=12` / `first j with j*j>50: 8` |
| `05_functions.vela` | params, return, recursion, void function, forward calls, mutual recursion | — | `== functions ==` / `5! = 120` / `fib(10) = 55` / `2.5^3 = 15.625` / `true false` |
| `06_arrays.vela` | declaration, initializer, default fill, indexing, array params | — | `data[0] = 1` … `data[5] = 9` (sorted 1 2 3 5 7 9) / `sum = 27` / `alan false` / `11` |
| `07_io.vela` | `read` of int/char/string, switch on char | `4 7 * ada` | `a=4 b=7` / `28` / `hi ada` |
| `08_optimizer_showcase.vela` | folding, propagation, CSE, dead code, loop-invariant code | `5 7 3` | `205 50` |
| `09_strings_and_casts.vela` | `+` on strings, `as`, division/modulo signs, short-circuit, `not` precedence | — | `Vela compiler` / `65 B` / `3` / `3 1 -3 -1` / `3.5` / `checking -1` / `not both` / `n=5` / `true` |
| `10_scopes.vela` | global, nested blocks, shadowing, function after use | — | `global level = 1` / `block level = 2` / `inner level = 3` / `block level again = 2` / `global again = 1` / `after two bumps = 3` |

Each output item is one output line, in order.

---

## 16. Invalid example programs (error catalogue)

Every snippet is a complete test source file: save it exactly as shown as `tests/programs/invalid/<ID>.vela` (the `// <ID>` label is a trailing comment on **line 1**, so it never shifts any position). Positions are `line:col` of the diagnostic's primary span, 1-based. Syntax cases were verified to fail at exactly the listed token against the LL(1) parser; semantic and runtime cases were verified to parse successfully.

### 16.1 Lexical

```vela
func main() { // INV-LEX-01
    let x: int = 5 @ 3;
}
```
```vela
func main() { // INV-LEX-02
    show "hello;
}
```
```vela
func main() { // INV-LEX-03
    let x: int = 12abc;
}
```
```vela
func main() { // INV-LEX-04
    /* never closed
    show 1;
}
```
```vela
func main() { // INV-LEX-05
    show "a\qb";
}
```
```vela
func main() { // INV-LEX-06
    let x: int = 2147483648;
}
```
```vela
func main() { // INV-LEX-07
    let c: char = '';
}
```

| ID | Expected | Shows |
|---|---|---|
| INV-LEX-01 | `VL-LEX-001` @ 2:20 | invalid character `@` |
| INV-LEX-02 | `VL-LEX-002` @ 2:10 | unterminated string |
| INV-LEX-03 | `VL-LEX-008` @ 2:18 | malformed number `12abc` |
| INV-LEX-04 | `VL-LEX-007` @ 2:5 | unterminated block comment |
| INV-LEX-05 | `VL-LEX-006` @ 2:12 | invalid escape `\q` |
| INV-LEX-06 | `VL-LEX-009` @ 2:18 | integer out of range |
| INV-LEX-07 | `VL-LEX-004` @ 2:19 | empty char literal |

### 16.2 Syntax

```vela
func main() { // INV-SYN-01
    let x: int = 5
    show x;
}
```
```vela
func main() { // INV-SYN-02
    if (1 < 2 {
        show 1;
    }
}
```
```vela
func main() { // INV-SYN-03
    else {
    }
}
```
```vela
func main() { // INV-SYN-04
    let x: int = 1;
    if (x > 0) show x;
}
```
```vela
func main() { // INV-SYN-05
    show 1;
```
```vela
func main() { // INV-SYN-06
    for (let i: int = 0; i < 3 i++) {
        show i;
    }
}
```
```vela
func main() { // INV-SYN-07
    let x = 5;
}
```
```vela
func main() { // INV-SYN-08
    let a: int = ;
    let b: int = 2
    show a;
}
```

| ID | Expected | Shows |
|---|---|---|
| INV-SYN-01 | `VL-SYN-001` @ 3:5 | missing `;` is reported at the *next* token (`show`) |
| INV-SYN-02 | `VL-SYN-001` @ 2:15 | expected `)` but found `{` |
| INV-SYN-03 | `VL-SYN-001` @ 2:5 | `else` with no `if` |
| INV-SYN-04 | `VL-SYN-001` @ 3:16 | expected `{`: braces are mandatory |
| INV-SYN-05 | `VL-SYN-002` @ 3:1 | end of file; the EOF position is just past the final newline |
| INV-SYN-06 | `VL-SYN-001` @ 2:32 | expected `;` in the `for` header |
| INV-SYN-07 | `VL-SYN-001` @ 2:11 | expected `:` after the variable name |
| INV-SYN-08 | **two** `VL-SYN-001`: @ 2:18 (expected an expression, found `;`) and @ 4:5 (expected `;` before `show`) | panic-mode recovery finds both errors in one run |

### 16.3 Semantic

```vela
func main() { // INV-SEM-01
    show y;
}
```
```vela
func main() { // INV-SEM-02
    let a: int = 1;
    let a: int = 2;
}
```
```vela
func main() { // INV-SEM-03
    let a: int = "text";
}
```
```vela
func main() { // INV-SEM-04
    let f: float = 1.5;
    let i: int = f;
}
```
```vela
func main() { // INV-SEM-05
    if (1) {
        show 1;
    }
}
```
```vela
func add(a: int, b: int): int { // INV-SEM-06
    return a + b;
}

func main() {
    show add(1);
}
```
```vela
func twice(n: int): int { // INV-SEM-07
    return n * 2;
}

func main() {
    show twice("x");
}
```
```vela
func sign(n: int): int { // INV-SEM-08
    if (n > 0) {
        return 1;
    }
}

func main() {
    show sign(2);
}
```
```vela
func main() { // INV-SEM-09
    break;
}
```
```vela
func main() { // INV-SEM-10
    let n: int = 1;
    switch (n) {
        case 1: show 1;
        case 1: show 2;
    }
}
```
```vela
func hello() { // INV-SEM-11
    return 1;
}

func main() {
    hello();
}
```
```vela
func main() { // INV-SEM-12
    let a: int[2] = {1, 2, 3};
}
```
```vela
func main() { // INV-SEM-13
    let a: int[3];
    a[3] = 1;
}
```
```vela
func helper() { // INV-SEM-14
    show 1;
}
```
```vela
func main() { // INV-SEM-15
    show "5" as int;
}
```
```vela
func main() { // INV-SEM-16
    show "a" - "b";
}
```
```vela
func hello() { // INV-SEM-17
    show 1;
}

func main() {
    let x: int = hello();
}
```
```vela
let a: int = 1; // INV-SEM-18
let b: int = a + 1;

func main() {
    show b;
}
```
```vela
func main() { // INV-SEM-19
    let s: string = "x";
    switch (s) {
        case 1: show 1;
    }
}
```

| ID | Expected | Shows |
|---|---|---|
| INV-SEM-01 | `VL-SEM-001` @ 2:10 | undeclared variable |
| INV-SEM-02 | `VL-SEM-002` @ 3:9 | redeclaration in the same scope |
| INV-SEM-03 | `VL-SEM-003` @ 2:18 | string assigned to int |
| INV-SEM-04 | `VL-SEM-003` @ 3:18 | no implicit float → int |
| INV-SEM-05 | `VL-SEM-005` @ 2:9 | condition must be bool |
| INV-SEM-06 | `VL-SEM-007` @ 6:10 | 1 argument for 2 parameters |
| INV-SEM-07 | `VL-SEM-008` @ 6:16 | string argument for int parameter |
| INV-SEM-08 | `VL-SEM-010` @ 1:6 | missing return on the `n <= 0` path |
| INV-SEM-09 | `VL-SEM-011` @ 2:5 | `break` outside loop/switch |
| INV-SEM-10 | `VL-SEM-012` @ 5:14 | duplicate case label |
| INV-SEM-11 | `VL-SEM-009` @ 2:12 | value returned from function with no return type |
| INV-SEM-12 | `VL-SEM-016` @ 2:28 | 3 initializers for 2 elements |
| INV-SEM-13 | `VL-SEM-022` @ 3:7 | constant index out of range |
| INV-SEM-14 | `VL-SEM-018` @ 1:1 | no `main` |
| INV-SEM-15 | `VL-SEM-019` @ 2:14 | string cannot be cast to int |
| INV-SEM-16 | `VL-SEM-004` @ 2:14 | `string - string` |
| INV-SEM-17 | `VL-SEM-023` @ 6:18 | void call used as a value |
| INV-SEM-18 | `VL-SEM-020` @ 2:14 | global initializer must be a literal |
| INV-SEM-19 | `VL-SEM-013` @ 3:13 | switch on a string |

### 16.4 Runtime (compile cleanly; the VM reports the error)

```vela
func main() { // INV-RUN-01
    let d: int;
    read d;
    show 10 / d;
}
```
```vela
func main() { // INV-RUN-02
    let a: int[3];
    let i: int = 3;
    a[i] = 1;
}
```
```vela
func main() { // INV-RUN-03
    let x: int;
    read x;
    show x;
}
```
```vela
func f(n: int): int { // INV-RUN-04
    return f(n + 1);
}

func main() {
    show f(0);
}
```
```vela
func main() { // INV-RUN-05
    while (true) {
    }
}
```

| ID | stdin | Expected | Shows |
|---|---|---|---|
| INV-RUN-01 | `0` | `VL-RUN-001` @ 4:13 | division by zero |
| INV-RUN-02 | — | `VL-RUN-002` @ 4:5 | index 3 of a 3-element array (index is a variable, so not caught at compile time) |
| INV-RUN-03 | *(empty)* | `VL-RUN-003` @ 3:5 | input exhausted |
| INV-RUN-04 | — | `VL-RUN-006` @ 2:12 | stack overflow from unbounded recursion |
| INV-RUN-05 | — | `VL-RUN-007` @ 2:5 | instruction budget exceeded |

The optimizer must **not** change any of these outcomes (the same error code and position with and without optimization).

---

## 17. Open decisions for group review

1. Name and file extension (`Vela` / `.vela`).
2. Declaration style `let x: int = 5;` and function style `func f(x: int): int` (alternative: C-style `int x = 5;`).
3. Mandatory braces (chosen) versus optional braces plus the matched/unmatched grammar.
4. `show`/`read` statement keywords (alternative: `print(...)` / `input(...)` calls).
5. No fall-through in `switch` (chosen) versus C-style fall-through.
6. No function overloading (chosen); polymorphism shown through `+` overloading and `int→float` widening.
7. Strings have no indexing or `len`; arrays have no `len`.
