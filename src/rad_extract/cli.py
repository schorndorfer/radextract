"""Command line interface for rad-extract."""

from cyclopts import App
from pathlib import Path


def _path_exists(p):
    """Validate that a path exists. Accepts a string or Path-like object.

    Raises ValueError if the path doesn't exist to signal the CLI framework.
    Returns a pathlib.Path on success.
    """
    ppath = Path(p)
    if not ppath.exists():
        raise ValueError(f"path does not exist: {ppath}")
    return ppath
from pathlib import Path

app = App(
    name="rad-extract",
    version="0.1.0"
)
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
def batch_process(input_dir: Path, output_dir: Path | None = None, pattern: str = "*.txt") -> None:
    """Process multiple radiology reports in a directory."""
    # TODO: Implement batch processing logic
    print(f"Processing files matching '{pattern}' in {input_dir}")
    if output_dir:
        print(f"Results will be saved to {output_dir}")

def main():
    """Entry point for the CLI."""
    # Use the installed cyclopts API: run_async is a coroutine, so run it
    # in an event loop for synchronous entrypoint compatibility.
    import asyncio

    return asyncio.run(app.run_async())

if __name__ == "__main__":
    main()