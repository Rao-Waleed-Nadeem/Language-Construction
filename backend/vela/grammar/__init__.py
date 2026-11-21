"""Vela Grammar Engine Package."""

from vela.grammar.analysis import DerivationStep, GrammarAnalysis
from vela.grammar.classify import ChomskyClassification, classify_grammar
from vela.grammar.ll1 import LL1Conflict, LL1ParseResult, LL1Table
from vela.grammar.loader import BNFLoader
from vela.grammar.lr import LRBuilder, LRConflict, LRTable, LRType
from vela.grammar.model import EPSILON, Grammar, Production
from vela.grammar.op_precedence import (
    OperatorPrecedenceTable,
    OpParseResult,
    OpPrecedenceConflict,
)
from vela.grammar.rdgen import RecursiveDescentGenerator
from vela.grammar.shift_reduce import (
    ParseTreeNode,
    ShiftReduceParser,
    ShiftReduceResult,
)
from vela.grammar.transform import (
    TransformStep,
    eliminate_left_recursion,
    left_factor,
)

__all__ = [
    "EPSILON",
    "BNFLoader",
    "ChomskyClassification",
    "DerivationStep",
    "Grammar",
    "GrammarAnalysis",
    "LL1Conflict",
    "LL1ParseResult",
    "LL1Table",
    "LRBuilder",
    "LRConflict",
    "LRTable",
    "LRType",
    "OpParseResult",
    "OpPrecedenceConflict",
    "OperatorPrecedenceTable",
    "ParseTreeNode",
    "Production",
    "RecursiveDescentGenerator",
    "ShiftReduceParser",
    "ShiftReduceResult",
    "TransformStep",
    "classify_grammar",
    "eliminate_left_recursion",
    "left_factor",
]
