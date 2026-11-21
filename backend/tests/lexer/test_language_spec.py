"""Unit tests for vela.language.spec.

Verifies:
- Exactly 26 keywords defined and categorized
- Operators and delimiters complete per doc 01 §2.6
- Precedence table has 8 levels per doc 01 §6.1
- Token regexes compile and match expected samples
- get_language_spec dictionary structure
"""

import re

from vela.language.spec import (
    BASE_TYPES,
    DELIMITERS,
    KEYWORDS,
    KEYWORDS_BY_GROUP,
    OPERATORS,
    PRECEDENCE_TABLE,
    TOKEN_REGEX_TABLE,
    get_language_spec,
)


def test_keywords_count_and_uniqueness():
    """Verify exactly 26 unique keywords per doc 01 §2.4."""
    assert len(KEYWORDS) == 26
    assert len(set(KEYWORDS)) == 26

    # Verify group partitioning sums to 26
    total_grouped = sum(len(group) for group in KEYWORDS_BY_GROUP.values())
    assert total_grouped == 26

    # Verify exact keyword names
    expected = {
        "let",
        "func",
        "int",
        "float",
        "char",
        "string",
        "bool",
        "true",
        "false",
        "if",
        "else",
        "switch",
        "case",
        "default",
        "for",
        "while",
        "do",
        "break",
        "continue",
        "return",
        "show",
        "read",
        "and",
        "or",
        "not",
        "as",
    }
    assert set(KEYWORDS) == expected


def test_base_types():
    """Verify 5 base types per doc 01 §4."""
    assert set(BASE_TYPES) == {"int", "float", "char", "string", "bool"}


def test_delimiters():
    """Verify 9 delimiters per doc 01 §2.6."""
    expected = {"(", ")", "{", "}", "[", "]", ";", ",", ":"}
    assert set(DELIMITERS) == expected
    assert len(DELIMITERS) == 9


def test_operators():
    """Verify operators match doc 01 §2.6."""
    assert "+" in OPERATORS
    assert "-" in OPERATORS
    assert "*" in OPERATORS
    assert "/" in OPERATORS
    assert "%" in OPERATORS
    assert "<=" in OPERATORS
    assert "==" in OPERATORS
    assert "++" in OPERATORS
    assert "--" in OPERATORS
    assert "as" in OPERATORS
    assert "and" in OPERATORS
    assert "or" in OPERATORS
    assert "not" in OPERATORS


def test_precedence_table():
    """Verify precedence levels 1 through 8 per doc 01 §6.1."""
    assert len(PRECEDENCE_TABLE) == 8
    levels = [p.level for p in PRECEDENCE_TABLE]
    assert levels == list(range(1, 9))


def test_token_regexes():
    """Verify regular expressions compile and match valid samples."""
    for pattern in TOKEN_REGEX_TABLE:
        compiled = re.compile(pattern.regex)
        assert compiled is not None

    # Test individual regexes
    patterns = {p.name: p.regex for p in TOKEN_REGEX_TABLE}
    float_re = re.compile(patterns["FLOAT_LIT"])
    int_re = re.compile(patterns["INT_LIT"])
    id_re = re.compile(patterns["ID"])
    str_re = re.compile(patterns["STRING_LIT"])
    char_re = re.compile(patterns["CHAR_LIT"])

    assert float_re.fullmatch("3.14")
    assert not float_re.fullmatch("3.")
    assert not float_re.fullmatch(".14")

    assert int_re.fullmatch("12345")
    assert not int_re.fullmatch("12a")

    assert id_re.fullmatch("foo_bar_123")
    assert id_re.fullmatch("_temp")
    assert not id_re.fullmatch("123foo")

    assert str_re.fullmatch('"hello, world!\\n"')
    assert char_re.fullmatch("'x'")
    assert char_re.fullmatch("'\\n'")


def test_language_spec_dict():
    """Verify get_language_spec returns properly formatted dictionary."""
    spec = get_language_spec()
    assert spec["name"] == "Vela"
    assert len(spec["keywords"]) == 26
    assert len(spec["delimiters"]) == 9
    assert len(spec["precedence"]) == 8
