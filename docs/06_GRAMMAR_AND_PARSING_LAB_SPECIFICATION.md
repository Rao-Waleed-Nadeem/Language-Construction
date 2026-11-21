# 06 — Grammar & Parsing Lab Specification (Phase 3 Theory)

> Status: written by the implementation agent, needs group review
> Authority: follows `docs/00_PROJECT_MASTER_SPEC.md` and `docs/01_LANGUAGE_SPECIFICATION.md` §13.

---

## 1. Overview and Scope
The Grammar Engine (`vela.grammar`) is an independent library for formal language analysis and parser generation. It operates on arbitrary context-free grammars specified in BNF, including Vela's authoritative grammar `G` (`vela.bnf`) and derived LL(1) grammar `G'` (`vela_ll1.bnf`).

---

## 2. BNF Grammar Format
- Plain text file encoding productions.
- Lines starting with `#` are comments.
- Nonterminals on LHS, followed by `->`, followed by space-separated symbols.
- A line starting with `|` continues the previous production's LHS.
- The empty word (epsilon) is represented by `ε`.
- Terminals are any symbols that never appear on any LHS.

---

## 3. Data Structures (`vela.grammar.model`)
```python
@dataclass(frozen=True)
class Production:
    lhs: str
    rhs: tuple[str, ...]  # Empty tuple () represents ε

@dataclass
class Grammar:
    start_symbol: str
    productions: list[Production]
    nonterminals: set[str]
    terminals: set[str]
```

---

## 4. Grammar Analysis (`vela.grammar.analysis`)
1. **Nullable Computation**: Fixed-point iteration finding all nonterminals $A$ such that $A \Rightarrow^* \varepsilon$.
2. **FIRST Sets**: Computes $FIRST(\alpha)$ for all symbols and symbol strings. Records step-by-step derivation history.
3. **FOLLOW Sets**: Fixed-point computation of $FOLLOW(A)$ for all nonterminals, with $EOF$ ($) in $FOLLOW(S)$.

---

## 5. Chomsky Hierarchy Classification (`vela.grammar.classify`)
- **Type 3 (Regular)**: Every production is either all right-linear ($A \to w B$ or $A \to w$) or all left-linear ($A \to B w$ or $A \to w$), where $w \in \Sigma^*$.
- **Type 2 (Context-Free)**: Single nonterminal on LHS ($|LHS| = 1$), unrestricted RHS.
- Automatic classifier outputs classification category, justification, and identifying productions.
