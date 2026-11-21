"""Smoke tests for Vela package structure and module imports."""

import sys


def test_vela_import():
    """Verify that 'vela' can be imported and does not pull in web frameworks."""
    # Ensure fastapi is not pre-imported
    sys.modules.pop("fastapi", None)

    import vela

    assert vela is not None
    assert "fastapi" not in sys.modules, "AP-1 violation: vela imported fastapi!"


def test_subpackages_import():
    """Verify core compiler subpackages are importable."""
    import vela.ast
    import vela.codegen
    import vela.common
    import vela.grammar
    import vela.ir
    import vela.language
    import vela.lexer
    import vela.opt
    import vela.parser
    import vela.semantic
    import vela.vm

    assert vela.common is not None
