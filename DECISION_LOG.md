# Decision Log

Record of technical, architectural, and design decisions made during the development of the Vela Compiler and Vela Studio.

| ID | Date | Topic | Decision | Reason / Context | Made by |
|---|---|---|---|---|---|
| DEC-001 | 2026-11-21 | Workspace structure | Adopt standard layout per doc 02 §3 with separated `backend/`, `frontend/`, `scripts/`, `docs/`, `examples/` | Maintain clean separation of concerns and pure Python compiler library | Implementation Agent |
| DEC-002 | 2026-11-21 | Spec Gap Filling | Create `docs/04_LEXER_SPECIFICATION.md` defining token classes, data structures, two-buffer scheme, and error recovery rules | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-003 | 2026-11-21 | Spec Gap Filling | Create `docs/06_GRAMMAR_AND_PARSING_LAB_SPECIFICATION.md` defining grammar engine model, BNF loader, analysis algorithms, and Chomsky classification | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-004 | 2026-11-21 | Spec Gap Filling | Create `docs/08_AST_DAG_SDD_SDT_SPECIFICATION.md` defining AST node hierarchy, S-expression printer, and JSON structure | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-005 | 2026-11-21 | Spec Gap Filling | Create `docs/05_PARSER_SPECIFICATION.md` defining recursive descent parser over LL(1) grammar $G'$, CST nodes, panic-mode recovery, and call tracing | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-006 | 2026-11-21 | Spec Gap Filling | Create `docs/07_SEMANTIC_ANALYSIS_SPECIFICATION.md` defining type representation, symbol table hierarchy, event logging, return-path analysis, and semantic check rules | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-007 | 2026-11-21 | Spec Gap Filling | Extend `docs/08_AST_DAG_SDD_SDT_SPECIFICATION.md` defining SDD/SDT engine, safe rule evaluation, S/L-attributed classifier, dependency graphs, and presets | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-008 | 2026-11-21 | Spec Gap Filling | Extend `docs/08_AST_DAG_SDD_SDT_SPECIFICATION.md` defining Expression DAG value numbering, commutativity normalization, node metrics, and construction tracing | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
| DEC-009 | 2026-11-21 | Spec Gap Filling | Create `docs/09_TAC_SPECIFICATION.md` defining Three-Address Code (TAC) quadruples, operand taxonomy, short-circuit boolean lowering, control-flow jump targets, and startup sequence | Per agent-prompt.md Section 8 (ALLOW_SPEC_GAP_FILLING = true) | Implementation Agent |
