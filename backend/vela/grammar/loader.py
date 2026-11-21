"""BNF Grammar File Loader.

Per doc 01 §13.1 and doc 06 §2:
Parses .bnf files with # comments, -> arrows, | continuation lines, and ε.
"""

from __future__ import annotations

from pathlib import Path

from vela.grammar.model import EPSILON, Grammar, Production


class BNFLoader:
    """Loads a context-free grammar from a .bnf file or string."""

    @classmethod
    def load_file(cls, path: str | Path, start_symbol: str | None = None) -> Grammar:
        file_path = Path(path)
        content = file_path.read_text(encoding="utf-8")
        return cls.load_string(content, start_symbol=start_symbol)

    @classmethod
    def load_string(cls, content: str, start_symbol: str | None = None) -> Grammar:
        lines = content.splitlines()
        productions: list[Production] = []
        current_lhs: str | None = None
        derived_start: str | None = None
        prod_id = 0

        for line in lines:
            # Strip trailing comments and whitespace
            # Note: # at start of line or after whitespace
            clean_line = line
            if "#" in clean_line:
                clean_line = clean_line.split("#", 1)[0]
            clean_line = clean_line.strip()

            if not clean_line:
                continue

            if "->" in clean_line:
                parts = clean_line.split("->", 1)
                lhs = parts[0].strip()
                rhs_text = parts[1].strip()
                current_lhs = lhs
                if derived_start is None:
                    derived_start = lhs

                # Split alternatives by |
                alts = [alt.strip() for alt in rhs_text.split("|")]
                for alt in alts:
                    symbols = tuple(alt.split()) if alt and alt != EPSILON else ()
                    productions.append(Production(id=prod_id, lhs=lhs, rhs=symbols))
                    prod_id += 1

            elif clean_line.startswith("|"):
                if current_lhs is None:
                    raise ValueError(f"Continuation line without preceding LHS: {line}")
                rhs_text = clean_line[1:].strip()
                alts = [alt.strip() for alt in rhs_text.split("|")]
                for alt in alts:
                    symbols = tuple(alt.split()) if alt and alt != EPSILON else ()
                    productions.append(Production(id=prod_id, lhs=current_lhs, rhs=symbols))
                    prod_id += 1
            else:
                raise ValueError(f"Malformed BNF line: {line}")

        start = start_symbol or derived_start or "Program"
        return Grammar(start_symbol=start, productions=productions)
