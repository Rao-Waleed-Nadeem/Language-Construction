"""Vela Lexical Analyzer (Scanner).

Per doc 01 §2, §12, §16.1 and doc 04:
- Hand-written scanner driven by explicit DFAs.
- Longest match (maximal munch) disambiguation.
- Two-buffer scheme with sentinels and refill tracking.
- Collects all lexical errors (VL-LEX-001...011, VL-LIM-001).
- Emits detailed DFA traces and buffer traces.
"""

from __future__ import annotations

from typing import Any

from vela.common.diagnostics import Diagnostic
from vela.common.limits import LIMITS
from vela.common.source import SourceFile, Span
from vela.language.spec import (
    DELIMITERS,
    KEYWORDS,
    TokenCategory,
)
from vela.lexer.buffer import SENTINEL, InputBuffer
from vela.lexer.fsm import (
    DFASimulator,
    build_identifier_dfa,
    build_number_dfa,
    build_operator_dfa,
)
from vela.lexer.tokens import LexResult, Token


class Scanner:
    """Scans Vela source code into tokens."""

    def __init__(self, source: SourceFile, buffer_size: int = 4096) -> None:
        self.source: SourceFile = source
        self.buffer: InputBuffer = InputBuffer(source.content, buffer_size=buffer_size)
        self.tokens: list[Token] = []
        self.diagnostics: list[Diagnostic] = []
        self.dfa_trace: list[dict[str, Any]] = []

        # Built DFAs
        self.id_dfa = build_identifier_dfa()
        self.num_dfa = build_number_dfa()
        self.op_dfa = build_operator_dfa()

    def scan(self) -> LexResult:
        """Run the scanner across the entire source input."""
        while not self.buffer.is_eof:
            # Cooperative limit check
            if len(self.tokens) >= LIMITS.MAX_TOKENS:
                loc = self.source.location_at(self.buffer.forward_offset)
                span = Span(loc, loc)
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-LIM-001",
                        span,
                        "more than 50 000 tokens (compiler limit; scan stopped)",
                    )
                )
                break

            ch = self.buffer.advance()
            if ch == SENTINEL:
                break

            # 1. Skip whitespace
            if ch in (" ", "\t", "\n", "\r"):
                self.buffer.commit_lexeme()
                continue

            # 2. Comments (// and /* ... */)
            if ch == "/":
                next_ch = self.buffer.peek()
                if next_ch == "/":
                    # Line comment: consume until newline or EOF
                    self.buffer.advance()
                    while not self.buffer.is_eof:
                        c = self.buffer.advance()
                        if c == "\n" or c == SENTINEL:
                            break
                    self.buffer.commit_lexeme()
                    continue
                elif next_ch == "*":
                    # Block comment: consume until */
                    start_offset = self.buffer.lexeme_begin_offset
                    self.buffer.advance()  # consume '*'
                    closed = False
                    while not self.buffer.is_eof:
                        c = self.buffer.advance()
                        if c == "*" and self.buffer.peek() == "/":
                            self.buffer.advance()  # consume '/'
                            closed = True
                            break
                        if c == SENTINEL:
                            break

                    if not closed:
                        # VL-LEX-007: unterminated block comment at start /*
                        span = self.source.span_between(start_offset, start_offset + 2)
                        self.diagnostics.append(
                            Diagnostic.create(
                                "VL-LEX-007",
                                span,
                                "unterminated block comment",
                            )
                        )
                    self.buffer.commit_lexeme()
                    continue

            # Retract initial char so DFAs and token handlers see full lexeme
            self.buffer.retract(1)
            start_offset = self.buffer.forward_offset
            ch = self.buffer.peek()

            # 3. String literals ("...")
            if ch == '"':
                self._scan_string(start_offset)
                continue

            # 4. Character literals ('...')
            if ch == "'":
                self._scan_char(start_offset)
                continue

            # 5. Number literals (Integer & Float) or Malformed Numbers
            if ch.isdigit():
                self._scan_number(start_offset)
                continue

            # 6. Identifiers & Keywords
            if ch.isalpha() or ch == "_":
                self._scan_identifier_or_keyword(start_offset)
                continue

            # 7. Operators & Delimiters
            if self._scan_operator_or_delimiter(start_offset):
                continue

            # 8. Unrecognized / invalid character -> VL-LEX-001
            bad_ch = self.buffer.advance()
            span = self.source.span_between(start_offset, start_offset + 1)
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-LEX-001",
                    span,
                    f"invalid character '{bad_ch}'",
                )
            )
            self.buffer.commit_lexeme()

        # Emit EOF token
        eof_loc = self.source.location_at(len(self.source.content))
        eof_span = Span(eof_loc, eof_loc)
        self.tokens.append(
            Token(
                category=TokenCategory.EOF,
                symbol="$",
                lexeme="",
                value=None,
                span=eof_span,
            )
        )

        return LexResult(
            tokens=self.tokens,
            diagnostics=self.diagnostics,
            dfa_trace=self.dfa_trace,
            buffer_trace=self.buffer.trace,
        )

    def _scan_string(self, start_offset: int) -> None:
        self.buffer.advance()  # consume opening quote
        chars: list[str] = []
        has_error = False

        while True:
            if self.buffer.is_eof:
                span = self.source.span_between(start_offset, start_offset + 1)
                self.diagnostics.append(
                    Diagnostic.create("VL-LEX-002", span, "unterminated string literal")
                )
                has_error = True
                break

            ch = self.buffer.advance()
            if ch == "\n" or ch == SENTINEL:
                span = self.source.span_between(start_offset, start_offset + 1)
                self.diagnostics.append(
                    Diagnostic.create("VL-LEX-002", span, "unterminated string literal")
                )
                has_error = True
                break

            if ch == '"':
                # Successfully closed string
                break

            if ch == "\\":
                # Escape sequence
                esc_start = self.buffer.forward_offset - 1
                if self.buffer.is_eof:
                    span = self.source.span_between(esc_start, esc_start + 1)
                    self.diagnostics.append(
                        Diagnostic.create("VL-LEX-006", span, "invalid escape sequence")
                    )
                    has_error = True
                    break

                esc_ch = self.buffer.advance()
                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "0": "\0",
                    "\\": "\\",
                    "'": "'",
                    '"': '"',
                }
                if esc_ch in escape_map:
                    chars.append(escape_map[esc_ch])
                else:
                    span = self.source.span_between(esc_start, esc_start + 1)
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-LEX-006",
                            span,
                            f"invalid escape sequence '\\{esc_ch}'",
                        )
                    )
                    has_error = True
                    chars.append(esc_ch)
            else:
                chars.append(ch)

        end_offset = self.buffer.forward_offset
        span = self.source.span_between(start_offset, end_offset)
        lexeme = self.source.slice(span)
        val = "".join(chars) if not has_error else None

        self.tokens.append(
            Token(
                category=TokenCategory.STRING_LITERAL,
                symbol="STRING_LIT",
                lexeme=lexeme,
                value=val,
                span=span,
            )
        )
        self.buffer.commit_lexeme()

    def _scan_char(self, start_offset: int) -> None:
        self.buffer.advance()  # consume opening quote
        chars: list[str] = []
        has_error = False

        if self.buffer.peek() == "'":
            # Empty char literal: '' -> VL-LEX-004
            self.buffer.advance()  # consume closing quote
            span = self.source.span_between(start_offset, self.buffer.forward_offset)
            self.diagnostics.append(
                Diagnostic.create("VL-LEX-004", span, "empty char literal")
            )
            self.tokens.append(
                Token(
                    category=TokenCategory.CHAR_LITERAL,
                    symbol="CHAR_LIT",
                    lexeme="''",
                    value=None,
                    span=span,
                )
            )
            self.buffer.commit_lexeme()
            return

        while True:
            if self.buffer.is_eof:
                span = self.source.span_between(start_offset, start_offset + 1)
                self.diagnostics.append(
                    Diagnostic.create("VL-LEX-003", span, "unterminated char literal")
                )
                has_error = True
                break

            ch = self.buffer.advance()
            if ch == "\n" or ch == SENTINEL:
                span = self.source.span_between(start_offset, start_offset + 1)
                self.diagnostics.append(
                    Diagnostic.create("VL-LEX-003", span, "unterminated char literal")
                )
                has_error = True
                break

            if ch == "'":
                # Closing quote
                break

            if ch == "\\":
                esc_start = self.buffer.forward_offset - 1
                if self.buffer.is_eof:
                    span = self.source.span_between(esc_start, esc_start + 1)
                    self.diagnostics.append(
                        Diagnostic.create("VL-LEX-006", span, "invalid escape sequence")
                    )
                    has_error = True
                    break
                esc_ch = self.buffer.advance()
                escape_map = {
                    "n": "\n",
                    "t": "\t",
                    "r": "\r",
                    "0": "\0",
                    "\\": "\\",
                    "'": "'",
                    '"': '"',
                }
                if esc_ch in escape_map:
                    chars.append(escape_map[esc_ch])
                else:
                    span = self.source.span_between(esc_start, esc_start + 1)
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-LEX-006",
                            span,
                            f"invalid escape sequence '\\{esc_ch}'",
                        )
                    )
                    has_error = True
                    chars.append(esc_ch)
            else:
                chars.append(ch)

        end_offset = self.buffer.forward_offset
        span = self.source.span_between(start_offset, end_offset)
        lexeme = self.source.slice(span)

        if not has_error:
            if len(chars) > 1:
                # VL-LEX-005: char literal has more than one character
                err_span = self.source.span_between(start_offset, start_offset + 1)
                self.diagnostics.append(
                    Diagnostic.create(
                        "VL-LEX-005",
                        err_span,
                        "char literal has more than one character",
                    )
                )
                val = None
            elif len(chars) == 1:
                char_val = chars[0]
                if ord(char_val) > 255:
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-LEX-011",
                            span,
                            f"char literal outside Latin-1 (code {ord(char_val)} > 255)",
                        )
                    )
                    val = None
                else:
                    val = char_val
            else:
                val = None
        else:
            val = None

        self.tokens.append(
            Token(
                category=TokenCategory.CHAR_LITERAL,
                symbol="CHAR_LIT",
                lexeme=lexeme,
                value=val,
                span=span,
            )
        )
        self.buffer.commit_lexeme()

    def _scan_number(self, start_offset: int) -> None:
        # Check if this number is immediately followed by alpha/_ (VL-LEX-008, e.g. 12abc)
        remaining = self.source.content[start_offset:]

        # Run NumberDFA simulation
        sim = DFASimulator.simulate(self.num_dfa, remaining)

        # Check for malformed number with letter/underscore suffix (e.g. 12abc)
        # Advance digits first
        digits_len = 0
        while digits_len < len(remaining) and remaining[digits_len].isdigit():
            digits_len += 1

        if digits_len < len(remaining) and (
            remaining[digits_len].isalpha() or remaining[digits_len] == "_"
        ):
            # Malformed number: consume the entire alphanumeric run
            malformed_len = digits_len
            while malformed_len < len(remaining) and (
                remaining[malformed_len].isalnum() or remaining[malformed_len] == "_"
            ):
                malformed_len += 1

            for _ in range(malformed_len):
                self.buffer.advance()

            span = self.source.span_between(start_offset, start_offset + malformed_len)
            lexeme = self.source.slice(span)
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-LEX-008",
                    span,
                    f"malformed number '{lexeme}'",
                )
            )
            self.tokens.append(
                Token(
                    category=TokenCategory.ERROR,
                    symbol="INT_LIT",
                    lexeme=lexeme,
                    value=None,
                    span=span,
                )
            )
            self.buffer.commit_lexeme()
            return

        # Check for malformed float like '12.' without digits following
        if (
            digits_len < len(remaining)
            and remaining[digits_len] == "."
            and (
                digits_len + 1 >= len(remaining)
                or not remaining[digits_len + 1].isdigit()
            )
        ):
            # Consume the number and dot
            for _ in range(digits_len + 1):
                self.buffer.advance()
            span = self.source.span_between(start_offset, start_offset + digits_len + 1)
            lexeme = self.source.slice(span)
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-LEX-008",
                    span,
                    f"malformed number '{lexeme}'",
                )
            )
            self.tokens.append(
                Token(
                    category=TokenCategory.ERROR,
                    symbol="FLOAT_LIT",
                    lexeme=lexeme,
                    value=None,
                    span=span,
                )
            )
            self.buffer.commit_lexeme()
            return

        if sim.matched and sim.token_type is not None:
            for _ in range(sim.matched_length):
                self.buffer.advance()

            span = self.source.span_between(start_offset, start_offset + sim.matched_length)
            lexeme = self.source.slice(span)

            # Record DFA trace
            self.dfa_trace.append(
                {
                    "token": lexeme,
                    "dfa": self.num_dfa.name,
                    "path": [
                        {
                            "from": s.state,
                            "char": s.char,
                            "to": s.next_state,
                            "cond": s.condition,
                        }
                        for s in sim.path
                    ],
                }
            )

            if sim.token_type == "INT_LIT":
                val = int(lexeme)
                if val > 2_147_483_647:
                    # VL-LEX-009: integer out of range
                    self.diagnostics.append(
                        Diagnostic.create(
                            "VL-LEX-009",
                            span,
                            f"integer literal out of range '{lexeme}' (max 2147483647)",
                        )
                    )
                self.tokens.append(
                    Token(
                        category=TokenCategory.INT_LITERAL,
                        symbol="INT_LIT",
                        lexeme=lexeme,
                        value=val,
                        span=span,
                    )
                )
            else:
                self.tokens.append(
                    Token(
                        category=TokenCategory.FLOAT_LITERAL,
                        symbol="FLOAT_LIT",
                        lexeme=lexeme,
                        value=float(lexeme),
                        span=span,
                    )
                )
            self.buffer.commit_lexeme()
        else:
            # Fallback advance single digit
            self.buffer.advance()
            span = self.source.span_between(start_offset, start_offset + 1)
            lexeme = self.source.slice(span)
            self.tokens.append(
                Token(
                    category=TokenCategory.INT_LITERAL,
                    symbol="INT_LIT",
                    lexeme=lexeme,
                    value=int(lexeme),
                    span=span,
                )
            )
            self.buffer.commit_lexeme()

    def _scan_identifier_or_keyword(self, start_offset: int) -> None:
        remaining = self.source.content[start_offset:]
        sim = DFASimulator.simulate(self.id_dfa, remaining)
        matched_len = sim.matched_length if sim.matched else 1

        for _ in range(matched_len):
            self.buffer.advance()

        span = self.source.span_between(start_offset, start_offset + matched_len)
        lexeme = self.source.slice(span)

        # Check identifier length limit (VL-LEX-010 > 64 chars)
        if len(lexeme) > LIMITS.MAX_IDENTIFIER_LENGTH:
            self.diagnostics.append(
                Diagnostic.create(
                    "VL-LEX-010",
                    span,
                    f"identifier longer than 64 characters ({len(lexeme)} chars)",
                )
            )

        # Record DFA trace
        self.dfa_trace.append(
            {
                "token": lexeme,
                "dfa": self.id_dfa.name,
                "path": [
                    {
                        "from": s.state,
                        "char": s.char,
                        "to": s.next_state,
                        "cond": s.condition,
                    }
                    for s in sim.path
                ],
            }
        )

        # Disambiguate Keyword vs Identifier
        if lexeme in KEYWORDS:
            if lexeme in ("true", "false"):
                self.tokens.append(
                    Token(
                        category=TokenCategory.KEYWORD,
                        symbol=lexeme,
                        lexeme=lexeme,
                        value=(lexeme == "true"),
                        span=span,
                    )
                )
            elif lexeme in ("and", "or", "not", "as"):
                self.tokens.append(
                    Token(
                        category=TokenCategory.OPERATOR,
                        symbol=lexeme,
                        lexeme=lexeme,
                        value=None,
                        span=span,
                    )
                )
            else:
                self.tokens.append(
                    Token(
                        category=TokenCategory.KEYWORD,
                        symbol=lexeme,
                        lexeme=lexeme,
                        value=None,
                        span=span,
                    )
                )
        else:
            self.tokens.append(
                Token(
                    category=TokenCategory.IDENTIFIER,
                    symbol="ID",
                    lexeme=lexeme,
                    value=None,
                    span=span,
                )
            )
        self.buffer.commit_lexeme()

    def _scan_operator_or_delimiter(self, start_offset: int) -> bool:
        remaining = self.source.content[start_offset:]

        # 1. Try Operator DFA first for longest match (<=, ++, ==, etc.)
        sim = DFASimulator.simulate(self.op_dfa, remaining)
        if sim.matched and sim.token_type is not None:
            for _ in range(sim.matched_length):
                self.buffer.advance()

            span = self.source.span_between(start_offset, start_offset + sim.matched_length)
            lexeme = self.source.slice(span)

            self.dfa_trace.append(
                {
                    "token": lexeme,
                    "dfa": self.op_dfa.name,
                    "path": [
                        {
                            "from": s.state,
                            "char": s.char,
                            "to": s.next_state,
                            "cond": s.condition,
                        }
                        for s in sim.path
                    ],
                }
            )

            self.tokens.append(
                Token(
                    category=TokenCategory.OPERATOR,
                    symbol=lexeme,
                    lexeme=lexeme,
                    value=None,
                    span=span,
                )
            )
            self.buffer.commit_lexeme()
            return True

        # 2. Check single-character delimiters: ( ) { } [ ] ; , :
        ch = remaining[0]
        if ch in DELIMITERS:
            self.buffer.advance()
            span = self.source.span_between(start_offset, start_offset + 1)
            self.tokens.append(
                Token(
                    category=TokenCategory.DELIMITER,
                    symbol=ch,
                    lexeme=ch,
                    value=None,
                    span=span,
                )
            )
            self.buffer.commit_lexeme()
            return True

        return False
