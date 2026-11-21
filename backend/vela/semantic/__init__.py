"""Vela Semantic Analysis Package."""

from vela.semantic.returns import block_returns, statement_returns
from vela.semantic.symbols import Scope, ScopeKind, Symbol, SymbolEvent, SymbolTable
from vela.semantic.types import (
    BOOL,
    CHAR,
    ERROR,
    FLOAT,
    INT,
    STRING,
    VOID,
    ArrayType,
    VelaType,
    are_types_equivalent,
    can_explicit_cast,
    can_implicit_widen,
    get_binary_op_result_type,
    get_type_by_name,
    get_unary_op_result_type,
    is_assignable,
)

__all__ = [
    "BOOL",
    "CHAR",
    "ERROR",
    "FLOAT",
    "INT",
    "STRING",
    "VOID",
    "ArrayType",
    "Scope",
    "ScopeKind",
    "Symbol",
    "SymbolEvent",
    "SymbolTable",
    "VelaType",
    "are_types_equivalent",
    "block_returns",
    "can_explicit_cast",
    "can_implicit_widen",
    "get_binary_op_result_type",
    "get_type_by_name",
    "get_unary_op_result_type",
    "is_assignable",
    "statement_returns",
]
