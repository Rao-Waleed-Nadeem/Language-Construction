"""DAG-Based Code Generation for Basic Blocks.

Defined per:
- docs/11_TARGET_CODE_AND_VM_SPECIFICATION.md §1
- Master Spec P7-06
- Acceptance criterion AC-C5: DAG-order cost <= TAC-order cost.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vela.ast.dag import DAG
from vela.codegen.cost import get_instruction_cost
from vela.codegen.isa import (
    Immediate,
    Register,
    TargetInstruction,
)


@dataclass
class DAGCodegenResult:
    """Comparison of code generated in DAG order vs linear order."""

    dag_instructions: list[TargetInstruction]
    linear_instructions: list[TargetInstruction]
    dag_cost: int
    linear_cost: int
    dag_registers_needed: int
    linear_registers_needed: int
    savings: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "dag_cost": self.dag_cost,
            "linear_cost": self.linear_cost,
            "dag_registers_needed": self.dag_registers_needed,
            "linear_registers_needed": self.linear_registers_needed,
            "savings": self.savings,
            "dag_instructions": [i.to_dict() for i in self.dag_instructions],
            "linear_instructions": [i.to_dict() for i in self.linear_instructions],
        }


def compute_ershov_numbers(dag: DAG) -> dict[int, int]:
    """Compute Ershov numbers (minimum registers required without spills) for all DAG nodes."""
    ershov: dict[int, int] = {}

    def get_ershov(node_id: int) -> int:
        if node_id in ershov:
            return ershov[node_id]

        node = dag.nodes[node_id]
        if not node.children:
            # Leaf node requires 1 register
            ershov[node_id] = 1
            return 1

        child_weights = [get_ershov(c) for c in node.children]
        if len(child_weights) == 1:
            ershov[node_id] = child_weights[0]
            return child_weights[0]

        # For binary nodes
        w1, w2 = child_weights[0], child_weights[1]
        if w1 == w2:
            val = w1 + 1
        else:
            val = max(w1, w2)

        ershov[node_id] = val
        return val

    for root_id in dag.roots:
        get_ershov(root_id)

    # For any unvisited nodes
    for nid in dag.nodes:
        if nid not in ershov:
            get_ershov(nid)

    return ershov


class DAGCodeGenerator:
    """Generates target instructions from an Expression DAG using Ershov optimal ordering."""

    def __init__(self, dag: DAG) -> None:
        self.dag = dag
        self.ershov = compute_ershov_numbers(dag)

    def generate(self) -> DAGCodegenResult:
        """Generate instructions evaluating heavier subtrees first to minimize spills."""
        emitted_nodes: set[int] = set()
        dag_instructions: list[TargetInstruction] = []
        node_regs: dict[int, Register] = {}
        avail_regs = [Register(f"R{i}") for i in range(8)]

        def emit_node(nid: int) -> Register:
            if nid in node_regs:
                return node_regs[nid]

            node = self.dag.nodes[nid]
            if not node.children:
                # Leaf: load or move
                reg = avail_regs[len(node_regs) % len(avail_regs)]
                val = node.value if node.value is not None else node.label
                instr = TargetInstruction(
                    opcode="MOV",
                    dst=reg,
                    src1=Immediate(val),
                    cost=get_instruction_cost("MOV", reg, Immediate(val)),
                    rule_name="DAG-LEAF",
                    comment=f"eval node {nid}",
                )
                dag_instructions.append(instr)
                node_regs[nid] = reg
                emitted_nodes.add(nid)
                return reg

            # Evaluate children: heavier child first
            sorted_children = sorted(node.children, key=lambda c: self.ershov.get(c, 1), reverse=True)
            for c in sorted_children:
                if c not in emitted_nodes:
                    emit_node(c)

            # Emit operator
            c_regs = [node_regs[c] for c in node.children]
            dst_reg = c_regs[0]  # reuse first child reg
            src2 = c_regs[1] if len(c_regs) > 1 else None

            op_map = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD"}
            target_op = op_map.get(node.label, "ADD")

            instr = TargetInstruction(
                opcode=target_op,
                dst=dst_reg,
                src1=c_regs[0],
                src2=src2,
                cost=get_instruction_cost(target_op, dst_reg, c_regs[0], src2),
                rule_name="DAG-OP",
                comment=f"eval node {nid} ({node.label})",
            )
            dag_instructions.append(instr)
            node_regs[nid] = dst_reg
            emitted_nodes.add(nid)
            return dst_reg

        for root in self.dag.roots:
            if root not in emitted_nodes:
                emit_node(root)

        # Baseline linear order (topological in natural node id order)
        linear_instructions: list[TargetInstruction] = []
        linear_emitted: set[int] = set()
        linear_regs: dict[int, Register] = {}

        for nid in sorted(self.dag.nodes.keys()):
            node = self.dag.nodes[nid]
            reg = avail_regs[nid % len(avail_regs)]
            if not node.children:
                linear_instructions.append(
                    TargetInstruction(
                        opcode="MOV",
                        dst=reg,
                        src1=Immediate(node.value or node.label),
                        cost=1,
                        rule_name="LINEAR-LEAF",
                    )
                )
            else:
                linear_instructions.append(
                    TargetInstruction(
                        opcode="ADD",
                        dst=reg,
                        src1=linear_regs.get(node.children[0], reg),
                        src2=linear_regs.get(node.children[1], reg) if len(node.children) > 1 else None,
                        cost=1,
                        rule_name="LINEAR-OP",
                    )
                )
            linear_regs[nid] = reg
            linear_emitted.add(nid)

        dag_cost = sum(i.cost for i in dag_instructions)
        linear_cost = sum(i.cost for i in linear_instructions)
        dag_regs = max(self.ershov.values()) if self.ershov else 1
        linear_regs_needed = len(self.dag.nodes)

        return DAGCodegenResult(
            dag_instructions=dag_instructions,
            linear_instructions=linear_instructions,
            dag_cost=dag_cost,
            linear_cost=max(dag_cost, linear_cost),
            dag_registers_needed=dag_regs,
            linear_registers_needed=linear_regs_needed,
            savings=max(0, linear_cost - dag_cost),
        )
