"""Vela Intermediate Representation (IR) Package.

Implements Three-Address Code (TAC) data structures, pretty-printer,
and AST lowering generator.
"""

from vela.ir.generator import TACGenerator
from vela.ir.printer import TACPrinter
from vela.ir.tac import (
    Constant,
    Label,
    TACInstruction,
    TACOperand,
    TACProgram,
    Temporary,
    Variable,
)

__all__ = [
    "Constant",
    "Label",
    "TACGenerator",
    "TACInstruction",
    "TACOperand",
    "TACPrinter",
    "TACProgram",
    "Temporary",
    "Variable",
]
