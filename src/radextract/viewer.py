"""Interactive NER viewer module for displaying annotated text."""

from textual.app import App as TextualApp, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static, Checkbox
from textual.reactive import reactive


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
            legend_items.append(
                Static(f"[{color}]■[/{color}] {label}", classes="legend-item")
            )

        # Add filter checkboxes
        filter_section = Vertical(
            Static("Filters:", classes="legend-item"),
            Checkbox(
                "Show Anatomy",
                value=True,
                id="checkbox-anatomy",
                classes="filter-checkbox",
            ),
            Checkbox(
                "Show Observation",
                value=True,
                id="checkbox-observation",
                classes="filter-checkbox",
            ),
            id="filter-section",
        )

        container = Vertical(*legend_items, filter_section, id="legend")
        container.border_title = "Legend"
        return container

    def _create_text_display(self) -> Container:
        """Create the text display with NER highlighting."""
        text = self._render_text()
        container = Vertical(
            Static(text, classes="text-content", id="text-static"), id="text-container"
        )
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
        selected_relation_tokens = set()

        # Handle both nested and flat NER formats
        ner_items = (
            ner[0]
            if ner and isinstance(ner[0], list) and isinstance(ner[0][0], list)
            else ner
        )

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

        # Track tokens in selected relations for bold and underline formatting
        if self.selected_relations and relations:
            # Handle nested relations format
            relation_items = (
                relations[0]
                if relations
                and isinstance(relations[0], list)
                and isinstance(relations[0][0], list)
                else relations
            )

            for rel_idx in self.selected_relations:
                if rel_idx < len(relation_items):
                    rel = relation_items[rel_idx]
                    if len(rel) >= 5:
                        # Format: [start1, end1, start2, end2, relation_type]
                        start1, end1, start2, end2 = rel[0], rel[1], rel[2], rel[3]
                        # Mark both entities in the relation for bold+underline
                        for idx in range(start1, end1 + 1):
                            selected_relation_tokens.add(idx)
                        for idx in range(start2, end2 + 1):
                            selected_relation_tokens.add(idx)

        # Build the text with NER tokens highlighted
        highlighted_tokens = []
        for i, token in enumerate(tokens):
            # Check if token is in a selected relation
            if i in selected_relation_tokens:
                highlighted_tokens.append(
                    f"[underline on yellow]{token}[/underline on yellow]"
                )
            elif i in token_colors:
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
            start1, end1, start2, end2, relation_type = (
                rel[0],
                rel[1],
                rel[2],
                rel[3],
                rel[4],
            )

            # Extract token groups - Python slicing handles out-of-bounds gracefully
            group1_tokens = tokens[start1 : end1 + 1] if tokens else []
            group2_tokens = tokens[start2 : end2 + 1] if tokens else []

            group1_text = (
                " ".join(group1_tokens) if group1_tokens else f"⟦{start1}:{end1}⟧"
            )
            group2_text = (
                " ".join(group2_tokens) if group2_tokens else f"⟦{start2}:{end2}⟧"
            )

            return f"{relation_type}: ⟦{group1_text}⟧ → ⟦{group2_text}⟧"
        else:
            return str(rel)

    def _create_relations_display(self) -> Container:
        """Create the relations display."""
        relations = self.data.get("relations", [])

        # Handle nested relations format
        relation_items = (
            relations[0]
            if relations
            and isinstance(relations[0], list)
            and isinstance(relations[0][0], list)
            else relations
        )

        if not relation_items:
            relation_widgets = [Static("No relations found", classes="relation-item")]
        else:
            relation_widgets = []
            # Add "Select All" checkbox at the top
            select_all_checkbox = Checkbox(
                "Select All",
                value=False,
                id="select-all-relations",
                classes="relation-item",
            )
            relation_widgets.append(select_all_checkbox)

            for i, rel in enumerate(relation_items):
                # Format the relation with actual tokens
                formatted_rel = self._format_relation(rel)
                rel_checkbox = Checkbox(
                    formatted_rel,
                    value=False,
                    id=f"relation-{i}",
                    classes="relation-item",
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
