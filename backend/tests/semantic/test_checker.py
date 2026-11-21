"""Tests for the Vela Semantic Checker (M4-T2).

Per doc 01 §6.2–§6.5, §7–§10, §16.3 and agent-prompt.md:
- All 10 examples/*.vela pass semantic checking with 0 errors.
- INV-SEM-01..19 give exact error codes and line:col coordinates.
- Systematic testing of every row of the conversion table in doc 01 §6.3.
- ImplicitCast node insertion during widening.
"""

from pathlib import Path

import pytest

from vela.ast.nodes import ImplicitCast
from vela.semantic.checker import check_source

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"
INVALID_DIR = Path(__file__).resolve().parent.parent / "programs" / "invalid"


def test_all_10_examples_semantic_clean() -> None:
    example_files = sorted(EXAMPLES_DIR.glob("*.vela"))
    assert len(example_files) == 10

    for fpath in example_files:
        code = fpath.read_text(encoding="utf-8")
        res = check_source(code, fpath.name)
        errors = [d for d in res.diagnostics if d.severity == "error"]
        assert res.success, f"{fpath.name} failed semantic check with errors: {[e.message for e in errors]}"
        assert len(errors) == 0


@pytest.mark.parametrize(
    ("inv_id", "expected_code", "expected_line", "expected_col"),
    [
        ("INV-SEM-01", "VL-SEM-001", 2, 10),
        ("INV-SEM-02", "VL-SEM-002", 3, 9),
        ("INV-SEM-03", "VL-SEM-003", 2, 18),
        ("INV-SEM-04", "VL-SEM-003", 3, 18),
        ("INV-SEM-05", "VL-SEM-005", 2, 9),
        ("INV-SEM-06", "VL-SEM-007", 6, 10),
        ("INV-SEM-07", "VL-SEM-008", 6, 16),
        ("INV-SEM-08", "VL-SEM-010", 1, 6),
        ("INV-SEM-09", "VL-SEM-011", 2, 5),
        ("INV-SEM-10", "VL-SEM-012", 5, 14),
        ("INV-SEM-11", "VL-SEM-009", 2, 12),
        ("INV-SEM-12", "VL-SEM-016", 2, 28),
        ("INV-SEM-13", "VL-SEM-022", 3, 7),
        ("INV-SEM-14", "VL-SEM-018", 1, 1),
        ("INV-SEM-15", "VL-SEM-019", 2, 14),
        ("INV-SEM-16", "VL-SEM-004", 2, 14),
        ("INV-SEM-17", "VL-SEM-023", 6, 18),
        ("INV-SEM-18", "VL-SEM-020", 2, 14),
        ("INV-SEM-19", "VL-SEM-013", 3, 13),
    ],
)
def test_inv_sem_catalog(inv_id: str, expected_code: str, expected_line: int, expected_col: int) -> None:
    fpath = INVALID_DIR / f"{inv_id}.vela"
    code = fpath.read_text(encoding="utf-8")
    res = check_source(code, fpath.name)

    errors = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errors) >= 1, f"{inv_id} unexpectedly passed semantic checking"

    # Find the primary diagnostic matching expected code
    matching = [d for d in errors if d.code == expected_code]
    assert len(matching) >= 1, f"Expected {expected_code} for {inv_id}, found {[d.code for d in errors]}"
    diag = matching[0]

    assert diag.span.start.line == expected_line, (
        f"{inv_id}: expected line {expected_line}, got {diag.span.start.line}"
    )
    assert diag.span.start.column == expected_col, (
        f"{inv_id}: expected col {expected_col}, got {diag.span.start.column}"
    )


def test_conversion_table_all_rows() -> None:
    # Test valid casts
    valid_snippets = [
        "func main() { let x: float = 5 as float; }",
        "func main() { let x: char = 65 as char; }",
        "func main() { let x: string = 42 as string; }",
        "func main() { let x: int = 3.7 as int; }",
        "func main() { let x: string = 3.14 as string; }",
        "func main() { let x: int = 'A' as int; }",
        "func main() { let x: string = 'z' as string; }",
        "func main() { let x: int = true as int; }",
        "func main() { let x: string = false as string; }",
    ]
    for snip in valid_snippets:
        res = check_source(snip)
        errors = [d for d in res.diagnostics if d.severity == "error"]
        assert len(errors) == 0, f"Snippet failed valid cast: {snip}, errors: {errors}"

    # Test invalid casts (VL-SEM-019)
    invalid_snippets = [
        "func main() { let x: bool = 1 as bool; }",
        "func main() { let x: char = 2.5 as char; }",
        "func main() { let x: bool = 2.5 as bool; }",
        "func main() { let x: float = 'a' as float; }",
        "func main() { let x: bool = 'a' as bool; }",
        "func main() { let x: int = \"hello\" as int; }",
        "func main() { let x: float = \"hello\" as float; }",
        "func main() { let x: char = \"hello\" as char; }",
        "func main() { let x: bool = \"hello\" as bool; }",
        "func main() { let x: float = true as float; }",
        "func main() { let x: char = true as char; }",
    ]
    for snip in invalid_snippets:
        res = check_source(snip)
        errors = [d for d in res.diagnostics if d.code == "VL-SEM-019"]
        assert len(errors) >= 1, f"Snippet should have failed cast: {snip}"


def test_implicit_cast_insertion() -> None:
    # 1. Assignment
    code = "func main() {\n    let f: float = 1;\n    f = 2;\n}\n"
    res = check_source(code)
    assert res.success

    func = res.ast.items[0]
    var_decl = func.body.statements[0]
    assign_stmt = func.body.statements[1]

    assert isinstance(var_decl.init, ImplicitCast)
    assert var_decl.init.from_type == "int"
    assert var_decl.init.to_type == "float"

    assert isinstance(assign_stmt.value, ImplicitCast)
    assert assign_stmt.value.from_type == "int"
    assert assign_stmt.value.to_type == "float"

    # 2. Binary operation
    code2 = "func main() {\n    let f: float = 1 + 2.5;\n}\n"
    res2 = check_source(code2)
    assert res2.success
    var_decl2 = res2.ast.items[0].body.statements[0]
    bin_expr = var_decl2.init
    assert isinstance(bin_expr.left, ImplicitCast)
    assert bin_expr.left.from_type == "int"
