"""Finite State Machines (DFA) for token recognition.

Per doc 01 §2, doc 02 §2, doc 04 §1:
Explicit DFAs for token classes, simulator with maximal munch, and path tracing for UI.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class DFATransition:
    from_state: str
    to_state: str
    condition_desc: str
    matcher: Callable[[str], bool]


class DFA:
    """Deterministic Finite Automaton with transition tracking."""

    def __init__(self, name: str, start_state: str) -> None:
        self.name: str = name
        self.start_state: str = start_state
        self.states: set[str] = {start_state}
        self.accepting_states: dict[str, str] = {}  # state -> token type/category
        self._transitions: list[DFATransition] = []

    def add_state(self, state: str, accepting_as: str | None = None) -> None:
        self.states.add(state)
        if accepting_as is not None:
            self.accepting_states[state] = accepting_as

    def add_transition(
        self,
        from_state: str,
        to_state: str,
        condition_desc: str,
        matcher: Callable[[str], bool],
    ) -> None:
        self.states.add(from_state)
        self.states.add(to_state)
        self._transitions.append(
            DFATransition(
                from_state=from_state,
                to_state=to_state,
                condition_desc=condition_desc,
                matcher=matcher,
            )
        )

    def transition(self, state: str, ch: str) -> tuple[str, str] | None:
        """Return (next_state, condition_desc) if a transition exists, else None."""
        for t in self._transitions:
            if t.from_state == state and t.matcher(ch):
                return t.to_state, t.condition_desc
        return None

    def get_token_type(self, state: str) -> str | None:
        return self.accepting_states.get(state)


@dataclass
class DFAPathStep:
    state: str
    char: str
    next_state: str
    condition: str


@dataclass
class DFARunResult:
    matched: bool
    token_type: str | None
    matched_length: int
    path: list[DFAPathStep] = field(default_factory=list)


def build_number_dfa() -> DFA:
    """DFA recognizing Integer and Float literals.

    States:
      START -> [0-9] -> INT (accepting INT_LIT)
      INT -> [0-9] -> INT
      INT -> '.' -> DOT (non-accepting)
      DOT -> [0-9] -> FLOAT (accepting FLOAT_LIT)
      FLOAT -> [0-9] -> FLOAT
    """
    dfa = DFA("NumberDFA", "START")
    dfa.add_state("INT", accepting_as="INT_LIT")
    dfa.add_state("DOT")
    dfa.add_state("FLOAT", accepting_as="FLOAT_LIT")

    dfa.add_transition("START", "INT", "[0-9]", lambda c: c.isdigit())
    dfa.add_transition("INT", "INT", "[0-9]", lambda c: c.isdigit())
    dfa.add_transition("INT", "DOT", "'.'", lambda c: c == ".")
    dfa.add_transition("DOT", "FLOAT", "[0-9]", lambda c: c.isdigit())
    dfa.add_transition("FLOAT", "FLOAT", "[0-9]", lambda c: c.isdigit())
    return dfa


def build_identifier_dfa() -> DFA:
    """DFA recognizing Identifiers (and keywords before categorization).

    States:
      START -> [A-Za-z_] -> ID (accepting IDENTIFIER)
      ID -> [A-Za-z0-9_] -> ID
    """
    dfa = DFA("IdentifierDFA", "START")
    dfa.add_state("ID", accepting_as="IDENTIFIER")

    is_id_start = lambda c: c.isalpha() or c == "_"
    is_id_part = lambda c: c.isalnum() or c == "_"

    dfa.add_transition("START", "ID", "[A-Za-z_]", is_id_start)
    dfa.add_transition("ID", "ID", "[A-Za-z0-9_]", is_id_part)
    return dfa


def build_operator_dfa() -> DFA:
    """DFA recognizing symbolic operators with longest match.

    Handles:
      +, ++, +=
      -, --, -=
      *, *=
      /, /=
      %, %=
      <, <=
      >, >=
      =, ==
      !=
    """
    dfa = DFA("OperatorDFA", "START")

    # + family
    dfa.add_state("PLUS", accepting_as="+")
    dfa.add_state("PLUS_PLUS", accepting_as="++")
    dfa.add_state("PLUS_ASSIGN", accepting_as="+=")
    dfa.add_transition("START", "PLUS", "'+'", lambda c: c == "+")
    dfa.add_transition("PLUS", "PLUS_PLUS", "'+'", lambda c: c == "+")
    dfa.add_transition("PLUS", "PLUS_ASSIGN", "'='", lambda c: c == "=")

    # - family
    dfa.add_state("MINUS", accepting_as="-")
    dfa.add_state("MINUS_MINUS", accepting_as="--")
    dfa.add_state("MINUS_ASSIGN", accepting_as="-=")
    dfa.add_transition("START", "MINUS", "'-'", lambda c: c == "-")
    dfa.add_transition("MINUS", "MINUS_MINUS", "'-'", lambda c: c == "-")
    dfa.add_transition("MINUS", "MINUS_ASSIGN", "'='", lambda c: c == "=")

    # * family
    dfa.add_state("STAR", accepting_as="*")
    dfa.add_state("STAR_ASSIGN", accepting_as="*=")
    dfa.add_transition("START", "STAR", "'*'", lambda c: c == "*")
    dfa.add_transition("STAR", "STAR_ASSIGN", "'='", lambda c: c == "=")

    # / family
    dfa.add_state("SLASH", accepting_as="/")
    dfa.add_state("SLASH_ASSIGN", accepting_as="/=")
    dfa.add_transition("START", "SLASH", "'/'", lambda c: c == "/")
    dfa.add_transition("SLASH", "SLASH_ASSIGN", "'='", lambda c: c == "=")

    # % family
    dfa.add_state("PERCENT", accepting_as="%")
    dfa.add_state("PERCENT_ASSIGN", accepting_as="%=")
    dfa.add_transition("START", "PERCENT", "'%'", lambda c: c == "%")
    dfa.add_transition("PERCENT", "PERCENT_ASSIGN", "'='", lambda c: c == "=")

    # < family
    dfa.add_state("LT", accepting_as="<")
    dfa.add_state("LTE", accepting_as="<=")
    dfa.add_transition("START", "LT", "'<'", lambda c: c == "<")
    dfa.add_transition("LT", "LTE", "'='", lambda c: c == "=")

    # > family
    dfa.add_state("GT", accepting_as=">")
    dfa.add_state("GTE", accepting_as=">=")
    dfa.add_transition("START", "GT", "'>'", lambda c: c == ">")
    dfa.add_transition("GT", "GTE", "'='", lambda c: c == "=")

    # = family
    dfa.add_state("ASSIGN", accepting_as="=")
    dfa.add_state("EQ", accepting_as="==")
    dfa.add_transition("START", "ASSIGN", "'='", lambda c: c == "=")
    dfa.add_transition("ASSIGN", "EQ", "'='", lambda c: c == "=")

    # ! family
    dfa.add_state("BANG")
    dfa.add_state("NEQ", accepting_as="!=")
    dfa.add_transition("START", "BANG", "'!'", lambda c: c == "!")
    dfa.add_transition("BANG", "NEQ", "'='", lambda c: c == "=")

    return dfa


class DFASimulator:
    """Simulates DFA execution over a character sequence with longest match."""

    @staticmethod
    def simulate(dfa: DFA, text: str, start_index: int = 0) -> DFARunResult:
        current_state = dfa.start_state
        last_accepting_state: str | None = None
        last_accepting_len = 0
        path: list[DFAPathStep] = []

        idx = start_index
        n = len(text)

        while idx < n:
            ch = text[idx]
            res = dfa.transition(current_state, ch)
            if res is None:
                break
            next_state, cond = res
            path.append(
                DFAPathStep(
                    state=current_state,
                    char=ch,
                    next_state=next_state,
                    condition=cond,
                )
            )
            current_state = next_state
            idx += 1
            if dfa.get_token_type(current_state) is not None:
                last_accepting_state = current_state
                last_accepting_len = idx - start_index

        if last_accepting_state is not None:
            return DFARunResult(
                matched=True,
                token_type=dfa.get_token_type(last_accepting_state),
                matched_length=last_accepting_len,
                path=path[:last_accepting_len],
            )
        return DFARunResult(matched=False, token_type=None, matched_length=0, path=path)
