"""Diagnostic system and comprehensive error codes.

Per doc 01 §12:
Message format: `line:col: error[CODE]: message` plus optional `hint`.
Every diagnostic has: `code`, `severity`, `phase`, `message`, `span`, optional `hint`.
Phase gating: lexical -> syntax -> semantic -> runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from vela.common.source import Span


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class Phase(str, Enum):
    LEXICAL = "lexical"
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    RUNTIME = "runtime"


@dataclass(frozen=True)
class DiagnosticCodeInfo:
    code: str
    phase: Phase
    default_severity: Severity
    description: str


# All standardized diagnostic codes per doc 01 §12
DIAGNOSTIC_CODES: dict[str, DiagnosticCodeInfo] = {
    # Lexical (VL-LEX-001 ... 011, VL-LIM-001)
    "VL-LEX-001": DiagnosticCodeInfo(
        "VL-LEX-001", Phase.LEXICAL, Severity.ERROR, "invalid character"
    ),
    "VL-LEX-002": DiagnosticCodeInfo(
        "VL-LEX-002", Phase.LEXICAL, Severity.ERROR, "unterminated string literal"
    ),
    "VL-LEX-003": DiagnosticCodeInfo(
        "VL-LEX-003", Phase.LEXICAL, Severity.ERROR, "unterminated char literal"
    ),
    "VL-LEX-004": DiagnosticCodeInfo(
        "VL-LEX-004", Phase.LEXICAL, Severity.ERROR, "empty char literal"
    ),
    "VL-LEX-005": DiagnosticCodeInfo(
        "VL-LEX-005", Phase.LEXICAL, Severity.ERROR, "char literal has more than one character"
    ),
    "VL-LEX-006": DiagnosticCodeInfo(
        "VL-LEX-006", Phase.LEXICAL, Severity.ERROR, "invalid escape sequence"
    ),
    "VL-LEX-007": DiagnosticCodeInfo(
        "VL-LEX-007", Phase.LEXICAL, Severity.ERROR, "unterminated block comment"
    ),
    "VL-LEX-008": DiagnosticCodeInfo(
        "VL-LEX-008", Phase.LEXICAL, Severity.ERROR, "malformed number"
    ),
    "VL-LEX-009": DiagnosticCodeInfo(
        "VL-LEX-009", Phase.LEXICAL, Severity.ERROR, "integer literal out of range"
    ),
    "VL-LEX-010": DiagnosticCodeInfo(
        "VL-LEX-010", Phase.LEXICAL, Severity.ERROR, "identifier longer than 64 characters"
    ),
    "VL-LEX-011": DiagnosticCodeInfo(
        "VL-LEX-011", Phase.LEXICAL, Severity.ERROR, "char literal outside Latin-1 (code > 255)"
    ),
    "VL-LIM-001": DiagnosticCodeInfo(
        "VL-LIM-001", Phase.LEXICAL, Severity.ERROR, "more than 50 000 tokens (compiler limit)"
    ),
    # Syntax (VL-SYN-001 ... 003)
    "VL-SYN-001": DiagnosticCodeInfo(
        "VL-SYN-001", Phase.SYNTAX, Severity.ERROR, "unexpected token"
    ),
    "VL-SYN-002": DiagnosticCodeInfo(
        "VL-SYN-002", Phase.SYNTAX, Severity.ERROR, "unexpected end of file"
    ),
    "VL-SYN-003": DiagnosticCodeInfo(
        "VL-SYN-003", Phase.SYNTAX, Severity.ERROR, "nesting too deep (> 200)"
    ),
    # Semantic (VL-SEM-001 ... 023)
    "VL-SEM-001": DiagnosticCodeInfo(
        "VL-SEM-001", Phase.SEMANTIC, Severity.ERROR, "undeclared variable"
    ),
    "VL-SEM-002": DiagnosticCodeInfo(
        "VL-SEM-002", Phase.SEMANTIC, Severity.ERROR, "redeclaration in the same scope"
    ),
    "VL-SEM-003": DiagnosticCodeInfo(
        "VL-SEM-003", Phase.SEMANTIC, Severity.ERROR, "type mismatch in initialization/assignment"
    ),
    "VL-SEM-004": DiagnosticCodeInfo(
        "VL-SEM-004", Phase.SEMANTIC, Severity.ERROR, "invalid operand types for operator"
    ),
    "VL-SEM-005": DiagnosticCodeInfo(
        "VL-SEM-005", Phase.SEMANTIC, Severity.ERROR, "condition is not bool"
    ),
    "VL-SEM-006": DiagnosticCodeInfo(
        "VL-SEM-006",
        Phase.SEMANTIC,
        Severity.ERROR,
        "call to undeclared function / name is not a function",
    ),
    "VL-SEM-007": DiagnosticCodeInfo(
        "VL-SEM-007", Phase.SEMANTIC, Severity.ERROR, "wrong number of arguments"
    ),
    "VL-SEM-008": DiagnosticCodeInfo(
        "VL-SEM-008", Phase.SEMANTIC, Severity.ERROR, "argument type mismatch"
    ),
    "VL-SEM-009": DiagnosticCodeInfo(
        "VL-SEM-009", Phase.SEMANTIC, Severity.ERROR, "return value/type mismatch"
    ),
    "VL-SEM-010": DiagnosticCodeInfo(
        "VL-SEM-010", Phase.SEMANTIC, Severity.ERROR, "missing return on some path"
    ),
    "VL-SEM-011": DiagnosticCodeInfo(
        "VL-SEM-011", Phase.SEMANTIC, Severity.ERROR, "break/continue outside a valid construct"
    ),
    "VL-SEM-012": DiagnosticCodeInfo(
        "VL-SEM-012", Phase.SEMANTIC, Severity.ERROR, "duplicate case label"
    ),
    "VL-SEM-013": DiagnosticCodeInfo(
        "VL-SEM-013",
        Phase.SEMANTIC,
        Severity.ERROR,
        "switch expression not int/char, or label type mismatch",
    ),
    "VL-SEM-014": DiagnosticCodeInfo(
        "VL-SEM-014", Phase.SEMANTIC, Severity.ERROR, "array index not int"
    ),
    "VL-SEM-015": DiagnosticCodeInfo(
        "VL-SEM-015", Phase.SEMANTIC, Severity.ERROR, "indexing a non-array"
    ),
    "VL-SEM-016": DiagnosticCodeInfo(
        "VL-SEM-016", Phase.SEMANTIC, Severity.ERROR, "too many array initializers"
    ),
    "VL-SEM-017": DiagnosticCodeInfo(
        "VL-SEM-017", Phase.SEMANTIC, Severity.ERROR, "invalid array size (not 1..10 000)"
    ),
    "VL-SEM-018": DiagnosticCodeInfo(
        "VL-SEM-018", Phase.SEMANTIC, Severity.ERROR, "missing/ill-formed main"
    ),
    "VL-SEM-019": DiagnosticCodeInfo(
        "VL-SEM-019", Phase.SEMANTIC, Severity.ERROR, "invalid as conversion"
    ),
    "VL-SEM-020": DiagnosticCodeInfo(
        "VL-SEM-020", Phase.SEMANTIC, Severity.ERROR, "global initializer not a literal"
    ),
    "VL-SEM-021": DiagnosticCodeInfo(
        "VL-SEM-021", Phase.SEMANTIC, Severity.ERROR, "array used as a value"
    ),
    "VL-SEM-022": DiagnosticCodeInfo(
        "VL-SEM-022", Phase.SEMANTIC, Severity.ERROR, "constant index out of range"
    ),
    "VL-SEM-023": DiagnosticCodeInfo(
        "VL-SEM-023", Phase.SEMANTIC, Severity.ERROR, "void function used as a value"
    ),
    # Runtime (VL-RUN-001 ... 008)
    "VL-RUN-001": DiagnosticCodeInfo(
        "VL-RUN-001", Phase.RUNTIME, Severity.ERROR, "division or modulo by zero"
    ),
    "VL-RUN-002": DiagnosticCodeInfo(
        "VL-RUN-002", Phase.RUNTIME, Severity.ERROR, "array index out of bounds"
    ),
    "VL-RUN-003": DiagnosticCodeInfo(
        "VL-RUN-003", Phase.RUNTIME, Severity.ERROR, "input exhausted"
    ),
    "VL-RUN-004": DiagnosticCodeInfo(
        "VL-RUN-004", Phase.RUNTIME, Severity.ERROR, "invalid input format"
    ),
    "VL-RUN-005": DiagnosticCodeInfo(
        "VL-RUN-005", Phase.RUNTIME, Severity.ERROR, "conversion out of range"
    ),
    "VL-RUN-006": DiagnosticCodeInfo(
        "VL-RUN-006", Phase.RUNTIME, Severity.ERROR, "call stack overflow (depth > 1000)"
    ),
    "VL-RUN-007": DiagnosticCodeInfo(
        "VL-RUN-007", Phase.RUNTIME, Severity.ERROR, "instruction budget exceeded"
    ),
    "VL-RUN-008": DiagnosticCodeInfo(
        "VL-RUN-008", Phase.RUNTIME, Severity.ERROR, "output limit exceeded"
    ),
    # Warnings (VL-WRN-001)
    "VL-WRN-001": DiagnosticCodeInfo(
        "VL-WRN-001", Phase.SEMANTIC, Severity.WARNING, "unused local variable"
    ),
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: str
    phase: str
    message: str
    span: Span
    hint: str | None = None

    def __post_init__(self) -> None:
        if self.code not in DIAGNOSTIC_CODES:
            # Allow custom or dynamic codes but validate format
            pass

    @property
    def formatted(self) -> str:
        """Formatted per doc 01 §12: `line:col: error[CODE]: message`"""
        loc = self.span.start
        msg = f"{loc.line}:{loc.col}: {self.severity}[{self.code}]: {self.message}"
        if self.hint:
            msg += f"\n  hint: {self.hint}"
        return msg

    def to_dict(self) -> dict:
        d = {
            "code": self.code,
            "severity": self.severity,
            "phase": self.phase,
            "message": self.message,
            "span": self.span.to_dict(),
        }
        if self.hint:
            d["hint"] = self.hint
        return d

    @classmethod
    def from_dict(cls, data: dict) -> Diagnostic:
        return cls(
            code=data["code"],
            severity=data["severity"],
            phase=data["phase"],
            message=data["message"],
            span=Span.from_dict(data["span"]),
            hint=data.get("hint"),
        )

    @classmethod
    def create(
        cls,
        code: str,
        span: Span,
        message: str | None = None,
        hint: str | None = None,
        severity: str | None = None,
        phase: str | None = None,
    ) -> Diagnostic:
        info = DIAGNOSTIC_CODES.get(code)
        eff_severity = severity or (info.default_severity.value if info else Severity.ERROR.value)
        eff_phase = phase or (info.phase.value if info else Phase.SEMANTIC.value)
        eff_message = message or (info.description if info else code)
        return cls(
            code=code,
            severity=eff_severity,
            phase=eff_phase,
            message=eff_message,
            span=span,
            hint=hint,
        )
