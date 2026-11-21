"""Vela Intermediate Representation (IR) Package.

Implements Three-Address Code (TAC) data structures, pretty-printer,
AST lowering generator, and independent execution oracle interpreter.
"""

from vela.ir.generator import TACGenerator
from vela.ir.interpreter import ExecutionResult, TACInterpreter, TACRuntimeError
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
    "ExecutionResult",
    "Label",
    "TACGenerator",
    "TACInstruction",
    "TACInterpreter",
    "TACOperand",
    "TACPrinter",
    "TACProgram",
    "TACRuntimeError",
    "Temporary",
    "Variable",
]
