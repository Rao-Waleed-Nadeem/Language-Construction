"""Vela Language Specification Tables.

Per doc 01 §2, §6.1, §14:
The single source of truth for keywords (26), operators, delimiters,
token regular expressions, and precedence table across the lexer,
API /api/language, and editor syntax highlighting.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TokenCategory(str, Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    INT_LITERAL = "INT_LITERAL"
    FLOAT_LITERAL = "FLOAT_LITERAL"
    CHAR_LITERAL = "CHAR_LITERAL"
    STRING_LITERAL = "STRING_LITERAL"
    OPERATOR = "OPERATOR"
    DELIMITER = "DELIMITER"
    EOF = "EOF"
    ERROR = "ERROR"


# Exactly 26 keywords per doc 01 §2.4
KEYWORDS: tuple[str, ...] = (
    # Declarations (2)
    "let",
    "func",
    # Types (5)
    "int",
    "float",
    "char",
    "string",
    "bool",
    # Literals (2)
    "true",
    "false",
    # Selection (5)
    "if",
    "else",
    "switch",
    "case",
    "default",
    # Loops / Jumps (6)
    "for",
    "while",
    "do",
    "break",
    "continue",
    "return",
    # I/O (2)
    "show",
    "read",
    # Operators & Conversions (4)
    "and",
    "or",
    "not",
    "as",
)

KEYWORDS_BY_GROUP: dict[str, tuple[str, ...]] = {
    "declarations": ("let", "func"),
    "types": ("int", "float", "char", "string", "bool"),
    "literals": ("true", "false"),
    "selection": ("if", "else", "switch", "case", "default"),
    "loops_jumps": ("for", "while", "do", "break", "continue", "return"),
    "io": ("show", "read"),
    "operators": ("and", "or", "not", "as"),
}

BASE_TYPES: tuple[str, ...] = ("int", "float", "char", "string", "bool")

# Operators per doc 01 §2.6
OPERATORS: tuple[str, ...] = (
    # Arithmetic (5)
    "+",
    "-",
    "*",
    "/",
    "%",
    # Relational (6)
    "<",
    "<=",
    ">",
    ">=",
    "==",
    "!=",
    # Logical (3) - also keywords
    "and",
    "or",
    "not",
    # Assignment (6)
    "=",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    # Statement Inc/Dec (2)
    "++",
    "--",
    # Conversion (1) - also keyword
    "as",
)

SYMBOLIC_OPERATORS: tuple[str, ...] = (
    "+",
    "-",
    "*",
    "/",
    "%",
    "<",
    "<=",
    ">",
    ">=",
    "==",
    "!=",
    "=",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "++",
    "--",
)

DELIMITERS: tuple[str, ...] = ("(", ")", "{", "}", "[", "]", ";", ",", ":")


@dataclass(frozen=True)
class PrecedenceLevel:
    level: int
    name: str
    associativity: str  # 'left', 'right', 'none'
    operators: tuple[str, ...]


# Precedence table per doc 01 §6.1 (1 = highest, 8 = lowest)
PRECEDENCE_TABLE: tuple[PrecedenceLevel, ...] = (
    PrecedenceLevel(
        level=1,
        name="Postfix",
        associativity="left",
        operators=("()", "[]"),
    ),
    PrecedenceLevel(
        level=2,
        name="Unary / Cast",
        associativity="right",
        operators=("-", "not", "as"),
    ),
    PrecedenceLevel(
        level=3,
        name="Multiplicative",
        associativity="left",
        operators=("*", "/", "%"),
    ),
    PrecedenceLevel(
        level=4,
        name="Additive",
        associativity="left",
        operators=("+", "-"),
    ),
    PrecedenceLevel(
        level=5,
        name="Relational",
        associativity="left",
        operators=("<", "<=", ">", ">="),
    ),
    PrecedenceLevel(
        level=6,
        name="Equality",
        associativity="left",
        operators=("==", "!="),
    ),
    PrecedenceLevel(
        level=7,
        name="Logical AND",
        associativity="left",
        operators=("and",),
    ),
    PrecedenceLevel(
        level=8,
        name="Logical OR",
        associativity="left",
        operators=("or",),
    ),
)


@dataclass(frozen=True)
class TokenPattern:
    category: TokenCategory
    name: str
    regex: str
    description: str


# Token regular expressions per doc 01 §2
TOKEN_REGEX_TABLE: tuple[TokenPattern, ...] = (
    TokenPattern(
        category=TokenCategory.FLOAT_LITERAL,
        name="FLOAT_LIT",
        regex=r"[0-9]+\.[0-9]+",
        description="Floating-point literal with mandatory digits on both sides",
    ),
    TokenPattern(
        category=TokenCategory.INT_LITERAL,
        name="INT_LIT",
        regex=r"[0-9]+",
        description="Decimal integer literal (0 to 2147483647)",
    ),
    TokenPattern(
        category=TokenCategory.STRING_LITERAL,
        name="STRING_LIT",
        regex=r'"([^"\\\n]|\\[ntr0\\\'"])*"',
        description="Double-quoted string with escape sequences",
    ),
    TokenPattern(
        category=TokenCategory.CHAR_LITERAL,
        name="CHAR_LIT",
        regex=r"'([^'\\\n]|\\[ntr0\\\'\"])'",
        description="Single-quoted character literal (ASCII/Latin-1 <= 255)",
    ),
    TokenPattern(
        category=TokenCategory.IDENTIFIER,
        name="ID",
        regex=r"[A-Za-z_][A-Za-z0-9_]*",
        description="ASCII identifier up to 64 chars",
    ),
)


def get_language_spec() -> dict[str, Any]:
    """Return dictionary representation for /api/language and editor configuration."""
    return {
        "name": "Vela",
        "file_extension": ".vela",
        "keywords": list(KEYWORDS),
        "keywords_by_group": {k: list(v) for k, v in KEYWORDS_BY_GROUP.items()},
        "base_types": list(BASE_TYPES),
        "operators": list(OPERATORS),
        "symbolic_operators": list(SYMBOLIC_OPERATORS),
        "delimiters": list(DELIMITERS),
        "precedence": [
            {
                "level": p.level,
                "name": p.name,
                "associativity": p.associativity,
                "operators": list(p.operators),
            }
            for p in PRECEDENCE_TABLE
        ],
        "token_patterns": [
            {
                "category": tp.category.value,
                "name": tp.name,
                "regex": tp.regex,
                "description": tp.description,
            }
            for tp in TOKEN_REGEX_TABLE
        ],
    }
