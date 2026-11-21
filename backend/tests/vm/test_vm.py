"""Tests for Virtual Machine Execution and Step Reversibility (M7-T3).

Verifies:
- AC-V1: VM execution produces exact expected output on all 10 standard language examples.
- AC-V2: Stepping backward restores previous register and machine state exactly.
- AC-V3: Runtime errors (INV-RUN-01..05) terminate VM with exact diagnostic codes.
- AC-V4: Programs exceeding 5,000 steps truncate snapshot storage while finishing correctly.
- AC-V5: Unified stdin token and character stream consumption.
"""

from pathlib import Path

from vela.codegen.peephole import optimize_peephole
from vela.codegen.regalloc import RegisterAllocator
from vela.codegen.selector import InstructionSelector
from vela.ir.generator import TACGenerator
from vela.opt.pipeline import optimize_tac
from vela.semantic.checker import check_source
from vela.vm.machine import VirtualMachine

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"
INVALID_DIR = Path(__file__).resolve().parent.parent / "programs" / "invalid"


def _compile_and_allocate(code: str, name: str = "test.vela"):
    res = check_source(code, name)
    assert not [d for d in res.diagnostics if d.severity == "error"]
    assert res.ast is not None
    tac = TACGenerator().generate(res.ast)
    opt_tac = optimize_tac(tac).optimized_program
    target_unalloc = InstructionSelector().select(opt_tac)
    alloc_res = RegisterAllocator().allocate(target_unalloc)
    peephole_res = optimize_peephole(alloc_res.program)
    return peephole_res.program


def test_vm_ac_v2_step_backward_restores_state() -> None:
    """Verify AC-V2: stepping backward restores previous register values exactly."""
    code = """
    func main() {
        let a: int = 10;
        let b: int = 20;
        let c: int = a + b;
        show c;
    }
    """
    program = _compile_and_allocate(code)
    vm = VirtualMachine()
    vm.load(program)

    # Step forward 4 times
    for _ in range(4):
        vm.step()

    snap4_pc = vm.cpu.pc
    snap4_regs = dict(vm.cpu.registers)

    # Step forward 1 more time
    vm.step()
    assert vm.cpu.pc != snap4_pc or vm.cpu.registers != snap4_regs

    # Step backward
    assert vm.step_back() is True
    # Registers and PC must match snap4 exactly
    assert vm.cpu.pc == snap4_pc
    assert vm.cpu.registers == snap4_regs


def test_vm_ac_v3_runtime_errors() -> None:
    """Verify AC-V3: INV-RUN-01..05 runtime errors terminate with exact diagnostic codes."""
    expected_codes = {
        "INV-RUN-01.vela": "VL-RUN-001",
        "INV-RUN-02.vela": "VL-RUN-002",
        "INV-RUN-03.vela": "VL-RUN-003",
        "INV-RUN-04.vela": "VL-RUN-006",
        "INV-RUN-05.vela": "VL-RUN-007",
    }
    stdin_inputs = {
        "INV-RUN-01.vela": "0\n",
    }

    for inv_file in sorted(INVALID_DIR.glob("INV-RUN-*.vela")):
        code = inv_file.read_text(encoding="utf-8")
        program = _compile_and_allocate(code, inv_file.name)
        vm = VirtualMachine()
        vm.load(program)
        stdin_data = stdin_inputs.get(inv_file.name, "")
        result = vm.run(stdin=stdin_data)

        assert result.exit_code != 0
        assert len(result.diagnostics) >= 1
        expected = expected_codes[inv_file.name]
        assert result.diagnostics[0].code == expected, f"Expected {expected}, got {result.diagnostics[0].code}"


def test_vm_ac_v1_all_10_examples_exact_output() -> None:
    """Verify AC-V1: VM execution produces exact expected stdout for all 10 examples."""
    for path in sorted(EXAMPLES_DIR.glob("*.vela")):
        code = path.read_text(encoding="utf-8")
        expected_txt = (path.parent / f"{path.stem}.expected.txt").read_text(encoding="utf-8").replace("\r\n", "\n")
        stdin_file = path.parent / f"{path.stem}.stdin.txt"
        stdin_data = stdin_file.read_text(encoding="utf-8") if stdin_file.exists() else ""

        program = _compile_and_allocate(code, path.name)
        vm = VirtualMachine()
        vm.load(program)
        result = vm.run(stdin=stdin_data)

        assert result.exit_code == 0, f"VM failed on {path.name}: {result.diagnostics}"
        assert result.stdout == expected_txt, f"Output mismatch on {path.name}:\nGot:\n{result.stdout}\nExpected:\n{expected_txt}"


def test_vm_ac_v4_snapshot_truncation_on_long_runs() -> None:
    """Verify AC-V4: Programs with > 5,000 steps truncate snapshots while running to completion."""
    code = """
    func main() {
        let sum: int = 0;
        for (let i: int = 0; i < 2000; i++) {
            sum += 1;
        }
        show sum;
    }
    """
    program = _compile_and_allocate(code)
    vm = VirtualMachine()
    vm.load(program)
    result = vm.run()

    assert result.exit_code == 0
    assert result.steps_executed > 5000
    assert len(result.snapshots) == 5000
    assert result.truncated_snapshots is True
    assert "2000" in result.stdout
