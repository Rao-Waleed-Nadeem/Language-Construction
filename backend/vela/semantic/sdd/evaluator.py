"""Restricted, safe expression evaluator for SDD semantic rules.

Per doc 03 §5.6, doc 08 §3, and agent-prompt.md:
- Strictly prohibits eval() and exec().
- Evaluates attribute expressions using a whitelisted AST interpreter.
- Statically extracts attribute dependencies (symbol.attr).
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Any

# Whitelisted global helper functions
_LABEL_COUNTER = 0
_TEMP_COUNTER = 0


def _new_label(prefix: str = "L") -> str:
    global _LABEL_COUNTER
    _LABEL_COUNTER += 1
    return f"{prefix}{_LABEL_COUNTER}"


def _new_temp(prefix: str = "t") -> str:
    global _TEMP_COUNTER
    _TEMP_COUNTER += 1
    return f"{prefix}{_TEMP_COUNTER}"


def reset_counters() -> None:
    global _LABEL_COUNTER, _TEMP_COUNTER
    _LABEL_COUNTER = 0
    _TEMP_COUNTER = 0


WHITELISTED_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "int": int,
    "float": float,
    "str": str,
    "max": max,
    "min": min,
    "new_label": _new_label,
    "new_temp": _new_temp,
}


class SafeSDDEvaluator:
    """Evaluates whitelisted SDD expressions over an environment dictionary."""

    @staticmethod
    def extract_dependencies(expr_str: str) -> list[tuple[str, str]]:
        """Statically extract all (symbol, attribute) dependencies referenced in expr_str."""
        try:
            tree = ast.parse(expr_str, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid SDD rule syntax '{expr_str}': {e}") from e

        deps: list[tuple[str, str]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                deps.append((node.value.id, node.attr))
        return deps

    @classmethod
    def evaluate(cls, expr_str: str, env: dict[str, dict[str, Any]]) -> Any:
        """Safely evaluate expr_str against an environment mapping symbol -> {attr: value}."""
        try:
            tree = ast.parse(expr_str, mode="eval")
        except SyntaxError as e:
            raise ValueError(f"Invalid SDD rule expression '{expr_str}': {e}") from e

        return cls._eval_node(tree.body, env)

    @classmethod
    def _eval_node(cls, node: ast.AST, env: dict[str, dict[str, Any]]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value

        if isinstance(node, ast.Name):
            # Whitelisted function reference or symbol
            if node.id in WHITELISTED_FUNCTIONS:
                return WHITELISTED_FUNCTIONS[node.id]
            if node.id in ("True", "False", "None"):
                return {"True": True, "False": False, "None": None}[node.id]
            raise ValueError(f"Undefined variable '{node.id}'; attributes must be accessed as 'Symbol.attr'")

        if isinstance(node, ast.Attribute):
            if not isinstance(node.value, ast.Name):
                raise TypeError("Nested attribute access is not permitted; use Symbol.attr")
            sym = node.value.id
            attr = node.attr
            if sym not in env:
                raise KeyError(f"Symbol '{sym}' not found in rule environment")
            if attr not in env[sym]:
                raise KeyError(f"Attribute '{attr}' not yet computed on symbol '{sym}'")
            return env[sym][attr]

        if isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left, env)
            right = cls._eval_node(node.right, env)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.FloorDiv):
                return left // right
            if isinstance(node.op, ast.Mod):
                return left % right
            raise ValueError(f"Disallowed binary operator: {type(node.op).__name__}")

        if isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand, env)
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.Not):
                return not operand
            raise ValueError(f"Disallowed unary operator: {type(node.op).__name__}")

        if isinstance(node, ast.Compare):
            left = cls._eval_node(node.left, env)
            for op, comparator in zip(node.ops, node.comparators):
                right = cls._eval_node(comparator, env)
                if isinstance(op, ast.Eq):
                    if left != right:
                        return False
                elif isinstance(op, ast.NotEq):
                    if left == right:
                        return False
                elif isinstance(op, ast.Lt):
                    if not (left < right):
                        return False
                elif isinstance(op, ast.LtE):
                    if not (left <= right):
                        return False
                elif isinstance(op, ast.Gt):
                    if not (left > right):
                        return False
                elif isinstance(op, ast.GtE):
                    if not (left >= right):
                        return False
                else:
                    raise TypeError(f"Disallowed comparison operator: {type(op).__name__}")
                left = right
            return True

        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                for val in node.values:
                    if not cls._eval_node(val, env):
                        return False
                return True
            if isinstance(node.op, ast.Or):
                for val in node.values:
                    if cls._eval_node(val, env):
                        return True
                return False
            raise ValueError(f"Disallowed boolean operator: {type(node.op).__name__}")

        if isinstance(node, ast.IfExp):
            test = cls._eval_node(node.test, env)
            return cls._eval_node(node.body, env) if test else cls._eval_node(node.orelse, env)

        if isinstance(node, ast.Call):
            func = cls._eval_node(node.func, env)
            if not callable(func):
                raise TypeError(f"Target '{ast.dump(node.func)}' is not a callable function")
            args = [cls._eval_node(arg, env) for arg in node.args]
            return func(*args)

        raise ValueError(f"Disallowed expression node in SDD rule: {type(node).__name__}")
