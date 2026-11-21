"""Pydantic Request and Response Schemas for the Vela Studio API.

Defines typed, JSON-serializable schemas for all API endpoints per doc 02 §8 and doc 10.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# Health
class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"


# Language Specification
class PrecedenceLevel(BaseModel):
    level: int
    name: str
    operators: list[str]
    associativity: str
    description: str = ""


class LanguageResponse(BaseModel):
    keywords: list[str]
    operators: list[str]
    delimiters: list[str]
    precedence: list[PrecedenceLevel]
    types: list[str]
    grammar: str
    grammar_ll1: str


# Examples
class ExampleItem(BaseModel):
    id: str
    title: str
    filename: str
    description: str = ""


class ExampleDetail(BaseModel):
    id: str
    title: str
    filename: str
    description: str = ""
    source: str
    stdin: str = ""
    expected_output: str = ""


# Compile
class CompileRequest(BaseModel):
    source: str = Field(..., max_length=100000, description="Vela source code (max 100k chars)")
    filename: str = "main.vela"
    optimize: bool = True
    opt_level: int = 1
    max_opt_iterations: int = 10
    stop_after_phase: str | None = None


class CompileResponse(BaseModel):
    filename: str
    source_hash: str
    success: bool
    halted_at_phase: str | None = None
    timings_ms: dict[str, float]
    diagnostics: list[dict[str, Any]]
    tokens: list[dict[str, Any]] | None = None
    tokens_count: int = 0
    ast: dict[str, Any] | None = None
    cst: dict[str, Any] | None = None
    semantic: dict[str, Any] | None = None
    tac: dict[str, Any] | None = None
    blocks: list[dict[str, Any]] | None = None
    cfg: dict[str, Any] | None = None
    optimized_tac: dict[str, Any] | None = None
    opt_passes: list[dict[str, Any]] | None = None
    target_unallocated: list[dict[str, Any]] | None = None
    target_program: dict[str, Any] | None = None
    register_allocation: dict[str, Any] | None = None
    peephole_changes: list[dict[str, Any]] | None = None


# Run
class RunRequest(BaseModel):
    source: str = Field(..., max_length=100000)
    stdin: str = ""
    optimize: bool = True
    use_oracle: bool = False


class RunResponse(BaseModel):
    stdout: str
    exit_code: int
    success: bool
    steps_executed: int
    total_cost: int
    diagnostics: list[dict[str, Any]]
    snapshots: list[dict[str, Any]] = Field(default_factory=list)
    truncated_snapshots: bool = False


# Verify
class VerifyRequest(BaseModel):
    source: str = Field(..., max_length=100000)
    stdin: str = ""


class VerifyResponse(BaseModel):
    match: bool
    oracle_unopt: dict[str, Any]
    oracle_opt: dict[str, Any]
    vm: dict[str, Any]
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


# Self-Test
class SelfTestItem(BaseModel):
    name: str
    category: str
    passed: bool
    expected: str = ""
    actual: str = ""
    diagnostics: list[dict[str, Any]] = Field(default_factory=list)


class SelfTestResponse(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    items: list[SelfTestItem]


# Grammar Presets
class GrammarPresetItem(BaseModel):
    id: str
    name: str
    description: str = ""


class GrammarPresetDetail(BaseModel):
    id: str
    name: str
    description: str = ""
    bnf_text: str
    start_symbol: str = "Program"


# Grammar Analysis
class GrammarAnalyzeRequest(BaseModel):
    grammar_text: str
    start_symbol: str | None = None


class GrammarAnalyzeResponse(BaseModel):
    nullable: list[str]
    first: dict[str, list[str]]
    follow: dict[str, list[str]]
    classification: dict[str, Any]
    steps: list[dict[str, Any]] = Field(default_factory=list)


# Grammar Transform
class GrammarTransformRequest(BaseModel):
    grammar_text: str
    transform_type: str = "both"  # "left_recursion", "left_factoring", or "both"


class GrammarTransformResponse(BaseModel):
    original_bnf: str
    transformed_bnf: str
    steps: list[dict[str, Any]] = Field(default_factory=list)


# Grammar LL(1)
class GrammarLL1Request(BaseModel):
    grammar_text: str
    start_symbol: str | None = None
    input_string: str | None = None


class GrammarLL1Response(BaseModel):
    is_ll1: bool
    table: dict[str, dict[str, str]]
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    parse_trace: list[dict[str, Any]] | None = None


# Grammar LR
class GrammarLRRequest(BaseModel):
    grammar_text: str
    variant: str = "slr1"  # "lr0", "slr1", "clr1", "lalr1"
    precedence_declarations: list[dict[str, Any]] | None = None
    input_string: str | None = None


class GrammarLRResponse(BaseModel):
    variant: str
    states_count: int
    is_conflict_free: bool
    action_table: dict[str, dict[str, str]]
    goto_table: dict[str, dict[str, int]]
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    states: list[dict[str, Any]] = Field(default_factory=list)
    parse_trace: list[dict[str, Any]] | None = None


# Grammar Operator Precedence
class GrammarOpPrecedenceRequest(BaseModel):
    grammar_text: str
    input_string: str | None = None


class GrammarOpPrecedenceResponse(BaseModel):
    is_operator_grammar: bool
    leading: dict[str, list[str]]
    trailing: dict[str, list[str]]
    relations: dict[str, dict[str, str]]
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    parse_trace: list[dict[str, Any]] | None = None


# Grammar RD Pseudocode
class GrammarRDPseudocodeRequest(BaseModel):
    grammar_text: str


class GrammarRDPseudocodeResponse(BaseModel):
    pseudocode: str
    functions: list[dict[str, Any]] = Field(default_factory=list)


# SDD / SDT Evaluate
class SDDEvaluateRequest(BaseModel):
    preset: str | None = "desk_calculator"
    custom_rules: list[dict[str, Any]] | None = None
    input_text: str = ""


class SDDEvaluateResponse(BaseModel):
    annotated_tree: dict[str, Any]
    dependency_graph: dict[str, Any]
    evaluation_order: list[str]
    classification: dict[str, Any]
    attributes: dict[str, Any] = Field(default_factory=dict)


# Docs
class DocDetail(BaseModel):
    name: str
    title: str
    content: str
