"""Tests for End-to-End Pipeline and CLI Driver (M7-T4).

Verifies:
- Phase-gated compilation pipeline (lexer -> parser -> semantic -> ir -> cfg -> opt -> codegen -> peephole)
- Timings in milliseconds across all phases
- Early termination and phase gating on syntax/semantic errors
- Program execution via VM and TAC oracle
- CLI subcommands: compile, run, verify, selftest
"""

import subprocess
import sys
from pathlib import Path

from vela.pipeline import RunOptions, compile_source, run_program

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"


def test_pipeline_compile_source_success() -> None:
    code = """
    func main() {
        let x: int = 42;
        show "value: ", x;
    }
    """
    res = compile_source(code, filename="test.vela")

    assert res.success is True
    assert not res.has_errors()
    assert res.source_hash != ""
    assert res.tokens is not None and len(res.tokens) > 0
    assert res.ast is not None
    assert res.semantic_result is not None
    assert res.tac_program is not None
    assert res.blocks is not None
    assert res.cfg is not None
    assert res.optimized_tac is not None
    assert res.target_unallocated is not None
    assert res.allocation_result is not None
    assert res.target_program is not None
    assert "lexer" in res.timings_ms
    assert "parser" in res.timings_ms
    assert "semantic" in res.timings_ms
    assert "ir" in res.timings_ms
    assert "cfg" in res.timings_ms
    assert "optimizer" in res.timings_ms
    assert "codegen" in res.timings_ms
    assert "peephole" in res.timings_ms


def test_pipeline_phase_gating_lexer_error() -> None:
    code = "func main() { let x: int = 5 @ 3; }"
    res = compile_source(code, filename="bad_lex.vela")

    assert res.success is False
    assert res.halted_at_phase == "lexer"
    assert any(d.code == "VL-LEX-001" for d in res.diagnostics)
    assert res.ast is None
    assert res.tac_program is None
    assert res.target_program is None


def test_pipeline_phase_gating_parser_error() -> None:
    code = "func main() { let x = 5; }"  # missing : type
    res = compile_source(code, filename="bad_parse.vela")

    assert res.success is False
    assert res.halted_at_phase == "parser"
    assert any(d.code == "VL-SYN-001" for d in res.diagnostics)
    assert res.semantic_result is None
    assert res.tac_program is None
    assert res.target_program is None


def test_pipeline_phase_gating_semantic_error() -> None:
    code = "func main() { let x: int = \"hello\"; }"
    res = compile_source(code, filename="bad_sem.vela")

    assert res.success is False
    assert res.halted_at_phase == "semantic"
    assert any(d.code == "VL-SEM-003" for d in res.diagnostics)
    assert res.tac_program is None
    assert res.target_program is None


def test_pipeline_run_program_vm_and_oracle() -> None:
    code = """
    func main() {
        let a: int = 15;
        let b: int = 27;
        show a + b;
    }
    """
    c_res = compile_source(code)
    assert c_res.success is True

    # Run VM
    vm_res = run_program(c_res)
    assert vm_res.exit_code == 0
    assert vm_res.stdout.strip() == "42"

    # Run Oracle
    oracle_res = run_program(c_res, options=RunOptions(use_oracle=True))
    assert oracle_res.exit_code == 0
    assert oracle_res.stdout.strip() == "42"


def test_cli_compile_dump_flags(tmp_path: Path) -> None:
    src_file = tmp_path / "hello.vela"
    src_file.write_text("func main() { show \"hello CLI\"; }\n", encoding="utf-8")

    # Run python -m vela.cli compile --dump-tac --dump-target
    cmd = [
        sys.executable,
        "-m",
        "vela.cli",
        "compile",
        str(src_file),
        "--dump-tac",
        "--dump-target",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    assert "THREE-ADDRESS CODE" in proc.stdout
    assert "TARGET ASSEMBLY" in proc.stdout


def test_cli_run_example() -> None:
    ex = EXAMPLES_DIR / "01_hello_types.vela"
    cmd = [sys.executable, "-m", "vela.cli", "run", str(ex)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    expected = (ex.parent / f"{ex.stem}.expected.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
    assert proc.stdout == expected


def test_cli_selftest() -> None:
    cmd = [sys.executable, "-m", "vela.cli", "selftest"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    assert "100.0%" in proc.stdout
