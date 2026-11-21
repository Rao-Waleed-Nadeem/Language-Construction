# 10 — Code Optimization Specification (Phase 6)

> Status: written by the implementation agent (ALLOW_SPEC_GAP_FILLING = true)
> Authority: follows `docs/00_PROJECT_MASTER_SPEC.md` (§5.9) and `docs/01_LANGUAGE_SPECIFICATION.md` §11, §15.

---

## 1. Overview and Architecture
Code optimization transforms Three-Address Code into semantically equivalent, more efficient Three-Address Code (Phase 6).
The optimization subsystem comprises:
1. **Control-Flow Analysis** (`vela.opt.blocks`, `cfg`, `dominators`): Partitioning TAC into basic blocks, building directed CFGs, computing dominators and identifying natural loops.
2. **Data-Flow Analysis Framework** (`vela.opt.dataflow`): Generic iterative fixed-point engine supporting forward and backward data-flow problems over sets or bitvectors.
3. **Transformational Passes** (`vela.opt.passes.*`): Local and global optimizations (constant folding/propagation, copy propagation, CSE, dead-code elimination, algebraic simplification, LICM, strength reduction).
4. **Pipeline & Validator** (`vela.opt.pipeline`, `validate`): Ordered pass execution to fixed point with change logging and IR well-formedness verification.

---

## 2. Basic Blocks and Control-Flow Graph (CFG)

### 2.1 Basic Block Leader Rules (Algorithm 8.5)
A basic block is a maximal sequence of consecutive instructions with single-entry and single-exit execution.
An instruction is a **Leader** if:
1. It is the first instruction of the program or function (`reason = "first instruction"`).
2. It is the target of any conditional or unconditional jump (`reason = "jump target: L"`).
3. It immediately follows a conditional or unconditional jump or return (`reason = "follows jump/branch/return"`).

Each block starts at a leader and includes all instructions up to (but not including) the next leader or program/function end.

### 2.2 CFG Structure
A directed graph $G = (V, E)$ where:
- Vertices $V$ are basic blocks (`BasicBlock`).
- Directed edges $E$ represent possible control transfers:
  - **Fall-through**: from block ending without unconditional jump to immediately following block.
  - **Branch**: from conditional jump to target label block and fall-through block.
  - **Jump**: from unconditional jump to target label block.
- Special nodes: `ENTRY` and `EXIT`.

---

## 3. Dominators and Natural Loops

### 3.1 Dominator Tree
A node $d$ dominates node $n$ ($d \text{ dom } n$) if every path from `ENTRY` to $n$ in the CFG must pass through $d$.
- Iterative data-flow formulation:
  $$DOM(n) = \{n\} \cup \left( \bigcap_{p \in Pred(n)} DOM(p) \right)$$
  with boundary condition $DOM(ENTRY) = \{ENTRY\}$.
- **Immediate Dominator** ($idom(n)$): The unique strict dominator of $n$ that does not dominate any other strict dominator of $n$.

### 3.2 Natural Loops
A **back edge** is an edge $n \to d$ where $d$ dominates $n$ ($d \text{ dom } n$).
$d$ is called the **loop header**.
The **natural loop** of $n \to d$ is the set of nodes:
$$\{d\} \cup \{m \mid m \text{ can reach } n \text{ without going through } d\}$$

---

## 4. Generic Data-Flow Analysis Framework

The framework executes iterative worklist fixed-point propagation over CFG nodes:
- Transfer function: $OUT[B] = f_B(IN[B])$
- Meet operator: $\bigwedge$ ($\bigcup$ for ANY / union problems, $\bigcap$ for ALL / intersection problems).
- Direction: Forward or Backward.

| Analysis | Direction | Meet ($\bigwedge$) | Transfer Function | Boundary | Initial Value |
|---|---|---|---|---|---|
| **Reaching Definitions** | Forward | $\bigcup$ | $OUT[B] = GEN[B] \cup (IN[B] - KILL[B])$ | $OUT[ENTRY] = \emptyset$ | $\emptyset$ |
| **Live Variables** | Backward | $\bigcup$ | $IN[B] = USE[B] \cup (OUT[B] - DEF[B])$ | $IN[EXIT] = \emptyset$ | $\emptyset$ |
| **Available Expressions** | Forward | $\bigcap$ | $OUT[B] = GEN[B] \cup (IN[B] - KILL[B])$ | $OUT[ENTRY] = \emptyset$ | $\mathcal{U}$ |
| **Available Copies** | Forward | $\bigcap$ | $OUT[B] = GEN[B] \cup (IN[B] - KILL[B])$ | $OUT[ENTRY] = \emptyset$ | $\mathcal{U}$ |

Step-by-step iteration logs capture IN and OUT sets per block for academic inspection and GUI visualization.

---

## 5. Optimization Passes

1. **Constant Folding**: Statically evaluates constant expressions (e.g. `2 + 3 -> 5`). Must obey 32-bit wrap-around (`wrap32`). **Never fold division or modulo by zero** to preserve runtime error `VL-RUN-001`.
2. **Constant Propagation**: Replaces uses of variables known to have constant values (local within block + global across CFG via reaching definitions).
3. **Copy Propagation**: Replaces uses of $x$ with $y$ following copy $x = y$ when no intervening redefinition occurs.
4. **Common Subexpression Elimination (CSE)**: Reuses previously computed values identified via local DAG value numbering or global available expressions.
5. **Dead-Code Elimination (DCE)**: Removes instructions defining variables that are not live at the point of definition (excluding instructions with side effects such as `CALL`, `SHOW`, `READ`).
6. **Algebraic Simplification**: Simplifies algebraic identities ($x + 0 \to x$, $x * 1 \to x$, $x * 0 \to 0$, $x - 0 \to x$, $-(-x) \to x$).
7. **Loop-Invariant Code Motion (LICM)**: Hoists invariant computations out of natural loops into newly inserted preheader blocks.
8. **Induction-Variable Strength Reduction**: Replaces expensive multiplications $i * c$ on linear loop induction variables with additions $t = t + c$.

---

## 6. Equivalence Invariant
The optimization pipeline must never alter program semantics:
1. Execution of optimized TAC by the oracle interpreter must produce the exact same stdout as unoptimized TAC for all inputs.
2. Invalid runtime programs (`INV-RUN-01..05`) must preserve their exact error codes and coordinate positions.
