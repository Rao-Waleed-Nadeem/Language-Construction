"""Compiler and Execution API routes.

Provides endpoints for:
- /api/language: Language specification tables and grammar
- /api/examples: Bundled example programs
- /api/compile: Full phase-gated compilation
- /api/run: Virtual machine execution and snapshots
- /api/verify: Tri-way execution verification (unopt oracle, opt oracle, VM)
- /api/selftest: Bundled test corpus verification
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from api.schemas import (
    CompileRequest,
    CompileResponse,
    ExampleDetail,
    ExampleItem,
    LanguageResponse,
    PrecedenceLevel,
    RunRequest,
    RunResponse,
    SelfTestItem,
    SelfTestResponse,
    VerifyRequest,
    VerifyResponse,
)
from vela.language.spec import DELIMITERS, KEYWORDS, OPERATORS, PRECEDENCE_TABLE
from vela.pipeline import CompileOptions, RunOptions, compile_source, run_program

router = APIRouter(prefix="/api", tags=["compiler"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
EXAMPLES_DIR = ROOT_DIR / "examples"
DOCS_DIR = ROOT_DIR / "docs"
TESTS_PROGRAMS_DIR = ROOT_DIR / "backend" / "tests" / "programs"


@router.get("/language", response_model=LanguageResponse)
def get_language_spec() -> LanguageResponse:
    """Return complete language specification tables and BNF grammars."""
    bnf_path = DOCS_DIR / "grammar" / "vela.bnf"
    ll1_path = DOCS_DIR / "grammar" / "vela_ll1.bnf"

    grammar_text = bnf_path.read_text(encoding="utf-8") if bnf_path.exists() else ""
    ll1_text = ll1_path.read_text(encoding="utf-8") if ll1_path.exists() else ""

    precedence = [
        PrecedenceLevel(
            level=p.level,
            name=p.name,
            operators=sorted(p.operators),
            associativity=p.associativity,
            description=p.name,
        )
        for p in PRECEDENCE_TABLE
    ]

    return LanguageResponse(
        keywords=sorted(KEYWORDS),
        operators=sorted(OPERATORS),
        delimiters=sorted(DELIMITERS),
        precedence=precedence,
        types=[
            "int",
            "float",
            "bool",
            "char",
            "string",
            "void",
            "int[]",
            "float[]",
            "bool[]",
            "char[]",
            "string[]",
        ],
        grammar=grammar_text,
        grammar_ll1=ll1_text,
    )


@router.get("/examples", response_model=list[ExampleItem])
def list_examples() -> list[ExampleItem]:
    """List all bundled language example programs."""
    items: list[ExampleItem] = []
    titles = {
        "01_hello_types": "Hello World & Basic Types",
        "02_conditions": "Conditionals & Logic",
        "03_switch": "Pattern Matching Switch",
        "04_loops": "While & For Loops",
        "05_functions": "Functions & Recursion",
        "06_arrays": "Arrays & Buffer Ops",
        "07_io": "Standard I/O Streams",
        "08_optimizer_showcase": "Optimizer Showcase",
        "09_strings_and_casts": "Strings & Type Casts",
        "10_scopes": "Block Scopes & Shadowing",
    }
    for p in sorted(EXAMPLES_DIR.glob("*.vela")):
        stem = p.stem
        title = titles.get(stem, stem.replace("_", " ").title())
        items.append(ExampleItem(id=stem, title=title, filename=p.name))
    return items


@router.get("/examples/{example_id}", response_model=ExampleDetail)
def get_example(example_id: str) -> ExampleDetail:
    """Return single example program with source code, stdin, and expected output."""
    path = EXAMPLES_DIR / f"{example_id}.vela"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Example '{example_id}' not found")

    source = path.read_text(encoding="utf-8")
    expected_path = EXAMPLES_DIR / f"{example_id}.expected.txt"
    expected = (
        expected_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if expected_path.exists()
        else ""
    )
    stdin_path = EXAMPLES_DIR / f"{example_id}.stdin.txt"
    stdin = stdin_path.read_text(encoding="utf-8") if stdin_path.exists() else ""

    return ExampleDetail(
        id=example_id,
        title=example_id.replace("_", " ").title(),
        filename=path.name,
        source=source,
        stdin=stdin,
        expected_output=expected,
    )


@router.post("/compile", response_model=CompileResponse)
def compile_endpoint(req: CompileRequest) -> CompileResponse:
    """Execute complete phase-gated compilation pipeline."""
    opts = CompileOptions(
        optimize=req.optimize,
        opt_level=req.opt_level,
        max_opt_iterations=req.max_opt_iterations,
        stop_after_phase=req.stop_after_phase,
    )
    res = compile_source(req.source, filename=req.filename, options=opts)

    return CompileResponse(
        filename=res.filename,
        source_hash=res.source_hash,
        success=res.success,
        halted_at_phase=res.halted_at_phase,
        timings_ms=res.timings_ms,
        diagnostics=[d.to_dict() for d in res.diagnostics],
        tokens=[t.to_dict() for t in res.tokens] if res.tokens else None,
        tokens_count=len(res.tokens) if res.tokens else 0,
        ast=res.ast.to_dict() if res.ast else None,
        cst=res.parse_tree.to_dict() if res.parse_tree else None,
        semantic=res.semantic_result.to_dict() if res.semantic_result else None,
        tac=res.tac_program.to_dict() if res.tac_program else None,
        blocks=[b.to_dict() for b in res.blocks] if res.blocks else None,
        cfg=res.cfg.to_dict() if res.cfg else None,
        optimized_tac=res.optimized_tac.to_dict() if res.optimized_tac else None,
        opt_passes=[p.to_dict() for p in res.opt_result.passes] if res.opt_result else None,
        target_unallocated=[i.to_dict() for i in res.target_unallocated.instructions]
        if res.target_unallocated
        else None,
        target_program=res.target_program.to_dict() if res.target_program else None,
        register_allocation=res.allocation_result.to_dict() if res.allocation_result else None,
        peephole_changes=[c.to_dict() for c in res.peephole_changes]
        if res.peephole_changes
        else None,
    )


@router.post("/run", response_model=RunResponse)
def run_endpoint(req: RunRequest) -> RunResponse:
    """Compile and execute program on Virtual Machine (or TAC oracle)."""
    c_opts = CompileOptions(optimize=req.optimize)
    c_res = compile_source(req.source, filename="main.vela", options=c_opts)

    if not c_res.success or c_res.has_errors():
        return RunResponse(
            stdout="",
            exit_code=1,
            success=False,
            steps_executed=0,
            total_cost=0,
            diagnostics=[d.to_dict() for d in c_res.diagnostics],
            snapshots=[],
            truncated_snapshots=False,
        )

    run_opts = RunOptions(stdin=req.stdin, use_oracle=req.use_oracle)
    exec_res = run_program(c_res, stdin=req.stdin, options=run_opts)

    snapshots_list: list[dict[str, Any]] = []
    truncated = False
    total_cost = 0

    if hasattr(exec_res, "snapshots"):
        snapshots_list = [s.to_dict() for s in exec_res.snapshots]
        truncated = getattr(exec_res, "truncated_snapshots", False)
        total_cost = getattr(exec_res, "total_cost", 0)

    steps = getattr(exec_res, "steps_executed", getattr(exec_res, "instructions_executed", 0))

    return RunResponse(
        stdout=exec_res.stdout,
        exit_code=exec_res.exit_code,
        success=exec_res.exit_code == 0,
        steps_executed=steps,
        total_cost=total_cost,
        diagnostics=[d.to_dict() for d in exec_res.diagnostics],
        snapshots=snapshots_list,
        truncated_snapshots=truncated,
    )


@router.post("/verify", response_model=VerifyResponse)
def verify_endpoint(req: VerifyRequest) -> VerifyResponse:
    """Tri-way execution equivalence verification across O0 oracle, O1 oracle, and Target VM."""
    c_unopt = compile_source(req.source, options=CompileOptions(optimize=False))
    c_opt = compile_source(req.source, options=CompileOptions(optimize=True))

    if not c_opt.success:
        return VerifyResponse(
            match=False,
            oracle_unopt={
                "stdout": "",
                "exit_code": 1,
                "diagnostics": [d.to_dict() for d in c_unopt.diagnostics],
            },
            oracle_opt={
                "stdout": "",
                "exit_code": 1,
                "diagnostics": [d.to_dict() for d in c_opt.diagnostics],
            },
            vm={
                "stdout": "",
                "exit_code": 1,
                "diagnostics": [d.to_dict() for d in c_opt.diagnostics],
            },
            diagnostics=[d.to_dict() for d in c_opt.diagnostics],
        )

    oracle_unopt = run_program(c_unopt, stdin=req.stdin, options=RunOptions(use_oracle=True))
    oracle_opt = run_program(c_opt, stdin=req.stdin, options=RunOptions(use_oracle=True))
    vm_res = run_program(c_opt, stdin=req.stdin, options=RunOptions(use_oracle=False))

    match = (
        oracle_unopt.stdout == oracle_opt.stdout == vm_res.stdout
        and oracle_unopt.exit_code == oracle_opt.exit_code == vm_res.exit_code
    )

    return VerifyResponse(
        match=match,
        oracle_unopt={
            "stdout": oracle_unopt.stdout,
            "exit_code": oracle_unopt.exit_code,
            "instructions": oracle_unopt.instructions_executed,
        },
        oracle_opt={
            "stdout": oracle_opt.stdout,
            "exit_code": oracle_opt.exit_code,
            "instructions": oracle_opt.instructions_executed,
        },
        vm={
            "stdout": vm_res.stdout,
            "exit_code": vm_res.exit_code,
            "steps": getattr(vm_res, "steps_executed", 0),
            "total_cost": getattr(vm_res, "total_cost", 0),
        },
        diagnostics=[d.to_dict() for d in vm_res.diagnostics],
    )


@router.get("/selftest", response_model=SelfTestResponse)
def selftest_endpoint() -> SelfTestResponse:
    """Run comprehensive self-test over all bundled programs and sidecars."""
    invalid_dir = TESTS_PROGRAMS_DIR / "invalid"
    valid_dir = TESTS_PROGRAMS_DIR / "valid"

    items: list[SelfTestItem] = []
    total = 0
    passed = 0

    # 1. Examples
    for ex_path in sorted(EXAMPLES_DIR.glob("*.vela")):
        total += 1
        source = ex_path.read_text(encoding="utf-8")
        expected_txt = (
            (ex_path.parent / f"{ex_path.stem}.expected.txt")
            .read_text(encoding="utf-8")
            .replace("\r\n", "\n")
        )
        stdin_file = ex_path.parent / f"{ex_path.stem}.stdin.txt"
        stdin_data = stdin_file.read_text(encoding="utf-8") if stdin_file.exists() else ""

        c_res = compile_source(source, filename=ex_path.name)
        if not c_res.success:
            items.append(
                SelfTestItem(
                    name=ex_path.name,
                    category="example",
                    passed=False,
                    expected=expected_txt,
                    actual="Compilation failed",
                    diagnostics=[d.to_dict() for d in c_res.diagnostics],
                )
            )
            continue

        exec_res = run_program(c_res, stdin=stdin_data)
        ok = exec_res.stdout == expected_txt and exec_res.exit_code == 0
        if ok:
            passed += 1
        items.append(
            SelfTestItem(
                name=ex_path.name,
                category="example",
                passed=ok,
                expected=expected_txt,
                actual=exec_res.stdout,
                diagnostics=[d.to_dict() for d in exec_res.diagnostics],
            )
        )

    # 2. Valid programs
    for val_path in sorted(valid_dir.glob("*.vela")):
        total += 1
        source = val_path.read_text(encoding="utf-8")
        c_res = compile_source(source, filename=val_path.name)
        if not c_res.success:
            items.append(
                SelfTestItem(
                    name=val_path.name,
                    category="valid",
                    passed=False,
                    diagnostics=[d.to_dict() for d in c_res.diagnostics],
                )
            )
            continue

        exec_res = run_program(c_res)
        ok = exec_res.exit_code == 0
        if ok:
            passed += 1
        items.append(
            SelfTestItem(
                name=val_path.name,
                category="valid",
                passed=ok,
                actual=exec_res.stdout,
                diagnostics=[d.to_dict() for d in exec_res.diagnostics],
            )
        )

    # 3. Invalid programs
    for inv_path in sorted(invalid_dir.glob("*.vela")):
        total += 1
        source = inv_path.read_text(encoding="utf-8")
        sidecar_path = inv_path.parent / f"{inv_path.stem}.expect.json"
        expect_data: dict[str, Any] = {}
        if sidecar_path.exists():
            expect_data = json.loads(sidecar_path.read_text(encoding="utf-8"))

        c_res = compile_source(source, filename=inv_path.name)
        expected_code = expect_data.get("code", "")

        if inv_path.name.startswith("INV-RUN"):
            if not c_res.success:
                items.append(
                    SelfTestItem(
                        name=inv_path.name,
                        category="invalid_runtime",
                        passed=False,
                        expected=expected_code,
                        actual="Compilation failed unexpectedly",
                        diagnostics=[d.to_dict() for d in c_res.diagnostics],
                    )
                )
                continue
            exec_res = run_program(c_res, stdin=expect_data.get("stdin", ""))
            ok = exec_res.exit_code != 0 and any(
                d.code == expected_code for d in exec_res.diagnostics
            )
            if ok:
                passed += 1
            items.append(
                SelfTestItem(
                    name=inv_path.name,
                    category="invalid_runtime",
                    passed=ok,
                    expected=expected_code,
                    actual=",".join(d.code for d in exec_res.diagnostics),
                    diagnostics=[d.to_dict() for d in exec_res.diagnostics],
                )
            )
        else:
            ok = not c_res.success and any(d.code == expected_code for d in c_res.diagnostics)
            if ok:
                passed += 1
            items.append(
                SelfTestItem(
                    name=inv_path.name,
                    category="invalid_compile",
                    passed=ok,
                    expected=expected_code,
                    actual=",".join(d.code for d in c_res.diagnostics),
                    diagnostics=[d.to_dict() for d in c_res.diagnostics],
                )
            )

    return SelfTestResponse(
        total=total,
        passed=passed,
        failed=total - passed,
        pass_rate=(passed / total) * 100.0 if total > 0 else 0.0,
        items=items,
    )
