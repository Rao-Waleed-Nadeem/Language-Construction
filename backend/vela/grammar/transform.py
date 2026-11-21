"""Grammar Transformations: Left-Recursion Elimination and Left Factoring.

Per doc 01 §13.3, doc 06 §4 and textbook (Dragon Book §4.3):
- Immediate left-recursion elimination (A -> A alpha | beta)
- General (indirect) left-recursion elimination
- Left factoring (A -> alpha beta1 | alpha beta2)
- Step-by-step logs for UI visualization in Grammar Lab
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vela.grammar.model import EPSILON, Grammar, Production


@dataclass
class TransformStep:
    step_number: int
    transformation: str  # 'indirect_substitute', 'immediate_elimination', 'left_factoring'
    nonterminal: str
    before_productions: list[str]
    after_productions: list[str]
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_number": self.step_number,
            "transformation": self.transformation,
            "nonterminal": self.nonterminal,
            "before_productions": self.before_productions,
            "after_productions": self.after_productions,
            "explanation": self.explanation,
        }


def _get_unique_prime(base: str, existing: set[str]) -> str:
    candidate = f"{base}'"
    while candidate in existing:
        candidate += "'"
    existing.add(candidate)
    return candidate


def eliminate_immediate_left_recursion(
    grammar: Grammar,
    nonterminal: str,
    existing_nts: set[str],
    step_counter: list[int],
) -> tuple[list[Production], list[Production], list[TransformStep]]:
    """Eliminate immediate left recursion A -> A alpha1 | ... | beta1 | ...

    Replaces with:
      A -> beta1 A' | beta2 A' ...
      A' -> alpha1 A' | alpha2 A' ... | ε
    """
    prods = grammar.productions_for(nonterminal)
    alphas: list[tuple[str, ...]] = []
    betas: list[tuple[str, ...]] = []

    for p in prods:
        rhs = p.normalized_rhs()
        if rhs and rhs[0] == nonterminal:
            alphas.append(rhs[1:])
        else:
            betas.append(rhs)

    if not alphas:
        # No immediate left recursion
        return prods, [], []

    steps: list[TransformStep] = []
    new_prime_nt = _get_unique_prime(nonterminal, existing_nts)

    new_a_prods: list[Production] = []
    new_prime_prods: list[Production] = []

    # If no betas existed, beta = (ε,)
    effective_betas = betas if betas else [()]

    # A -> beta A'
    for b in effective_betas:
        new_rhs = b + (new_prime_nt,)
        new_a_prods.append(Production(id=0, lhs=nonterminal, rhs=new_rhs))

    # A' -> alpha A' | ε
    for a in alphas:
        new_rhs = a + (new_prime_nt,)
        new_prime_prods.append(Production(id=0, lhs=new_prime_nt, rhs=new_rhs))
    new_prime_prods.append(Production(id=0, lhs=new_prime_nt, rhs=()))

    step_counter[0] += 1
    steps.append(
        TransformStep(
            step_number=step_counter[0],
            transformation="immediate_elimination",
            nonterminal=nonterminal,
            before_productions=[str(p) for p in prods],
            after_productions=[str(p) for p in new_a_prods + new_prime_prods],
            explanation=(
                f"Eliminated immediate left recursion on {nonterminal} by introducing new "
                f"nonterminal {new_prime_nt}."
            ),
        )
    )

    return new_a_prods, new_prime_prods, steps


def eliminate_left_recursion(
    grammar: Grammar,
) -> tuple[Grammar, list[TransformStep]]:
    """Algorithm 4.19: Eliminating left recursion (indirect and immediate)."""
    nts = list(grammar.nonterminals)
    existing_nts = set(nts)
    steps: list[TransformStep] = []
    step_counter = [0]

    # Current productions grouped by LHS
    prod_map: dict[str, list[Production]] = {
        nt: grammar.productions_for(nt) for nt in nts
    }

    new_prime_prods_all: list[Production] = []

    for i in range(len(nts)):
        ai = nts[i]
        # Inner loop: substitute previous nonterminals Aj into Ai
        for j in range(i):
            aj = nts[j]
            current_ai_prods = prod_map[ai]
            new_ai_prods: list[Production] = []
            substituted = False

            for p in current_ai_prods:
                rhs = p.normalized_rhs()
                if rhs and rhs[0] == aj:
                    substituted = True
                    gamma = rhs[1:]
                    # Replace with delta gamma for each Aj -> delta
                    for aj_p in prod_map[aj]:
                        delta = aj_p.normalized_rhs()
                        new_rhs = delta + gamma
                        new_ai_prods.append(Production(id=0, lhs=ai, rhs=new_rhs))
                else:
                    new_ai_prods.append(p)

            if substituted:
                step_counter[0] += 1
                steps.append(
                    TransformStep(
                        step_number=step_counter[0],
                        transformation="indirect_substitute",
                        nonterminal=ai,
                        before_productions=[str(p) for p in current_ai_prods],
                        after_productions=[str(p) for p in new_ai_prods],
                        explanation=f"Substituted {aj} productions into leading positions of {ai}.",
                    )
                )
                prod_map[ai] = new_ai_prods

        # Eliminate immediate left recursion on Ai
        temp_grammar = Grammar(start_symbol=grammar.start_symbol, productions=prod_map[ai])
        new_ai, new_primes, imm_steps = eliminate_immediate_left_recursion(
            temp_grammar, ai, existing_nts, step_counter
        )
        prod_map[ai] = new_ai
        new_prime_prods_all.extend(new_primes)
        steps.extend(imm_steps)

    # Reconstruct grammar with re-indexed production ids
    all_final_prods: list[Production] = []
    pid = 0
    for nt in nts:
        for p in prod_map[nt]:
            all_final_prods.append(Production(id=pid, lhs=p.lhs, rhs=p.rhs))
            pid += 1

    for p in new_prime_prods_all:
        all_final_prods.append(Production(id=pid, lhs=p.lhs, rhs=p.rhs))
        pid += 1

    new_grammar = Grammar(start_symbol=grammar.start_symbol, productions=all_final_prods)
    return new_grammar, steps


def left_factor(grammar: Grammar) -> tuple[Grammar, list[TransformStep]]:
    """Algorithm 4.22: Left factoring.

    Finds nonterminals with alternatives sharing a common prefix and factors them.
    Repeats until no two alternatives share a common prefix.
    """
    existing_nts = set(grammar.nonterminals)
    steps: list[TransformStep] = []
    step_counter = [0]

    # Map LHS -> list of RHS tuples
    prod_map: dict[str, list[tuple[str, ...]]] = {}
    for p in grammar.productions:
        prod_map.setdefault(p.lhs, []).append(p.normalized_rhs())

    changed = True
    while changed:
        changed = False
        current_nts = list(prod_map.keys())

        for nt in current_nts:
            rhss = prod_map[nt]
            if len(rhss) < 2:
                continue

            # Find longest common prefix between any pair of RHSs
            best_prefix: tuple[str, ...] = ()
            for i in range(len(rhss)):
                for j in range(i + 1, len(rhss)):
                    # Compute common prefix of rhss[i] and rhss[j]
                    pfx: list[str] = []
                    for k in range(min(len(rhss[i]), len(rhss[j]))):
                        if rhss[i][k] == rhss[j][k]:
                            pfx.append(rhss[i][k])
                        else:
                            break
                    if len(pfx) > len(best_prefix):
                        best_prefix = tuple(pfx)

            if best_prefix:
                # Group alternatives by whether they start with best_prefix
                matching: list[tuple[str, ...]] = []
                non_matching: list[tuple[str, ...]] = []
                pfx_len = len(best_prefix)

                for r in rhss:
                    if len(r) >= pfx_len and r[:pfx_len] == best_prefix:
                        matching.append(r[pfx_len:])
                    else:
                        non_matching.append(r)

                if len(matching) >= 2:
                    changed = True
                    new_prime_nt = _get_unique_prime(nt, existing_nts)

                    # Replace matching alternatives in nt with best_prefix + (new_prime_nt,)
                    new_nt_rhss = non_matching + [best_prefix + (new_prime_nt,)]
                    prod_map[nt] = new_nt_rhss

                    # new_prime_nt gets the remaining suffixes
                    prod_map[new_prime_nt] = matching

                    step_counter[0] += 1
                    pfx_str = " ".join(best_prefix)
                    steps.append(
                        TransformStep(
                            step_number=step_counter[0],
                            transformation="left_factoring",
                            nonterminal=nt,
                            before_productions=[f"{nt} -> {' '.join(r) if r else EPSILON}" for r in rhss],
                            after_productions=[
                                f"{nt} -> {' '.join(r) if r else EPSILON}" for r in new_nt_rhss
                            ]
                            + [
                                f"{new_prime_nt} -> {' '.join(r) if r else EPSILON}"
                                for r in matching
                            ],
                            explanation=f"Factored out common prefix '{pfx_str}' from {nt} into {new_prime_nt}.",
                        )
                    )
                    break

    # Reconstruct Grammar
    final_prods: list[Production] = []
    pid = 0
    for nt, rhss in prod_map.items():
        for r in rhss:
            final_prods.append(Production(id=pid, lhs=nt, rhs=r))
            pid += 1

    return Grammar(start_symbol=grammar.start_symbol, productions=final_prods), steps
