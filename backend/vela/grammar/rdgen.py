"""Recursive-descent pseudocode generator from LL(1) grammars.

Per doc 02 §7, doc 03 §5.5, doc 06 §4:
Generates textbook-style recursive-descent parsing pseudocode from an LL(1) parsing table.
"""

from __future__ import annotations

from typing import Any

from vela.grammar.ll1 import LL1Table
from vela.grammar.model import Grammar


class RecursiveDescentGenerator:
    """Generates recursive-descent pseudocode from an LL(1) grammar."""

    def __init__(self, grammar: Grammar, table: LL1Table | None = None) -> None:
        self.grammar: Grammar = grammar
        self.table: LL1Table = table or LL1Table(grammar)

    def generate(self) -> str:
        """Generate formatted pseudocode string for all nonterminals."""
        lines: list[str] = [
            f"# Recursive-Descent Parser for Grammar '{self.grammar.start_symbol}'",
            "# Automatically generated from LL(1) predictive parsing table",
            "",
            "lookahead = get_next_token()",
            "",
            "def match(expected):",
            "    global lookahead",
            "    if lookahead == expected:",
            "        lookahead = get_next_token()",
            "    else:",
            '        raise SyntaxError(f"Expected {expected}, got {lookahead}")',
            "",
        ]

        for nt in self.grammar.nonterminals:
            lines.append(f"def parse_{nt}():")
            prods = self.grammar.productions_for(nt)

            # Group terminals by production
            prod_terms: dict[int, list[str]] = {}
            for term in list(self.grammar.terminals) + [self.table.EOF_SYMBOL]:
                p = self.table.get_production(nt, term)
                if p is not None:
                    prod_terms.setdefault(p.id, []).append(term)

            if not prod_terms:
                lines.append('    raise SyntaxError("No valid transitions")')
                lines.append("")
                continue

            first_branch = True
            for p in prods:
                terms = prod_terms.get(p.id, [])
                if not terms:
                    continue

                terms_repr = ", ".join(repr(t) for t in terms)
                cond = f"lookahead in ({terms_repr})"
                branch_kw = "if" if first_branch else "elif"
                first_branch = False

                lines.append(f"    {branch_kw} {cond}:")
                rhs = p.normalized_rhs()
                if not rhs:
                    lines.append("        # Epsilon production: do nothing")
                    lines.append("        pass")
                else:
                    for sym in rhs:
                        if self.grammar.is_nonterminal(sym):
                            lines.append(f"        parse_{sym}()")
                        else:
                            lines.append(f"        match({sym!r})")

            lines.append("    else:")
            lines.append(
                f'        raise SyntaxError(f"Unexpected token {{lookahead}} in {nt}")'
            )
            lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_symbol": self.grammar.start_symbol,
            "pseudocode": self.generate(),
        }
