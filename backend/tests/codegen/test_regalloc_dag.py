"""Tests for Register Allocation, DAG Code Generation, and Peephole Optimization (M7-T2).

Verifies:
- AC-C3: Register snapshots never show two live variables in one register.
- AC-C4: Functions with > 8 simultaneously live values show spills (regpressure.vela).
- Temporary to location mapping (t -> R / stack).
- AC-C5: DAG-order cost <= TAC-order cost using Ershov optimal numbering.
- Peephole optimization patterns (redundant loads, self moves, redundant jumps).
"""

from pathlib import Path

from vela.ast.dag import build_expression_dag
from vela.codegen.dag_codegen import DAGCodeGenerator, compute_ershov_numbers
from vela.codegen.isa import (
    MemoryRef,
    Register,
    TargetInstruction,
    TargetProgram,
)
from vela.codegen.peephole import optimize_peephole
from vela.codegen.regalloc import RegisterAllocator
from vela.codegen.selector import InstructionSelector
from vela.ir.generator import TACGenerator
from vela.semantic.checker import check_source

PROGRAMS_DIR = Path(__file__).resolve().parent.parent / "programs" / "valid"


def _compile_to_target(code: str, name: str = "test.vela") -> TargetProgram:
    res = check_source(code, name)
    assert not [d for d in res.diagnostics if d.severity == "error"]
    assert res.ast is not None
    tac = TACGenerator().generate(res.ast)
    return InstructionSelector().select(tac)


def test_register_allocation_ac_c3_no_two_live_variables_in_one_reg() -> None:
    """Verify AC-C3: Register snapshots never show two live variables in one register."""
    code = """
    func main() {
        let x: int = 10;
        let y: int = 20;
        let z: int = x + y;
        show z;
    }
    """
    target = _compile_to_target(code)
    alloc_res = RegisterAllocator().allocate(target)

    assert len(alloc_res.snapshots) > 0
    # In every snapshot, each register holds at most 1 active variable
    for snap in alloc_res.snapshots:
        for reg_name, vars_held in snap.register_descriptors.items():
            assert len(vars_held) <= 1, f"Register {reg_name} holds multiple variables: {vars_held}"


def test_register_allocation_ac_c4_spills_under_high_pressure() -> None:
    """Verify AC-C4: Functions with > 8 live variables show register spills."""
    regpressure_path = PROGRAMS_DIR / "regpressure.vela"
    code = regpressure_path.read_text(encoding="utf-8")
    target = _compile_to_target(code, "regpressure.vela")

    alloc_res = RegisterAllocator().allocate(target)

    # 10 simultaneously live variables on 8 registers must produce at least 1 spill
    assert alloc_res.spills_count > 0, f"Expected spills, got {alloc_res.spills_count}"
    assert alloc_res.max_registers_used == 8

    # Spilled variables must have stack locations [FP - offset]
    assert any("[" in loc for loc in alloc_res.temp_to_location.values())

    # Snapshot serialization
    d = alloc_res.to_dict()
    assert d["spills_count"] > 0
    assert d["max_registers_used"] == 8
    assert len(d["snapshots"]) > 0


def test_dag_based_code_generation_ac_c5() -> None:
    """Verify AC-C5: DAG-order cost <= linear-order cost using Ershov optimal ordering."""
    code = """
    func main() {
        let a: int = 1;
        let b: int = 2;
        let c: int = 3;
        let d: int = 4;
        let e: int = 5;
        let x: int = ((a + b) * c) + (d * e);
        show x;
    }
    """
    res = check_source(code)
    assert res.ast is not None
    from vela.ast.nodes import FuncDecl, VarDecl

    func = next(it for it in res.ast.items if isinstance(it, FuncDecl))
    decl = next(st for st in func.body.statements if isinstance(st, VarDecl) and st.name == "x")
    assert decl.init is not None
    dag = build_expression_dag([decl.init])
    ershov = compute_ershov_numbers(dag)
    assert len(ershov) == len(dag.nodes)

    result = DAGCodeGenerator(dag).generate()

    # AC-C5: DAG-order cost <= linear-order cost
    assert result.dag_cost <= result.linear_cost
    assert result.dag_registers_needed <= result.linear_registers_needed

    d = result.to_dict()
    assert "dag_cost" in d
    assert "linear_cost" in d
    assert "dag_registers_needed" in d


def test_peephole_optimization() -> None:
    """Verify machine-dependent peephole optimization patterns."""
    r1 = Register("R1")
    r2 = Register("R2")
    m = MemoryRef(symbol="x")

    prog = TargetProgram(
        instructions=[
            # Self-move (should be eliminated)
            TargetInstruction("MOV", dst=r1, src1=r1, cost=1),
            # Redundant load after store (load should be eliminated)
            TargetInstruction("STORE", dst=m, src1=r1, cost=2),
            TargetInstruction("LOAD", dst=r1, src1=m, cost=2),
            # Redundant jump to next label
            TargetInstruction("JMP", dst="L1", cost=1),
            TargetInstruction("LABEL", dst="L1", cost=0),
            # Inverse moves (second move should be eliminated)
            TargetInstruction("MOV", dst=r1, src1=r2, cost=1),
            TargetInstruction("MOV", dst=r2, src1=r1, cost=1),
        ]
    )

    result = optimize_peephole(prog)

    assert result.cost_saved > 0
    assert result.cost_after < result.cost_before
    assert len(result.changes) >= 4

    patterns = {c.pattern_name for c in result.changes}
    assert "Redundant Move Elimination" in patterns
    assert "Redundant Load Elimination" in patterns
    assert "Redundant Jump Elimination" in patterns
    assert "Inverse Move Elimination" in patterns
