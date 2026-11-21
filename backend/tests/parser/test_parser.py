"""Tests for the Recursive-Descent Parser (M3-T2).

Per doc 01 §12, §16.2, and agent-prompt.md:
- All 10 examples/*.vela parse with 0 errors.
- INV-SYN-01..08 report exact diagnostic codes and line:col coordinates.
- INV-SYN-08 reports two errors from panic-mode recovery.
- Nesting depth > 200 triggers VL-SYN-003.
- Differential testing: RD parser and SLR(1) parser agree on accept/reject.
"""

from pathlib import Path

import pytest

from vela.common.source import SourceFile
from vela.grammar.loader import BNFLoader
from vela.grammar.lr import LRBuilder
from vela.grammar.shift_reduce import ShiftReduceParser
from vela.lexer.scanner import Scanner
from vela.parser.recursive_descent import (
    parse_source,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"
INVALID_DIR = Path(__file__).resolve().parent.parent / "programs" / "invalid"
GRAMMAR_DIR = Path(__file__).resolve().parent.parent.parent.parent / "docs" / "grammar"


@pytest.fixture(scope="module")
def slr_parser() -> ShiftReduceParser:
    grammar = BNFLoader.load_file(GRAMMAR_DIR / "vela.bnf")
    builder = LRBuilder(grammar)
    table = builder.build_slr1()
    return ShiftReduceParser(table)


def test_all_10_examples_parse_cleanly() -> None:
    example_files = sorted(EXAMPLES_DIR.glob("*.vela"))
    assert len(example_files) == 10, f"Expected 10 example files, found {len(example_files)}"

    for fpath in example_files:
        code = fpath.read_text(encoding="utf-8")
        res = parse_source(code, fpath.name)
        assert res.success, f"{fpath.name} failed to parse: {[d.message for d in res.diagnostics]}"
        assert res.ast is not None
        assert res.cst is not None
        assert len(res.diagnostics) == 0
        assert len(res.call_trace) > 0


def test_inv_syn_01_missing_semicolon() -> None:
    fpath = INVALID_DIR / "INV-SYN-01.vela"
    res = parse_source(fpath.read_text(encoding="utf-8"), fpath.name)
    assert not res.success
    errs = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errs) == 1
    assert errs[0].code == "VL-SYN-001"
    assert errs[0].span.start.line == 3
    assert errs[0].span.start.column == 5


def test_inv_syn_02_missing_paren() -> None:
    fpath = INVALID_DIR / "INV-SYN-02.vela"
    res = parse_source(fpath.read_text(encoding="utf-8"), fpath.name)
    assert not res.success
    errs = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errs) == 1
    assert errs[0].code == "VL-SYN-001"
    assert errs[0].span.start.line == 2
    assert errs[0].span.start.column == 15


def test_inv_syn_03_else_without_if() -> None:
    fpath = INVALID_DIR / "INV-SYN-03.vela"
    res = parse_source(fpath.read_text(encoding="utf-8"), fpath.name)
    assert not res.success
    errs = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errs) == 1
    assert errs[0].code == "VL-SYN-001"
    assert errs[0].span.start.line == 2
    assert errs[0].span.start.column == 5


def test_inv_syn_04_missing_braces() -> None:
    fpath = INVALID_DIR / "INV-SYN-04.vela"
    res = parse_source(fpath.read_text(encoding="utf-8"), fpath.name)
    assert not res.success
    errs = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errs) == 1
    assert errs[0].code == "VL-SYN-001"
    assert errs[0].span.start.line == 3
    assert errs[0].span.start.column == 16


def test_inv_syn_05_unexpected_eof() -> None:
    fpath = INVALID_DIR / "INV-SYN-05.vela"
    res = parse_source(fpath.read_text(encoding="utf-8"), fpath.name)
    assert not res.success
    errs = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errs) == 1
    assert errs[0].code == "VL-SYN-002"
    assert errs[0].span.start.line == 3
    assert errs[0].span.start.column == 1


def test_inv_syn_06_missing_semicolon_in_for_header() -> None:
    fpath = INVALID_DIR / "INV-SYN-06.vela"
    res = parse_source(fpath.read_text(encoding="utf-8"), fpath.name)
    assert not res.success
    errs = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errs) == 1
    assert errs[0].code == "VL-SYN-001"
    assert errs[0].span.start.line == 2
    assert errs[0].span.start.column == 32


def test_inv_syn_07_missing_colon_in_var_decl() -> None:
    fpath = INVALID_DIR / "INV-SYN-07.vela"
    res = parse_source(fpath.read_text(encoding="utf-8"), fpath.name)
    assert not res.success
    errs = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errs) == 1
    assert errs[0].code == "VL-SYN-001"
    assert errs[0].span.start.line == 2
    assert errs[0].span.start.column == 11


def test_inv_syn_08_two_syntax_errors() -> None:
    fpath = INVALID_DIR / "INV-SYN-08.vela"
    res = parse_source(fpath.read_text(encoding="utf-8"), fpath.name)
    assert not res.success
    errs = [d for d in res.diagnostics if d.severity == "error"]
    assert len(errs) == 2, f"Expected 2 syntax errors, found: {[d.to_dict() for d in errs]}"
    assert errs[0].code == "VL-SYN-001"
    assert errs[0].span.start.line == 2
    assert errs[0].span.start.column == 18

    assert errs[1].code == "VL-SYN-001"
    assert errs[1].span.start.line == 4
    assert errs[1].span.start.column == 5


def test_nesting_depth_limit() -> None:
    # Build an expression with 205 levels of nesting: ((( ... 1 ... )))
    nested_code = "func main() {\n    let x: int = " + ("(" * 205) + "1" + (")" * 205) + ";\n}\n"
    res = parse_source(nested_code)
    assert not res.success
    errs = [d for d in res.diagnostics if d.code == "VL-SYN-003"]
    assert len(errs) >= 1
    assert "nesting too deep (> 200)" in errs[0].message


def test_cst_and_call_trace_export() -> None:
    code = "func main() {\n    let x: int = 42;\n    show x;\n}\n"
    res = parse_source(code)
    assert res.success
    assert res.cst is not None
    cst_dict = res.cst.to_dict()
    assert cst_dict["name"] == "Program"
    assert len(cst_dict["children"]) > 0

    pretty = res.cst.pretty_print()
    assert "Program" in pretty
    assert "FuncDecl" in pretty

    assert len(res.call_trace) > 0
    trace_step = res.call_trace[0].to_dict()
    assert "nonterminal" in trace_step
    assert "action" in trace_step


def test_differential_testing_examples_with_slr(slr_parser: ShiftReduceParser) -> None:
    example_files = sorted(EXAMPLES_DIR.glob("*.vela"))
    for fpath in example_files:
        code = fpath.read_text(encoding="utf-8")
        source = SourceFile(fpath.name, code)
        scanner = Scanner(source)
        lex_res = scanner.scan()
        tokens = [t.symbol for t in lex_res.tokens]

        # SLR(1) parser
        slr_res = slr_parser.parse(tokens)

        # Recursive descent parser
        rd_res = parse_source(code, fpath.name)

        assert slr_res.accepted, f"SLR parser failed on {fpath.name}: {slr_res.error}"
        assert rd_res.success, f"RD parser failed on {fpath.name}: {rd_res.diagnostics}"
        assert slr_res.accepted == rd_res.success


def test_differential_testing_invalid_with_slr(slr_parser: ShiftReduceParser) -> None:
    for i in range(1, 9):
        fpath = INVALID_DIR / f"INV-SYN-{i:02d}.vela"
        code = fpath.read_text(encoding="utf-8")
        source = SourceFile(fpath.name, code)
        scanner = Scanner(source)
        lex_res = scanner.scan()
        tokens = [t.symbol for t in lex_res.tokens]

        slr_res = slr_parser.parse(tokens)
        rd_res = parse_source(code, fpath.name)

        assert not slr_res.accepted, f"SLR parser should reject {fpath.name}"
        assert not rd_res.success, f"RD parser should reject {fpath.name}"
        assert slr_res.accepted == rd_res.success


def test_differential_testing_mutated_sentences(slr_parser: ShiftReduceParser) -> None:
    base_program = (EXAMPLES_DIR / "01_hello_types.vela").read_text(encoding="utf-8")
    lines = base_program.splitlines()

    # Create 30 deterministic mutations: deleting lines, inserting garbage, missing braces
    for i in range(min(len(lines), 30)):
        mutated_lines = list(lines)
        # Drop line i
        mutated_lines.pop(i)
        mutated_code = "\n".join(mutated_lines)

        source = SourceFile(f"mutated_{i}.vela", mutated_code)
        scanner = Scanner(source)
        lex_res = scanner.scan()
        tokens = [t.symbol for t in lex_res.tokens]

        slr_res = slr_parser.parse(tokens)
        rd_res = parse_source(mutated_code)

        # Both parsers should agree on whether the mutation is syntactically valid or rejected
        assert (
            slr_res.accepted == rd_res.success
        ), f"Differential mismatch on mutation {i}: SLR={slr_res.accepted}, RD={rd_res.success}"
