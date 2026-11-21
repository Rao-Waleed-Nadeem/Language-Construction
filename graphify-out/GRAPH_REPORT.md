# Graph Report - vela-spec  (2026-11-21)

## Corpus Check
- Corpus is ~22,732 words - fits in a single context window. You may not need a graph.

## Summary
- 71 nodes · 57 edges · 17 communities (7 shown, 10 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 10 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Type System and Optimization
- VM and Intermediate Representation
- Grammar and Parser Pipeline
- Control Flow Test Suite
- Functions and Scopes Test Suite
- Core Specification & Course Assignment
- Compiler Architecture Principles
- IO and Optimizer Test Suite
- Syntax and Language Design
- Error Diagnostics and Fail-Soft
- Vela Studio IDE Workbench
- Specification Package Workflow
- Types and Strings Test Suite
- Project Definition of Done
- Runtime Execution Semantics

## God Nodes (most connected - your core abstractions)
1. `Requirement Traceability Matrix` - 9 edges
2. `Vela Virtual Machine and ISA` - 5 edges
3. `Loops Expected Output` - 5 edges
4. `Phase 1: Language Specification and Grammar Design` - 4 edges
5. `Functions Expected Output` - 4 edges
6. `Architectural Principles (AP-1 to AP-10)` - 3 edges
7. `Vela Compiler 9-Stage Pipeline` - 3 edges
8. `Three-Address Code Intermediate Representation` - 3 edges
9. `TAC Interpreter Independent Oracle` - 3 edges
10. `CS 4031 Semester Project Assignment` - 2 edges

## Surprising Connections (you probably didn't know these)
- `Requirement Traceability Matrix` --implements--> `Phase 5: Intermediate Code Generation`  [EXTRACTED]
  docs/00_PROJECT_MASTER_SPEC.md → docs/Semester Project.md
- `Requirement Traceability Matrix` --implements--> `Phase 7: Target Code Generation`  [EXTRACTED]
  docs/00_PROJECT_MASTER_SPEC.md → docs/Semester Project.md
- `Loops Expected Output` --conceptually_related_to--> `Conditions Expected Output`  [INFERRED]
  examples/04_loops.expected.txt → examples/02_conditions.expected.txt
- `Arrays Expected Output` --conceptually_related_to--> `Loops Expected Output`  [INFERRED]
  examples/06_arrays.expected.txt → examples/04_loops.expected.txt
- `Requirement Traceability Matrix` --implements--> `Phase 1: Language Specification and Grammar Design`  [EXTRACTED]
  docs/00_PROJECT_MASTER_SPEC.md → docs/Semester Project.md

## Hyperedges (group relationships)
- **Three-way output verification flow between unoptimized TAC oracle, optimized TAC oracle, and VM target execution** — docs_02_compiler_architecture_compiler_pipeline, docs_02_compiler_architecture_tac_oracle, docs_02_compiler_architecture_target_vm, docs_03_ui_ux_specification_optimization_lab [INFERRED]
- **Dual-grammar strategy pairing natural left-recursive BNF G with transformed LL(1) G' across production compiler and educational lab** — docs_01_language_specification_grammar_g, docs_01_language_specification_grammar_g_prime, docs_00_project_master_spec_decision_d01_parser_separation, docs_03_ui_ux_specification_grammar_lab [INFERRED]
- **End-to-end diagnostic and recovery flow from standardized error codes to fail-soft phase gating and UI problem reporting** — docs_01_language_specification_error_model, docs_02_compiler_architecture_phase_gating, docs_03_ui_ux_specification_compiler_playground [INFERRED]

## Communities (17 total, 10 thin omitted)

### Community 0 - "Type System and Optimization"
Cohesion: 0.17
Nodes (10): Requirement Traceability Matrix, Vela Type System and Equivalence, Optimization Framework, Code Optimization Lab View, AST and DAG Visualizer, Mandatory Language Constructs, Phase 2: Lexical Analysis, Phase 3: Syntax Analysis (+2 more)

### Community 1 - "VM and Intermediate Representation"
Cohesion: 0.20
Nodes (8): Three-Address Code Intermediate Representation, TAC Interpreter Independent Oracle, Vela Virtual Machine and ISA, Intermediate Code Explorer, Target Code and Register Allocation View, Virtual Machine Execution and Step Player, Phase 5: Intermediate Code Generation, Phase 7: Target Code Generation

### Community 2 - "Grammar and Parser Pipeline"
Cohesion: 0.22
Nodes (8): Vela Chomsky Hierarchy Classification, Authoritative Grammar G, Transformed LL(1) Grammar G', Operator Precedence and Associativity, Vela Compiler 9-Stage Pipeline, Compiler Playground and Console, Vela Studio Grammar Lab, Phase 1: Language Specification and Grammar Design

### Community 3 - "Control Flow Test Suite"
Cohesion: 0.25
Nodes (8): Conditions Expected Output, Switch Expected Output, Loops Break Condition Test Case, Loops Collatz Steps Test Case, Loops Expected Output, Loops Sum 1..5 Test Case, Arrays Expected Output, Arrays Sum Test Case

### Community 4 - "Functions and Scopes Test Suite"
Cohesion: 0.33
Nodes (6): Functions Factorial Test Case, Functions Fibonacci Test Case, Functions Expected Output, Functions Float Power Test Case, Scopes Nested Levels Test Case, Scopes Expected Output

### Community 5 - "Core Specification & Course Assignment"
Cohesion: 0.50
Nodes (3): Project Master Specification, Vela Programming Language, CS 4031 Semester Project Assignment

### Community 7 - "IO and Optimizer Test Suite"
Cohesion: 0.50
Nodes (4): IO Expected Output, IO Standard Input, Optimizer Showcase Expected Output, Optimizer Showcase Standard Input

## Knowledge Gaps
- **32 isolated node(s):** `Phase 2: Lexical Analysis`, `Phase 3: Syntax Analysis`, `Vela Specification Package Overview`, `Project Definition of Done`, `Vela Programming Language` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 45 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Requirement Traceability Matrix` connect `Type System and Optimization` to `VM and Intermediate Representation`, `Grammar and Parser Pipeline`?**
  _High betweenness centrality (0.145) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Loops Expected Output` (e.g. with `Conditions Expected Output` and `Arrays Expected Output`) actually correct?**
  _`Loops Expected Output` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Phase 2: Lexical Analysis`, `Phase 3: Syntax Analysis`, `Vela Specification Package Overview` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Why does `Phase 1: Language Specification and Grammar Design` connect `Grammar and Parser Pipeline` to `Type System and Optimization`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._