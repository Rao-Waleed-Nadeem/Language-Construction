"""Unit and golden tests for the Vela Lexer.

Per M1-T2 requirements:
- tests pass for all token classes
- 'show' is KEYWORD and 'shown' is IDENTIFIER
- longest match ('<=', '++', '==')
- a token spanning a buffer refill
- INV-LEX-01...07 give the exact code and line:col of doc 01 §16.1
- every examples/*.vela scans with no errors
"""

from pathlib import Path

from vela.common.source import SourceFile
from vela.language.spec import TokenCategory
from vela.lexer.scanner import Scanner


def test_token_classes_and_literals():
    """Verify scanning of all literal token classes, delimiters and operators."""
    source_text = """
    let x: int = 42;
    let pi: float = 3.14159;
    let c: char = 'A';
    let s: string = "hello\\nworld";
    let flag: bool = true;
    """
    source = SourceFile("test.vela", source_text)
    scanner = Scanner(source)
    res = scanner.scan()

    assert not res.has_errors
    symbols = [t.symbol for t in res.tokens]
    assert "let" in symbols
    assert "int" in symbols
    assert "INT_LIT" in symbols
    assert "float" in symbols
    assert "FLOAT_LIT" in symbols
    assert "char" in symbols
    assert "CHAR_LIT" in symbols
    assert "string" in symbols
    assert "STRING_LIT" in symbols
    assert "bool" in symbols
    assert "true" in symbols

    # Check evaluated literal values
    int_token = next(t for t in res.tokens if t.symbol == "INT_LIT")
    assert int_token.value == 42

    float_token = next(t for t in res.tokens if t.symbol == "FLOAT_LIT")
    assert float_token.value == 3.14159

    char_token = next(t for t in res.tokens if t.symbol == "CHAR_LIT")
    assert char_token.value == "A"

    str_token = next(t for t in res.tokens if t.symbol == "STRING_LIT")
    assert str_token.value == "hello\nworld"


def test_keyword_vs_identifier():
    """Verify 'show' is KEYWORD and 'shown' is IDENTIFIER."""
    source = SourceFile("test.vela", "show shown")
    scanner = Scanner(source)
    res = scanner.scan()

    assert not res.has_errors
    assert len(res.tokens) == 3  # show, shown, $

    t0 = res.tokens[0]
    assert t0.category == TokenCategory.KEYWORD
    assert t0.symbol == "show"
    assert t0.lexeme == "show"

    t1 = res.tokens[1]
    assert t1.category == TokenCategory.IDENTIFIER
    assert t1.symbol == "ID"
    assert t1.lexeme == "shown"


def test_longest_match():
    """Verify maximal munch on operators like <=, ++, ==."""
    source = SourceFile("test.vela", "<= < ++ + == = += -=")
    scanner = Scanner(source)
    res = scanner.scan()

    assert not res.has_errors
    symbols = [t.symbol for t in res.tokens[:-1]]
    assert symbols == ["<=", "<", "++", "+", "==", "=", "+=", "-="]


def test_token_spanning_buffer_refill():
    """Verify that tokens and comments spanning buffer boundaries scan cleanly."""
    # Using small buffer_size=8 so almost every token/identifier spans refills
    source_text = "let variable_with_a_long_name: int = 123456789; show variable_with_a_long_name;"
    source = SourceFile("test.vela", source_text)
    scanner = Scanner(source, buffer_size=8)
    res = scanner.scan()

    assert not res.has_errors
    symbols = [t.symbol for t in res.tokens[:-1]]
    assert symbols == [
        "let",
        "ID",
        ":",
        "int",
        "=",
        "INT_LIT",
        ";",
        "show",
        "ID",
        ";",
    ]
    # Check that buffer refill trace recorded events
    refill_events = [e for e in res.buffer_trace if e["event"] == "load_buffer"]
    assert len(refill_events) > 2


def test_inv_lex_01():
    """INV-LEX-01: invalid character @ at 2:20."""
    code = "func main() { // INV-LEX-01\n    let x: int = 5 @ 3;\n}"
    source = SourceFile("inv01.vela", code)
    res = Scanner(source).scan()
    assert res.has_errors
    err = next(d for d in res.diagnostics if d.code == "VL-LEX-001")
    assert err.span.start.line == 2
    assert err.span.start.col == 20


def test_inv_lex_02():
    """INV-LEX-02: unterminated string at 2:10."""
    code = 'func main() { // INV-LEX-02\n    show "hello;\n}'
    source = SourceFile("inv02.vela", code)
    res = Scanner(source).scan()
    assert res.has_errors
    err = next(d for d in res.diagnostics if d.code == "VL-LEX-002")
    assert err.span.start.line == 2
    assert err.span.start.col == 10


def test_inv_lex_03():
    """INV-LEX-03: malformed number 12abc at 2:18."""
    code = "func main() { // INV-LEX-03\n    let x: int = 12abc;\n}"
    source = SourceFile("inv03.vela", code)
    res = Scanner(source).scan()
    assert res.has_errors
    err = next(d for d in res.diagnostics if d.code == "VL-LEX-008")
    assert err.span.start.line == 2
    assert err.span.start.col == 18


def test_inv_lex_04():
    """INV-LEX-04: unterminated block comment at 2:5."""
    code = "func main() { // INV-LEX-04\n    /* never closed\n    show 1;\n}"
    source = SourceFile("inv04.vela", code)
    res = Scanner(source).scan()
    assert res.has_errors
    err = next(d for d in res.diagnostics if d.code == "VL-LEX-007")
    assert err.span.start.line == 2
    assert err.span.start.col == 5


def test_inv_lex_05():
    """INV-LEX-05: invalid escape \\q at 2:12."""
    code = 'func main() { // INV-LEX-05\n    show "a\\qb";\n}'
    source = SourceFile("inv05.vela", code)
    res = Scanner(source).scan()
    assert res.has_errors
    err = next(d for d in res.diagnostics if d.code == "VL-LEX-006")
    assert err.span.start.line == 2
    assert err.span.start.col == 12


def test_inv_lex_06():
    """INV-LEX-06: integer out of range 2147483648 at 2:18."""
    code = "func main() { // INV-LEX-06\n    let x: int = 2147483648;\n}"
    source = SourceFile("inv06.vela", code)
    res = Scanner(source).scan()
    assert res.has_errors
    err = next(d for d in res.diagnostics if d.code == "VL-LEX-009")
    assert err.span.start.line == 2
    assert err.span.start.col == 18


def test_inv_lex_07():
    """INV-LEX-07: empty char literal '' at 2:19."""
    code = "func main() { // INV-LEX-07\n    let c: char = '';\n}"
    source = SourceFile("inv07.vela", code)
    res = Scanner(source).scan()
    assert res.has_errors
    err = next(d for d in res.diagnostics if d.code == "VL-LEX-004")
    assert err.span.start.line == 2
    assert err.span.start.col == 19


def test_all_examples_scan_without_errors():
    """Verify that every examples/*.vela scans with zero errors."""
    examples_dir = Path(__file__).resolve().parents[3] / "examples"
    assert examples_dir.exists(), f"Examples directory not found at {examples_dir}"

    vela_files = sorted(examples_dir.glob("*.vela"))
    assert len(vela_files) == 10, f"Expected 10 example files, found {len(vela_files)}"

    for f in vela_files:
        content = f.read_text(encoding="utf-8")
        source = SourceFile(f.name, content)
        res = Scanner(source).scan()
        assert not res.has_errors, f"Example {f.name} had lexical errors: {res.diagnostics}"
        assert len(res.tokens) > 0
        assert res.tokens[-1].symbol == "$"
