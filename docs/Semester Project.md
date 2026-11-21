# CS 4031
## Compiler Construction
### Final Semester Project

## Project Description

Students are required to design and develop their own programming language and implement a complete compiler for that language. Each group will decide the language name, keywords, syntax, data types, operators, and programming rules. The designed language must support fundamental programming constructs, including variable declarations, data types, conditional statements, switch-case structures, loops, functions, arrays, and input/output operations.

After designing the language, students must develop a compiler that translates programs written in their language into target instructions. The compiler must implement all major phases of compiler construction, including lexical analysis, syntax analysis, semantic analysis, syntax-directed translation, intermediate code generation, code optimization, and target code generation. The central idea is that students design the language first and then build a compiler according to the grammar and rules of their own language.

## Language Design Requirements

Each group must independently design a programming language with its own:

- Language name.
- Keywords and reserved words.
- Identifiers and naming conventions.
- Data types.
- Arithmetic and logical operators.
- Relational operators.
- Assignment operators.
- Conditional structures.
- Looping structures.
- Switch-case structure.
- Function declaration and calling syntax.
- Array declaration and access syntax.
- Input/output statements.
- Comments and delimiters.
- Mandatory programming constructs.

### Feature Requirements

| Feature | Required functionality |
|---|---|
| Data types | Integer, Float, Character, String, Boolean |
| Variables | Declaration, initialization, assignment |
| Arithmetic | +, -, *, /, % |
| Relational | >, <, >=, <=, ==, != |
| Logical | AND, OR, NOT |
| Conditional | IF, IF-ELSE, nested IF |
| Selection | SWITCH-CASE, DEFAULT |
| Loops | FOR, WHILE, DO-WHILE |
| Functions | Declaration, parameters, return |
| Arrays | Declaration, initialization, indexing |
| Input/output | Read/Input and Print/Output |

- Students may define their own syntax for each construct, but all mandatory functionality must be supported.

## Language Example

| Sample 1 | Sample 2 | Sample 3 |
|---|---|---|
| `BEGIN Gamma` | `START Beta` | `LANGUAGE Alpha {` |
| `INT age = 20;` | `NUM age := 20` | `INTEGER age = 20;` |
| `CHECK age >= 18 {` | `WHEN age >= 18 DO` | `IF (age >= 18) {` |
| `PRINT("Eligible");` | `SHOW "Eligible"` | `DISPLAY("Eligible");` |
| `}` | `OTHERWISE` | `}` |
| `OTHERWISE {` | `SHOW "Not Eligible"` | `ELSE {` |
| `PRINT("Not Eligible");` | `ENDWHEN` | `PRINT("Not Eligible");` |
| `}` |  | `}` |
| `END` | `STOP` |  |

## Compiler

Once students have designed their language, they must develop a compiler specifically according to its grammar and syntax.

### Phase 1: Language Specification and Grammar Design

Students must define and document the specifications of their proposed programming language. This phase must include defining the language's syntax and semantics, identifying keywords, identifiers, literals, and operators, and specifying supported data types and programming constructs. Students must develop formal grammar productions using Backus–Naur Form (BNF), define operator precedence and associativity, identify and resolve grammar ambiguities, classify their grammar according to the Chomsky hierarchy with justification, and design the overall compiler architecture, explaining its major phases and components.

### Phase 2: Lexical Analysis

Students must design and implement a lexical analyzer (scanner) for their proposed programming language. This phase must include defining regular expressions for tokens, designing finite state machines for token recognition, identifying tokens and lexemes, recognizing keywords, identifiers, operators, and literals, implementing input buffering, and handling lexical errors. Students may implement the scanner manually or use LEX/Flex. Example: If a group defines DISPLAY as its output keyword, the lexical analyzer must recognize DISPLAY as a reserved token rather than an ordinary identifier.

### Phase 3: Syntax Analysis

Students must implement a parser based on their proposed language grammar and demonstrate the application of relevant parsing techniques. The implementation and documentation must cover recursive descent parsing, LL(1) parsing, FIRST and FOLLOW sets, left recursion elimination, left factoring, ambiguous grammar resolution (including the dangling-else problem), operator precedence parsing, and bottom-up shift-reduce parsing.

Students must also study and demonstrate LR(0), SLR(1), CLR(1), and LALR(1) parsing techniques, including parsing table construction. YACC/Bison may be used for parser implementation. The parser must detect and handle syntax errors and correctly recognize the language's supported constructs, including IF, SWITCH, FOR, WHILE, DO-WHILE, and function definitions.

### Phase 4: Syntax-Directed Translation and Semantic Analysis

Students must implement syntax-directed translation and semantic analysis for their proposed language. This phase must include constructing Abstract Syntax Trees (ASTs) and Directed Acyclic Graphs (DAGs), developing Syntax-Directed Definitions (SDD) and Syntax-Directed Translation Schemes (SDT), and demonstrating S-attributed and L-attributed definitions with attribute evaluation.

Furthermore, students must implement symbol tables and scope management, perform type checking, demonstrate type equivalence and type conversion, validate function arguments and return types, and detect semantic errors such as undeclared and redeclared variables. Function/operator overloading and polymorphism must also be demonstrated where supported by the proposed language.

### Phase 5: Intermediate Code Generation

Students must implement an intermediate code generator that translates their proposed programming language into Three-Address Code (TAC). The generated intermediate code must demonstrate the translation of variable declarations, arithmetic expressions, IF-ELSE statements, nested conditions, SWITCH-CASE statements, FOR loops, WHILE loops, DO-WHILE loops, function definitions and calls, and array operations.

### Phase 6: Code Optimization

Students must implement and demonstrate code optimization techniques on the generated intermediate code. This phase must include basic block identification, control-flow graph construction, DAG-based optimization, constant folding, constant propagation, common subexpression elimination, dead-code elimination, copy propagation, loop optimization, global optimization, and machine-dependent optimization.

Students must provide a clear comparison of the original and optimized intermediate code and explain the improvements achieved through each optimization technique.

### Phase 7: Target Code Generation

Students must design and implement the target code generation phase to translate optimized Three-Address Code into target instructions. This phase must include designing a target instruction set, instruction selection, instruction cost calculation, register allocation, assigning registers to temporary variables, and DAG-based code generation.

The generated target code must demonstrate how the compiler translates optimized intermediate instructions into executable or simulated target instructions.