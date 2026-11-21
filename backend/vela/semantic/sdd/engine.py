"""Syntax-Directed Definition (SDD) evaluation engine and dependency graph builder.

Per doc 03 §5.6, doc 08 §3, and agent-prompt.md:
- Builds attribute dependency graphs across annotated parse trees.
- Computes topological evaluation order and detects circular dependencies.
- Evaluates attribute rules in topological order without using eval().
- Emits action traces for visualization in the Vela Studio SDD/SDT explorer.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

from vela.semantic.sdd.classifier import ClassificationResult, SDDClassifier
from vela.semantic.sdd.evaluator import SafeSDDEvaluator, reset_counters
from vela.semantic.sdd.model import (
    AnnotatedNode,
    SDDProduction,
    SDTActionStep,
    SemanticRule,
)


@dataclass
class SDDEvaluationResult:
    """Outcome of evaluating an SDD over a parse tree."""

    annotated_tree: AnnotatedNode
    dependency_graph: dict[str, list[str]]  # u -> [v1, v2] (v depends on u)
    evaluation_order: list[str]  # ["node_id.attr", ...]
    action_trace: list[SDTActionStep] = field(default_factory=list)
    is_cyclic: bool = False
    classification: ClassificationResult | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_cyclic": self.is_cyclic,
            "classification": self.classification.to_dict() if self.classification else None,
            "evaluation_order": self.evaluation_order,
            "dependency_graph": self.dependency_graph,
            "action_trace": [s.to_dict() for s in self.action_trace],
            "annotated_tree": self.annotated_tree.to_dict(),
        }


class SDDEngine:
    """Engine for analyzing and executing Syntax-Directed Definitions."""

    def __init__(self, productions: list[SDDProduction]) -> None:
        self.productions: list[SDDProduction] = productions
        self.prod_by_lhs_rhs: dict[tuple[str, tuple[str, ...]], SDDProduction] = {
            (p.lhs, tuple(p.rhs)): p for p in productions
        }

    def classify(self) -> ClassificationResult:
        """Classify this SDD as S-attributed / L-attributed."""
        return SDDClassifier.classify(self.productions)

    def evaluate(self, root: AnnotatedNode) -> SDDEvaluationResult:
        """Evaluate attribute rules across the annotated parse tree rooted at `root`."""
        reset_counters()
        classification = self.classify()

        # 1. Collect all nodes in the tree by ID
        node_map: dict[int, AnnotatedNode] = {}
        parent_map: dict[int, AnnotatedNode] = {}

        def index_nodes(node: AnnotatedNode, parent: AnnotatedNode | None = None) -> None:
            node_map[node.id] = node
            if parent:
                parent_map[node.id] = parent
            for c in node.children:
                index_nodes(c, node)

        index_nodes(root)

        # 2. Match productions to each nonterminal node and instantiate attribute dependency graph
        # Map: "node_id.attr" -> list of "node_id.attr" that it depends on
        # and reverse: "node_id.attr" -> list of "node_id.attr" that depend on it
        in_degree: dict[str, int] = defaultdict(int)
        adj: dict[str, list[str]] = defaultdict(list)
        all_attr_keys: set[str] = set()

        # Map: "node_id.attr" -> (rule, rule_env_map)
        rule_map: dict[str, tuple[SemanticRule, dict[str, AnnotatedNode]]] = {}

        # Terminal nodes initialize their lexval as an attribute if present
        for node in node_map.values():
            if node.is_terminal and node.lexval is not None:
                key = f"{node.id}.lexval"
                node.attributes["lexval"] = node.lexval
                all_attr_keys.add(key)
                if key not in in_degree:
                    in_degree[key] = 0

        # For each internal node, match its production and instantiate rules
        for node in node_map.values():
            if not node.children:
                continue

            rhs_tuple = tuple(c.symbol for c in node.children)
            prod = self.prod_by_lhs_rhs.get((node.symbol, rhs_tuple))
            if prod is None:
                # Fallback: match by LHS if RHS matches
                continue

            # Build environment mapping for rule symbols to actual tree nodes
            env_nodes: dict[str, AnnotatedNode] = {}
            env_nodes[prod.lhs] = node
            counts: dict[str, int] = {}
            for pos, child in enumerate(node.children):
                counts[child.symbol] = counts.get(child.symbol, 0) + 1
                if child.symbol not in env_nodes:
                    env_nodes[child.symbol] = child
                sub_name = f"{child.symbol}{counts[child.symbol]}"
                env_nodes[sub_name] = child

            for rule in prod.rules:
                target_node = env_nodes.get(rule.target_symbol)
                if target_node is None:
                    continue

                target_key = f"{target_node.id}.{rule.target_attr}"
                all_attr_keys.add(target_key)
                if target_key not in in_degree:
                    in_degree[target_key] = 0

                rule_map[target_key] = (rule, env_nodes)

                # Extract dependencies
                deps = rule.source_refs or SafeSDDEvaluator.extract_dependencies(rule.expr_str)
                for dep_sym, dep_attr in deps:
                    dep_node = env_nodes.get(dep_sym)
                    if dep_node is None:
                        continue
                    dep_key = f"{dep_node.id}.{dep_attr}"
                    all_attr_keys.add(dep_key)

                    # dep_key -> target_key
                    adj[dep_key].append(target_key)
                    in_degree[target_key] += 1
                    if dep_key not in in_degree:
                        in_degree[dep_key] = 0

        # 3. Topological sort (Kahn's algorithm)
        queue: deque[str] = deque([k for k in all_attr_keys if in_degree[k] == 0])
        eval_order: list[str] = []

        while queue:
            curr = queue.popleft()
            eval_order.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        is_cyclic = len(eval_order) < len(all_attr_keys)

        # 4. Evaluate attributes in topological order
        action_trace: list[SDTActionStep] = []
        step_num = 0

        if not is_cyclic:
            for attr_key in eval_order:
                if attr_key not in rule_map:
                    # Leaf or constant already set
                    continue

                rule, env_nodes = rule_map[attr_key]
                node_id_str, attr_name = attr_key.split(".", 1)
                node_id = int(node_id_str)
                target_node = node_map[node_id]

                # Prepare evaluation environment: symbol -> attributes dict
                eval_env: dict[str, dict[str, Any]] = {}
                for sym_name, sym_node in env_nodes.items():
                    eval_env[sym_name] = sym_node.attributes

                # Safely evaluate
                val = SafeSDDEvaluator.evaluate(rule.expr_str, eval_env)
                target_node.attributes[attr_name] = val

                step_num += 1
                action_type = "synthesize" if target_node == env_nodes.get(rule.target_symbol) else "inherit"
                action_trace.append(
                    SDTActionStep(
                        step=step_num,
                        action_type=action_type,
                        target_node_id=node_id,
                        symbol=target_node.symbol,
                        attribute=attr_name,
                        value=val,
                        rule_str=str(rule),
                    )
                )

        return SDDEvaluationResult(
            annotated_tree=root,
            dependency_graph=dict(adj),
            evaluation_order=eval_order,
            action_trace=action_trace,
            is_cyclic=is_cyclic,
            classification=classification,
        )
