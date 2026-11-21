"""Milestone M10 Architecture & Dependency Linting Tests.

Enforces:
1. Doc 02 §3 Dependency Rule: pure Python backend/vela without web imports.
2. Golden Rule AP-4: No fake/mock compiler data in frontend/src/pages.
3. Doc 01 §12: All 47 diagnostic error codes properly registered.
4. Runtime inputs: vela.bnf and vela_ll1.bnf are valid and loaded.
"""

from __future__ import annotations

import ast
from pathlib import Path

from vela.common.diagnostics import DIAGNOSTIC_CODES
from vela.grammar.loader import BNFLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_VELA = PROJECT_ROOT / "backend" / "vela"
FRONTEND_PAGES = PROJECT_ROOT / "frontend" / "src" / "pages"
BNF_FILE = PROJECT_ROOT / "docs" / "grammar" / "vela.bnf"
LL1_BNF_FILE = PROJECT_ROOT / "docs" / "grammar" / "vela_ll1.bnf"

FORBIDDEN_WEB_MODULES = {
    "fastapi",
    "starlette",
    "pydantic",
    "uvicorn",
    "requests",
    "httpx",
    "flask",
    "django",
}


def test_doc02_dependency_rule_no_web_imports_in_vela_library() -> None:
    """Verify backend/vela never imports web frameworks or HTTP clients."""
    violations: list[str] = []

    for py_file in BACKEND_VELA.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_mod = alias.name.split(".")[0]
                    if top_mod in FORBIDDEN_WEB_MODULES:
                        violations.append(f"{py_file.name}:{node.lineno} imports '{alias.name}'")
            elif isinstance(node, ast.ImportFrom) and node.module:
                top_mod = node.module.split(".")[0]
                if top_mod in FORBIDDEN_WEB_MODULES:
                    violations.append(f"{py_file.name}:{node.lineno} imports from '{node.module}'")

    assert not violations, "Forbidden web imports found in vela compiler library:\n" + "\n".join(violations)


def test_ap4_golden_rule_no_fake_compiler_data_in_frontend_pages() -> None:
    """Verify frontend/src/pages does not contain hard-coded fake tokens or instructions."""
    forbidden_patterns = [
        "const fakeTokens",
        "const mockTokens",
        "const fakeTac",
        "const mockTac",
        "const fakeInstructions",
        "const mockInstructions",
        "const fakeAst",
        "const mockAst",
    ]

    violations: list[str] = []
    for tsx_file in FRONTEND_PAGES.glob("*.tsx"):
        content = tsx_file.read_text(encoding="utf-8")
        for pat in forbidden_patterns:
            if pat in content:
                violations.append(f"{tsx_file.name} contains forbidden pattern '{pat}'")

    assert not violations, "Mock compiler data found in frontend pages:\n" + "\n".join(violations)


def test_doc01_sec12_all_47_error_codes_present() -> None:
    """Verify all 47 error codes specified in doc 01 §12 are registered in compiler."""
    expected_codes = [
        # Lexical (11)
        "VL-LEX-001", "VL-LEX-002", "VL-LEX-003", "VL-LEX-004", "VL-LEX-005",
        "VL-LEX-006", "VL-LEX-007", "VL-LEX-008", "VL-LEX-009", "VL-LEX-010", "VL-LEX-011",
        # Syntax (3)
        "VL-SYN-001", "VL-SYN-002", "VL-SYN-003",
        # Limit (1)
        "VL-LIM-001",
        # Semantic (23)
        "VL-SEM-001", "VL-SEM-002", "VL-SEM-003", "VL-SEM-004", "VL-SEM-005",
        "VL-SEM-006", "VL-SEM-007", "VL-SEM-008", "VL-SEM-009", "VL-SEM-010",
        "VL-SEM-011", "VL-SEM-012", "VL-SEM-013", "VL-SEM-014", "VL-SEM-015",
        "VL-SEM-016", "VL-SEM-017", "VL-SEM-018", "VL-SEM-019", "VL-SEM-020",
        "VL-SEM-021", "VL-SEM-022", "VL-SEM-023",
        # Runtime (8)
        "VL-RUN-001", "VL-RUN-002", "VL-RUN-003", "VL-RUN-004", "VL-RUN-005",
        "VL-RUN-006", "VL-RUN-007", "VL-RUN-008",
        # Warning (1)
        "VL-WRN-001",
    ]

    assert len(expected_codes) == 47, f"Expected 47 codes, got {len(expected_codes)}"
    for code in expected_codes:
        assert code in DIAGNOSTIC_CODES, f"Missing diagnostic code: {code}"


def test_grammar_bnf_files_load_at_runtime() -> None:
    """Verify runtime input BNF files load and parse into valid Grammar instances."""
    assert BNF_FILE.exists(), f"BNF file not found: {BNF_FILE}"
    g = BNFLoader.load_file(BNF_FILE)
    assert len(g.productions) > 0, "No productions loaded from vela.bnf"

    assert LL1_BNF_FILE.exists(), f"LL1 BNF file not found: {LL1_BNF_FILE}"
    g_ll1 = BNFLoader.load_file(LL1_BNF_FILE)
    assert len(g_ll1.productions) > 0, "No productions loaded from vela_ll1.bnf"
