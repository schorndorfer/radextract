from io import StringIO
import inspect
import json
import tempfile
from pathlib import Path

import pytest

from rich.console import Console

import radextract.cli as cli


def test_cli_module_exports():
    # Basic smoke tests for exported symbols
    assert hasattr(cli, "app")
    assert hasattr(cli, "main")
    assert hasattr(cli, "extract_entities")
    assert hasattr(cli, "batch_process")
    assert hasattr(cli, "show_jsonl_row")

    assert callable(cli.main)
    assert callable(cli.extract_entities)
    assert callable(cli.batch_process)
    assert callable(cli.show_jsonl_row)


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
    assert "show-row" in out


def test_show_jsonl_row_basic():
    """Test basic functionality of show_jsonl_row with valid data."""
    # Create a temporary JSONL file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        test_data = [
            {"tokens": ["Hello", "world"], "ner": [0], "relations": []},
            {"tokens": ["Test", "sentence", "here"], "ner": [1, 2], "relations": []},
            {"tokens": ["Another", "example"], "ner": [], "relations": []},
        ]
        for record in test_data:
            f.write(json.dumps(record) + "\n")
        temp_path = Path(f.name)

    try:
        # Capture output
        buf = StringIO()
        console = Console(file=buf, force_terminal=False, markup=True)

        # Temporarily replace the global console
        original_console = cli.console
        cli.console = console

        # Test reading row 0
        cli.show_jsonl_row(temp_path, 0)
        output = buf.getvalue()
        assert "Hello" in output
        assert "world" in output

    finally:
        # Restore original console and clean up
        cli.console = original_console
        temp_path.unlink()


def test_show_jsonl_row_file_not_found():
    """Test that show_jsonl_row raises ValueError for non-existent file."""
    with pytest.raises(ValueError, match="File does not exist"):
        cli.show_jsonl_row(Path("/nonexistent/file.jsonl"), 0)


def test_show_jsonl_row_wrong_extension():
    """Test that show_jsonl_row raises ValueError for non-JSONL file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="must have .jsonl extension"):
            cli.show_jsonl_row(temp_path, 0)
    finally:
        temp_path.unlink()


def test_show_jsonl_row_negative_index():
    """Test that show_jsonl_row raises ValueError for negative row index."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({"tokens": ["test"], "ner": [], "relations": []}) + "\n")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="must be non-negative"):
            cli.show_jsonl_row(temp_path, -1)
    finally:
        temp_path.unlink()


def test_show_jsonl_row_out_of_bounds():
    """Test that show_jsonl_row raises ValueError for out of bounds index."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({"tokens": ["test"], "ner": [], "relations": []}) + "\n")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="out of bounds"):
            cli.show_jsonl_row(temp_path, 10)
    finally:
        temp_path.unlink()


def test_display_data_with_ner_highlighting():
    """Test that display_data highlights NER tokens correctly."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=False, markup=True)

    # Temporarily replace the global console
    original_console = cli.console
    cli.console = console

    try:
        test_data = {
            "tokens": ["The", "patient", "has", "fever"],
            "ner": [1, 3],  # "patient" and "fever" are entities
            "relations": [],
        }

        cli.display_data(test_data)
        output = buf.getvalue()

        # The output should contain the tokens
        assert "patient" in output
        assert "fever" in output
        assert "The" in output
        assert "has" in output

    finally:
        cli.console = original_console
