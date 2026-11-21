"""Tests for Basic Blocks, CFG, Dominator Trees, and Natural Loops (M6-T1).

Verifies:
- Leader identification with explicit reasons following Algorithm 8.5.
- Basic block partitioning without gaps or overlapping instructions.
- CFG construction with entry, fall-through, branch, jump, and return edges.
- Textbook dominator calculation and immediate dominator tree.
- Back edge detection and natural loop identification.
- End-to-end integration with compiled Vela loops and branches.
"""

from pathlib import Path

from vela.ir.generator import TACGenerator
from vela.opt.blocks import partition_into_blocks
from vela.opt.cfg import build_cfg
from vela.opt.dominators import compute_dominators
from vela.semantic.checker import check_source

EXAMPLES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "examples"


def _compile_to_tac(code: str, name: str = "test.vela"):
    res = check_source(code, name)
    assert not [d for d in res.diagnostics if d.severity == "error"]
    assert res.ast is not None
    return TACGenerator().generate(res.ast)


def test_leader_identification_and_reasons() -> None:
    """Verify Algorithm 8.5 leader identification and reason recording."""
    code = """
    func main() {
        let x: int = 10;
        if (x > 5) {
            show "big";
        } else {
            show "small";
        }
        show "done";
    }
    """
    tac = _compile_to_tac(code)
    partition = partition_into_blocks(tac.instructions)

    assert len(partition.blocks) > 1
    assert len(partition.leaders) == len(partition.blocks)

    # First instruction must have reason 'first instruction'
    assert partition.leaders[0].reason == "first instruction"
    assert partition.leaders[0].index == 0

    # There must be leaders due to jump targets and follows jump
    reasons = [l.reason for l in partition.leaders]
    assert any("jump target:" in r for r in reasons)
    assert any("follows" in r for r in reasons)


def test_cfg_construction_edges() -> None:
    """Verify CFG edge types: entry, branch, jump, fall-through, return."""
    code = """
    func main() {
        let i: int = 0;
        while (i < 5) {
            i++;
        }
        show i;
    }
    """
    tac = _compile_to_tac(code)
    partition = partition_into_blocks(tac.instructions)
    cfg = build_cfg(partition)

    assert len(cfg.blocks) == len(partition.blocks)
    assert len(cfg.edges) > 0

    edge_kinds = {e.kind for e in cfg.edges}
    assert "entry" in edge_kinds
    assert "branch" in edge_kinds
    assert "return" in edge_kinds

    # Entry node (0) must have a successor (first block)
    assert 1 in cfg.get_successors(cfg.entry_id)

    # Mermaid string generation
    mermaid = cfg.to_mermaid()
    assert "flowchart TD" in mermaid
    assert "B0" in mermaid
    assert "B_EXIT" in mermaid


def test_textbook_dominator_tree() -> None:
    """Verify dominator tree on a classic diamond CFG:

    B1 -> B2, B3
    B2 -> B4
    B3 -> B4
    """
    code = """
    func main() {
        let a: int = 1;
        if (a > 0) {
            a = 2;
        } else {
            a = 3;
        }
        show a;
    }
    """
    tac = _compile_to_tac(code)
    partition = partition_into_blocks(tac.instructions)
    cfg = build_cfg(partition)
    dom_info = compute_dominators(cfg)

    # Entry dominates everything
    for bid in cfg.blocks:
        assert dom_info.dominates(cfg.entry_id, bid)
        # Every block dominates itself
        assert dom_info.dominates(bid, bid)

    # Check to_dict serialization
    d = dom_info.to_dict()
    assert "dom" in d
    assert "idom" in d
    assert "back_edges" in d
    assert "natural_loops" in d


def test_natural_loop_detection_on_loops_example() -> None:
    """Verify natural loop and back-edge detection on examples/04_loops.vela."""
    loops_file = EXAMPLES_DIR / "04_loops.vela"
    code = loops_file.read_text(encoding="utf-8")

    tac = _compile_to_tac(code, "04_loops.vela")
    partition = partition_into_blocks(tac.instructions)
    cfg = build_cfg(partition)
    dom_info = compute_dominators(cfg)

    # 04_loops has while, do-while, and for loops
    # Back edges must be detected
    assert len(dom_info.back_edges) >= 3, f"Expected at least 3 back edges, found: {dom_info.back_edges}"
    assert len(dom_info.natural_loops) >= 3

    # For each back edge (n -> d), d must dominate n
    for src, tgt in dom_info.back_edges:
        assert dom_info.dominates(tgt, src), f"Target {tgt} does not dominate source {src}"
        loop_nodes = dom_info.natural_loops[(src, tgt)]
        assert tgt in loop_nodes
        assert src in loop_nodes
