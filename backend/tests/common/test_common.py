"""Unit tests for vela.common modules: source, diagnostics, limits, budget.

Verifies:
- newline normalization (\\r\\n and \\r to \\n)
- offset -> line/col conversions (1-based line/col, multi-line, edge cases)
- every diagnostic code from doc 01 §12 existing exactly once
- budget tracking and limit checks
"""

import pytest

from vela.common.budget import Budget, BudgetExceededError
from vela.common.diagnostics import DIAGNOSTIC_CODES, Diagnostic, Phase, Severity
from vela.common.limits import LIMITS
from vela.common.source import SourceFile, SourceLocation, Span, normalize_newlines


def test_newline_normalization():
    """Verify \\r\\n and \\r are correctly normalized to \\n."""
    assert normalize_newlines("hello\r\nworld\r") == "hello\nworld\n"
    assert normalize_newlines("a\rb\r\nc\n") == "a\nb\nc\n"
    assert normalize_newlines("") == ""


def test_source_file_offset_to_coordinates():
    """Verify offset to line:col conversion with 1-based indexing."""
    content = "func main() {\n    let x: int = 42;\n    show x;\n}"
    source = SourceFile("test.vela", content)

    # Offset 0: start of line 1 -> 1:1
    loc0 = source.location_at(0)
    assert loc0.line == 1
    assert loc0.col == 1
    assert loc0.offset == 0

    # Start of line 2: offset 14 -> 2:1
    loc_line2 = source.location_at(14)
    assert loc_line2.line == 2
    assert loc_line2.col == 1

    # Inside line 2: offset 18 -> 'l' in 'let' -> 2:5
    loc_let = source.location_at(18)
    assert loc_let.line == 2
    assert loc_let.col == 5

    # Span between offsets
    span = source.span_between(18, 21)  # 'let'
    assert span.start.line == 2
    assert span.start.col == 5
    assert span.end.line == 2
    assert span.end.col == 8
    assert source.slice(span) == "let"

    # Out of bounds clamping
    assert source.location_at(-5).offset == 0
    assert source.location_at(1000).offset == len(source.content)


def test_diagnostic_codes_completeness():
    """Verify that every diagnostic code defined in doc 01 §12 exists exactly once."""
    expected_lex = [f"VL-LEX-{i:03d}" for i in range(1, 12)] + ["VL-LIM-001"]
    expected_syn = [f"VL-SYN-{i:03d}" for i in range(1, 4)]
    expected_sem = [f"VL-SEM-{i:03d}" for i in range(1, 24)]
    expected_run = [f"VL-RUN-{i:03d}" for i in range(1, 9)]
    expected_wrn = ["VL-WRN-001"]

    all_expected = expected_lex + expected_syn + expected_sem + expected_run + expected_wrn

    # Total expected codes: 12 + 3 + 23 + 8 + 1 = 47
    assert len(all_expected) == 47

    # Every code exists in DIAGNOSTIC_CODES exactly once
    assert len(DIAGNOSTIC_CODES) == 47
    for code in all_expected:
        assert code in DIAGNOSTIC_CODES, f"Missing diagnostic code: {code}"
        info = DIAGNOSTIC_CODES[code]
        assert info.code == code
        assert len(info.description) > 0


def test_diagnostic_formatting():
    """Verify standard message formatting line:col: error[CODE]: message."""
    loc_start = SourceLocation(line=2, col=18, offset=30)
    loc_end = SourceLocation(line=2, col=23, offset=35)
    span = Span(start=loc_start, end=loc_end)

    diag = Diagnostic.create("VL-LEX-008", span, "malformed number 12abc")
    assert diag.formatted == "2:18: error[VL-LEX-008]: malformed number 12abc"
    assert diag.severity == Severity.ERROR.value
    assert diag.phase == Phase.LEXICAL.value

    # With hint
    diag_hint = Diagnostic.create("VL-SYN-001", span, "expected ';'", hint="add a semicolon")
    assert "hint: add a semicolon" in diag_hint.formatted


def test_budget_enforcement():
    """Verify Budget limits and exceptions."""
    b = Budget("instructions", limit=5)
    for _ in range(5):
        b.tick()
    assert b.count == 5

    with pytest.raises(BudgetExceededError) as exc_info:
        b.tick()
    assert "instructions" in str(exc_info.value)
    assert b.is_truncated is True

    # Soft budget
    b_soft = Budget("steps", limit=3)
    assert b_soft.check_soft() is True
    assert b_soft.check_soft() is True
    assert b_soft.check_soft() is True
    assert b_soft.check_soft() is False  # exceeded
    assert b_soft.is_truncated is True


def test_limits_values():
    """Verify limit constants conform to doc 02 §10."""
    assert LIMITS.MAX_SOURCE_LENGTH == 100_000
    assert LIMITS.MAX_TOKENS == 50_000
    assert LIMITS.MAX_IDENTIFIER_LENGTH == 64
    assert LIMITS.MAX_PARSER_NESTING == 200
    assert LIMITS.MAX_VM_INSTRUCTIONS == 1_000_000
    assert LIMITS.MAX_VM_CALL_DEPTH == 1_000
    assert LIMITS.MAX_REQUEST_SECONDS == 10.0
