"""Command line interface for rad-extract."""

import json
import rich
from cyclopts import App
from pathlib import Path

from .viewer import NERViewer
from .extract import extract_entities as extract_entities_fn

console = rich.get_console()


def _path_exists(p):
    """Validate that a path exists. Accepts a string or Path-like object.

    Raises ValueError if the path doesn't exist to signal the CLI framework.
    Returns a pathlib.Path on success.
    """
    ppath = Path(p)
    if not ppath.exists():
        raise ValueError(f"path does not exist: {ppath}")
    return ppath


app = App(name="rad-extract", version="0.1.0")
# NOTE: `cyclopts.App` in the installed version may not accept a `description` kwarg.
# If a description is needed, set it on the app object after construction or
# use the library's supported API for help text.


@app.command(name="extract")
def extract_entities(input_file: Path, output_file: Path | None = None) -> None:
    """Extract clinical entities from a radiology report file.

    Accepts JSON files with a required "text" field and optional "entities"
    and "relations" fields. For plain text files, reads the entire content as text.
    """
    if not input_file.exists():
        raise ValueError(f"Input file does not exist: {input_file}")

    # Read the input file
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if input is JSON
    if input_file.suffix.lower() in [".json", ".jsonl"]:
        try:
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("JSON input must be an object/dictionary")
            if "text" in data:
                text = data["text"]
            elif "tokens" in data:
                text = " ".join(data["tokens"])
            else:
                raise ValueError("JSON input must contain a 'text' or 'tokens' field")
            
            # Preserve optional fields if present
            existing_entities = data.get("entities", [])
            existing_relations = data.get("relations", [])
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in input file: {e}")
    else:
        # Plain text file
        text = content
        existing_entities = []
        existing_relations = []

    # Extract entities
    result = extract_entities_fn(text)

    # Merge with existing data if JSON input had these fields
    if input_file.suffix.lower() in [".json", ".jsonl"]:
        # Preserve entities field if it existed in input
        if "entities" in data:
            result["entities"] = existing_entities
        # Preserve relations field if it existed in input
        if "relations" in data:
            result["relations"] = existing_relations

    # Output results
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        console.print(f"[green]Results saved to {output_file}[/green]")
    else:
        console.print_json(data=result)


@app.command(name="display")
async def show_jsonl_row(jsonl_file: Path, row: int) -> None:
    """Display a specific row from a JSONL file using an interactive Textual UI.

    Args:
        jsonl_file: Path to the JSONL file
        row: Row index (0-based) to display
    """
    if not jsonl_file.exists():
        raise ValueError(f"File does not exist: {jsonl_file}")

    if not jsonl_file.suffix == ".jsonl":
        raise ValueError(f"File must have .jsonl extension: {jsonl_file}")

    if row < 0:
        raise ValueError(f"Row index must be non-negative, got: {row}")

    try:
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i == row:
                    data = json.loads(line)
                    viewer = NERViewer(data)
                    await viewer.run_async()
                    return

        # If we get here, the row index was out of bounds
        raise ValueError(f"Row index {row} out of bounds (file has {i + 1} rows)")

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON at row {row}: {e}")


def main():
    """Entry point for the CLI."""
    # Use the installed cyclopts API: run_async is a coroutine, so run it
    # in an event loop for synchronous entrypoint compatibility.
    import asyncio

    return asyncio.run(app.run_async())


if __name__ == "__main__":
    main()
