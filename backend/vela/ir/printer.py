"""TAC pretty-printing and formatting utilities for CLI and API.

Defined per docs/09_TAC_SPECIFICATION.md.
"""

from __future__ import annotations

from typing import Any

from vela.ir.tac import TACInstruction, TACProgram


class TACPrinter:
    """Pretty-printer for Three-Address Code."""

    @staticmethod
    def format_instruction(instr: TACInstruction, index: int | None = None) -> str:
        idx_str = f"{index:4d}: " if index is not None else ""
        text = str(instr)
        if instr.opcode in ("LABEL", "FUNC_BEGIN", "FUNC_END"):
            return f"{idx_str}{text}"
        return f"{idx_str}    {text}"

    @classmethod
    def print_program(cls, program: TACProgram) -> str:
        lines: list[str] = []
        for i, instr in enumerate(program.instructions):
            lines.append(cls.format_instruction(instr, i))
        return "\n".join(lines)

    @staticmethod
    def to_table(program: TACProgram) -> list[dict[str, Any]]:
        """Output tabular quadruple view for frontend IR visualizer."""
        rows: list[dict[str, Any]] = []
        for i, instr in enumerate(program.instructions):
            rows.append(
                {
                    "index": i,
                    "opcode": instr.opcode,
                    "arg1": str(instr.arg1) if instr.arg1 is not None else "",
                    "arg2": str(instr.arg2) if instr.arg2 is not None else "",
                    "result": str(instr.result) if instr.result is not None else "",
                    "text": str(instr),
                    "rule_id": instr.rule_id,
                    "ast_id": instr.ast_id,
                    "span": instr.src_span.to_dict(),
                }
            )
        return rows
