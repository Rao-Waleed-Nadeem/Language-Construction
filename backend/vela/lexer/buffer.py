"""Two-buffer input scheme with sentinels for lexical analysis.

Per doc 01 §2.5, doc 04 §4 and textbook (Dragon Book §3.2):
- Two buffers B1 and B2, each of configurable size N (default 4096).
- Each buffer ends with a sentinel character (SENTINEL = '\\0').
- Pointers: lexeme_begin and forward.
- Handles buffer refills when forward hits a sentinel at the end of a buffer.
- Records refill and sentinel events in buffer_trace for the UI.
"""

from __future__ import annotations

from typing import Any

SENTINEL = "\0"


class InputBuffer:
    """Two-buffer stream reader with sentinels."""

    def __init__(self, text: str, buffer_size: int = 4096) -> None:
        self.text: str = text
        self.buffer_size: int = max(4, buffer_size)
        self.total_length: int = len(text)

        # Source text reading cursor
        self._source_pos: int = 0

        # Buffers: buffer_size + 1 (for sentinel)
        self._b1: list[str] = [SENTINEL] * (self.buffer_size + 1)
        self._b2: list[str] = [SENTINEL] * (self.buffer_size + 1)

        # Total characters loaded into each buffer
        self._b1_len: int = 0
        self._b2_len: int = 0

        # Absolute source offset at the start of B1 and B2
        self._b1_start_offset: int = 0
        self._b2_start_offset: int = 0

        # Which buffer forward is currently in (1 or 2)
        self._current_buffer: int = 1
        self._buf_pos: int = 0  # Index within current buffer

        # Absolute offset tracking
        self.lexeme_begin_offset: int = 0
        self.forward_offset: int = 0

        # Trace for UI / verification
        self.trace: list[dict[str, Any]] = []

        # Load initial buffer B1
        self._load_b1()

    def _load_b1(self) -> None:
        chunk = self.text[self._source_pos : self._source_pos + self.buffer_size]
        self._b1_start_offset = self._source_pos
        self._source_pos += len(chunk)
        self._b1_len = len(chunk)
        for i, ch in enumerate(chunk):
            self._b1[i] = ch
        self._b1[self._b1_len] = SENTINEL
        self.trace.append(
            {
                "event": "load_buffer",
                "buffer": 1,
                "offset": self._b1_start_offset,
                "length": self._b1_len,
            }
        )

    def _load_b2(self) -> None:
        chunk = self.text[self._source_pos : self._source_pos + self.buffer_size]
        self._b2_start_offset = self._source_pos
        self._source_pos += len(chunk)
        self._b2_len = len(chunk)
        for i, ch in enumerate(chunk):
            self._b2[i] = ch
        self._b2[self._b2_len] = SENTINEL
        self.trace.append(
            {
                "event": "load_buffer",
                "buffer": 2,
                "offset": self._b2_start_offset,
                "length": self._b2_len,
            }
        )

    @property
    def is_eof(self) -> bool:
        return self.forward_offset >= self.total_length

    def advance(self) -> str:
        """Advance the forward pointer by one character and return it.

        Returns SENTINEL ('\\0') when end of source text is reached.
        """
        if self.forward_offset >= self.total_length:
            return SENTINEL

        buf = self._b1 if self._current_buffer == 1 else self._b2
        ch = buf[self._buf_pos]

        if ch == SENTINEL:
            # Check if we hit the end-of-buffer sentinel
            if self._current_buffer == 1:
                self.trace.append(
                    {"event": "sentinel_hit", "buffer": 1, "offset": self.forward_offset}
                )
                self._load_b2()
                self._current_buffer = 2
                self._buf_pos = 0
                buf = self._b2
                ch = buf[self._buf_pos]
            else:
                self.trace.append(
                    {"event": "sentinel_hit", "buffer": 2, "offset": self.forward_offset}
                )
                self._load_b1()
                self._current_buffer = 1
                self._buf_pos = 0
                buf = self._b1
                ch = buf[self._buf_pos]

            if ch == SENTINEL:
                # True EOF
                return SENTINEL

        self._buf_pos += 1
        self.forward_offset += 1
        return ch

    def peek(self) -> str:
        """Look at the current forward character without advancing."""
        if self.forward_offset >= self.total_length:
            return SENTINEL
        return self.text[self.forward_offset]

    def peek_next(self, distance: int = 1) -> str:
        """Look ahead by distance characters."""
        target = self.forward_offset + distance
        if target >= self.total_length:
            return SENTINEL
        return self.text[target]

    def retract(self, count: int = 1) -> None:
        """Move the forward pointer backwards by count positions."""
        for _ in range(count):
            if self.forward_offset <= self.lexeme_begin_offset:
                break
            self.forward_offset -= 1
            if self._buf_pos > 0:
                self._buf_pos -= 1
            else:
                # Crossed buffer boundary backwards
                if self._current_buffer == 1:
                    self._current_buffer = 2
                    self._buf_pos = self._b2_len - 1
                else:
                    self._current_buffer = 1
                    self._buf_pos = self._b1_len - 1

    def current_lexeme(self) -> str:
        """Return the source substring between lexeme_begin and forward."""
        return self.text[self.lexeme_begin_offset : self.forward_offset]

    def commit_lexeme(self) -> None:
        """Set lexeme_begin = forward."""
        self.lexeme_begin_offset = self.forward_offset
