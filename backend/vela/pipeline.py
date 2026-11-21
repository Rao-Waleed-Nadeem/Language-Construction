"""End-to-End Compilation and Execution Pipeline.

Implements:
- Phase-gated compilation pipeline per doc 02 §4 and AP-8
- Phase timings in milliseconds
- CompileResult and RunOptions
- Source SHA-256 caching identity
- Execution dispatch to Target Virtual Machine or TAC Oracle
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

from vela.ast.nodes import Program
from vela.codegen.isa import TargetProgram
from vela.codegen.peephole import PeepholeChange, optimize_peephole
from vela.codegen.regalloc import AllocationResult, RegisterAllocator
from vela.codegen.selector import InstructionSelector
from vela.common.diagnostics import Diagnostic
from vela.common.source import SourceFile
from vela.ir.generator import TACGenerator
from vela.ir.interpreter import ExecutionResult as OracleExecutionResult
from vela.ir.interpreter import TACInterpreter
from vela.ir.tac import TACProgram
from vela.lexer.scanner import Scanner
from vela.lexer.tokens import Token
from vela.opt.blocks import BasicBlock, partition_into_blocks
from vela.opt.cfg import ControlFlowGraph, build_cfg
from vela.opt.pipeline import OptimizationResult, optimize_tac
from vela.parser.parse_tree import ParseTreeNode
from vela.parser.recursive_descent import RecursiveDescentParser
from vela.semantic.checker import CheckResult, SemanticChecker
from vela.vm.machine import VirtualMachine, VMResult


@dataclass
class CompileOptions:
    """Options controlling compiler pipeline execution."""

    optimize: bool = True
    opt_level: int = 1
    max_opt_iterations: int = 10
    stop_after_phase: str | None = None  # "lexer", "parser", "semantic", "ir", "opt", "codegen"


@dataclass
class RunOptions:
    """Options controlling program execution."""

    stdin: str = ""
    use_oracle: bool = False
    max_steps: int | None = None


@dataclass
class CompileResult:
    """Complete aggregated results across all compiler phases."""

    source: str
    filename: str
    source_hash: str
    success: bool
    diagnostics: list[Diagnostic] = field(default_factory=list)
    timings_ms: dict[str, float] = field(default_factory=dict)
    tokens: list[Token] | None = None
    parse_tree: ParseTreeNode | None = None
    ast: Program | None = None
    semantic_result: CheckResult | None = None
    tac_program: TACProgram | None = None
    blocks: list[BasicBlock] | None = None
    cfg: ControlFlowGraph | None = None
    opt_result: OptimizationResult | None = None
    optimized_tac: TACProgram | None = None
    target_unallocated: TargetProgram | None = None
    allocation_result: AllocationResult | None = None
    target_program: TargetProgram | None = None
    peephole_changes: list[PeepholeChange] = field(default_factory=list)
    halted_at_phase: str | None = None

    def has_errors(self) -> bool:
        """Check if any phase produced error diagnostics."""
        return any(d.severity == "error" for d in self.diagnostics)

    def to_dict(self) -> dict[str, Any]:
        """Serialize complete compile result into JSON-compatible dictionary."""
        return {
            "filename": self.filename,
            "source_hash": self.source_hash,
            "success": self.success,
            "halted_at_phase": self.halted_at_phase,
            "timings_ms": self.timings_ms,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "tokens_count": len(self.tokens) if self.tokens is not None else 0,
            "ast": self.ast.to_dict() if self.ast is not None else None,
            "tac_instructions_count": len(self.tac_program.instructions) if self.tac_program is not None else 0,
            "optimized_tac_count": len(self.optimized_tac.instructions) if self.optimized_tac is not None else 0,
            "target_instructions_count": len(self.target_program.instructions) if self.target_program is not None else 0,
            "target_total_cost": self.target_program.total_cost() if self.target_program is not None else 0,
            "peephole_changes_count": len(self.peephole_changes),
        }


def compile_source(
    source: str,
    filename: str = "main.vela",
    options: CompileOptions | None = None,
) -> CompileResult:
    """Execute phase-gated compiler pipeline from source text through target code generation."""
    opts = options or CompileOptions()
    source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()

    result = CompileResult(
        source=source,
        filename=filename,
        source_hash=source_hash,
        success=False,
    )

    source_file = SourceFile(filename, source)

    # 1. Lexical Analysis
    t0 = time.perf_counter()
    scanner = Scanner(source_file)
    lex_res = scanner.scan()
    result.timings_ms["lexer"] = (time.perf_counter() - t0) * 1000.0
    result.tokens = lex_res.tokens
    result.diagnostics.extend(lex_res.diagnostics)

    if any(d.severity == "error" for d in lex_res.diagnostics):
        result.halted_at_phase = "lexer"
        return result

    if opts.stop_after_phase == "lexer":
        result.success = True
        return result

    # 2. Syntax Analysis
    t0 = time.perf_counter()
    parser = RecursiveDescentParser(lex_res.tokens, source_file)
    parse_res = parser.parse()
    result.timings_ms["parser"] = (time.perf_counter() - t0) * 1000.0
    result.parse_tree = parse_res.cst
    result.ast = parse_res.ast
    result.diagnostics.extend(parse_res.diagnostics)

    if any(d.severity == "error" for d in parse_res.diagnostics) or result.ast is None:
        result.halted_at_phase = "parser"
        return result

    if opts.stop_after_phase == "parser":
        result.success = True
        return result

    # 3. Semantic Analysis
    t0 = time.perf_counter()
    checker = SemanticChecker(result.ast)
    sem_res = checker.check()
    result.timings_ms["semantic"] = (time.perf_counter() - t0) * 1000.0
    result.semantic_result = sem_res
    result.diagnostics.extend(sem_res.diagnostics)

    if any(d.severity == "error" for d in sem_res.diagnostics):
        result.halted_at_phase = "semantic"
        return result

    if opts.stop_after_phase == "semantic":
        result.success = True
        return result

    # 4. Three-Address Code (TAC) Generation
    t0 = time.perf_counter()
    tac_gen = TACGenerator()
    tac_prog = tac_gen.generate(result.ast)
    result.timings_ms["ir"] = (time.perf_counter() - t0) * 1000.0
    result.tac_program = tac_prog

    # 5. Basic Blocks & Control Flow Graph
    t0 = time.perf_counter()
    partition = partition_into_blocks(tac_prog.instructions)
    cfg = build_cfg(partition)
    result.timings_ms["cfg"] = (time.perf_counter() - t0) * 1000.0
    result.blocks = partition.blocks
    result.cfg = cfg

    if opts.stop_after_phase == "ir":
        result.optimized_tac = tac_prog
        result.success = True
        return result

    # 6. Optimization Passes
    t0 = time.perf_counter()
    if opts.optimize and opts.opt_level > 0:
        opt_res = optimize_tac(tac_prog, max_iterations=opts.max_opt_iterations)
        result.opt_result = opt_res
        result.optimized_tac = opt_res.optimized_program
    else:
        result.optimized_tac = tac_prog
    result.timings_ms["optimizer"] = (time.perf_counter() - t0) * 1000.0

    if opts.stop_after_phase == "opt":
        result.success = True
        return result

    # 7. Target Instruction Selection & Register Allocation
    t0 = time.perf_counter()
    selector = InstructionSelector()
    unallocated = selector.select(result.optimized_tac)
    result.target_unallocated = unallocated

    regalloc = RegisterAllocator()
    alloc_res = regalloc.allocate(unallocated)
    result.allocation_result = alloc_res
    result.target_allocated = alloc_res.program
    result.timings_ms["codegen"] = (time.perf_counter() - t0) * 1000.0

    # 8. Target Code Peephole Optimization
    t0 = time.perf_counter()
    peephole_res = optimize_peephole(alloc_res.program)
    result.target_program = peephole_res.program
    result.peephole_changes = peephole_res.changes
    result.timings_ms["peephole"] = (time.perf_counter() - t0) * 1000.0

    result.success = True
    return result


def run_program(
    compile_result: CompileResult,
    stdin: str = "",
    options: RunOptions | None = None,
) -> VMResult | OracleExecutionResult:
    """Execute compiled program using the Target VM (or TAC Oracle)."""
    opts = options or RunOptions()
    input_data = stdin or opts.stdin

    if opts.use_oracle:
        if compile_result.optimized_tac is None and compile_result.tac_program is None:
            raise ValueError("No TAC program available for oracle execution")
        tac_prog = compile_result.optimized_tac or compile_result.tac_program
        assert tac_prog is not None
        interpreter = TACInterpreter()
        return interpreter.interpret(tac_prog, stdin=input_data)

    if compile_result.target_program is None:
        raise ValueError("Cannot run program: target code generation did not complete")

    vm = VirtualMachine()
    vm.load(compile_result.target_program)
    return vm.run(stdin=input_data)
