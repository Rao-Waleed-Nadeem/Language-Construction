# 10-Minute Viva and Demonstration Guide: Vela Studio (CS 4031)

This script provides an exact, minute-by-minute walkthrough designed for defending the **Vela Compiler and Vela Studio** before an academic jury or course examiner.

---

## Preparation & Launch (0:00)
1. Open PowerShell in the project root:
   ```powershell
   powershell -File .\scripts\start.ps1
   ```
2. Open the browser at `http://localhost:5173`.
3. Point out the dark pedagogical theme, the left 48px ActivityBar, the top TitleBar, and the pipeline PhaseBar.

---

## Minute 0–2: Dashboard & Automated Verification
- **Page**: `/` (Dashboard)
- **Key Talking Points**:
  - Show the 7-phase clickable compiler pipeline architecture from Source Code $\to$ Lexer $\to$ Parser $\to$ Semantic $\to$ IR $\to$ Optimizer $\to$ CodeGen & VM.
  - Show the 10 quickstart example cards covering all language constructs.
  - Click **"Run Automated Selftest (50 Programs)"**.
  - Watch the live progress bar execute 50 test programs (10 valid examples, `regpressure.vela`, and 39 error programs from doc 01 §16) with 100% pass rate.
  - Explain: *"Every phase of the compiler is backed by automated tests, and our backend passes 199 pytest cases and 50 integration programs."*

---

## Minute 2–4: Playground & Tri-Way Equivalence Proof
- **Page**: `/playground`
- **Key Talking Points**:
  - Select Example `08_optimizer_showcase.vela` from the Example dropdown.
  - Point out Monaco editor syntax coloring, line numbers, and keyboard shortcuts.
  - Click **"Compile & Run"**: show stdout output in the console with instruction count and machine cycle cost.
  - Click **"Verify Equivalence"**:
    - Explain the Tri-Way Verification Engine: the exact same program is executed across:
      1. Unoptimized TAC Oracle (`vela.ir.interpreter`)
      2. Optimized TAC Oracle (after 8 passes of optimization)
      3. Target ISA Virtual Machine (`vela.vm.machine`)
    - Highlight the green badge confirming all three outputs match identically, mathematically proving that compiler optimizations preserve semantic behavior.

---

## Minute 4–5: Lexer & Parser Phases
- **Pages**: `/lexer` and `/parser`
- **Key Talking Points**:
  - **Lexer**:
    - Show the Tokens DataTable with category filters (Keyword, Identifier, Literals, Operators).
    - Hover over a token row to demonstrate source span highlighting in the code pane.
    - Inspect the DFA Finite State Machine graph and character scan trace StepPlayer.
    - Demonstrate the Two-Buffer simulation with adjustable buffer sizes ($N = 16, 32, 64$).
  - **Parser**:
    - Switch to `/parser`: display the interactive Concrete Syntax Tree (CST) rendered via React Flow.
    - Step through the Recursive-Descent call trace StepPlayer showing call stack depth and lookahead.
    - Mention panic-mode error recovery (synchronizing on `;` and `}`) which finds multiple syntax errors in a single compiler pass.

---

## Minute 5–6: Grammar & Parsing Theory Lab
- **Page**: `/grammar-lab`
- **Key Talking Points**:
  - Show that the Grammar Lab is a full parsing theory workstation for arbitrary CFGs.
  - **Tab 1 (Analysis)**: Step through FIRST/FOLLOW fixed-point derivations and Chomsky classification (Type-2 Context-Free).
  - **Tab 2 (Transform)**: Show Algorithm 4.19 left-recursion elimination and Algorithm 4.22 left factoring.
  - **Tab 3 (LL(1) Predictive Table)**: Display LL(1) parsing table with FIRST/FOLLOW lookaheads and recursive-descent pseudocode generator.
  - **Tab 4 (LR Family)**: Show LR(0), SLR(1), CLR(1), and LALR(1) item sets, ACTION/GOTO tables, and shift-reduce trace.
  - **Tab 5 (Operator Precedence)**: Display leading/trailing sets and precedence relations matrix.
  - **Tab 6 (Dangling Else)**: Load the 3 Dangling Else presets to explain classical ambiguity vs. mandatory brace resolution.

---

## Minute 6–7: Semantic Analysis & Expression DAG
- **Pages**: `/semantic` and `/trees`
- **Key Talking Points**:
  - **Semantic Analysis**:
    - Show type validation, implicit integer-to-float widening, and scope symbol tables.
    - Step through the scope event log StepPlayer (ENTER_SCOPE, DECLARE, RESOLVE, EXIT_SCOPE).
    - Inspect the live SDD/SDT attribute grammar evaluator classifying S-attributed vs L-attributed grammars.
  - **Trees & Expression DAG**:
    - Show the typed Abstract Syntax Tree (AST) with inferred type tags.
    - Switch to the Basic Block Expression DAG: show local value numbering and common subexpression sharing, pointing out the **36.4% node savings metric**.

---

## Minute 7–8: Intermediate Code (TAC) & Code Optimization Lab
- **Pages**: `/ir` and `/optimizer`
- **Key Talking Points**:
  - **IR Page**:
    - Inspect Three-Address Code (TAC) quadruples with translation rule provenance (`TAC-WHILE`, `TAC-BOOL-SC`).
    - Explain why boolean `and`/`or` lower directly to conditional jump code rather than bitwise operations.
    - Show basic block partitioning under Algorithm 8.5 leader rules and the interactive Control-Flow Graph (CFG) with back-edges and dominator trees.
  - **Optimizer Lab**:
    - Inspect the 8 optimization passes: Constant Folding, Algebraic Simplification, Copy Propagation, CSE, DCE, LICM, Strength Reduction, Peephole.
    - Use the side-by-side `DiffView` to examine TAC before and after optimization.
    - Show the transformations log detailing the exact replacement quadruples and instruction reduction percentage.

---

## Minute 8–9: Target CodeGen & Step-by-Step VM Execution
- **Pages**: `/codegen` and `/vm`
- **Key Talking Points**:
  - **Target CodeGen**:
    - Show the 24-instruction target ISA assembly with `tac_index` alignment (AC-C1).
    - Verify that the sum of per-instruction costs equals the displayed total cost (AC-C2).
    - Step through Register Allocation snapshots: explain the Dragon Book Algorithm 8.7 `getReg` logic and physical register descriptors R0–R7 (AC-C3).
    - Compare Ershov DAG-order evaluation against linear TAC order (AC-C5).
  - **Virtual Machine**:
    - Switch to `/vm` 3-column view: Disassembly, Machine State, and Console.
    - Demonstrate **Step Forward** and click **Step Back (Backwards)**: point out that stepping backward restores previous register and memory values exactly (AC-V2).
    - Add a breakpoint by clicking the gutter on an instruction, press **Run**, and watch the VM halt on the breakpoint.

---

## Minute 9–10: Reference Manual & Wrap-Up
- **Page**: `/reference`
- **Key Talking Points**:
  - Show the Language Tour with keyword and operator precedence tables loaded directly from `/api/language`.
  - Show the Error Catalogue listing all 47 diagnostic error codes with sample invalid code and fixes.
  - In the search bar, type `"dangling"`: show instant cross-document search matching the grammar spec.
  - Click **"Open in Playground"** on any example to show seamless round-trip navigation.
  - Conclude: *"Vela Studio fulfills 100% of the CS 4031 capstone specification across all 10 milestones with zero mock data and complete theoretical rigor."*
