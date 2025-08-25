![Deploy](https://github.com/wr1/treeparse/actions/workflows/ci.yml/badge.svg)![Version](https://img.shields.io/github/v/release/wr1/treeparse)

# Treeparse

CLI framework using argparse, rich, and pydantic, showing a treeview representation of CLI help. 
This provides very compact full overview help, showing hierarchy. 

![gif](docs/assets/output.gif)

## Features

- Define CLI structure using Pydantic models for groups, commands, arguments, and options.
- Automatic validation of callback parameters against CLI definitions.
- Rich tree-based help output with optional type display.
- JSON help output.
- Pluggable, a CLI for an app can be made a branch of a higher level CLI without modifications. 

## Installation

```bash
pip install treeparse
```

Or with development dependencies:

```bash
uv venv
uv pip install -e .[dev]
```

## Usage

### Basic Example

```python
from treeparse import cli, command

def hello():
    print("Hello, world!")

app = cli(
    name="basic.py",
    help="A basic CLI example.",
    commands=[
        command(
            name="hello",
            help="Print hello world.",
            callback=hello,
        )
    ],
)

def main():
    app.run()

if __name__ == "__main__":
    main()

```

Run with:

```bash
python examples/basic.py hello
```

### Demo Example

See `examples/demo.py` for a more complex CLI with groups, subcommands, arguments, and options.

### List Demo Example

See `examples/list_demo.py` for demonstration of list arguments (nargs='*') and list options (nargs='+').

## Development

- Run tests: `uv run pytest -v`
- Lint: `ruff check --fix`
- Format: `ruff format`

## License

MIT License. See [LICENSE](LICENSE) for details.


