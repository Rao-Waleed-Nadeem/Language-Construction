"""Symbol table, lexical scopes, and symbol tracking for Vela.

Per doc 01 §5.2, doc 02 §5, and doc 07 §3:
- Hierarchical lexical scoping (global, function, block, for-header, case).
- Shadowing tracking and redeclaration detection (VL-SEM-002).
- Detailed symbol table event log and scope tree for the Vela Studio Semantic Explorer.
- Offsets and use tracking for unused variable warnings (VL-WRN-001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from vela.common.source import Span
from vela.semantic.types import VelaType


class ScopeKind(str, Enum):
    GLOBAL = "global"
    FUNCTION = "function"
    BLOCK = "block"
    FOR_HEADER = "for_header"
    CASE = "case"


@dataclass
class Symbol:
    """A declared entity in the symbol table."""

    name: str
    symbol_type: VelaType
    kind: str  # "var", "func", "param"
    scope_id: int
    decl_span: Span
    param_types: list[VelaType] = field(default_factory=list)
    return_type: VelaType | None = None
    is_array: bool = False
    array_size: int | None = None
    offset: int = 0
    uses: list[Span] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.symbol_type.name,
            "kind": self.kind,
            "scope_id": self.scope_id,
            "decl_span": self.decl_span.to_dict(),
            "param_types": [p.name for p in self.param_types],
            "return_type": self.return_type.name if self.return_type else None,
            "is_array": self.is_array,
            "array_size": self.array_size,
            "offset": self.offset,
            "use_count": len(self.uses),
        }


@dataclass(frozen=True)
class SymbolEvent:
    """Event log record for symbol table operations."""

    event_type: str  # "enter_scope", "exit_scope", "define_symbol", "lookup_symbol", "shadow_symbol"
    scope_id: int
    symbol_name: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "scope_id": self.scope_id,
            "symbol_name": self.symbol_name,
            "detail": self.detail,
        }


@dataclass
class Scope:
    """A single lexical scope frame."""

    id: int
    name: str
    kind: ScopeKind
    parent: Scope | None = None
    children: list[Scope] = field(default_factory=list)
    symbols: dict[str, Symbol] = field(default_factory=dict)

    def define(self, symbol: Symbol) -> bool:
        """Define a symbol in this scope. Returns False on redeclaration."""
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup_local(self, name: str) -> Symbol | None:
        """Lookup symbol strictly in this scope."""
        return self.symbols.get(name)

    def lookup(self, name: str) -> Symbol | None:
        """Lookup symbol starting here and walking up enclosing scopes."""
        curr: Scope | None = self
        while curr is not None:
            if name in curr.symbols:
                return curr.symbols[name]
            curr = curr.parent
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "kind": self.kind.value,
            "parent_id": self.parent.id if self.parent else None,
            "symbols": {k: v.to_dict() for k, v in self.symbols.items()},
            "children": [c.to_dict() for c in self.children],
        }


class SymbolTable:
    """Hierarchical symbol table manager with event telemetry."""

    def __init__(self) -> None:
        self._next_scope_id: int = 0
        self.root_scope: Scope = Scope(
            id=self._alloc_id(),
            name="global",
            kind=ScopeKind.GLOBAL,
        )
        self.current_scope: Scope = self.root_scope
        self.all_scopes: list[Scope] = [self.root_scope]
        self.events: list[SymbolEvent] = []
        self._log("enter_scope", self.root_scope.id, "", "global scope created")

    def _alloc_id(self) -> int:
        sid = self._next_scope_id
        self._next_scope_id += 1
        return sid

    def _log(self, event_type: str, scope_id: int, symbol_name: str, detail: str) -> None:
        if len(self.events) < 5000:
            self.events.append(
                SymbolEvent(
                    event_type=event_type,
                    scope_id=scope_id,
                    symbol_name=symbol_name,
                    detail=detail,
                )
            )

    def enter_scope(self, kind: ScopeKind, name: str = "") -> Scope:
        """Enter a new nested scope."""
        scope_name = name or f"{kind.value}_{len(self.all_scopes)}"
        new_scope = Scope(
            id=self._alloc_id(),
            name=scope_name,
            kind=kind,
            parent=self.current_scope,
        )
        self.current_scope.children.append(new_scope)
        self.all_scopes.append(new_scope)
        self.current_scope = new_scope
        self._log("enter_scope", new_scope.id, "", f"entered {kind.value} scope '{scope_name}'")
        return new_scope

    def exit_scope(self) -> Scope:
        """Exit the current scope back to its parent."""
        if self.current_scope.parent is None:
            return self.current_scope

        exited = self.current_scope
        self._log("exit_scope", exited.id, "", f"exited scope '{exited.name}'")
        self.current_scope = self.current_scope.parent
        return exited

    def define(self, symbol: Symbol) -> tuple[bool, Symbol | None]:
        """Define a symbol in the current scope.

        Returns (True, None) if successful, or (False, existing_symbol) on redeclaration.
        Logs shadow_symbol event if an outer scope has a symbol with the same name.
        """
        existing = self.current_scope.lookup_local(symbol.name)
        if existing is not None:
            self._log(
                "define_symbol",
                self.current_scope.id,
                symbol.name,
                f"REDECLARATION ERROR: already defined in scope {self.current_scope.id}",
            )
            return False, existing

        # Check for shadowing an outer scope symbol
        if self.current_scope.parent is not None:
            outer = self.current_scope.parent.lookup(symbol.name)
            if outer is not None:
                self._log(
                    "shadow_symbol",
                    self.current_scope.id,
                    symbol.name,
                    f"shadows symbol in outer scope {outer.scope_id}",
                )

        self.current_scope.define(symbol)
        self._log(
            "define_symbol",
            self.current_scope.id,
            symbol.name,
            f"defined {symbol.kind} '{symbol.name}' : {symbol.symbol_type.name}",
        )
        return True, None

    def lookup(self, name: str) -> Symbol | None:
        """Lookup symbol in current scope or any parent scope."""
        sym = self.current_scope.lookup(name)
        if sym is not None:
            self._log(
                "lookup_symbol",
                self.current_scope.id,
                name,
                f"found in scope {sym.scope_id}",
            )
        else:
            self._log(
                "lookup_symbol",
                self.current_scope.id,
                name,
                "not found",
            )
        return sym

    def record_use(self, name: str, span: Span) -> Symbol | None:
        """Lookup symbol and record a reference usage span."""
        sym = self.lookup(name)
        if sym is not None:
            sym.uses.append(span)
        return sym

    def get_scope_tree(self) -> dict[str, Any]:
        """Return the complete hierarchical scope tree."""
        return self.root_scope.to_dict()
