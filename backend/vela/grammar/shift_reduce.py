"""Bottom-up Shift-Reduce Parser Driver and Parse Tree Construction.

Per doc 01 §13.4, doc 02 §7, doc 06 §4:
Executes LR shift-reduce parsing, builds parse trees, and emits execution traces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from vela.grammar.lr import LRTable


@dataclass
class ParseTreeNode:
    symbol: str
    children: list[ParseTreeNode] = field(default_factory=list)
    lexeme: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "lexeme": self.lexeme,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class ShiftReduceStep:
    step: int
    states: list[int]
    symbols: list[str]
    input: list[str]
    action: str


@dataclass
class ShiftReduceResult:
    accepted: bool
    error: str | None
    parse_tree: ParseTreeNode | None
    steps: list[ShiftReduceStep] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "error": self.error,
            "parse_tree": self.parse_tree.to_dict() if self.parse_tree else None,
            "step_count": len(self.steps),
            "steps": [
                {
                    "step": s.step,
                    "states": s.states,
                    "symbols": s.symbols,
                    "input": s.input,
                    "action": s.action,
                }
                for s in self.steps
            ],
        }


class ShiftReduceParser:
    """Driver for bottom-up LR shift-reduce parsing."""

    def __init__(self, table: LRTable) -> None:
        self.table: LRTable = table

    def parse(self, tokens: list[str], max_steps: int = 5000) -> ShiftReduceResult:
        """Parse token sequence (list of terminal strings) with shift-reduce."""
        input_stream = list(tokens)
        if not input_stream or input_stream[-1] != "$":
            input_stream.append("$")

        state_stack: list[int] = [0]
        node_stack: list[ParseTreeNode] = []
        ip = 0
        step_num = 0
        steps: list[ShiftReduceStep] = []

        while step_num < max_steps:
            current_state = state_stack[-1]
            current_tok = input_stream[ip]

            actions = self.table.action.get((current_state, current_tok), [])
            symbol_names = [n.symbol for n in node_stack]

            if not actions:
                err = (
                    f"Syntax error at state {current_state} on terminal '{current_tok}': "
                    "no action defined"
                )
                steps.append(
                    ShiftReduceStep(
                        step=step_num,
                        states=list(state_stack),
                        symbols=symbol_names,
                        input=input_stream[ip:],
                        action=f"Error: {err}",
                    )
                )
                return ShiftReduceResult(accepted=False, error=err, parse_tree=None, steps=steps)

            action = actions[0]

            if action == "acc":
                steps.append(
                    ShiftReduceStep(
                        step=step_num,
                        states=list(state_stack),
                        symbols=symbol_names,
                        input=input_stream[ip:],
                        action="Accept",
                    )
                )
                root = node_stack[0] if node_stack else None
                return ShiftReduceResult(accepted=True, error=None, parse_tree=root, steps=steps)

            elif action.startswith("s"):
                # Shift next_state
                next_state = int(action[1:])
                steps.append(
                    ShiftReduceStep(
                        step=step_num,
                        states=list(state_stack),
                        symbols=symbol_names,
                        input=input_stream[ip:],
                        action=f"Shift '{current_tok}' -> state {next_state}",
                    )
                )
                state_stack.append(next_state)
                node_stack.append(ParseTreeNode(symbol=current_tok, lexeme=current_tok))
                ip += 1

            elif action.startswith("r"):
                # Reduce by production prod_id
                prod_id = int(action[1:])
                prod = self.table.productions[prod_id]
                rhs = prod.normalized_rhs()
                rhs_len = len(rhs)

                popped_children: list[ParseTreeNode] = []
                for _ in range(rhs_len):
                    state_stack.pop()
                    popped_children.insert(0, node_stack.pop())

                parent_state = state_stack[-1]
                goto_state = self.table.goto.get((parent_state, prod.lhs))
                if goto_state is None:
                    err = f"Goto table error: no transition for ({parent_state}, {prod.lhs})"
                    return ShiftReduceResult(accepted=False, error=err, parse_tree=None, steps=steps)

                state_stack.append(goto_state)
                new_node = ParseTreeNode(symbol=prod.lhs, children=popped_children)
                node_stack.append(new_node)

                steps.append(
                    ShiftReduceStep(
                        step=step_num,
                        states=list(state_stack),
                        symbols=[n.symbol for n in node_stack],
                        input=input_stream[ip:],
                        action=f"Reduce {prod} -> state {goto_state}",
                    )
                )

            step_num += 1

        return ShiftReduceResult(
            accepted=False,
            error="Exceeded maximum parsing steps (5000)",
            parse_tree=None,
            steps=steps,
        )
