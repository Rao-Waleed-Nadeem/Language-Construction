"""Generic Data-Flow Analysis Framework and Canonical Analyses.

Defined per:
- docs/10_CODE_OPTIMIZATION.md §4
- Dragon Book (Aho, Lam, Sethi, Ullman) §9.2 - §9.3
- Master Spec P6-10
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from vela.ir.tac import TACInstruction, Temporary, Variable
from vela.opt.cfg import ControlFlowGraph


class Direction(Enum):
    FORWARD = "FORWARD"
    BACKWARD = "BACKWARD"


class MeetOperator(Enum):
    UNION = "UNION"
    INTERSECTION = "INTERSECTION"


def get_var_name(op: Any) -> str | None:
    """Extract string variable/temporary identifier if operand is a variable."""
    if isinstance(op, (Variable, Temporary)):
        return str(op)
    return None


def get_def_var(instr: TACInstruction) -> str | None:
    """Return the variable defined by an instruction, if any."""
    op = instr.opcode
    if op in (
        "ASSIGN",
        "ADD",
        "SUB",
        "MUL",
        "DIV",
        "MOD",
        "NEG",
        "NOT",
        "CAST",
        "ALLOC_ARRAY",
        "ARRAY_GET",
        "RECEIVE",
    ):
        return get_var_name(instr.result)
    if op == "READ":
        return get_var_name(instr.result)
    if op == "CALL" and instr.result is not None:
        return get_var_name(instr.result)
    return None


def get_use_vars(instr: TACInstruction) -> list[str]:
    """Return all variables read by an instruction."""
    op = instr.opcode
    uses: list[str] = []

    if op in ("ASSIGN", "NEG", "NOT", "CAST", "PARAM", "SHOW"):
        v = get_var_name(instr.arg1)
        if v:
            uses.append(v)
    elif op in ("ADD", "SUB", "MUL", "DIV", "MOD", "LT", "LE", "GT", "GE", "EQ", "NE"):
        v1 = get_var_name(instr.arg1)
        v2 = get_var_name(instr.arg2)
        if v1:
            uses.append(v1)
        if v2:
            uses.append(v2)
    elif op in ("JUMP_IF", "JUMP_IF_FALSE") or (op == "RETURN" and instr.arg1 is not None):
        v = get_var_name(instr.arg1)
        if v:
            uses.append(v)
    elif op == "ARRAY_GET":
        v1 = get_var_name(instr.arg1)
        v2 = get_var_name(instr.arg2)
        if v1:
            uses.append(v1)
        if v2:
            uses.append(v2)
    elif op == "ARRAY_SET":
        v1 = get_var_name(instr.arg1)
        v2 = get_var_name(instr.arg2)
        vres = get_var_name(instr.result)
        if v1:
            uses.append(v1)
        if v2:
            uses.append(v2)
        if vres:
            uses.append(vres)
    elif op == "ALLOC_ARRAY":
        v1 = get_var_name(instr.arg1)
        v2 = get_var_name(instr.arg2)
        if v1:
            uses.append(v1)
        if v2:
            uses.append(v2)

    return uses


# ---------------------------------------------------------------------------
# Representations of Data-Flow Items
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Definition:
    """A variable definition at a specific instruction index in a block."""

    var_name: str
    block_id: int
    instr_index: int

    def __str__(self) -> str:
        return f"{self.var_name}@(B{self.block_id}:{self.instr_index})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "var_name": self.var_name,
            "block_id": self.block_id,
            "instr_index": self.instr_index,
            "text": str(self),
        }


@dataclass(frozen=True)
class ExprItem:
    """A binary or unary expression candidate for available expressions."""

    opcode: str
    arg1: str
    arg2: str | None = None

    def __str__(self) -> str:
        if self.arg2 is not None:
            return f"{self.arg1} {self.opcode} {self.arg2}"
        return f"{self.opcode} {self.arg1}"

    def to_dict(self) -> dict[str, Any]:
        return {"opcode": self.opcode, "arg1": self.arg1, "arg2": self.arg2, "text": str(self)}


@dataclass(frozen=True)
class CopyItem:
    """A copy statement x = y candidate for copy propagation."""

    dest: str
    src: str

    def __str__(self) -> str:
        return f"{self.dest} = {self.src}"

    def to_dict(self) -> dict[str, Any]:
        return {"dest": self.dest, "src": self.src, "text": str(self)}


# ---------------------------------------------------------------------------
# Framework Iteration Log and Result
# ---------------------------------------------------------------------------


@dataclass
class IterationLog:
    """Snapshot of IN and OUT sets across all blocks during one solver iteration."""

    iteration: int
    in_sets: dict[int, list[str]]
    out_sets: dict[int, list[str]]
    changed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "in_sets": {str(k): sorted(v) for k, v in self.in_sets.items()},
            "out_sets": {str(k): sorted(v) for k, v in self.out_sets.items()},
            "changed": self.changed,
        }


@dataclass
class DataFlowResult:
    """Complete results of a solved data-flow problem."""

    name: str
    direction: str
    meet: str
    universe: set[Any]
    gen: dict[int, set[Any]]
    kill: dict[int, set[Any]]
    in_sets: dict[int, set[Any]]
    out_sets: dict[int, set[Any]]
    iterations: list[IterationLog] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "direction": self.direction,
            "meet": self.meet,
            "universe_size": len(self.universe),
            "iterations_count": len(self.iterations),
            "gen": {str(k): [str(x) for x in sorted(v, key=str)] for k, v in self.gen.items()},
            "kill": {str(k): [str(x) for x in sorted(v, key=str)] for k, v in self.kill.items()},
            "in_sets": {str(k): [str(x) for x in sorted(v, key=str)] for k, v in self.in_sets.items()},
            "out_sets": {str(k): [str(x) for x in sorted(v, key=str)] for k, v in self.out_sets.items()},
            "iterations": [log.to_dict() for log in self.iterations],
        }


# ---------------------------------------------------------------------------
# Canonical Solvers
# ---------------------------------------------------------------------------


def solve_reaching_definitions(cfg: ControlFlowGraph) -> DataFlowResult:
    """Compute reaching definitions across all basic blocks (Dragon Book §9.2.4).

    Direction: Forward
    Meet: Union
    GEN[B]: definitions in B not killed within B
    KILL[B]: all other definitions of variables defined in B
    """
    # 1. Identify all definitions in the program
    universe: set[Definition] = set()
    block_defs: dict[int, list[Definition]] = {}

    for bid, block in cfg.blocks.items():
        block_defs[bid] = []
        for idx, instr in enumerate(block.instructions):
            v = get_def_var(instr)
            if v:
                d = Definition(var_name=v, block_id=bid, instr_index=idx)
                universe.add(d)
                block_defs[bid].append(d)

    # 2. Compute GEN and KILL per block
    gen: dict[int, set[Definition]] = {}
    kill: dict[int, set[Definition]] = {}

    for bid, block in cfg.blocks.items():
        b_gen: set[Definition] = set()
        b_kill: set[Definition] = set()
        assigned_vars: set[str] = set()

        for d in block_defs[bid]:
            # Later def kills earlier def of same var in same block
            b_gen = {x for x in b_gen if x.var_name != d.var_name}
            b_gen.add(d)
            assigned_vars.add(d.var_name)

        # KILL[B] is all definitions in universe of variables defined in B, except those generated in B
        for d in universe:
            if d.var_name in assigned_vars and d not in b_gen:
                b_kill.add(d)

        gen[bid] = b_gen
        kill[bid] = b_kill

    # 3. Solve forward iterative data-flow
    # Boundary: OUT[ENTRY] = empty
    in_sets: dict[int, set[Definition]] = {bid: set() for bid in cfg.blocks}
    out_sets: dict[int, set[Definition]] = {bid: set() for bid in cfg.blocks}

    iterations: list[IterationLog] = []
    iter_num = 0
    changed = True

    while changed:
        iter_num += 1
        changed = False

        for bid in sorted(cfg.blocks.keys()):
            preds = cfg.get_predecessors(bid)
            # Meet: Union over predecessors (ENTRY has out_set = empty)
            new_in: set[Definition] = set()
            for p in preds:
                if p in out_sets:
                    new_in |= out_sets[p]

            in_sets[bid] = new_in

            # Transfer: OUT[B] = GEN[B] U (IN[B] - KILL[B])
            new_out = gen[bid] | (in_sets[bid] - kill[bid])
            if new_out != out_sets[bid]:
                out_sets[bid] = new_out
                changed = True

        iterations.append(
            IterationLog(
                iteration=iter_num,
                in_sets={b: [str(x) for x in in_sets[b]] for b in cfg.blocks},
                out_sets={b: [str(x) for x in out_sets[b]] for b in cfg.blocks},
                changed=changed,
            )
        )

    return DataFlowResult(
        name="Reaching Definitions",
        direction="FORWARD",
        meet="UNION",
        universe=universe,
        gen=gen,
        kill=kill,
        in_sets=in_sets,
        out_sets=out_sets,
        iterations=iterations,
    )


def solve_live_variables(cfg: ControlFlowGraph) -> DataFlowResult:
    """Compute live variables across all basic blocks (Dragon Book §9.2.5).

    Direction: Backward
    Meet: Union
    DEF[B]: variables defined in B before any use in B
    USE[B]: variables used in B before any definition in B
    IN[B] = USE[B] U (OUT[B] - DEF[B])
    """
    # 1. Identify all variables and temporaries in the program
    universe: set[str] = set()
    def_sets: dict[int, set[str]] = {}
    use_sets: dict[int, set[str]] = {}

    for bid, block in cfg.blocks.items():
        b_def: set[str] = set()
        b_use: set[str] = set()

        for instr in block.instructions:
            # Uses in this instruction
            for u in get_use_vars(instr):
                universe.add(u)
                if u not in b_def:
                    b_use.add(u)

            # Defs in this instruction
            d = get_def_var(instr)
            if d:
                universe.add(d)
                b_def.add(d)

        def_sets[bid] = b_def
        use_sets[bid] = b_use

    # 2. Solve backward iterative data-flow
    # Boundary: IN[EXIT] = empty
    in_sets: dict[int, set[str]] = {bid: set() for bid in cfg.blocks}
    out_sets: dict[int, set[str]] = {bid: set() for bid in cfg.blocks}

    iterations: list[IterationLog] = []
    iter_num = 0
    changed = True

    while changed:
        iter_num += 1
        changed = False

        for bid in sorted(cfg.blocks.keys(), reverse=True):
            succs = cfg.get_successors(bid)
            # Meet: Union over successors (EXIT has in_set = empty)
            new_out: set[str] = set()
            for s in succs:
                if s in in_sets:
                    new_out |= in_sets[s]

            out_sets[bid] = new_out

            # Transfer: IN[B] = USE[B] U (OUT[B] - DEF[B])
            new_in = use_sets[bid] | (out_sets[bid] - def_sets[bid])
            if new_in != in_sets[bid]:
                in_sets[bid] = new_in
                changed = True

        iterations.append(
            IterationLog(
                iteration=iter_num,
                in_sets={b: sorted(in_sets[b]) for b in cfg.blocks},
                out_sets={b: sorted(out_sets[b]) for b in cfg.blocks},
                changed=changed,
            )
        )

    return DataFlowResult(
        name="Live Variables",
        direction="BACKWARD",
        meet="UNION",
        universe=universe,
        gen=use_sets,  # In liveness, USE acts as GEN
        kill=def_sets,  # In liveness, DEF acts as KILL
        in_sets=in_sets,
        out_sets=out_sets,
        iterations=iterations,
    )


def solve_available_expressions(cfg: ControlFlowGraph) -> DataFlowResult:
    """Compute available expressions across all basic blocks (Dragon Book §9.2.6).

    Direction: Forward
    Meet: Intersection
    GEN[B]: expressions computed in B whose operands are not killed after computation
    KILL[B]: all expressions in universe whose operands are redefined in B
    """
    # 1. Collect all binary/unary expressions in universe
    universe: set[ExprItem] = set()
    binary_ops = {"ADD", "SUB", "MUL", "DIV", "MOD"}

    for block in cfg.blocks.values():
        for instr in block.instructions:
            if instr.opcode in binary_ops and instr.arg1 is not None and instr.arg2 is not None:
                a1 = str(instr.arg1)
                a2 = str(instr.arg2)
                universe.add(ExprItem(opcode=instr.opcode, arg1=a1, arg2=a2))
            elif instr.opcode in ("NEG", "NOT") and instr.arg1 is not None:
                universe.add(ExprItem(opcode=instr.opcode, arg1=str(instr.arg1), arg2=None))

    # 2. Compute GEN and KILL per block
    gen: dict[int, set[ExprItem]] = {}
    kill: dict[int, set[ExprItem]] = {}

    for bid, block in cfg.blocks.items():
        b_gen: set[ExprItem] = set()
        killed_vars: set[str] = set()

        for instr in block.instructions:
            # Check if instruction evaluates an expression
            if instr.opcode in binary_ops and instr.arg1 is not None and instr.arg2 is not None:
                item = ExprItem(opcode=instr.opcode, arg1=str(instr.arg1), arg2=str(instr.arg2))
                b_gen.add(item)
            elif instr.opcode in ("NEG", "NOT") and instr.arg1 is not None:
                item = ExprItem(opcode=instr.opcode, arg1=str(instr.arg1), arg2=None)
                b_gen.add(item)

            # Check if instruction redefines any operand
            d = get_def_var(instr)
            if d:
                killed_vars.add(d)
                # Remove expressions from b_gen if operand is overwritten
                b_gen = {e for e in b_gen if e.arg1 != d and e.arg2 != d}

        # KILL[B] contains any expression in universe that uses any killed variable
        b_kill: set[ExprItem] = set()
        for e in universe:
            if e.arg1 in killed_vars or (e.arg2 is not None and e.arg2 in killed_vars):
                b_kill.add(e)

        gen[bid] = b_gen
        kill[bid] = b_kill

    # 3. Solve forward iterative data-flow with intersection
    # Boundary: OUT[ENTRY] = empty
    # Initial: OUT[B] = Universal set for all B != ENTRY
    first_bid = cfg.blocks[min(cfg.blocks.keys())].id if cfg.blocks else 1
    in_sets: dict[int, set[ExprItem]] = {bid: set(universe) for bid in cfg.blocks}
    out_sets: dict[int, set[ExprItem]] = {bid: set(universe) for bid in cfg.blocks}

    # For entry block(s), IN starts empty
    in_sets[first_bid] = set()
    out_sets[first_bid] = gen[first_bid] | (in_sets[first_bid] - kill[first_bid])

    iterations: list[IterationLog] = []
    iter_num = 0
    changed = True

    while changed:
        iter_num += 1
        changed = False

        for bid in sorted(cfg.blocks.keys()):
            if bid == first_bid:
                continue

            preds = [p for p in cfg.get_predecessors(bid) if p in out_sets]
            if not preds:
                new_in = set()
            else:
                new_in = set(out_sets[preds[0]])
                for p in preds[1:]:
                    new_in &= out_sets[p]

            in_sets[bid] = new_in
            new_out = gen[bid] | (in_sets[bid] - kill[bid])
            if new_out != out_sets[bid]:
                out_sets[bid] = new_out
                changed = True

        iterations.append(
            IterationLog(
                iteration=iter_num,
                in_sets={b: [str(x) for x in in_sets[b]] for b in cfg.blocks},
                out_sets={b: [str(x) for x in out_sets[b]] for b in cfg.blocks},
                changed=changed,
            )
        )

    return DataFlowResult(
        name="Available Expressions",
        direction="FORWARD",
        meet="INTERSECTION",
        universe=universe,
        gen=gen,
        kill=kill,
        in_sets=in_sets,
        out_sets=out_sets,
        iterations=iterations,
    )


def solve_available_copies(cfg: ControlFlowGraph) -> DataFlowResult:
    """Compute available copies across all basic blocks (Dragon Book §9.4.4).

    Direction: Forward
    Meet: Intersection
    GEN[B]: copy statements x = y generated in B where neither x nor y is subsequently defined in B
    KILL[B]: copy statements in universe where either x or y is defined in B
    """
    # 1. Collect all copy statements in universe
    universe: set[CopyItem] = set()
    for block in cfg.blocks.values():
        for instr in block.instructions:
            if instr.opcode == "ASSIGN" and isinstance(instr.result, (Variable, Temporary)):
                src_var = get_var_name(instr.arg1)
                dest_var = get_var_name(instr.result)
                if src_var and dest_var and src_var != dest_var:
                    universe.add(CopyItem(dest=dest_var, src=src_var))

    # 2. Compute GEN and KILL per block
    gen: dict[int, set[CopyItem]] = {}
    kill: dict[int, set[CopyItem]] = {}

    for bid, block in cfg.blocks.items():
        b_gen: set[CopyItem] = set()
        killed_vars: set[str] = set()

        for instr in block.instructions:
            d = get_def_var(instr)
            if d:
                killed_vars.add(d)
                # Overwriting d kills any copy involving d
                b_gen = {c for c in b_gen if c.dest != d and c.src != d}

            if instr.opcode == "ASSIGN" and isinstance(instr.result, (Variable, Temporary)):
                src_var = get_var_name(instr.arg1)
                dest_var = get_var_name(instr.result)
                if src_var and dest_var and src_var != dest_var:
                    b_gen.add(CopyItem(dest=dest_var, src=src_var))

        # KILL[B] contains any copy where dest or src is in killed_vars, minus what's generated in B
        b_kill: set[CopyItem] = set()
        for c in universe:
            if (c.dest in killed_vars or c.src in killed_vars) and c not in b_gen:
                b_kill.add(c)

        gen[bid] = b_gen
        kill[bid] = b_kill

    # 3. Solve forward iterative data-flow with intersection
    first_bid = cfg.blocks[min(cfg.blocks.keys())].id if cfg.blocks else 1
    in_sets: dict[int, set[CopyItem]] = {bid: set(universe) for bid in cfg.blocks}
    out_sets: dict[int, set[CopyItem]] = {bid: set(universe) for bid in cfg.blocks}

    in_sets[first_bid] = set()
    out_sets[first_bid] = gen[first_bid] | (in_sets[first_bid] - kill[first_bid])

    iterations: list[IterationLog] = []
    iter_num = 0
    changed = True

    while changed:
        iter_num += 1
        changed = False

        for bid in sorted(cfg.blocks.keys()):
            if bid == first_bid:
                continue

            preds = [p for p in cfg.get_predecessors(bid) if p in out_sets]
            if not preds:
                new_in = set()
            else:
                new_in = set(out_sets[preds[0]])
                for p in preds[1:]:
                    new_in &= out_sets[p]

            in_sets[bid] = new_in
            new_out = gen[bid] | (in_sets[bid] - kill[bid])
            if new_out != out_sets[bid]:
                out_sets[bid] = new_out
                changed = True

        iterations.append(
            IterationLog(
                iteration=iter_num,
                in_sets={b: [str(x) for x in in_sets[b]] for b in cfg.blocks},
                out_sets={b: [str(x) for x in out_sets[b]] for b in cfg.blocks},
                changed=changed,
            )
        )

    return DataFlowResult(
        name="Available Copies",
        direction="FORWARD",
        meet="INTERSECTION",
        universe=universe,
        gen=gen,
        kill=kill,
        in_sets=in_sets,
        out_sets=out_sets,
        iterations=iterations,
    )
