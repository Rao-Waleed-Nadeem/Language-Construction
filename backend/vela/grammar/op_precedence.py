"""Operator-Precedence Relations and Parsing.

Per doc 01 §13.4, doc 02 §7, doc 06 §4 and textbook (Dragon Book §4.6):
- Eligibility check (no epsilon, no adjacent nonterminals)
- Leading and Trailing terminal set computation
- Operator-precedence relation matrix (<., =., .>)
- Conflict detection (e.g., unary minus vs binary minus)
- Operator-precedence parser simulation and trace
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.grammar.model import Grammar


@dataclass
class OpPrecedenceConflict:
    term_a: str
    term_b: str
    relations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "term_a": self.term_a,
            "term_b": self.term_b,
            "relations": self.relations,
        }


@dataclass
class OpParseStep:
    step: int
    stack: list[str]
    input: list[str]
    action: str


@dataclass
class OpParseResult:
    accepted: bool
    error: str | None
    steps: list[OpParseStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "error": self.error,
            "step_count": len(self.steps),
            "steps": [
                {
                    "step": s.step,
                    "stack": s.stack,
                    "input": s.input,
                    "action": s.action,
                }
                for s in self.steps
            ],
        }


class OperatorPrecedenceTable:
    """Computes operator-precedence relations for an operator grammar."""

    EOF = "$"

    def __init__(self, grammar: Grammar) -> None:
        self.grammar: Grammar = grammar
        self.is_eligible: bool = True
        self.eligibility_errors: list[str] = []
        self._check_eligibility()

        # Leading and Trailing sets for nonterminals
        self.leading: dict[str, set[str]] = {}
        self.trailing: dict[str, set[str]] = {}

        # Relations table: (a, b) -> set of relations in {'<.', '=.', '.>'}
        self.relations: dict[tuple[str, str], set[str]] = {}
        self.conflicts: list[OpPrecedenceConflict] = []

        if self.is_eligible:
            self._compute_leading_trailing()
            self._build_relations()

    def _check_eligibility(self) -> None:
        """Verify grammar has no epsilon productions and no adjacent nonterminals."""
        for p in self.grammar.productions:
            if p.is_epsilon:
                self.is_eligible = False
                self.eligibility_errors.append(f"Production {p} is an epsilon production")

            rhs = p.normalized_rhs()
            for i in range(len(rhs) - 1):
                if self.grammar.is_nonterminal(rhs[i]) and self.grammar.is_nonterminal(rhs[i + 1]):
                    self.is_eligible = False
                    self.eligibility_errors.append(
                        f"Production {p} has adjacent nonterminals ({rhs[i]} {rhs[i+1]})"
                    )

    def _compute_leading_trailing(self) -> None:
        """Compute LEADING(A) and TRAILING(A) fixed-point sets."""
        for nt in self.grammar.nonterminals:
            self.leading[nt] = set()
            self.trailing[nt] = set()

        # Base passes: direct terminals
        for p in self.grammar.productions:
            rhs = p.normalized_rhs()
            if not rhs:
                continue
            # LEADING direct
            if self.grammar.is_terminal(rhs[0]):
                self.leading[p.lhs].add(rhs[0])
            elif len(rhs) > 1 and self.grammar.is_terminal(rhs[1]):
                self.leading[p.lhs].add(rhs[1])

            # TRAILING direct
            if self.grammar.is_terminal(rhs[-1]):
                self.trailing[p.lhs].add(rhs[-1])
            elif len(rhs) > 1 and self.grammar.is_terminal(rhs[-2]):
                self.trailing[p.lhs].add(rhs[-2])

        # Iterative propagation
        changed = True
        while changed:
            changed = False
            for p in self.grammar.productions:
                rhs = p.normalized_rhs()
                if not rhs:
                    continue
                # If rhs starts with nonterminal B, LEADING(A) contains LEADING(B)
                if self.grammar.is_nonterminal(rhs[0]):
                    B = rhs[0]
                    before = len(self.leading[p.lhs])
                    self.leading[p.lhs].update(self.leading[B])
                    if len(self.leading[p.lhs]) > before:
                        changed = True

                # If rhs ends with nonterminal B, TRAILING(A) contains TRAILING(B)
                if self.grammar.is_nonterminal(rhs[-1]):
                    B = rhs[-1]
                    before = len(self.trailing[p.lhs])
                    self.trailing[p.lhs].update(self.trailing[B])
                    if len(self.trailing[p.lhs]) > before:
                        changed = True

    def _build_relations(self) -> None:
        """Construct precedence relations: =., <., .>."""
        terminals = list(self.grammar.terminals) + [self.EOF]
        for a in terminals:
            for b in terminals:
                self.relations[(a, b)] = set()

        for p in self.grammar.productions:
            rhs = p.normalized_rhs()
            n = len(rhs)
            for i in range(n - 1):
                # 1. a =. b if A -> ... a b ...
                if self.grammar.is_terminal(rhs[i]) and self.grammar.is_terminal(rhs[i + 1]):
                    self.relations[(rhs[i], rhs[i + 1])].add("=.")

                # 2. a =. b if A -> ... a B b ...
                if (
                    i < n - 2
                    and self.grammar.is_terminal(rhs[i])
                    and self.grammar.is_nonterminal(rhs[i + 1])
                    and self.grammar.is_terminal(rhs[i + 2])
                ):
                    self.relations[(rhs[i], rhs[i + 2])].add("=.")

                # 3. a <. b if A -> ... a B ... and b in LEADING(B)
                if self.grammar.is_terminal(rhs[i]) and self.grammar.is_nonterminal(rhs[i + 1]):
                    B = rhs[i + 1]
                    for b in self.leading.get(B, set()):
                        self.relations[(rhs[i], b)].add("<.")

                # 4. a .> b if A -> ... B b ... and a in TRAILING(B)
                if self.grammar.is_nonterminal(rhs[i]) and self.grammar.is_terminal(rhs[i + 1]):
                    B = rhs[i]
                    for a in self.trailing.get(B, set()):
                        self.relations[(a, rhs[i + 1])].add(".>")

        # End markers
        start_nt = self.grammar.start_symbol
        for b in self.leading.get(start_nt, set()):
            self.relations[(self.EOF, b)].add("<.")
        for a in self.trailing.get(start_nt, set()):
            self.relations[(a, self.EOF)].add(".>")
        self.relations[(self.EOF, self.EOF)].add("=.")

        # Check conflicts
        for (a, b), rels in self.relations.items():
            if len(rels) > 1:
                self.conflicts.append(
                    OpPrecedenceConflict(
                        term_a=a,
                        term_b=b,
                        relations=sorted(rels),
                    )
                )

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def parse(self, tokens: list[str], max_steps: int = 5000) -> OpParseResult:
        """Parse token sequence using operator precedence relations."""
        if not self.is_eligible:
            return OpParseResult(
                accepted=False,
                error=f"Grammar is not an operator grammar: {'; '.join(self.eligibility_errors)}",
            )
        if self.has_conflicts:
            return OpParseResult(
                accepted=False,
                error=f"Grammar has {len(self.conflicts)} operator-precedence conflicts",
            )

        input_stream = list(tokens)
        if not input_stream or input_stream[-1] != self.EOF:
            input_stream.append(self.EOF)

        # Stack holds terminals and nonterminals. Initialized to ['$']
        stack: list[str] = [self.EOF]
        ip = 0
        step_num = 0
        steps: list[OpParseStep] = []

        while step_num < max_steps:
            # Find the top-most terminal on the stack
            top_term_idx = len(stack) - 1
            while top_term_idx >= 0 and self.grammar.is_nonterminal(stack[top_term_idx]):
                top_term_idx -= 1

            top_term = stack[top_term_idx]
            current_tok = input_stream[ip]

            if top_term == self.EOF and current_tok == self.EOF:
                steps.append(
                    OpParseStep(
                        step=step_num,
                        stack=list(stack),
                        input=input_stream[ip:],
                        action="Accept",
                    )
                )
                return OpParseResult(accepted=True, error=None, steps=steps)

            rels = self.relations.get((top_term, current_tok), set())
            if not rels:
                err = f"Operator precedence error: no relation between '{top_term}' and '{current_tok}'"
                steps.append(
                    OpParseStep(
                        step=step_num,
                        stack=list(stack),
                        input=input_stream[ip:],
                        action=f"Error: {err}",
                    )
                )
                return OpParseResult(accepted=False, error=err, steps=steps)

            rel = next(iter(rels))

            if rel in ("<.", "=."):
                # Shift
                steps.append(
                    OpParseStep(
                        step=step_num,
                        stack=list(stack),
                        input=input_stream[ip:],
                        action=f"Shift '{current_tok}' (relation {top_term} {rel} {current_tok})",
                    )
                )
                stack.append(current_tok)
                ip += 1
            elif rel == ".>":
                # Reduce handle: search down the stack for <.
                # Find the handle [q .. end]
                j = top_term_idx
                while j > 0:
                    prev_term_idx = j - 1
                    while prev_term_idx >= 0 and self.grammar.is_nonterminal(stack[prev_term_idx]):
                        prev_term_idx -= 1
                    if prev_term_idx < 0:
                        break
                    p_term = stack[prev_term_idx]
                    p_rels = self.relations.get((p_term, stack[j]), set())
                    if "<." in p_rels:
                        break
                    j = prev_term_idx

                handle_start = prev_term_idx + 1 if prev_term_idx >= 0 else 0
                handle = stack[handle_start:]
                handle_str = " ".join(handle)

                steps.append(
                    OpParseStep(
                        step=step_num,
                        stack=list(stack),
                        input=input_stream[ip:],
                        action=f"Reduce handle [{handle_str}] (relation {top_term} .> {current_tok})",
                    )
                )
                stack = stack[:handle_start]
                # Replace with placeholder nonterminal 'N'
                stack.append("N")

            step_num += 1

        return OpParseResult(accepted=False, error="Exceeded max parse steps (5000)", steps=steps)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_eligible": self.is_eligible,
            "eligibility_errors": self.eligibility_errors,
            "has_conflicts": self.has_conflicts,
            "conflict_count": len(self.conflicts),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "leading": {k: sorted(v) for k, v in self.leading.items()},
            "trailing": {k: sorted(v) for k, v in self.trailing.items()},
        }
