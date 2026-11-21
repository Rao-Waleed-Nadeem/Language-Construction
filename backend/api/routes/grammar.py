"""Grammar Lab and Semantic SDD API routes.

Provides endpoints for:
- /api/grammar/presets: Preset educational BNF grammars
- /api/grammar/analyze: Nullable, FIRST, FOLLOW, and Chomsky classification
- /api/grammar/transform: Left-recursion elimination and left factoring
- /api/grammar/ll1: LL(1) parsing table, conflicts, and predictive parse trace
- /api/grammar/lr: LR(0), SLR(1), CLR(1), LALR(1) tables, conflicts, and trace
- /api/grammar/op-precedence: Operator precedence relations and conflicts
- /api/grammar/rd-pseudocode: Recursive descent pseudocode generator
- /api/sdd/evaluate: SDD / SDT evaluation, dependency graph, S/L classification
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from api.schemas import (
    GrammarAnalyzeRequest,
    GrammarAnalyzeResponse,
    GrammarLL1Request,
    GrammarLL1Response,
    GrammarLRRequest,
    GrammarLRResponse,
    GrammarOpPrecedenceRequest,
    GrammarOpPrecedenceResponse,
    GrammarPresetDetail,
    GrammarPresetItem,
    GrammarRDPseudocodeRequest,
    GrammarRDPseudocodeResponse,
    GrammarTransformRequest,
    GrammarTransformResponse,
    SDDEvaluateRequest,
    SDDEvaluateResponse,
)
from vela.grammar.analysis import GrammarAnalysis
from vela.grammar.classify import classify_grammar
from vela.grammar.ll1 import LL1Table
from vela.grammar.loader import BNFLoader
from vela.grammar.lr import LRBuilder
from vela.grammar.model import Grammar
from vela.grammar.op_precedence import OperatorPrecedenceTable
from vela.grammar.rdgen import RecursiveDescentGenerator
from vela.grammar.transform import eliminate_left_recursion, left_factor
from vela.semantic.sdd.engine import SDDEngine
from vela.semantic.sdd.model import AnnotatedNode
from vela.semantic.sdd.presets import (
    preset_boolean_labels,
    preset_desk_calculator,
    preset_type_declarations,
)

router = APIRouter(prefix="/api", tags=["grammar"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
GRAMMAR_DIR = ROOT_DIR / "docs" / "grammar"
PRESETS_DIR = GRAMMAR_DIR / "presets"


def _load_grammar(grammar_text: str, start_symbol: str | None = None):
    grammar = BNFLoader.load_string(grammar_text, start_symbol=start_symbol)
    if len(grammar.productions) > 300:
        raise HTTPException(
            status_code=422,
            detail=f"Grammar size exceeded: {len(grammar.productions)} productions (limit is 300)",
        )
    return grammar


def _grammar_to_bnf(grammar: Grammar) -> str:
    lines: list[str] = []
    for nt in grammar.nonterminals:
        prods = grammar.productions_for(nt)
        if prods:
            rhs_strs = [" ".join(p.rhs) if p.rhs else "ε" for p in prods]
            lines.append(f"{nt} -> {' | '.join(rhs_strs)}")
    return "\n".join(lines)


@router.get("/grammar/presets", response_model=list[GrammarPresetItem])
def list_grammar_presets() -> list[GrammarPresetItem]:
    """List all available educational grammar presets."""
    items: list[GrammarPresetItem] = [
        GrammarPresetItem(
            id="vela",
            name="Vela Authoritative Grammar",
            description="Complete context-free grammar G",
        ),
        GrammarPresetItem(
            id="vela_ll1", name="Vela LL(1) Grammar", description="Transformed LL(1) grammar G'"
        ),
    ]
    if PRESETS_DIR.exists():
        for p in sorted(PRESETS_DIR.glob("*.bnf")):
            stem = p.stem
            name = stem.replace("_", " ").title()
            items.append(
                GrammarPresetItem(id=stem, name=name, description=f"Preset grammar {p.name}")
            )
    return items


@router.get("/grammar/presets/{preset_id}", response_model=GrammarPresetDetail)
def get_grammar_preset(preset_id: str) -> GrammarPresetDetail:
    """Return single grammar preset text and metadata."""
    if preset_id == "vela":
        p = GRAMMAR_DIR / "vela.bnf"
    elif preset_id == "vela_ll1":
        p = GRAMMAR_DIR / "vela_ll1.bnf"
    else:
        p = PRESETS_DIR / f"{preset_id}.bnf"

    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Grammar preset '{preset_id}' not found")

    text = p.read_text(encoding="utf-8")
    return GrammarPresetDetail(
        id=preset_id,
        name=preset_id.replace("_", " ").title(),
        description=f"Preset {p.name}",
        bnf_text=text,
        start_symbol="Program" if "vela" in preset_id else "E",
    )


@router.post("/grammar/analyze", response_model=GrammarAnalyzeResponse)
def analyze_grammar(req: GrammarAnalyzeRequest) -> GrammarAnalyzeResponse:
    """Compute nullable, FIRST, and FOLLOW sets, plus Chomsky classification."""
    grammar = _load_grammar(req.grammar_text, req.start_symbol)
    analysis = GrammarAnalysis(grammar)
    classification = classify_grammar(grammar)

    first_dict = {nt: sorted(syms) for nt, syms in sorted(analysis.first.items())}
    follow_dict = {nt: sorted(syms) for nt, syms in sorted(analysis.follow.items())}

    steps = [
        {
            "iteration": s.iteration,
            "set_type": s.set_type,
            "symbol": s.symbol,
            "added": s.added,
            "reason": s.reason,
        }
        for s in analysis.steps
    ]

    return GrammarAnalyzeResponse(
        nullable=sorted(analysis.nullable),
        first=first_dict,
        follow=follow_dict,
        classification=classification.to_dict(),
        steps=steps,
    )


@router.post("/grammar/transform", response_model=GrammarTransformResponse)
def transform_grammar(req: GrammarTransformRequest) -> GrammarTransformResponse:
    """Eliminate left recursion and/or left factor grammar productions."""
    grammar = _load_grammar(req.grammar_text)
    steps: list[dict[str, Any]] = []

    current_grammar = grammar
    if req.transform_type in ("left_recursion", "both"):
        current_grammar, rec_steps = eliminate_left_recursion(current_grammar)
        steps.extend([s.to_dict() for s in rec_steps])

    if req.transform_type in ("left_factoring", "both"):
        current_grammar, fac_steps = left_factor(current_grammar)
        steps.extend([s.to_dict() for s in fac_steps])

    return GrammarTransformResponse(
        original_bnf=req.grammar_text,
        transformed_bnf=_grammar_to_bnf(current_grammar),
        steps=steps,
    )


@router.post("/grammar/ll1", response_model=GrammarLL1Response)
def ll1_grammar(req: GrammarLL1Request) -> GrammarLL1Response:
    """Build LL(1) parsing table, detect conflicts, and simulate parse trace."""
    grammar = _load_grammar(req.grammar_text, req.start_symbol)
    analysis = GrammarAnalysis(grammar)
    table = LL1Table(grammar, analysis)

    trace = None
    if req.input_string is not None:
        tokens = req.input_string.strip().split()
        trace_res = table.parse(tokens)
        trace = [
            {
                "step": s.step,
                "stack": s.stack,
                "input": s.input,
                "action": s.action,
            }
            for s in trace_res.steps
        ]

    table_dict: dict[str, dict[str, str]] = {}
    for (nt, t), prods in sorted(table.table.items()):
        if nt not in table_dict:
            table_dict[nt] = {}
        if prods:
            table_dict[nt][t] = " / ".join(str(p) for p in prods)

    return GrammarLL1Response(
        is_ll1=table.is_ll1,
        table=table_dict,
        conflicts=[c.to_dict() for c in table.conflicts],
        parse_trace=trace,
    )


@router.post("/grammar/lr", response_model=GrammarLRResponse)
def lr_grammar(req: GrammarLRRequest) -> GrammarLRResponse:
    """Construct LR(0), SLR(1), CLR(1), or LALR(1) automaton and parse tables."""
    grammar = _load_grammar(req.grammar_text)
    prec_dict: dict[str, tuple[str, int]] = {}
    if req.precedence_declarations:
        for d in req.precedence_declarations:
            prec_dict[d["operator"]] = (d["associativity"], int(d["level"]))

    builder = LRBuilder(grammar, precedence=prec_dict)
    variant = req.variant.lower()
    if variant == "lr0":
        lr_table = builder.build_lr0()
    elif variant == "slr1":
        lr_table = builder.build_slr1()
    elif variant == "clr1":
        lr_table = builder.build_clr1()
    elif variant == "lalr1":
        lr_table = builder.build_lalr1()
    else:
        lr_table = builder.build_slr1()

    action_table: dict[str, dict[str, str]] = {}
    for (st, sym), acts in lr_table.action.items():
        st_str = str(st)
        if st_str not in action_table:
            action_table[st_str] = {}
        action_table[st_str][sym] = "/".join(acts)

    goto_table: dict[str, dict[str, int]] = {}
    for (st, sym), target in lr_table.goto.items():
        st_str = str(st)
        if st_str not in goto_table:
            goto_table[st_str] = {}
        goto_table[st_str][sym] = target

    trace = None
    if req.input_string is not None:
        from vela.grammar.shift_reduce import ShiftReduceParser

        sr_parser = ShiftReduceParser(lr_table)
        tokens = req.input_string.strip().split()
        trace_res = sr_parser.parse(tokens)
        trace = [
            {
                "step": s.step,
                "states": s.states,
                "symbols": s.symbols,
                "input": s.input,
                "action": s.action,
            }
            for s in trace_res.steps
        ]

    return GrammarLRResponse(
        variant=req.variant,
        states_count=lr_table.states_count,
        is_conflict_free=lr_table.is_conflict_free,
        action_table=action_table,
        goto_table=goto_table,
        conflicts=[c.to_dict() for c in lr_table.conflicts],
        states=[],
        parse_trace=trace,
    )


@router.post("/grammar/op-precedence", response_model=GrammarOpPrecedenceResponse)
def op_precedence_grammar(req: GrammarOpPrecedenceRequest) -> GrammarOpPrecedenceResponse:
    """Compute operator precedence relations and detect ambiguity conflicts."""
    grammar = _load_grammar(req.grammar_text)
    op_table = OperatorPrecedenceTable(grammar)

    trace = None
    if req.input_string is not None and op_table.is_eligible:
        tokens = req.input_string.strip().split()
        trace_res = op_table.parse(tokens)
        trace = [
            {
                "step": s.step,
                "stack": s.stack,
                "input": s.input,
                "action": s.action,
            }
            for s in trace_res.steps
        ]

    leading_dict = {nt: sorted(syms) for nt, syms in sorted(op_table.leading.items())}
    trailing_dict = {nt: sorted(syms) for nt, syms in sorted(op_table.trailing.items())}

    rel_dict: dict[str, dict[str, str]] = {}
    for (a, b), rels in op_table.relations.items():
        if a not in rel_dict:
            rel_dict[a] = {}
        rel_dict[a][b] = "/".join(sorted(rels))

    return GrammarOpPrecedenceResponse(
        is_operator_grammar=op_table.is_eligible,
        leading=leading_dict,
        trailing=trailing_dict,
        relations=rel_dict,
        conflicts=[c.to_dict() for c in op_table.conflicts],
        parse_trace=trace,
    )


@router.post("/grammar/rd-pseudocode", response_model=GrammarRDPseudocodeResponse)
def rd_pseudocode_grammar(req: GrammarRDPseudocodeRequest) -> GrammarRDPseudocodeResponse:
    """Generate recursive-descent parser pseudocode from grammar."""
    grammar = _load_grammar(req.grammar_text)
    analysis = GrammarAnalysis(grammar)
    table = LL1Table(grammar, analysis)
    generator = RecursiveDescentGenerator(grammar, table)
    pseudocode = generator.generate()

    return GrammarRDPseudocodeResponse(
        pseudocode=pseudocode,
        functions=[
            {"name": f"parse_{nt}", "body": f"Recursive descent procedure for {nt}"}
            for nt in grammar.nonterminals
        ],
    )


@router.post("/sdd/evaluate", response_model=SDDEvaluateResponse)
def evaluate_sdd(req: SDDEvaluateRequest) -> SDDEvaluateResponse:
    """Evaluate Syntax-Directed Definition (SDD) and classify S/L-attributed."""
    preset_name = req.preset or "desk_calculator"
    if preset_name == "desk_calculator":
        prods = preset_desk_calculator()
    elif preset_name == "type_declarations":
        prods = preset_type_declarations()
    elif preset_name == "boolean_labels":
        prods = preset_boolean_labels()
    else:
        prods = preset_desk_calculator()

    engine = SDDEngine(prods)
    classification = engine.classify()

    d3 = AnnotatedNode(id=1, symbol="digit", is_terminal=True, lexval=3)
    f3 = AnnotatedNode(id=2, symbol="F", children=[d3])
    t3 = AnnotatedNode(id=3, symbol="T", children=[f3])
    e3 = AnnotatedNode(id=4, symbol="E", children=[t3])
    op_plus = AnnotatedNode(id=5, symbol="+", is_terminal=True, lexval="+")
    d4 = AnnotatedNode(id=6, symbol="digit", is_terminal=True, lexval=4)
    f4 = AnnotatedNode(id=7, symbol="F", children=[d4])
    t4 = AnnotatedNode(id=8, symbol="T", children=[f4])
    e_root = AnnotatedNode(id=9, symbol="E", children=[e3, op_plus, t4])

    eval_res = engine.evaluate(e_root)

    return SDDEvaluateResponse(
        annotated_tree=eval_res.annotated_tree.to_dict(),
        dependency_graph=eval_res.dependency_graph,
        evaluation_order=eval_res.evaluation_order,
        classification=classification.to_dict(),
        attributes=dict(eval_res.annotated_tree.attributes),
    )
