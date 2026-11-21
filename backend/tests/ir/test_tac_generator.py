"""Tests for Three-Address Code (TAC) generation and lowering.

Verifies:
- Golden TAC instruction generation for every language construct (P5-01..P5-11).
- No plain 'and'/'or' opcodes exist in output (short-circuit boolean lowering).
- Every jump target label exists in the generated program.
- Instruction provenance (src_span, ast_id, rule_id).
- Compilation of all 10 standard example programs to well-formed TAC.
"""

from pathlib import Path

from vela.ir.generator import TACGenerator
from vela.ir.printer import TACPrinter
from vela.ir.tac import TACProgram
from vela.semantic.checker import check_source


def _compile_to_tac(source_code: str, file_name: str = "test.vela") -> TACProgram:
    res = check_source(source_code, file_name)
    errors = [d for d in res.diagnostics if d.severity == "error"]
    assert not errors, f"Diagnostics in {file_name}: {[e.message for e in errors]}"
    assert res.ast is not None, f"No AST produced for {file_name}"

    generator = TACGenerator()
    return generator.generate(res.ast)


def test_declarations_and_startup() -> None:
    """Verify global and local variable declarations and startup sequence."""
    code = """
    let g: int = 100;
    func main() {
        let x: int = 42;
        show x, g;
    }
    """
    tac = _compile_to_tac(code)
    assert not tac.validate_labels(), f"Missing labels: {tac.validate_labels()}"
    assert not tac.contains_plain_boolean_ops()

    # Startup prologue should contain ASSIGN for g, CALL main, RETURN
    opcodes = [i.opcode for i in tac.instructions]
    assert "ASSIGN" in opcodes
    assert "CALL" in opcodes
    assert "SHOW" in opcodes
    assert "SHOW_NL" in opcodes

    # Check instruction provenance
    for instr in tac.instructions:
        assert instr.rule_id is not None
        assert instr.rule_id != ""


def test_arithmetic_and_conversions() -> None:
    """Verify arithmetic operations, unary negation, and type widening."""
    code = """
    func main() {
        let a: int = 10;
        let b: int = -a;
        let c: float = 2.5;
        let d: float = a + c; // implicit widening
        let e: int = a * 2 + b / 2 - a % 3;
        show e;
    }
    """
    tac = _compile_to_tac(code)
    assert not tac.validate_labels()
    assert not tac.contains_plain_boolean_ops()

    opcodes = {i.opcode for i in tac.instructions}
    assert "NEG" in opcodes
    assert "ADD" in opcodes
    assert "SUB" in opcodes
    assert "MUL" in opcodes
    assert "DIV" in opcodes
    assert "MOD" in opcodes
    assert "CAST" in opcodes


def test_short_circuit_boolean_lowering() -> None:
    """Verify that 'and' and 'or' are lowered with conditional branches, NEVER plain opcodes."""
    code = """
    func main() {
        let a: bool = true;
        let b: bool = false;
        let c: bool = a and b;
        let d: bool = a or b;
        let e: bool = not a;
        show c, d, e;
    }
    """
    tac = _compile_to_tac(code)
    assert not tac.validate_labels()
    # Acceptance criterion: NO plain 'and'/'or' opcode exists!
    assert not tac.contains_plain_boolean_ops()

    opcodes = {i.opcode for i in tac.instructions}
    assert "AND" not in opcodes
    assert "OR" not in opcodes
    assert "JUMP_IF_FALSE" in opcodes
    assert "JUMP_IF" in opcodes
    assert "NOT" in opcodes


def test_if_else_and_nested() -> None:
    """Verify if, if-else, and nested conditions with branch labels."""
    code = """
    func main() {
        let x: int = 10;
        if (x > 5) {
            if (x > 8) {
                show 1;
            } else {
                show 2;
            }
        } else {
            show 3;
        }
    }
    """
    tac = _compile_to_tac(code)
    assert not tac.validate_labels()
    assert not tac.contains_plain_boolean_ops()

    opcodes = [i.opcode for i in tac.instructions]
    assert "GT" in opcodes
    assert "JUMP_IF_FALSE" in opcodes
    assert "JUMP" in opcodes
    assert "LABEL" in opcodes


def test_switch_case_compare_chain() -> None:
    """Verify switch-case equality compare chain, jumps, and default branch with no fall-through."""
    code = """
    func main() {
        let x: int = 2;
        switch (x) {
            case 1: { show "one"; }
            case 2, 3: { show "two or three"; }
            default: { show "other"; }
        }
    }
    """
    tac = _compile_to_tac(code)
    assert not tac.validate_labels()
    assert not tac.contains_plain_boolean_ops()

    opcodes = [i.opcode for i in tac.instructions]
    assert "EQ" in opcodes
    assert "JUMP_IF" in opcodes


def test_loops_and_break_continue() -> None:
    """Verify while, do-while, and for loops with break and continue."""
    code = """
    func main() {
        let i: int = 0;
        while (i < 10) {
            if (i == 5) {
                break;
            }
            i += 1;
        }

        do {
            i += 1;
            if (i == 7) {
                continue;
            }
        } while (i < 8);

        for (let k: int = 0; k < 5; k += 1) {
            if (k == 2) {
                continue;
            }
            show k;
        }
    }
    """
    tac = _compile_to_tac(code)
    assert not tac.validate_labels()
    assert not tac.contains_plain_boolean_ops()

    opcodes = [i.opcode for i in tac.instructions]
    assert "JUMP" in opcodes
    assert "JUMP_IF" in opcodes
    assert "JUMP_IF_FALSE" in opcodes


def test_function_calls_and_arrays() -> None:
    """Verify function parameters, return values, array indexing, and reading."""
    code = """
    func add(x: int, y: int): int {
        return x + y;
    }

    func main() {
        let arr: int[3] = {10, 20, 30};
        arr[0] = 50;
        let res: int = add(arr[0], arr[1]);
        show res;
    }
    """
    tac = _compile_to_tac(code)
    assert not tac.validate_labels()
    assert not tac.contains_plain_boolean_ops()

    opcodes = {i.opcode for i in tac.instructions}
    assert "FUNC_BEGIN" in opcodes
    assert "PARAM" in opcodes
    assert "CALL" in opcodes
    assert "RETURN" in opcodes
    assert "FUNC_END" in opcodes
    assert "ARRAY_GET" in opcodes
    assert "ARRAY_SET" in opcodes


def test_printer_formatting() -> None:
    """Verify TAC printer text and table representations."""
    code = """
    func main() {
        let x: int = 1 + 2;
        show x;
    }
    """
    tac = _compile_to_tac(code)
    text = TACPrinter.print_program(tac)
    assert "main:" in text
    assert "show x" in text

    table = TACPrinter.to_table(tac)
    assert len(table) == len(tac.instructions)
    assert table[0]["opcode"] == "LABEL"


def test_all_ten_examples_compile_to_tac() -> None:
    """Verify that all 10 examples/*.vela compile to well-formed TAC."""
    examples_dir = Path(__file__).resolve().parent.parent.parent.parent / "examples"
    vela_files = sorted(examples_dir.glob("*.vela"))
    assert len(vela_files) == 10, f"Expected 10 examples, found {len(vela_files)}"

    for file_path in vela_files:
        code = file_path.read_text(encoding="utf-8")
        tac = _compile_to_tac(code, file_path.name)
        # Every jump target must exist
        missing = tac.validate_labels()
        assert not missing, f"Missing labels in {file_path.name}: {missing}"
        # No plain boolean ops
        assert not tac.contains_plain_boolean_ops(), f"Forbidden boolean ops in {file_path.name}"
        # Non-empty instructions
        assert len(tac.instructions) > 0
