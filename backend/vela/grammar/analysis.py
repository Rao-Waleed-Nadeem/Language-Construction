"""Grammar Analysis: Nullable, FIRST, and FOLLOW sets.

Per doc 01 §13, doc 02 §7, doc 06 §4 and textbook (Dragon Book §4.4):
Fixed-point computation of nullable symbols, FIRST sets, and FOLLOW sets with derivation steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vela.grammar.model import EPSILON, Grammar


@dataclass
class DerivationStep:
    iteration: int
    set_type: str  # 'nullable', 'first', 'follow'
    symbol: str
    added: list[str]
    reason: str


class GrammarAnalysis:
    """Computes and caches Nullable, FIRST, and FOLLOW sets for a Grammar."""

    EOF_SYMBOL = "$"

    def __init__(self, grammar: Grammar) -> None:
        self.grammar: Grammar = grammar
        self.nullable: set[str] = set()
        self.first: dict[str, set[str]] = {}
        self.follow: dict[str, set[str]] = {}
        self.steps: list[DerivationStep] = []

        self._compute_nullable()
        self._compute_first()
        self._compute_follow()

    def _compute_nullable(self) -> None:
        iteration = 1
        changed = True

        # Pass 1: immediate epsilon productions A -> ε
        for p in self.grammar.productions:
            if p.is_epsilon and p.lhs not in self.nullable:
                self.nullable.add(p.lhs)
                self.steps.append(
                    DerivationStep(
                        iteration=0,
                        set_type="nullable",
                        symbol=p.lhs,
                        added=[EPSILON],
                        reason=f"Immediate epsilon production: {p}",
                    )
                )

        while changed:
            changed = False
            for p in self.grammar.productions:
                if p.lhs in self.nullable:
                    continue
                # If all symbols in RHS are nullable, lhs is nullable
                if p.rhs and all(sym in self.nullable for sym in p.rhs):
                    self.nullable.add(p.lhs)
                    changed = True
                    self.steps.append(
                        DerivationStep(
                            iteration=iteration,
                            set_type="nullable",
                            symbol=p.lhs,
                            added=[EPSILON],
                            reason=f"All RHS symbols are nullable in {p}",
                        )
                    )
            iteration += 1

    def _compute_first(self) -> None:
        # Initialize FIRST sets
        for term in self.grammar.terminals:
            self.first[term] = {term}
        self.first[self.EOF_SYMBOL] = {self.EOF_SYMBOL}

        for nt in self.grammar.nonterminals:
            self.first[nt] = {EPSILON} if nt in self.nullable else set()

        changed = True
        iteration = 1

        while changed:
            changed = False
            for p in self.grammar.productions:
                lhs = p.lhs
                rhs = p.rhs

                if not rhs or p.is_epsilon:
                    continue

                # Add FIRST(Y1 Y2 ... Yk) to FIRST(lhs)
                before_len = len(self.first[lhs])
                for sym in rhs:
                    sym_first = self.first.get(sym, {sym})
                    self.first[lhs].update(sym_first - {EPSILON})
                    if sym not in self.nullable:
                        break
                else:
                    self.first[lhs].add(EPSILON)

                if len(self.first[lhs]) > before_len:
                    changed = True
                    new_symbols = sorted(self.first[lhs])
                    self.steps.append(
                        DerivationStep(
                            iteration=iteration,
                            set_type="first",
                            symbol=lhs,
                            added=new_symbols,
                            reason=f"Propagated from RHS of {p}",
                        )
                    )
            iteration += 1

    def first_of_sequence(self, sequence: tuple[str, ...]) -> set[str]:
        """Compute FIRST set for a sequence of symbols Y1 Y2 ... Yk."""
        if not sequence:
            return {EPSILON}

        result: set[str] = set()
        for sym in sequence:
            sym_first = self.first.get(sym, {sym})
            result.update(sym_first - {EPSILON})
            if sym not in self.nullable:
                return result

        result.add(EPSILON)
        return result

    def _compute_follow(self) -> None:
        # Initialize FOLLOW sets for nonterminals
        for nt in self.grammar.nonterminals:
            self.follow[nt] = set()

        # Rule 1: $ in FOLLOW(start_symbol)
        if self.grammar.start_symbol in self.follow:
            self.follow[self.grammar.start_symbol].add(self.EOF_SYMBOL)
            self.steps.append(
                DerivationStep(
                    iteration=0,
                    set_type="follow",
                    symbol=self.grammar.start_symbol,
                    added=[self.EOF_SYMBOL],
                    reason="Start symbol initial EOF marker",
                )
            )

        changed = True
        iteration = 1

        while changed:
            changed = False
            for p in self.grammar.productions:
                lhs = p.lhs
                rhs = p.rhs

                for i, sym in enumerate(rhs):
                    if not self.grammar.is_nonterminal(sym):
                        continue

                    # beta = rhs[i+1:]
                    beta = rhs[i + 1 :]
                    beta_first = self.first_of_sequence(beta)

                    before_len = len(self.follow[sym])
                    # Rule 2: add FIRST(beta) \ {ε} to FOLLOW(B)
                    self.follow[sym].update(beta_first - {EPSILON})

                    # Rule 3: if beta =>* ε (or beta is empty), add FOLLOW(A) to FOLLOW(B)
                    if EPSILON in beta_first:
                        self.follow[sym].update(self.follow[lhs])

                    if len(self.follow[sym]) > before_len:
                        changed = True
                        added_syms = sorted(self.follow[sym])
                        self.steps.append(
                            DerivationStep(
                                iteration=iteration,
                                set_type="follow",
                                symbol=sym,
                                added=added_syms,
                                reason=f"Propagated in production {p}",
                            )
                        )
            iteration += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "nullable": sorted(self.nullable),
            "first": {k: sorted(v) for k, v in self.first.items()},
            "follow": {k: sorted(v) for k, v in self.follow.items()},
            "derivation_steps": [
                {
                    "iteration": s.iteration,
                    "type": s.set_type,
                    "symbol": s.symbol,
                    "added": s.added,
                    "reason": s.reason,
                }
                for s in self.steps
            ],
        }
