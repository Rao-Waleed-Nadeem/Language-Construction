"""Command Line Interface (CLI) for the Vela Compiler and Virtual Machine.

Supported Commands:
- compile: Compile Vela source code to target assembly with optional dump flags
- run: Compile and execute Vela source code on the Virtual Machine (or TAC Oracle)
- verify: Check Vela source code for syntax/semantic errors and report diagnostics
- selftest: Execute comprehensive self-test suite across bundled valid/invalid test corpus
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from vela.pipeline import CompileOptions, CompileResult, RunOptions, compile_source, run_program


def _print_diagnostics(result: CompileResult) -> None:
    for diag in result.diagnostics:
        loc = f"{diag.span.start.line}:{diag.span.start.column}"
        color_prefix = "ERROR" if diag.severity == "error" else "WARNING"
        print(f"[{color_prefix}] {diag.code} at {loc}: {diag.message}", file=sys.stderr)
        if diag.hint:
            print(f"    hint: {diag.hint}", file=sys.stderr)


def cmd_compile(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file '{args.file}' not found", file=sys.stderr)
        return 1

    source = path.read_text(encoding="utf-8")
    opts = CompileOptions(optimize=not args.no_opt)
    res = compile_source(source, filename=path.name, options=opts)

    _print_diagnostics(res)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return 0 if res.success else 1

    if args.dump_tokens and res.tokens:
        print("=== TOKENS ===")
        for tok in res.tokens:
            print(f"{tok.kind:<16} {tok.value!r:<20} {tok.span.start.line}:{tok.span.start.column}")

    if args.dump_ast and res.ast:
        print("=== AST ===")
        from vela.ast.printer import ASTPrinter

        print(ASTPrinter().print(res.ast))

    if args.dump_tac and res.optimized_tac:
        print("=== THREE-ADDRESS CODE ===")
        print(res.optimized_tac.to_text())

    if args.dump_target and res.target_program:
        print("=== TARGET ASSEMBLY ===")
        print(res.target_program.to_text())

    if args.output and res.target_program:
        out_path = Path(args.output)
        out_path.write_text(res.target_program.to_text() + "\n", encoding="utf-8")
        print(f"Wrote target assembly to {out_path}")

    return 0 if res.success else 1


def cmd_run(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file '{args.file}' not found", file=sys.stderr)
        return 1

    source = path.read_text(encoding="utf-8")
    opts = CompileOptions(optimize=not args.no_opt)
    res = compile_source(source, filename=path.name, options=opts)

    if not res.success or res.has_errors():
        _print_diagnostics(res)
        return 1

    stdin_data = ""
    if args.stdin:
        stdin_data = args.stdin
    elif args.stdin_file:
        stdin_path = Path(args.stdin_file)
        if stdin_path.exists():
            stdin_data = stdin_path.read_text(encoding="utf-8")
    elif (path.parent / f"{path.stem}.stdin.txt").exists():
        stdin_data = (path.parent / f"{path.stem}.stdin.txt").read_text(encoding="utf-8")

    run_opts = RunOptions(stdin=stdin_data, use_oracle=args.oracle)
    exec_res = run_program(res, stdin=stdin_data, options=run_opts)

    if args.json:
        output_dict: dict[str, Any] = {
            "stdout": exec_res.stdout,
            "exit_code": exec_res.exit_code,
            "diagnostics": [d.to_dict() for d in exec_res.diagnostics],
        }
        if hasattr(exec_res, "snapshots") and args.trace:
            output_dict["snapshots"] = [s.to_dict() for s in exec_res.snapshots]
        print(json.dumps(output_dict, indent=2))
        return exec_res.exit_code

    if exec_res.stdout:
        print(exec_res.stdout, end="")

    if exec_res.diagnostics:
        for diag in exec_res.diagnostics:
            print(f"Runtime Error: [{diag.code}] {diag.message}", file=sys.stderr)

    if args.trace and hasattr(exec_res, "snapshots"):
        print("\n=== EXECUTION TRACE ===", file=sys.stderr)
        for s in exec_res.snapshots[:20]:
            print(f"Step {s.step:04d} | PC={s.pc:03d} | {s.instruction_text:<25} | Regs={s.registers}", file=sys.stderr)
        if len(exec_res.snapshots) > 20:
            print(f"... and {len(exec_res.snapshots) - 20} more snapshots", file=sys.stderr)

    return exec_res.exit_code


def cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.exists():
        print(f"Error: file '{args.file}' not found", file=sys.stderr)
        return 1

    source = path.read_text(encoding="utf-8")
    res = compile_source(source, filename=path.name)
    _print_diagnostics(res)

    if res.success and not res.has_errors():
        print(f"OK: {path.name} compiled successfully with 0 errors.")
        return 0

    print(f"FAIL: {path.name} failed with {len([d for d in res.diagnostics if d.severity == 'error'])} errors.")
    return 1


def cmd_selftest(args: argparse.Namespace) -> int:
    """Run comprehensive self-test over all bundled programs and sidecars."""
    print("Running Vela Compiler & VM Self-Test Suite...")
    root = Path(__file__).resolve().parent.parent.parent
    examples_dir = root / "examples"
    invalid_dir = root / "backend" / "tests" / "programs" / "invalid"
    valid_dir = root / "backend" / "tests" / "programs" / "valid"

    total = 0
    passed = 0
    failures: list[str] = []

    # 1. Test 10 Examples
    print("\n--> [1/3] Standard Language Examples (examples/*.vela):")
    for ex_path in sorted(examples_dir.glob("*.vela")):
        total += 1
        source = ex_path.read_text(encoding="utf-8")
        expected_txt = (ex_path.parent / f"{ex_path.stem}.expected.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
        stdin_file = ex_path.parent / f"{ex_path.stem}.stdin.txt"
        stdin_data = stdin_file.read_text(encoding="utf-8") if stdin_file.exists() else ""

        # Test both O0 and O1
        for opt in (False, True):
            c_res = compile_source(source, filename=ex_path.name, options=CompileOptions(optimize=opt))
            if not c_res.success:
                failures.append(f"{ex_path.name} (opt={opt}): Compilation failed: {c_res.diagnostics}")
                continue

            exec_res = run_program(c_res, stdin=stdin_data)
            if exec_res.stdout != expected_txt or exec_res.exit_code != 0:
                failures.append(f"{ex_path.name} (opt={opt}): Output mismatch or exit code {exec_res.exit_code}")
                continue

        print(f"  PASS: {ex_path.name}")
        passed += 1

    # 2. Test Additional Valid Programs
    print("\n--> [2/3] Additional Valid Programs (tests/programs/valid/*.vela):")
    for val_path in sorted(valid_dir.glob("*.vela")):
        total += 1
        source = val_path.read_text(encoding="utf-8")
        c_res = compile_source(source, filename=val_path.name)
        if not c_res.success:
            failures.append(f"{val_path.name}: Compilation failed: {c_res.diagnostics}")
            print(f"  FAIL: {val_path.name}")
            continue

        exec_res = run_program(c_res)
        if exec_res.exit_code != 0:
            failures.append(f"{val_path.name}: Runtime failed with code {exec_res.exit_code}")
            print(f"  FAIL: {val_path.name}")
            continue

        print(f"  PASS: {val_path.name}")
        passed += 1

    # 3. Test Invalid Programs Catalogue
    print("\n--> [3/3] Invalid Programs Error Catalogue (tests/programs/invalid/*.vela):")
    for inv_path in sorted(invalid_dir.glob("*.vela")):
        total += 1
        source = inv_path.read_text(encoding="utf-8")
        sidecar_path = inv_path.parent / f"{inv_path.stem}.expect.json"
        expect_data: dict[str, Any] = {}
        if sidecar_path.exists():
            expect_data = json.loads(sidecar_path.read_text(encoding="utf-8"))

        c_res = compile_source(source, filename=inv_path.name)

        if inv_path.name.startswith("INV-RUN"):
            # Runtime error program: must compile cleanly and fail at runtime
            if not c_res.success:
                failures.append(f"{inv_path.name}: Expected clean compile, but failed: {c_res.diagnostics}")
                print(f"  FAIL: {inv_path.name}")
                continue

            stdin_data = expect_data.get("stdin", "")
            exec_res = run_program(c_res, stdin=stdin_data)
            expected_code = expect_data.get("code")
            if exec_res.exit_code == 0 or not any(d.code == expected_code for d in exec_res.diagnostics):
                failures.append(f"{inv_path.name}: Expected runtime error {expected_code}, got {exec_res.diagnostics}")
                print(f"  FAIL: {inv_path.name}")
                continue

        else:
            # Lexical, Syntax, or Semantic error: must fail during compilation
            if c_res.success:
                failures.append(f"{inv_path.name}: Expected compilation error, but succeeded")
                print(f"  FAIL: {inv_path.name}")
                continue

            expected_code = expect_data.get("code")
            if expected_code and not any(d.code == expected_code for d in c_res.diagnostics):
                actual_codes = [d.code for d in c_res.diagnostics]
                failures.append(f"{inv_path.name}: Expected error {expected_code}, got {actual_codes}")
                print(f"  FAIL: {inv_path.name}")
                continue

        print(f"  PASS: {inv_path.name}")
        passed += 1

    print("\n" + "=" * 50)
    print(f"Self-Test Summary: {passed}/{total} passed ({(passed / total) * 100:.1f}%)")
    print("=" * 50)

    if failures:
        print("\nFailures:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print("All self-tests passed successfully (100% pass rate)!")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m vela.cli", description="Vela Compiler & VM CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Compile
    p_compile = subparsers.add_parser("compile", help="Compile Vela source code")
    p_compile.add_argument("file", help="Path to .vela source file")
    p_compile.add_argument("-o", "--output", help="Write target assembly to file")
    p_compile.add_argument("-O0", "--no-opt", action="store_true", help="Disable optimization passes")
    p_compile.add_argument("--dump-tokens", action="store_true", help="Print lexer tokens")
    p_compile.add_argument("--dump-ast", action="store_true", help="Print typed AST")
    p_compile.add_argument("--dump-tac", action="store_true", help="Print Three-Address Code")
    p_compile.add_argument("--dump-target", action="store_true", help="Print Target Assembly")
    p_compile.add_argument("--json", action="store_true", help="Output CompileResult as JSON")

    # Run
    p_run = subparsers.add_parser("run", help="Compile and execute Vela source code")
    p_run.add_argument("file", help="Path to .vela source file")
    p_run.add_argument("--stdin", help="Standard input string")
    p_run.add_argument("--stdin-file", help="Path to standard input file")
    p_run.add_argument("-O0", "--no-opt", action="store_true", help="Disable optimization passes")
    p_run.add_argument("--oracle", action="store_true", help="Execute with TAC interpreter oracle instead of VM")
    p_run.add_argument("--trace", action="store_true", help="Print execution step snapshots")
    p_run.add_argument("--json", action="store_true", help="Output execution results as JSON")

    # Verify
    p_verify = subparsers.add_parser("verify", help="Verify syntax and semantics of Vela source code")
    p_verify.add_argument("file", help="Path to .vela source file")

    # Self-test
    subparsers.add_parser("selftest", help="Run comprehensive compiler & VM self-test suite")

    args = parser.parse_args(argv)

    if args.command == "compile":
        sys.exit(cmd_compile(args))
    elif args.command == "run":
        sys.exit(cmd_run(args))
    elif args.command == "verify":
        sys.exit(cmd_verify(args))
    elif args.command == "selftest":
        sys.exit(cmd_selftest(args))


if __name__ == "__main__":
    main()
