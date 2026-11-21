"""Tests for Three-Address Code (TAC) Interpreter and Oracle (M5-T2).

Verifies:
- All 10 examples/*.vela reproduce exactly their *.expected.txt
  (supplying *.stdin.txt where present).
- INV-RUN-01..05 give exact error codes and line:col coordinates.
- 32-bit two's complement integer wrap-around.
- Truncating division toward zero and dividend-sign remainder (-7 / 2 == -3, -7 % 2 == -1).
- Out-of-bounds array access, input exhaustion, call stack overflow, instruction budget.
"""

from pathlib import Path

import pytest

from vela.ir.generator import TACGenerator
from vela.ir.interpreter import TACInterpreter
from vela.semantic.checker import check_source

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"
INVALID_DIR = Path(__file__).resolve().parent.parent / "programs" / "invalid"


def _run_source(code: str, file_name: str = "test.vela", stdin: str = ""):
    res = check_source(code, file_name)
    errors = [d for d in res.diagnostics if d.severity == "error"]
    assert not errors, f"Diagnostics in {file_name}: {[e.message for e in errors]}"
    assert res.ast is not None, f"No AST for {file_name}"

    generator = TACGenerator()
    tac = generator.generate(res.ast)

    interpreter = TACInterpreter()
    return interpreter.interpret(tac, stdin=stdin)


@pytest.mark.parametrize(
    "example_name",
    [
        "01_hello_types",
        "02_conditions",
        "03_switch",
        "04_loops",
        "05_functions",
        "06_arrays",
        "07_io",
        "08_optimizer_showcase",
        "09_strings_and_casts",
        "10_scopes",
    ],
)
def test_all_ten_examples_oracle(example_name: str) -> None:
    """Verify that every examples/*.vela produces exactly its *.expected.txt."""
    vela_file = EXAMPLES_DIR / f"{example_name}.vela"
    expected_file = EXAMPLES_DIR / f"{example_name}.expected.txt"
    stdin_file = EXAMPLES_DIR / f"{example_name}.stdin.txt"

    assert vela_file.exists(), f"Missing {vela_file}"
    assert expected_file.exists(), f"Missing {expected_file}"

    code = vela_file.read_text(encoding="utf-8")
    expected_stdout = expected_file.read_text(encoding="utf-8").replace("\r\n", "\n")
    stdin_content = stdin_file.read_text(encoding="utf-8") if stdin_file.exists() else ""

    result = _run_source(code, vela_file.name, stdin=stdin_content)
    actual_stdout = result.stdout.replace("\r\n", "\n")

    assert result.success, f"{example_name} runtime failed with diagnostics: {result.diagnostics}"
    assert actual_stdout == expected_stdout, (
        f"Output mismatch for {example_name}!\nExpected:\n{expected_stdout}\nGot:\n{actual_stdout}"
    )


@pytest.mark.parametrize(
    ("inv_id", "expected_code", "expected_line", "expected_col", "stdin"),
    [
        ("INV-RUN-01", "VL-RUN-001", 4, 13, "0"),
        ("INV-RUN-02", "VL-RUN-002", 4, 5, ""),
        ("INV-RUN-03", "VL-RUN-003", 3, 5, ""),
        ("INV-RUN-04", "VL-RUN-006", 2, 12, ""),
        ("INV-RUN-05", "VL-RUN-007", 2, 5, ""),
    ],
)
def test_inv_run_programs(
    inv_id: str,
    expected_code: str,
    expected_line: int,
    expected_col: int,
    stdin: str,
) -> None:
    """Verify exact diagnostic code and line:col coordinates for INV-RUN-01..05."""
    file_path = INVALID_DIR / f"{inv_id}.vela"
    assert file_path.exists(), f"Missing {file_path}"
    code = file_path.read_text(encoding="utf-8")

    result = _run_source(code, file_path.name, stdin=stdin)
    assert not result.success, f"{inv_id} was expected to fail runtime, but succeeded with stdout: {result.stdout}"
    assert len(result.diagnostics) > 0

    diag = result.diagnostics[0]
    assert diag.code == expected_code, f"Expected {expected_code}, got {diag.code} ({diag.message})"
    assert diag.span.start.line == expected_line, f"Expected line {expected_line}, got {diag.span.start.line}"
    assert diag.span.start.col == expected_col, f"Expected col {expected_col}, got {diag.span.start.col}"


def test_integer_wrap_semantics() -> None:
    """Verify 32-bit two's complement integer wrap-around (2147483647 + 1 == -2147483648)."""
    code = """
    func main() {
        let max_val: int = 2147483647;
        let wrapped: int = max_val + 1;
        show wrapped;
    }
    """
    res = _run_source(code)
    assert res.success
    assert res.stdout.strip() == "-2147483648"


def test_truncating_division_and_modulo() -> None:
    """Verify -7 / 2 == -3 and -7 % 2 == -1."""
    code = """
    func main() {
        let q: int = -7 / 2;
        let r: int = -7 % 2;
        show q, " ", r;
    }
    """
    res = _run_source(code)
    assert res.success
    assert res.stdout.strip() == "-3 -1"


def test_conversion_out_of_range() -> None:
    """Verify VL-RUN-005 on out-of-range conversions (e.g. 256 as char, 1e15 as int)."""
    code_char = """
    func main() {
        let n: int = 300;
        let c: char = n as char;
        show c;
    }
    """
    res = _run_source(code_char)
    assert not res.success
    assert res.diagnostics[0].code == "VL-RUN-005"


def test_output_limit_exceeded() -> None:
    """Verify VL-RUN-008 when output exceeds 100,000 characters."""
    code = """
    func main() {
        while (true) {
            show "12345678901234567890";
        }
    }
    """
    res = _run_source(code)
    assert not res.success
    assert res.diagnostics[0].code == "VL-RUN-008"
