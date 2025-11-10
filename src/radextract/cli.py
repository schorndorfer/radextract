"""Command line interface for rad-extract."""

import json
import rich
from cyclopts import App
from pathlib import Path
from textual.app import App as TextualApp, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, Label, Checkbox
from textual.screen import Screen
from textual.reactive import reactive

console = rich.get_console()


class NERViewer(TextualApp):
    """A Textual app to display NER data from a JSONL row."""

    CSS = """
    Screen {
        background: $surface;
    }

    #legend {
        height: auto;
        padding: 0 1;
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
        height: 1;
        padding: 0 1;
    }

    #filter-section {
        height: auto;
        margin-top: 0;
    }

    .filter-checkbox {
        height: 3;
        padding: 0;
        margin: 0;
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

    show_anatomy = reactive(True)
    show_observation = reactive(True)
    selected_relations = reactive(set())
    select_all_relations = reactive(False)

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
            "Anatomy Present": "green",
            "Observation Present": "blue",
            "Definitely Absent": "red",
            "Uncertain/Other": "yellow",
        }

        legend_items = []
        for label, color in color_map.items():
            legend_items.append(Static(f"[{color}]■[/{color}] {label}", classes="legend-item"))

        # Add filter checkboxes
        filter_section = Vertical(
            Static("Filters:", classes="legend-item"),
            Checkbox("Show Anatomy", value=True, id="checkbox-anatomy", classes="filter-checkbox"),
            Checkbox("Show Observation", value=True, id="checkbox-observation", classes="filter-checkbox"),
            id="filter-section"
        )

        container = Vertical(*legend_items, filter_section, id="legend")
        container.border_title = "Legend"
        return container

    def _create_text_display(self) -> Container:
        """Create the text display with NER highlighting."""
        text = self._render_text()
        container = Vertical(Static(text, classes="text-content", id="text-static"), id="text-container")
        container.border_title = "Text with NER Annotations"
        return container

    def _render_text(self) -> str:
        """Render the text with NER highlighting based on current filters."""
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
        relations = self.data.get("relations", [])

        # Map token indices to their labels and colors
        color_map = {
            "Anatomy::definitely present": "green",
            "Observation::definitely present": "blue",
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

                # Apply filters based on label
                if "Anatomy" in label and not self.show_anatomy:
                    continue
                if "Observation" in label and not self.show_observation:
                    continue

                color = color_map.get(label, "yellow")
                for idx in range(start, end + 1):
                    token_colors[idx] = color

        # Add yellow highlighting for tokens in selected relations
        if self.selected_relations and relations:
            # Handle nested relations format
            relation_items = relations[0] if relations and isinstance(relations[0], list) and isinstance(relations[0][0], list) else relations

            for rel_idx in self.selected_relations:
                if rel_idx < len(relation_items):
                    rel = relation_items[rel_idx]
                    if len(rel) >= 5:
                        # Format: [start1, end1, start2, end2, relation_type]
                        start1, end1, start2, end2 = rel[0], rel[1], rel[2], rel[3]
                        # Highlight both entities in the relation
                        for idx in range(start1, end1 + 1):
                            token_colors[idx] = "yellow"
                        for idx in range(start2, end2 + 1):
                            token_colors[idx] = "yellow"

        # Build the text with NER tokens highlighted
        highlighted_tokens = []
        for i, token in enumerate(tokens):
            if i in token_colors:
                color = token_colors[i]
                highlighted_tokens.append(f"[{color}]{token}[/{color}]")
            else:
                highlighted_tokens.append(token)

        return " ".join(highlighted_tokens)

    def _format_relation(self, rel: list) -> str:
        """Format a relation for display with actual tokens instead of indices.

        Args:
            rel: Relation in format [start1, end1, start2, end2, relation_type]

        Returns:
            Formatted string like "relation_type: [tokens1] -> [tokens2]"
        """
        # Get tokens
        if "tokens" in self.data:
            tokens = self.data["tokens"]
        elif "sentences" in self.data:
            tokens = []
            for sentence in self.data["sentences"]:
                tokens.extend(sentence)
        else:
            tokens = []

        if len(rel) >= 5:
            start1, end1, start2, end2, relation_type = rel[0], rel[1], rel[2], rel[3], rel[4]

            # Extract token groups
            group1_tokens = tokens[start1:end1 + 1] if start1 < len(tokens) and end1 < len(tokens) else []
            group2_tokens = tokens[start2:end2 + 1] if start2 < len(tokens) and end2 < len(tokens) else []

            group1_text = " ".join(group1_tokens)
            group2_text = " ".join(group2_tokens)

            return f"{relation_type}: [{group1_text}] -> [{group2_text}]"
        else:
            return str(rel)

    def _create_relations_display(self) -> Container:
        """Create the relations display."""
        relations = self.data.get("relations", [])

        # Handle nested relations format
        relation_items = relations[0] if relations and isinstance(relations[0], list) and isinstance(relations[0][0], list) else relations

        if not relation_items:
            relation_widgets = [Static("No relations found", classes="relation-item")]
        else:
            relation_widgets = []
            # Add "Select All" checkbox at the top
            select_all_checkbox = Checkbox(
                "Select All",
                value=False,
                id="select-all-relations",
                classes="relation-item"
            )
            relation_widgets.append(select_all_checkbox)

            for i, rel in enumerate(relation_items):
                # Format the relation with actual tokens
                formatted_rel = self._format_relation(rel)
                rel_checkbox = Checkbox(
                    formatted_rel,
                    value=False,
                    id=f"relation-{i}",
                    classes="relation-item"
                )
                relation_widgets.append(rel_checkbox)

        container = Vertical(*relation_widgets, id="relations-container")
        container.border_title = f"Relations ({len(relation_items)})"
        return container

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes."""
        if event.checkbox.id == "checkbox-anatomy":
            self.show_anatomy = event.value
        elif event.checkbox.id == "checkbox-observation":
            self.show_observation = event.value
        elif event.checkbox.id == "select-all-relations":
            self.select_all_relations = event.value
        elif event.checkbox.id and event.checkbox.id.startswith("relation-"):
            # Extract relation index from ID
            relation_idx = int(event.checkbox.id.split("-")[1])
            new_selected = set(self.selected_relations)
            if event.value:
                new_selected.add(relation_idx)
            else:
                new_selected.discard(relation_idx)
            self.selected_relations = new_selected

    def watch_show_anatomy(self, new_value: bool) -> None:
        """React to changes in show_anatomy."""
        if self.is_mounted:
            self._update_text_display()

    def watch_show_observation(self, new_value: bool) -> None:
        """React to changes in show_observation."""
        if self.is_mounted:
            self._update_text_display()

    def watch_selected_relations(self, new_value: set) -> None:
        """React to changes in selected_relations."""
        if self.is_mounted:
            self._update_text_display()

    def watch_select_all_relations(self, new_value: bool) -> None:
        """React to changes in select_all_relations."""
        if self.is_mounted:
            relations = self.data.get("relations", [])
            if new_value:
                # Select all relations
                self.selected_relations = set(range(len(relations)))
                # Update all individual checkboxes
                for i in range(len(relations)):
                    try:
                        checkbox = self.query_one(f"#relation-{i}", Checkbox)
                        checkbox.value = True
                    except Exception:
                        pass
            else:
                # Deselect all relations
                self.selected_relations = set()
                # Update all individual checkboxes
                for i in range(len(relations)):
                    try:
                        checkbox = self.query_one(f"#relation-{i}", Checkbox)
                        checkbox.value = False
                    except Exception:
                        pass

    def _update_text_display(self) -> None:
        """Update the text display with current filter settings."""
        try:
            text_widget = self.query_one("#text-static", Static)
            text_widget.update(self._render_text())
        except Exception:
            # Widget not yet mounted, skip update
            pass


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
