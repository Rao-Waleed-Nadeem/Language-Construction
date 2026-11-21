"""Tests for ISA, Cost Calculation, and Instruction Selection (M7-T1).

Verifies:
- Target instruction representations, registers, and addressing modes.
- Instruction cost model (AC-C2: sum of per-instruction costs equals total cost).
- Instruction selector coverage of all TAC opcodes (AC-C1: target instructions linked by tac_index).
- Selection runs cleanly across all 10 examples.
"""

from pathlib import Path

from vela.codegen.cost import get_instruction_cost
from vela.codegen.isa import (
    FP,
    R0,
    R1,
    R2,
    R7,
    SP,
    Immediate,
    MemoryRef,
    TargetInstruction,
    TargetProgram,
)
from vela.codegen.selector import InstructionSelector
from vela.ir.generator import TACGenerator
from vela.ir.tac import TACProgram
from vela.semantic.checker import check_source

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"


def _compile_to_tac(code: str, name: str = "test.vela") -> TACProgram:
    res = check_source(code, name)
    assert not [d for d in res.diagnostics if d.severity == "error"]
    assert res.ast is not None
    return TACGenerator().generate(res.ast)


def test_isa_registers_and_addressing_modes() -> None:
    """Verify register and memory addressing string representations."""
    assert str(R0) == "R0"
    assert str(R7) == "R7"
    assert str(SP) == "SP"
    assert str(FP) == "FP"

    # Immediate
    imm_int = Immediate(42)
    assert str(imm_int) == "42"
    imm_str = Immediate("hello")
    assert str(imm_str) == '"hello"'

    # MemoryRef
    m_sym = MemoryRef(symbol="x")
    assert str(m_sym) == "[x]"

    m_disp_pos = MemoryRef(base=FP, offset=8)
    assert str(m_disp_pos) == "[FP + 8]"

    m_disp_neg = MemoryRef(base=FP, offset=-4)
    assert str(m_disp_neg) == "[FP - 4]"


def test_instruction_cost_model_and_sum_acceptance() -> None:
    """Verify base costs and AC-C2: sum of instruction costs matches total."""
    assert get_instruction_cost("MOV", R1, R2) == 1
    assert get_instruction_cost("ADD", R1, R2, Immediate(5)) == 1
    assert get_instruction_cost("MUL", R1, R2, R0) == 3
    assert get_instruction_cost("DIV", R1, R2, R0) == 5
    assert get_instruction_cost("CALL", "foo") == 2
    assert get_instruction_cost("LABEL", "L1") == 0

    # Memory access penalty (+1)
    cost_load = get_instruction_cost("LOAD", R1, MemoryRef(base=FP, offset=-4))
    assert cost_load == 3  # 2 base + 1 memory

    prog = TargetProgram(
        instructions=[
            TargetInstruction("MOV", dst=R1, src1=Immediate(10), cost=1),
            TargetInstruction("MUL", dst=R1, src1=R1, src2=Immediate(2), cost=3),
            TargetInstruction("STORE", dst=MemoryRef(symbol="x"), src1=R1, cost=3),
        ]
    )

    # AC-C2: sum of per-instruction costs equals total_cost()
    assert prog.total_cost() == 7
    assert prog.total_cost() == sum(i.cost for i in prog.instructions)


def test_instruction_selection_links_tac_indices() -> None:
    """Verify AC-C1: every TAC quadruple maps to target instructions with tac_index."""
    code = """
    func main() {
        let a: int = 10;
        let b: int = 20;
        let c: int = a + b;
        show c;
    }
    """
    tac = _compile_to_tac(code)
    target = InstructionSelector().select(tac)

    assert len(target.instructions) >= len(tac.instructions)
    tac_indices = {i.tac_index for i in target.instructions}

    # Every TAC instruction index should be represented
    for idx in range(len(tac.instructions)):
        assert idx in tac_indices, f"TAC instruction at index {idx} not linked in target code"

    # All target instructions must have a non-empty rule_name
    for i in target.instructions:
        assert i.rule_name != "", f"Target instruction {i} has empty rule_name"


def test_instruction_selection_all_10_examples() -> None:
    """Verify InstructionSelector cleanly generates target code for all 10 examples."""
    for path in sorted(EXAMPLES_DIR.glob("*.vela")):
        code = path.read_text(encoding="utf-8")
        tac = _compile_to_tac(code, path.name)
        target = InstructionSelector().select(tac)

        assert len(target.instructions) > 0
        assert target.total_cost() > 0
        assert target.total_cost() == sum(i.cost for i in target.instructions)

        # Check serialization
        d = target.to_dict()
        assert "instruction_count" in d
        assert "total_cost" in d
        assert "instructions" in d
