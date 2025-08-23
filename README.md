# Treeparse

Intuitive CLI framework using argparse, rich, and pydantic.

## Features

- Define CLI structure using Pydantic models for groups, commands, arguments, and options.
- Automatic validation of callback parameters against CLI definitions.
- Rich tree-based help output with optional type display.
- Fast and transparent for LLMs with JSON help format (planned).
- Easily extensible and modular.

## Installation

```bash
uv pip install treeparse
```

Or with development dependencies:

```bash
uv venv
uv pip install -e .[dev]
```

## Usage

### Basic Example

```python
from treeparse import cli, command, group, argument

def hello():
    print("Hello, world!")

def hello1(name: str):
    print(f"Hello, {name}!")

app = cli(
    name="basic.py",
    help="A basic CLI example.",
    commands=[
        command(name="hello", help="Print hello world.", callback=hello, sort_key=-100)
    ],
    subgroups=[
        group(
            name="example",
            help="An example group.",
            commands=[
                command(
                    name="hello",
                    help="Print hello world from the group.",
                    callback=hello1,
                    arguments=[
                        argument(name="name", arg_type=str, sort_key=0),
                    ],
                )
            ],
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

## Development

- Run tests: `uv run pytest -v`
- Lint: `ruff check --fix`
- Format: `ruff format`

## License

MIT License. See [LICENSE](LICENSE) for details.



