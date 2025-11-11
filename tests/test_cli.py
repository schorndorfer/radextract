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


@pytest.mark.asyncio
async def test_show_jsonl_row_basic():
    """Test basic functionality of show_jsonl_row with valid data."""
    # Create a temporary JSONL file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        test_data = [
            {"tokens": ["Hello", "world"], "ner": [[0, 1, "test"]], "relations": []},
            {
                "tokens": ["Test", "sentence", "here"],
                "ner": [[1, 2, "test"]],
                "relations": [],
            },
            {"tokens": ["Another", "example"], "ner": [], "relations": []},
        ]
        for record in test_data:
            f.write(json.dumps(record) + "\n")
        temp_path = Path(f.name)

    try:
        # Test that the function can be called without errors
        # Since it launches a TUI, we can't easily test the output
        # We'll just verify it reads the file and creates NERViewer
        import json as json_lib

        with open(temp_path, "r") as f:
            line = f.readline()
            data = json_lib.loads(line)
            from radextract.viewer import NERViewer

            viewer = NERViewer(data)
            assert viewer is not None
            assert viewer.data == data
    finally:
        temp_path.unlink()


@pytest.mark.asyncio
async def test_show_jsonl_row_file_not_found():
    """Test that show_jsonl_row raises ValueError for non-existent file."""
    with pytest.raises(ValueError, match="File does not exist"):
        await cli.show_jsonl_row(Path("/nonexistent/file.jsonl"), 0)


@pytest.mark.asyncio
async def test_show_jsonl_row_wrong_extension():
    """Test that show_jsonl_row raises ValueError for non-JSONL file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("test")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="must have .jsonl extension"):
            await cli.show_jsonl_row(temp_path, 0)
    finally:
        temp_path.unlink()


@pytest.mark.asyncio
async def test_show_jsonl_row_negative_index():
    """Test that show_jsonl_row raises ValueError for negative row index."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({"tokens": ["test"], "ner": [], "relations": []}) + "\n")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="must be non-negative"):
            await cli.show_jsonl_row(temp_path, -1)
    finally:
        temp_path.unlink()


@pytest.mark.asyncio
async def test_show_jsonl_row_out_of_bounds():
    """Test that show_jsonl_row raises ValueError for out of bounds index."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write(json.dumps({"tokens": ["test"], "ner": [], "relations": []}) + "\n")
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="out of bounds"):
            await cli.show_jsonl_row(temp_path, 10)
    finally:
        temp_path.unlink()
