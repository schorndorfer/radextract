"""Command line interface for rad-extract."""

import json
import rich
from cyclopts import App
from pathlib import Path

console = rich.get_console()


def display_data(data: dict) -> None:
    """Display data from a JSONL row.

    Args:
        data: The parsed JSON data to display
    """
    tokens = data.get("tokens", [])
    ner = data.get("ner", [])
    relations = data.get("relations", [])

    # Map token indices to their labels and colors
    token_colors = {}

    if ner:
        # Check the format of NER data
        first_item = ner[0]

        if isinstance(first_item, int):
            # Simple format: [0, 1, 3] - just token indices (default to green)
            for idx in ner:
                token_colors[idx] = "green"
        elif isinstance(first_item, list):
            # Complex format: [[start, end, label], ...] - convert to tuples and extract spans
            ner_tuples = [tuple(item) for item in first_item]
            for item in ner_tuples:
                if len(item) >= 3:
                    start, end, label = item[0], item[1], item[2]
                    # Determine color based on label
                    color = (
                        "orange" if label == "Anatomy::definitely present" else "green"
                    )
                    for idx in range(start, end + 1):
                        token_colors[idx] = color

    # Build the text with NER tokens highlighted
    highlighted_tokens = []
    for i, token in enumerate(tokens):
        if i in token_colors:
            color = token_colors[i]
            highlighted_tokens.append(f"[{color}]{token}[/{color}]")
        else:
            highlighted_tokens.append(token)

    text = " ".join(highlighted_tokens)
    console.print(text)


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
    """Extract clinical entities from a radiology report file."""
    # TODO: Implement extraction logic
    print(f"Processing {input_file}")
    if output_file:
        print(f"Results will be saved to {output_file}")


@app.command(name="batch")
def batch_process(
    input_dir: Path, output_dir: Path | None = None, pattern: str = "*.txt"
) -> None:
    """Process multiple radiology reports in a directory."""
    # TODO: Implement batch processing logic
    print(f"Processing files matching '{pattern}' in {input_dir}")
    if output_dir:
        print(f"Results will be saved to {output_dir}")


@app.command(name="show-row")
def show_jsonl_row(jsonl_file: Path, row: int) -> None:
    """Display a specific row from a JSONL file.

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
                    display_data(data)
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
