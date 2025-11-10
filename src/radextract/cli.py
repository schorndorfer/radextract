"""Command line interface for rad-extract."""

import json
import rich
from cyclopts import App
from pathlib import Path
from textual.app import App as TextualApp, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Label
from textual.screen import Screen

console = rich.get_console()


class NERViewer(TextualApp):
    """A Textual app to display NER data from a JSONL row."""

    CSS = """
    Screen {
        background: $surface;
    }

    #legend {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
        margin: 1 2;
    }

    #text-container {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
        margin: 1 2;
    }

    #relations-container {
        height: auto;
        padding: 1;
        background: $panel;
        border: solid $primary;
        margin: 1 2;
    }

    .legend-item {
        height: auto;
        padding: 0 1;
    }

    .text-content {
        height: auto;
        padding: 1;
    }

    .relation-item {
        height: auto;
        padding: 0 1;
    }
    """

    def __init__(self, data: dict):
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield self._create_legend()
        yield self._create_text_display()
        yield self._create_relations_display()
        yield Footer()

    def _create_legend(self) -> Container:
        """Create the legend container."""
        color_map = {
            "Definitely Present": "green",
            "Definitely Absent": "red",
            "Uncertain/Other": "yellow",
        }

        legend_items = []
        for label, color in color_map.items():
            legend_items.append(Static(f"[{color}]■[/{color}] {label}", classes="legend-item"))

        container = Vertical(*legend_items, id="legend")
        container.border_title = "Legend"
        return container

    def _create_text_display(self) -> Container:
        """Create the text display with NER highlighting."""
        # Handle both "tokens" and "sentences" keys
        if "tokens" in self.data:
            tokens = self.data["tokens"]
        elif "sentences" in self.data:
            # Flatten sentences into a single list of tokens
            tokens = []
            for sentence in self.data["sentences"]:
                tokens.extend(sentence)
        else:
            tokens = []

        ner = self.data.get("ner", [])

        # Map token indices to their labels and colors
        color_map = {
            "Anatomy::definitely present": "green",
            "Observation::definitely present": "green",
            "Anatomy::definitely absent": "red",
            "Observation::definitely absent": "red",
            "Observation::uncertain": "yellow",
            "Anatomy::uncertain": "yellow",
        }

        token_colors = {}

        # Handle both nested and flat NER formats
        ner_items = ner[0] if ner and isinstance(ner[0], list) and isinstance(ner[0][0], list) else ner

        for item in ner_items:
            if len(item) >= 3:
                start, end, label = item[0], item[1], item[2]
                color = color_map.get(label, "yellow")
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
        container = Vertical(Static(text, classes="text-content"), id="text-container")
        container.border_title = "Text with NER Annotations"
        return container

    def _create_relations_display(self) -> Container:
        """Create the relations display."""
        relations = self.data.get("relations", [])

        if not relations:
            relation_widgets = [Static("No relations found", classes="relation-item")]
        else:
            relation_widgets = []
            for i, rel in enumerate(relations):
                relation_widgets.append(
                    Static(f"{i+1}. {rel}", classes="relation-item")
                )

        container = Vertical(*relation_widgets, id="relations-container")
        container.border_title = f"Relations ({len(relations)})"
        return container


def display_data(data: dict) -> None:
    """Display data from a JSONL row.

    Args:
        data: The parsed JSON data to display
    """
    tokens = data["tokens"]
    ner = data["ner"]
    relations = data["relations"]

    # Map token indices to their labels and colors
    color_map = {
        "Anatomy::definitely present": "green",
        "Observation::definitely present": "green",
        "Anatomy::definitely absent": "red",
        "Observation::definitely absent": "red",
        "Observation::uncertain": "yellow",
        "Anatomy::uncertain": "yellow",
    }

    token_colors = {}

    for item in ner:
        start, end, label = item[0], item[1], item[2]
        color = color_map.get(label, "yellow")
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

    # print a color legend
    legend_items = [
        "[green]Definitely Present[/green]",
        "[red]Definitely Absent[/red]",
        "[yellow]Uncertain/Other[/yellow]",
    ]
    console.print("-" * 80)
    console.print("Legend: " + " | ".join(legend_items))
    console.print("-" * 80)
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
