"""Source text management, coordinate tracking, and spans.

Per doc 01 §2.1 and doc 02 §5:
- UTF-8 text file. `\\r\\n` and `\\r` are normalized to `\\n` before scanning.
- Positions are 1-based `line:column`; column counts Unicode code points.
- Spans: start (inclusive) and end (exclusive) with line, col, and offset.
"""

from __future__ import annotations

from dataclasses import dataclass


def normalize_newlines(text: str) -> str:
    """Normalize \\r\\n and \\r to \\n."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


@dataclass(frozen=True)
class SourceLocation:
    """A single coordinate in source code.

    Line and column are 1-based.
    Offset is 0-based character index in the normalized source.
    """

    line: int
    col: int
    offset: int

    @property
    def column(self) -> int:
        return self.col

    def __lt__(self, other: SourceLocation) -> bool:
        return self.offset < other.offset

    def __le__(self, other: SourceLocation) -> bool:
        return self.offset <= other.offset

    def __gt__(self, other: SourceLocation) -> bool:
        return self.offset > other.offset

    def __ge__(self, other: SourceLocation) -> bool:
        return self.offset >= other.offset

    def __str__(self) -> str:
        return f"{self.line}:{self.col}"

    def to_dict(self) -> dict[str, int]:
        return {"line": self.line, "col": self.col, "offset": self.offset}

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> SourceLocation:
        return cls(line=data["line"], col=data["col"], offset=data["offset"])


@dataclass(frozen=True)
class Span:
    """A range in source code.

    Start is inclusive; end is exclusive.
    """

    start: SourceLocation
    end: SourceLocation

    def __str__(self) -> str:
        return f"{self.start}-{self.end}"

    def to_dict(self) -> dict[str, dict[str, int]]:
        return {"start": self.start.to_dict(), "end": self.end.to_dict()}

    @classmethod
    def zero(cls) -> Span:
        loc = SourceLocation(1, 1, 0)
        return cls(loc, loc)

    @classmethod
    def from_dict(cls, data: dict[str, dict[str, int]]) -> Span:
        return cls(
            start=SourceLocation.from_dict(data["start"]),
            end=SourceLocation.from_dict(data["end"]),
        )

    @classmethod
    def point(cls, loc: SourceLocation) -> Span:
        """Create a zero-length point span."""
        return cls(start=loc, end=loc)


class SourceFile:
    """Represents a source file with fast offset-to-coordinate lookup."""

    def __init__(self, filename: str, content: str) -> None:
        self.filename: str = filename
        self.raw_content: str = content
        self.content: str = normalize_newlines(content)
        self._line_offsets: list[int] = self._build_line_offsets(self.content)

    @staticmethod
    def _build_line_offsets(text: str) -> list[int]:
        """Record the start offset of each line."""
        offsets = [0]
        for i, char in enumerate(text):
            if char == "\n":
                offsets.append(i + 1)
        return offsets

    @property
    def length(self) -> int:
        return len(self.content)

    @property
    def line_count(self) -> int:
        return len(self._line_offsets)

    def location_at(self, offset: int) -> SourceLocation:
        """Convert a 0-based character offset into a 1-based SourceLocation."""
        offset = max(0, min(offset, len(self.content)))

        # Binary search for the line containing offset
        low = 0
        high = len(self._line_offsets) - 1
        line_idx = 0
        while low <= high:
            mid = (low + high) // 2
            if self._line_offsets[mid] <= offset:
                line_idx = mid
                low = mid + 1
            else:
                high = mid - 1

        line = line_idx + 1
        col = offset - self._line_offsets[line_idx] + 1
        return SourceLocation(line=line, col=col, offset=offset)

    def span_between(self, start_offset: int, end_offset: int) -> Span:
        """Construct a Span from start and end offsets."""
        return Span(
            start=self.location_at(start_offset),
            end=self.location_at(end_offset),
        )

    def slice(self, span: Span) -> str:
        """Extract source text corresponding to a Span."""
        return self.content[span.start.offset : span.end.offset]
