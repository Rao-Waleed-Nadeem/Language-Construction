"""Compiler and runtime resource limits.

Per doc 01 §2.1, §4, §11, §12 and doc 02 §10:
Cooperative resource budgets prevent unbounded loops/growth.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    MAX_SOURCE_LENGTH: int = 100_000
    MAX_TOKENS: int = 50_000
    MAX_IDENTIFIER_LENGTH: int = 64
    MAX_PARSER_NESTING: int = 200
    MAX_PARSE_TREE_NODES: int = 20_000
    MAX_ARRAY_SIZE: int = 10_000
    MAX_VM_INSTRUCTIONS: int = 1_000_000
    MAX_VM_CALL_DEPTH: int = 1_000
    MAX_VM_OUTPUT_LENGTH: int = 100_000
    MAX_VM_SNAPSHOTS: int = 5_000
    MAX_GRAMMAR_PRODUCTIONS: int = 300
    MAX_LR_STATES: int = 5_000
    MAX_PARSE_TRACE_STEPS: int = 5_000
    MAX_REQUEST_SECONDS: float = 10.0


LIMITS = Limits()

INT32_MIN = -2147483648
INT32_MAX = 2147483647


def wrap32(n: int) -> int:
    """Simulate 32-bit two's complement signed integer wrap-around."""
    n = n & 0xFFFFFFFF
    if n >= 0x80000000:
        n -= 0x100000000
    return n
