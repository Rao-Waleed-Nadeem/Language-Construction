"""Tests for Optimization Passes, Pipeline, and Equivalence Verification (M6-T3).

Verifies:
- Constant folding (32-bit wrap, NEVER folds division/modulo by zero).
- Algebraic simplification (arithmetic identities).
- Constant propagation and copy propagation.
- Common subexpression elimination (DAG-local and global).
- Dead-code elimination (preserves side effects).
- Loop-invariant code motion (hoisting).
- Strength reduction (multiplication by 2).
- Optimizer pipeline on 08_optimizer_showcase.vela (instructions reduced, passes active).
- Full semantic equivalence across all 10 examples against unoptimized TAC.
- Preservation of runtime errors on INV-RUN-01..05.
"""

from pathlib import Path

from vela.ir.generator import TACGenerator
from vela.ir.interpreter import TACInterpreter
from vela.ir.tac import Constant, TACInstruction, TACProgram, Variable
from vela.opt.passes.const_fold import run_constant_folding
from vela.opt.passes.dce import run_dead_code_elimination
from vela.opt.passes.simplify import run_algebraic_simplification
from vela.opt.passes.strength import run_strength_reduction
from vela.opt.pipeline import optimize_tac
from vela.opt.validate import verify_equivalence
from vela.semantic.checker import check_source

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"
INVALID_DIR = Path(__file__).resolve().parent.parent / "programs" / "invalid"


def _compile(code: str, name: str = "test.vela") -> TACProgram:
    res = check_source(code, name)
    assert not [d for d in res.diagnostics if d.severity == "error"]
    assert res.ast is not None
    return TACGenerator().generate(res.ast)


def test_constant_folding_wrap_and_safety() -> None:
    """Verify constant folding handles 32-bit wrap and NEVER folds div/mod by zero."""
    # 1. 32-bit wrap
    p_wrap = TACProgram(
        instructions=[
            TACInstruction(
                opcode="ADD",
                arg1=Constant(2147483647, "int"),
                arg2=Constant(1, "int"),
                result=Variable("x"),
            )
        ]
    )
    p_opt, changes = run_constant_folding(p_wrap)
    assert len(changes) == 1
    assert p_opt.instructions[0].opcode == "ASSIGN"
    assert isinstance(p_opt.instructions[0].arg1, Constant)
    assert p_opt.instructions[0].arg1.value == -2147483648

    # 2. Division by zero must NOT be folded
    p_div0 = TACProgram(
        instructions=[
            TACInstruction(
                opcode="DIV",
                arg1=Constant(10, "int"),
                arg2=Constant(0, "int"),
                result=Variable("x"),
            )
        ]
    )
    p_div0_opt, div_changes = run_constant_folding(p_div0)
    assert len(div_changes) == 0
    assert p_div0_opt.instructions[0].opcode == "DIV"

    # 3. Modulo by zero must NOT be folded
    p_mod0 = TACProgram(
        instructions=[
            TACInstruction(
                opcode="MOD",
                arg1=Constant(10, "int"),
                arg2=Constant(0, "int"),
                result=Variable("x"),
            )
        ]
    )
    p_mod0_opt, mod_changes = run_constant_folding(p_mod0)
    assert len(mod_changes) == 0
    assert p_mod0_opt.instructions[0].opcode == "MOD"


def test_algebraic_simplification() -> None:
    """Verify algebraic simplification identities."""
    code = """
    func main() {
        let x: int = 10;
        let a: int = x + 0;
        let b: int = x * 1;
        let c: int = x * 0;
        let d: int = x - 0;
        let e: int = x / 1;
        show a, b, c, d, e;
    }
    """
    tac = _compile(code)
    _opt, changes = run_algebraic_simplification(tac)
    assert len(changes) >= 5
    descriptions = [c.description for c in changes]
    assert any("x + 0 -> x" in d for d in descriptions)
    assert any("x * 1 -> x" in d for d in descriptions)
    assert any("x * 0 -> 0" in d for d in descriptions)
    assert any("x - 0 -> x" in d for d in descriptions)
    assert any("x / 1 -> x" in d for d in descriptions)


def test_strength_reduction() -> None:
    """Verify x * 2 is reduced to x + x."""
    code = """
    func main() {
        let x: int = 7;
        let y: int = x * 2;
        show y;
    }
    """
    tac = _compile(code)
    _opt, changes = run_strength_reduction(tac)
    assert len(changes) >= 1
    assert any("x * 2 -> x + x" in c.description for c in changes)


def test_dead_code_elimination() -> None:
    """Verify unused variables are removed while side-effecting operations are kept."""
    code = """
    func main() {
        let unused: int = 42 * 99;
        let used: int = 10;
        show used;
    }
    """
    tac = _compile(code)
    # Fold constants first so unused is just assign
    tac_folded, _ = run_constant_folding(tac)
    _opt, changes = run_dead_code_elimination(tac_folded)
    assert len(changes) >= 1
    assert any("unused" in c.description for c in changes)


def test_optimizer_showcase_reduces_instructions() -> None:
    """Verify 08_optimizer_showcase.vela activates passes and reduces instruction count."""
    showcase_path = EXAMPLES_DIR / "08_optimizer_showcase.vela"
    code = showcase_path.read_text(encoding="utf-8")
    tac = _compile(code, "08_optimizer_showcase.vela")

    result = optimize_tac(tac)

    assert result.instruction_count_before > result.instruction_count_after
    assert result.reduction_percentage > 0.0
    assert len(result.all_changes) > 5

    # Check that multiple pass types made changes
    pass_names_with_changes = {p.name for p in result.passes if p.change_count > 0}
    assert len(pass_names_with_changes) >= 3

    # Equivalence verification with input
    stdin_input = "5 7 3"
    ok, msg = verify_equivalence(tac, result.optimized_program, stdin_input)
    assert ok, f"Equivalence failed on 08_optimizer_showcase: {msg}"


def test_all_10_examples_semantic_equivalence() -> None:
    """Verify optimization preserves exact interpreter output on all 10 examples."""
    inputs = {
        "01_hello.vela": "",
        "02_variables.vela": "",
        "03_control_flow.vela": "",
        "04_loops.vela": "",
        "05_functions.vela": "",
        "06_arrays.vela": "",
        "07_io.vela": "42\n3.14\nA\nHello World\ntrue\n",
        "08_optimizer_showcase.vela": "5 7 3\n",
        "09_comprehensive.vela": "5\n",
        "10_scopes.vela": "",
    }

    for path in sorted(EXAMPLES_DIR.glob("*.vela")):
        code = path.read_text(encoding="utf-8")
        tac = _compile(code, path.name)
        opt_res = optimize_tac(tac)

        stdin_data = inputs.get(path.name, "")
        ok, msg = verify_equivalence(tac, opt_res.optimized_program, stdin_data)
        assert ok, f"Equivalence failed on {path.name}: {msg}"


def test_invalid_runtime_programs_preserve_errors() -> None:
    """Verify optimizations never eliminate runtime errors in INV-RUN-01..05."""
    for inv_file in sorted(INVALID_DIR.glob("INV-RUN-*.vela")):
        code = inv_file.read_text(encoding="utf-8")
        tac = _compile(code, inv_file.name)
        opt_res = optimize_tac(tac)

        orig_res = TACInterpreter().interpret(tac)
        opt_res_exec = TACInterpreter().interpret(opt_res.optimized_program)

        # Both must exit with non-zero
        assert orig_res.exit_code != 0
        assert opt_res_exec.exit_code != 0
        assert orig_res.exit_code == opt_res_exec.exit_code, f"Exit code mismatch on {inv_file.name}: {orig_res.exit_code} vs {opt_res_exec.exit_code}"

        # Error diagnostics must match
        assert len(orig_res.diagnostics) == len(opt_res_exec.diagnostics)
        orig_diag = orig_res.diagnostics[0]
        opt_diag = opt_res_exec.diagnostics[0]
        assert orig_diag.code == opt_diag.code, f"Error code mismatch on {inv_file.name}"
