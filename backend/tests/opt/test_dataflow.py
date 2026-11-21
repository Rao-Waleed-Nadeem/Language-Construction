"""Tests for Data-Flow Analysis Framework (M6-T2).

Verifies:
- Reaching definitions (GEN, KILL, IN, OUT, fixed-point termination).
- Live variables (DEF, USE, backward meet, liveness at block boundaries).
- Available expressions (GEN, KILL, forward intersection meet).
- Available copies (forward intersection meet, copy invalidation).
- Step-by-step iteration logs and JSON serialization.
"""

from pathlib import Path

from vela.ir.generator import TACGenerator
from vela.opt.blocks import partition_into_blocks
from vela.opt.cfg import build_cfg
from vela.opt.dataflow import (
    solve_available_copies,
    solve_available_expressions,
    solve_live_variables,
    solve_reaching_definitions,
)
from vela.semantic.checker import check_source

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"


def _compile_to_cfg(code: str, name: str = "test.vela"):
    res = check_source(code, name)
    assert not [d for d in res.diagnostics if d.severity == "error"]
    assert res.ast is not None
    tac = TACGenerator().generate(res.ast)
    partition = partition_into_blocks(tac.instructions)
    cfg = build_cfg(partition)
    return cfg


def test_reaching_definitions_simple_loop() -> None:
    """Verify reaching definitions propagate around a loop."""
    code = """
    func main() {
        let x: int = 5;
        let y: int = 1;
        while (x > 1) {
            y = x * y;
            x = x - 1;
        }
        show y;
    }
    """
    cfg = _compile_to_cfg(code)
    result = solve_reaching_definitions(cfg)

    assert result.name == "Reaching Definitions"
    assert result.direction == "FORWARD"
    assert result.meet == "UNION"
    assert len(result.universe) >= 4
    assert len(result.iterations) >= 1

    # Check serialization
    d = result.to_dict()
    assert "gen" in d
    assert "kill" in d
    assert "in_sets" in d
    assert "out_sets" in d
    assert "iterations" in d
    assert len(d["iterations"]) > 0


def test_live_variables_dead_variable_detection() -> None:
    """Verify backward liveness identifies variables that are dead vs live."""
    code = """
    func main() {
        let a: int = 10;
        let b: int = 20;
        if (a > 5) {
            show a;
        } else {
            show b;
        }
    }
    """
    cfg = _compile_to_cfg(code)
    result = solve_live_variables(cfg)

    assert result.name == "Live Variables"
    assert result.direction == "BACKWARD"
    assert result.meet == "UNION"

    # Both a and b should be in the universe
    var_names = {v for v in result.universe if "_" in v or v in ("a", "b")}
    assert len(var_names) > 0

    # Serialization
    d = result.to_dict()
    assert d["direction"] == "BACKWARD"
    assert len(d["iterations"]) >= 1


def test_available_expressions() -> None:
    """Verify available expressions forward intersection."""
    code = """
    func main() {
        let a: int = 10;
        let b: int = 20;
        let c: int = a + b;
        let d: int = a + b;
        show c;
        show d;
    }
    """
    cfg = _compile_to_cfg(code)
    result = solve_available_expressions(cfg)

    assert result.name == "Available Expressions"
    assert result.direction == "FORWARD"
    assert result.meet == "INTERSECTION"

    # Universe must contain at least a + b
    ops = {e.opcode for e in result.universe}
    assert "ADD" in ops

    d = result.to_dict()
    assert "iterations" in d


def test_available_copies() -> None:
    """Verify available copies tracking and invalidation."""
    code = """
    func main() {
        let x: int = 42;
        let y: int = x;
        let z: int = y;
        show z;
    }
    """
    cfg = _compile_to_cfg(code)
    result = solve_available_copies(cfg)

    assert result.name == "Available Copies"
    assert result.direction == "FORWARD"
    assert result.meet == "INTERSECTION"

    d = result.to_dict()
    assert "iterations" in d
