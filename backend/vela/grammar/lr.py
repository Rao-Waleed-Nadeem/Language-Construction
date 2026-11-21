"""LR Automata, Parsing Tables, and Conflict Resolution for LR(0), SLR(1), CLR(1), LALR(1).

Per doc 01 §13.4, doc 02 §7, doc 06 §4 and textbook (Dragon Book §4.5, §4.7):
- LR(0) and LR(1) items and closures
- Canonical collection of item sets with 5000-state limit
- Action and Goto table construction
- Conflict detection (Shift/Reduce, Reduce/Reduce)
- Precedence and associativity conflict resolution
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from vela.grammar.analysis import GrammarAnalysis
from vela.grammar.model import EPSILON, Grammar, Production


class LRType(str, Enum):
    LR0 = "LR(0)"
    SLR1 = "SLR(1)"
    CLR1 = "CLR(1)"
    LALR1 = "LALR(1)"


@dataclass(frozen=True)
class LR0Item:
    prod_id: int
    dot: int


@dataclass(frozen=True)
class LR1Item:
    prod_id: int
    dot: int
    lookahead: str

    @property
    def core(self) -> LR0Item:
        return LR0Item(self.prod_id, self.dot)


@dataclass
class LRConflict:
    state_id: int
    symbol: str
    conflict_type: str  # 'shift/reduce' or 'reduce/reduce'
    actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "state_id": self.state_id,
            "symbol": self.symbol,
            "conflict_type": self.conflict_type,
            "actions": self.actions,
        }


@dataclass
class LRTable:
    lr_type: LRType
    states_count: int
    action: dict[tuple[int, str], list[str]]  # (state, term) -> list of 'sX', 'rY', 'acc'
    goto: dict[tuple[int, str], int]  # (state, nt) -> next_state
    conflicts: list[LRConflict]
    limit_reached: bool
    productions: list[Production]
    terminals: list[str]
    nonterminals: list[str]
    augmented_start: str

    @property
    def is_conflict_free(self) -> bool:
        return len(self.conflicts) == 0

    def to_dict(self) -> dict[str, Any]:
        entries: list[dict[str, Any]] = []
        for (st, sym), acts in self.action.items():
            if acts:
                entries.append({"state": st, "symbol": sym, "type": "action", "actions": acts})
        for (st, sym), target in self.goto.items():
            entries.append(
                {"state": st, "symbol": sym, "type": "goto", "target": target}
            )

        return {
            "lr_type": self.lr_type.value,
            "states_count": self.states_count,
            "is_conflict_free": self.is_conflict_free,
            "conflict_count": len(self.conflicts),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "limit_reached": self.limit_reached,
            "entries_count": len(entries),
        }


class LRBuilder:
    """Builds LR(0), SLR(1), CLR(1), and LALR(1) tables."""

    EOF = "$"
    MAX_STATES = 5000

    def __init__(
        self,
        grammar: Grammar,
        analysis: GrammarAnalysis | None = None,
        precedence: dict[str, tuple[str, int]] | None = None,
    ) -> None:
        self.raw_grammar: Grammar = grammar
        self.precedence: dict[str, tuple[str, int]] = precedence or {}

        # 1. Augment grammar: S' -> S as production 0
        self.augmented_start = f"{grammar.start_symbol}'"
        while self.augmented_start in grammar.nonterminals:
            self.augmented_start += "'"

        aug_prod0 = Production(id=0, lhs=self.augmented_start, rhs=(grammar.start_symbol,))
        all_prods = [aug_prod0]
        for p in grammar.productions:
            all_prods.append(Production(id=len(all_prods), lhs=p.lhs, rhs=p.rhs))

        self.grammar = Grammar(start_symbol=self.augmented_start, productions=all_prods)
        self.analysis = analysis or GrammarAnalysis(self.grammar)

        self.prods_by_lhs: dict[str, list[Production]] = {}
        for p in self.grammar.productions:
            self.prods_by_lhs.setdefault(p.lhs, []).append(p)

    def _prod_precedence(self, prod: Production) -> tuple[str, int] | None:
        # Precedence of production is the precedence of its rightmost terminal
        rhs = prod.normalized_rhs()
        for sym in reversed(rhs):
            if sym in self.precedence:
                return self.precedence[sym]
        return None

    # ---- LR(0) Collection ----
    def _lr0_closure(self, items: frozenset[LR0Item]) -> frozenset[LR0Item]:
        closure = set(items)
        changed = True
        while changed:
            changed = False
            new_items: list[LR0Item] = []
            for item in closure:
                prod = self.grammar.productions[item.prod_id]
                rhs = prod.normalized_rhs()
                if item.dot < len(rhs):
                    B = rhs[item.dot]
                    if self.grammar.is_nonterminal(B):
                        for p in self.prods_by_lhs.get(B, []):
                            new_item = LR0Item(p.id, 0)
                            if new_item not in closure:
                                new_items.append(new_item)
            if new_items:
                closure.update(new_items)
                changed = True
        return frozenset(closure)

    def _lr0_goto(self, items: frozenset[LR0Item], symbol: str) -> frozenset[LR0Item]:
        moved: set[LR0Item] = set()
        for item in items:
            prod = self.grammar.productions[item.prod_id]
            rhs = prod.normalized_rhs()
            if item.dot < len(rhs) and rhs[item.dot] == symbol:
                moved.add(LR0Item(item.prod_id, item.dot + 1))
        return self._lr0_closure(frozenset(moved))

    def _build_lr0_collection(
        self,
    ) -> tuple[list[frozenset[LR0Item]], dict[tuple[int, str], int], bool]:
        init_item = LR0Item(0, 0)
        I0 = self._lr0_closure(frozenset([init_item]))
        C = [I0]
        state_map = {I0: 0}
        goto_map: dict[tuple[int, str], int] = {}

        symbols = self.grammar.nonterminals + self.grammar.terminals
        idx = 0
        limit_reached = False

        while idx < len(C):
            if len(C) >= self.MAX_STATES:
                limit_reached = True
                break
            I = C[idx]
            for X in symbols:
                if X == self.augmented_start:
                    continue
                goto_I_X = self._lr0_goto(I, X)
                if goto_I_X:
                    if goto_I_X not in state_map:
                        if len(C) >= self.MAX_STATES:
                            limit_reached = True
                            break
                        state_map[goto_I_X] = len(C)
                        C.append(goto_I_X)
                    goto_map[(idx, X)] = state_map[goto_I_X]
            idx += 1

        return C, goto_map, limit_reached

    # ---- LR(1) Collection ----
    def _lr1_closure(self, items: frozenset[LR1Item]) -> frozenset[LR1Item]:
        closure: dict[tuple[int, int], set[str]] = {}
        for it in items:
            closure.setdefault((it.prod_id, it.dot), set()).add(it.lookahead)

        changed = True
        while changed:
            changed = False
            additions: dict[tuple[int, int], set[str]] = {}
            for (prod_id, dot), lookaheads in list(closure.items()):
                prod = self.grammar.productions[prod_id]
                rhs = prod.normalized_rhs()
                if dot < len(rhs):
                    B = rhs[dot]
                    if self.grammar.is_nonterminal(B):
                        beta = rhs[dot + 1 :]
                        for a in lookaheads:
                            first_beta_a = self.analysis.first_of_sequence(beta + (a,))
                            for b in first_beta_a:
                                if b != EPSILON:
                                    for p in self.prods_by_lhs.get(B, []):
                                        key = (p.id, 0)
                                        current = closure.get(key, set())
                                        if b not in current:
                                            additions.setdefault(key, set()).add(b)

            if additions:
                for k, v in additions.items():
                    if k not in closure:
                        closure[k] = set(v)
                        changed = True
                    else:
                        before = len(closure[k])
                        closure[k].update(v)
                        if len(closure[k]) > before:
                            changed = True

        result: set[LR1Item] = set()
        for (prod_id, dot), lookaheads in closure.items():
            for a in lookaheads:
                result.add(LR1Item(prod_id, dot, a))
        return frozenset(result)

    def _lr1_goto(self, items: frozenset[LR1Item], symbol: str) -> frozenset[LR1Item]:
        moved: set[LR1Item] = set()
        for item in items:
            prod = self.grammar.productions[item.prod_id]
            rhs = prod.normalized_rhs()
            if item.dot < len(rhs) and rhs[item.dot] == symbol:
                moved.add(LR1Item(item.prod_id, item.dot + 1, item.lookahead))
        return self._lr1_closure(frozenset(moved))

    def _build_lr1_collection(
        self,
    ) -> tuple[list[frozenset[LR1Item]], dict[tuple[int, str], int], bool]:
        init_item = LR1Item(0, 0, self.EOF)
        I0 = self._lr1_closure(frozenset([init_item]))
        C = [I0]
        state_map = {I0: 0}
        goto_map: dict[tuple[int, str], int] = {}

        symbols = self.grammar.nonterminals + self.grammar.terminals
        idx = 0
        limit_reached = False

        while idx < len(C):
            if len(C) >= self.MAX_STATES:
                limit_reached = True
                break
            I = C[idx]
            for X in symbols:
                if X == self.augmented_start:
                    continue
                goto_I_X = self._lr1_goto(I, X)
                if goto_I_X:
                    if goto_I_X not in state_map:
                        if len(C) >= self.MAX_STATES:
                            limit_reached = True
                            break
                        state_map[goto_I_X] = len(C)
                        C.append(goto_I_X)
                    goto_map[(idx, X)] = state_map[goto_I_X]
            idx += 1

        return C, goto_map, limit_reached

    # ---- Table Builders ----
    def build_lr0(self) -> LRTable:
        C, goto_map, limit_reached = self._build_lr0_collection()
        action: dict[tuple[int, str], list[str]] = {}
        goto: dict[tuple[int, str], int] = {}
        conflicts: list[LRConflict] = []
        terminals = list(self.grammar.terminals) + [self.EOF]

        for i, I in enumerate(C):
            for a in terminals:
                action[(i, a)] = []

            # Shifts
            for a in self.grammar.terminals:
                if (i, a) in goto_map:
                    action[(i, a)].append(f"s{goto_map[(i, a)]}")

            # Nonterminal Gotos
            for A in self.grammar.nonterminals:
                if (i, A) in goto_map:
                    goto[(i, A)] = goto_map[(i, A)]

            # Reduces
            for item in I:
                prod = self.grammar.productions[item.prod_id]
                rhs = prod.normalized_rhs()
                if item.dot == len(rhs):
                    if item.prod_id == 0:
                        action[(i, self.EOF)].append("acc")
                    else:
                        for a in terminals:
                            action[(i, a)].append(f"r{item.prod_id}")

        self._check_and_resolve_conflicts(action, conflicts)
        return LRTable(
            lr_type=LRType.LR0,
            states_count=len(C),
            action=action,
            goto=goto,
            conflicts=conflicts,
            limit_reached=limit_reached,
            productions=self.grammar.productions,
            terminals=self.grammar.terminals,
            nonterminals=self.grammar.nonterminals,
            augmented_start=self.augmented_start,
        )

    def build_slr1(self) -> LRTable:
        C, goto_map, limit_reached = self._build_lr0_collection()
        action: dict[tuple[int, str], list[str]] = {}
        goto: dict[tuple[int, str], int] = {}
        conflicts: list[LRConflict] = []
        terminals = list(self.grammar.terminals) + [self.EOF]

        for i, I in enumerate(C):
            for a in terminals:
                action[(i, a)] = []

            # Shifts
            for a in self.grammar.terminals:
                if (i, a) in goto_map:
                    action[(i, a)].append(f"s{goto_map[(i, a)]}")

            # Gotos
            for A in self.grammar.nonterminals:
                if (i, A) in goto_map:
                    goto[(i, A)] = goto_map[(i, A)]

            # Reduces restricted to FOLLOW(A)
            for item in I:
                prod = self.grammar.productions[item.prod_id]
                rhs = prod.normalized_rhs()
                if item.dot == len(rhs):
                    if item.prod_id == 0:
                        action[(i, self.EOF)].append("acc")
                    else:
                        follow_A = self.analysis.follow.get(prod.lhs, set())
                        for a in follow_A:
                            action[(i, a)].append(f"r{item.prod_id}")

        self._check_and_resolve_conflicts(action, conflicts)
        return LRTable(
            lr_type=LRType.SLR1,
            states_count=len(C),
            action=action,
            goto=goto,
            conflicts=conflicts,
            limit_reached=limit_reached,
            productions=self.grammar.productions,
            terminals=self.grammar.terminals,
            nonterminals=self.grammar.nonterminals,
            augmented_start=self.augmented_start,
        )

    def build_clr1(self) -> LRTable:
        C, goto_map, limit_reached = self._build_lr1_collection()
        action: dict[tuple[int, str], list[str]] = {}
        goto: dict[tuple[int, str], int] = {}
        conflicts: list[LRConflict] = []
        terminals = list(self.grammar.terminals) + [self.EOF]

        for i, I in enumerate(C):
            for a in terminals:
                action[(i, a)] = []

            # Shifts
            for a in self.grammar.terminals:
                if (i, a) in goto_map:
                    action[(i, a)].append(f"s{goto_map[(i, a)]}")

            # Gotos
            for A in self.grammar.nonterminals:
                if (i, A) in goto_map:
                    goto[(i, A)] = goto_map[(i, A)]

            # Reduces based on item lookahead
            for item in I:
                prod = self.grammar.productions[item.prod_id]
                rhs = prod.normalized_rhs()
                if item.dot == len(rhs):
                    if item.prod_id == 0:
                        if item.lookahead == self.EOF:
                            action[(i, self.EOF)].append("acc")
                    else:
                        action[(i, item.lookahead)].append(f"r{item.prod_id}")

        self._check_and_resolve_conflicts(action, conflicts)
        return LRTable(
            lr_type=LRType.CLR1,
            states_count=len(C),
            action=action,
            goto=goto,
            conflicts=conflicts,
            limit_reached=limit_reached,
            productions=self.grammar.productions,
            terminals=self.grammar.terminals,
            nonterminals=self.grammar.nonterminals,
            augmented_start=self.augmented_start,
        )

    def build_lalr1(self) -> LRTable:
        # Build CLR(1) first, then merge states having identical LR(0) cores
        C, goto_map, limit_reached = self._build_lr1_collection()

        # Compute core for each CLR state
        def state_core(items: frozenset[LR1Item]) -> frozenset[LR0Item]:
            return frozenset(it.core for it in items)

        core_to_merged: dict[frozenset[LR0Item], int] = {}
        clr_to_lalr: dict[int, int] = {}
        merged_states: list[frozenset[LR1Item]] = []

        for i, items in enumerate(C):
            core = state_core(items)
            if core not in core_to_merged:
                new_id = len(merged_states)
                core_to_merged[core] = new_id
                merged_states.append(items)
                clr_to_lalr[i] = new_id
            else:
                target_id = core_to_merged[core]
                clr_to_lalr[i] = target_id
                # Union lookaheads
                merged_states[target_id] = merged_states[target_id].union(items)

        action: dict[tuple[int, str], list[str]] = {}
        goto: dict[tuple[int, str], int] = {}
        conflicts: list[LRConflict] = []
        terminals = list(self.grammar.terminals) + [self.EOF]

        num_lalr = len(merged_states)
        for i in range(num_lalr):
            for a in terminals:
                action[(i, a)] = []

        # Construct Gotos for LALR
        for (clr_state, X), clr_target in goto_map.items():
            lalr_from = clr_to_lalr[clr_state]
            lalr_target = clr_to_lalr[clr_target]
            if X in self.grammar.nonterminals:
                goto[(lalr_from, X)] = lalr_target
            elif X in self.grammar.terminals:
                s_act = f"s{lalr_target}"
                if s_act not in action[(lalr_from, X)]:
                    action[(lalr_from, X)].append(s_act)

        # Construct Reduces for LALR
        for i, items in enumerate(merged_states):
            for item in items:
                prod = self.grammar.productions[item.prod_id]
                rhs = prod.normalized_rhs()
                if item.dot == len(rhs):
                    if item.prod_id == 0:
                        if item.lookahead == self.EOF and "acc" not in action[(i, self.EOF)]:
                            action[(i, self.EOF)].append("acc")
                    else:
                        r_act = f"r{item.prod_id}"
                        if r_act not in action[(i, item.lookahead)]:
                            action[(i, item.lookahead)].append(r_act)

        self._check_and_resolve_conflicts(action, conflicts)
        return LRTable(
            lr_type=LRType.LALR1,
            states_count=num_lalr,
            action=action,
            goto=goto,
            conflicts=conflicts,
            limit_reached=limit_reached,
            productions=self.grammar.productions,
            terminals=self.grammar.terminals,
            nonterminals=self.grammar.nonterminals,
            augmented_start=self.augmented_start,
        )

    def _check_and_resolve_conflicts(
        self,
        action: dict[tuple[int, str], list[str]],
        conflicts: list[LRConflict],
    ) -> None:
        """Identify conflicts in action table and resolve via precedence where applicable."""
        for (st, sym), acts in list(action.items()):
            if len(acts) > 1:
                # Check for S/R conflict resolution using declared precedence
                shifts = [a for a in acts if a.startswith("s")]
                reduces = [a for a in acts if a.startswith("r")]

                resolved_acts: list[str] = list(acts)
                if len(shifts) == 1 and len(reduces) == 1 and sym in self.precedence:
                    shift_act = shifts[0]
                    reduce_act = reduces[0]
                    prod_id = int(reduce_act[1:])
                    prod = self.grammar.productions[prod_id]

                    prod_prec = self._prod_precedence(prod)
                    sym_assoc, sym_prec_val = self.precedence[sym]

                    if prod_prec is not None:
                        _prod_assoc, prod_prec_val = prod_prec
                        if prod_prec_val > sym_prec_val:
                            # Prefer reduce
                            resolved_acts = [reduce_act]
                        elif prod_prec_val < sym_prec_val:
                            # Prefer shift
                            resolved_acts = [shift_act]
                        else:
                            # Equal precedence -> check associativity
                            if sym_assoc == "left":
                                resolved_acts = [reduce_act]
                            elif sym_assoc == "right":
                                resolved_acts = [shift_act]

                action[(st, sym)] = resolved_acts

                if len(resolved_acts) > 1:
                    conf_type = "shift/reduce" if any(a.startswith("s") for a in resolved_acts) else "reduce/reduce"
                    conflicts.append(
                        LRConflict(
                            state_id=st,
                            symbol=sym,
                            conflict_type=conf_type,
                            actions=resolved_acts,
                        )
                    )
