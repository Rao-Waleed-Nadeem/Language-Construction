"""LL(1) Parsing Table, Conflict Detection, and Predictive Stack Parser.

Per doc 01 §13.4, doc 02 §7, doc 06 §4 and textbook (Dragon Book §4.4):
- Algorithm 4.31: Construction of predictive parsing table
- Detection of First/First and First/Follow conflicts
- Step-by-step predictive parsing simulation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.grammar.analysis import GrammarAnalysis
from vela.grammar.model import EPSILON, Grammar, Production


@dataclass
class LL1Conflict:
    nonterminal: str
    terminal: str
    productions: list[Production]
    conflict_type: str  # 'FIRST/FIRST' or 'FIRST/FOLLOW'

    def to_dict(self) -> dict[str, Any]:
        return {
            "nonterminal": self.nonterminal,
            "terminal": self.terminal,
            "conflict_type": self.conflict_type,
            "productions": [p.to_dict() for p in self.productions],
        }


@dataclass
class LL1ParseStep:
    step: int
    stack: list[str]
    input: list[str]
    action: str


@dataclass
class LL1ParseResult:
    accepted: bool
    error: str | None
    steps: list[LL1ParseStep] = field(default_factory=list)

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


class LL1Table:
    """Predictive LL(1) parsing table M[A, a]."""

    EOF_SYMBOL = "$"

    def __init__(self, grammar: Grammar, analysis: GrammarAnalysis | None = None) -> None:
        self.grammar: Grammar = grammar
        self.analysis: GrammarAnalysis = analysis or GrammarAnalysis(grammar)
        # table[(nonterminal, terminal)] = list of productions
        self.table: dict[tuple[str, str], list[Production]] = {}
        self.conflicts: list[LL1Conflict] = []
        self._build_table()

    def _build_table(self) -> None:
        """Algorithm 4.31: Construct table M[A, a]."""
        terminals_with_eof = list(self.grammar.terminals) + [self.EOF_SYMBOL]

        # Initialize empty lists for all (NT, T) pairs
        for nt in self.grammar.nonterminals:
            for term in terminals_with_eof:
                self.table[(nt, term)] = []

        for p in self.grammar.productions:
            alpha = p.normalized_rhs()
            first_alpha = self.analysis.first_of_sequence(alpha)

            # 1. For each terminal a in FIRST(alpha), add A -> alpha to M[A, a]
            for a in first_alpha:
                if a != EPSILON:
                    self.table[(p.lhs, a)].append(p)

            # 2. If ε in FIRST(alpha), for each b in FOLLOW(A), add A -> alpha to M[A, b]
            if EPSILON in first_alpha:
                follow_lhs = self.analysis.follow.get(p.lhs, set())
                for b in follow_lhs:
                    if p not in self.table[(p.lhs, b)]:
                        self.table[(p.lhs, b)].append(p)

        # Detect conflicts (cells with > 1 production)
        for (nt, term), prods in self.table.items():
            if len(prods) > 1:
                conflict_type = "FIRST/FIRST"
                # If one is epsilon and one is not, it's FIRST/FOLLOW
                has_eps = any(p.is_epsilon for p in prods)
                if has_eps:
                    conflict_type = "FIRST/FOLLOW"
                self.conflicts.append(
                    LL1Conflict(
                        nonterminal=nt,
                        terminal=term,
                        productions=prods,
                        conflict_type=conflict_type,
                    )
                )

    @property
    def is_ll1(self) -> bool:
        return len(self.conflicts) == 0

    @property
    def conflicted_nonterminals(self) -> set[str]:
        return {c.nonterminal for c in self.conflicts}

    def get_production(self, nonterminal: str, terminal: str) -> Production | None:
        """Return the unique production for M[A, a] if present, else None."""
        prods = self.table.get((nonterminal, terminal), [])
        return prods[0] if prods else None

    def parse(self, tokens: list[str], max_steps: int = 5000) -> LL1ParseResult:
        """Simulate LL(1) table-driven predictive parsing.

        Input tokens is a list of terminal symbols ending with optional '$'.
        """
        input_stream = list(tokens)
        if not input_stream or input_stream[-1] != self.EOF_SYMBOL:
            input_stream.append(self.EOF_SYMBOL)

        stack: list[str] = [self.EOF_SYMBOL, self.grammar.start_symbol]
        ip = 0
        step_num = 0
        steps: list[LL1ParseStep] = []

        while len(stack) > 0 and step_num < max_steps:
            top = stack[-1]
            current_tok = input_stream[ip]

            if top == self.EOF_SYMBOL:
                if current_tok == self.EOF_SYMBOL:
                    # Successfully parsed
                    steps.append(
                        LL1ParseStep(
                            step=step_num,
                            stack=list(stack),
                            input=input_stream[ip:],
                            action="Accept",
                        )
                    )
                    return LL1ParseResult(accepted=True, error=None, steps=steps)
                else:
                    return LL1ParseResult(
                        accepted=False,
                        error=f"Expected end of input, found '{current_tok}'",
                        steps=steps,
                    )

            if self.grammar.is_terminal(top) or top == self.EOF_SYMBOL:
                if top == current_tok:
                    steps.append(
                        LL1ParseStep(
                            step=step_num,
                            stack=list(stack),
                            input=input_stream[ip:],
                            action=f"Match '{top}'",
                        )
                    )
                    stack.pop()
                    ip += 1
                else:
                    err = f"Syntax error: expected terminal '{top}', found '{current_tok}'"
                    steps.append(
                        LL1ParseStep(
                            step=step_num,
                            stack=list(stack),
                            input=input_stream[ip:],
                            action=f"Error: {err}",
                        )
                    )
                    return LL1ParseResult(accepted=False, error=err, steps=steps)
            else:
                # top is a nonterminal
                prods = self.table.get((top, current_tok), [])
                if not prods:
                    err = f"Syntax error: unexpected token '{current_tok}' for nonterminal '{top}'"
                    steps.append(
                        LL1ParseStep(
                            step=step_num,
                            stack=list(stack),
                            input=input_stream[ip:],
                            action=f"Error: {err}",
                        )
                    )
                    return LL1ParseResult(accepted=False, error=err, steps=steps)

                prod = prods[0]  # Take first (deterministic if LL(1))
                steps.append(
                    LL1ParseStep(
                        step=step_num,
                        stack=list(stack),
                        input=input_stream[ip:],
                        action=f"Apply {prod}",
                    )
                )
                stack.pop()
                rhs = prod.normalized_rhs()
                # Push RHS in reverse order onto stack
                stack.extend(reversed(rhs))

            step_num += 1

        if step_num >= max_steps:
            return LL1ParseResult(
                accepted=False,
                error="Exceeded max step budget (5000 steps)",
                steps=steps,
            )

        return LL1ParseResult(accepted=False, error="Unexpected end of parse", steps=steps)

    def to_dict(self) -> dict[str, Any]:
        terminals = list(self.grammar.terminals) + [self.EOF_SYMBOL]
        entries: list[dict[str, Any]] = []
        for (nt, term), prods in self.table.items():
            if prods:
                entries.append(
                    {
                        "nonterminal": nt,
                        "terminal": term,
                        "productions": [p.to_dict() for p in prods],
                    }
                )
        return {
            "is_ll1": self.is_ll1,
            "conflict_count": len(self.conflicts),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "nonterminals": self.grammar.nonterminals,
            "terminals": terminals,
            "entries": entries,
        }
