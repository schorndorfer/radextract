from io import StringIO
import inspect

import pytest

from rich.console import Console

import rad_extract.cli as cli


def test_cli_module_exports():
    # Basic smoke tests for exported symbols
    assert hasattr(cli, "app")
    assert hasattr(cli, "main")
    assert hasattr(cli, "extract_entities")
    assert hasattr(cli, "batch_process")

    assert callable(cli.main)
    assert callable(cli.extract_entities)
    assert callable(cli.batch_process)


def test_extract_signature():
    sig = inspect.signature(cli.extract_entities)
    # Expect first parameter to be input_file, second optional output_file
    params = list(sig.parameters.values())
    assert len(params) >= 1
    assert params[0].name == "input_file"


def test_app_help_contains_commands():
    # Capture help printed by cyclopts into a StringIO via a Rich Console
    buf = StringIO()
    console = Console(file=buf, force_terminal=False)

    # Call help_print explicitly with our console
    cli.app.help_print(console=console)

    out = buf.getvalue()
    # Should contain help/commands and our command names
    assert "Commands" in out or "COMMANDS" in out or "Commands" in out
    assert "extract" in out
    assert "batch" in out
