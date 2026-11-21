"""Type representation and type compatibility rules for Vela.

Per doc 01 §4, §6.2–§6.4 and doc 07 §2:
- Primitive scalar types: int, float, char, string, bool.
- Sentinel/non-value types: void (function with no return type), error (prevents cascade errors).
- Fixed-size 1D arrays: T[N] or T[] for parameters.
- Assignment compatibility and explicit / implicit conversion tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VelaType:
    """Base class for all Vela types."""

    name: str

    @property
    def is_scalar(self) -> bool:
        return self in (INT, FLOAT, CHAR, STRING, BOOL)

    @property
    def is_numeric(self) -> bool:
        return self in (INT, FLOAT)

    @property
    def is_array(self) -> bool:
        return isinstance(self, ArrayType)

    @property
    def is_error(self) -> bool:
        return self == ERROR

    @property
    def is_void(self) -> bool:
        return self == VOID

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "is_array": self.is_array}

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True)
class ArrayType(VelaType):
    """Array type with element type and optional fixed dimension."""

    element_type: VelaType
    size: int | None = None

    def __init__(self, element_type: VelaType, size: int | None = None) -> None:
        dim_str = f"[{size}]" if size is not None else "[]"
        super().__init__(name=f"{element_type.name}{dim_str}")
        object.__setattr__(self, "element_type", element_type)
        object.__setattr__(self, "size", size)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "is_array": True,
            "element_type": self.element_type.to_dict(),
            "size": self.size,
        }


# Canonical primitive type instances
INT = VelaType("int")
FLOAT = VelaType("float")
CHAR = VelaType("char")
STRING = VelaType("string")
BOOL = VelaType("bool")
VOID = VelaType("void")
ERROR = VelaType("error")

PRIMITIVE_TYPES: dict[str, VelaType] = {
    "int": INT,
    "float": FLOAT,
    "char": CHAR,
    "string": STRING,
    "bool": BOOL,
    "void": VOID,
    "error": ERROR,
}


def get_type_by_name(name: str) -> VelaType:
    """Retrieve VelaType by string name."""
    if name in PRIMITIVE_TYPES:
        return PRIMITIVE_TYPES[name]
    if name.endswith("]") and "[" in name:
        base_name = name[: name.index("[")]
        inner = get_type_by_name(base_name)
        dim_part = name[name.index("[") + 1 : -1]
        sz = int(dim_part) if dim_part.isdigit() else None
        return ArrayType(inner, sz)
    return ERROR


# Explicit cast table (doc 01 §6.3): from_type -> set of allowed target types
VALID_EXPLICIT_CASTS: dict[VelaType, set[VelaType]] = {
    INT: {INT, FLOAT, CHAR, STRING},
    FLOAT: {FLOAT, INT, STRING},
    CHAR: {CHAR, INT, STRING},
    STRING: {STRING},
    BOOL: {BOOL, INT, STRING},
}


def can_explicit_cast(from_type: VelaType, to_type: VelaType) -> bool:
    """Check if 'from_type as to_type' is permitted (doc 01 §6.3)."""
    if from_type == ERROR or to_type == ERROR:
        return True
    if from_type in VALID_EXPLICIT_CASTS:
        return to_type in VALID_EXPLICIT_CASTS[from_type]
    return False


def can_implicit_widen(from_type: VelaType, to_type: VelaType) -> bool:
    """Check if from_type can be implicitly widened to to_type (int -> float only)."""
    return from_type == INT and to_type == FLOAT


def is_assignable(source: VelaType, target: VelaType) -> bool:
    """Check if a value of source type is assignable to target type (doc 01 §6.4)."""
    if source == ERROR or target == ERROR:
        return True
    if source == target:
        return True
    # Implicit int -> float widening
    return bool(can_implicit_widen(source, target))


def are_types_equivalent(t1: VelaType, t2: VelaType) -> bool:
    """Check type equivalence per doc 01 §4."""
    if t1 == ERROR or t2 == ERROR:
        return True
    if t1 == t2:
        return True
    # Array parameter matching: T[N] matches T[] or T[M]
    if isinstance(t1, ArrayType) and isinstance(t2, ArrayType):
        return t1.element_type == t2.element_type
    return False


def get_binary_op_result_type(left: VelaType, op: str, right: VelaType) -> VelaType | None:
    """Determine the resulting type of 'left op right' per doc 01 §6.2.

    Returns None if the operator application is semantically invalid.
    """
    if left == ERROR or right == ERROR:
        return ERROR

    # 1. Arithmetic (+, -, *, /, %)
    if op in ("+", "-", "*", "/"):
        if left == INT and right == INT:
            return INT
        if left in (INT, FLOAT) and right in (INT, FLOAT):
            return FLOAT
        if op == "+" and left == STRING and right == STRING:
            return STRING
        return None

    if op == "%":
        if left == INT and right == INT:
            return INT
        return None

    # 2. Relational (<, <=, >, >=)
    if op in ("<", "<=", ">", ">="):
        if left in (INT, FLOAT) and right in (INT, FLOAT):
            return BOOL
        if left == CHAR and right == CHAR:
            return BOOL
        return None

    # 3. Equality (==, !=)
    if op in ("==", "!="):
        if left in (INT, FLOAT) and right in (INT, FLOAT):
            return BOOL
        if left == right and left.is_scalar:
            return BOOL
        return None

    # 4. Logical (and, or)
    if op in ("and", "or"):
        if left == BOOL and right == BOOL:
            return BOOL
        return None

    return None


def get_unary_op_result_type(op: str, operand: VelaType) -> VelaType | None:
    """Determine the resulting type of 'op operand' per doc 01 §6.2."""
    if operand == ERROR:
        return ERROR

    if op == "-":
        if operand in (INT, FLOAT):
            return operand
        return None

    if op == "not":
        if operand == BOOL:
            return BOOL
        return None

    return None
