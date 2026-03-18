[![ci](https://github.com/wr1/treeparse/actions/workflows/ci.yml/badge.svg)](https://github.com/wr1/treeparse/actions/workflows/ci.yml)
![Version](https://img.shields.io/github/v/release/wr1/treeparse)

# Treeparse

**Tree-based CLI framework** for one-shot human and LLM CLI transparency.

## Overview

Treeparse is an intuitive CLI framework leveraging `argparse`, `rich`, and `pydantic` to create structured, testable command-line interfaces. It mirrors the tree-like help output of `treeclick` but uses `argparse` for parsing and `pydantic` for model-based definitions.

Key goals include speed, LLM transparency (JSON and rich tree help formats), ease of authoring (especially for AI-generated code), and **advanced composability**.

![Demo scripts](docs/assets/demos.gif)

## Key Features

- **Object-Oriented Structure**: Define CLI using Pydantic models: `cli`, `group`, `command`, `argument`, `option`.
- **Rich Tree Help**: Tree-structured help with branch pruning for subcommands, including higher levels.
- **JSON Output**: `--json` / `-j` provides syntax-highlighted JSON of the CLI structure for LLM parsing.
- **Parameter Validation**: Automatic matching of callback params to CLI definitions (names, types).
- **Folding**: Collapse deep subgroups in help output with `group.fold = True` (shows as `group [...]`).
- **Pluggability & Composition**: Full CLIs can be nested and reused as subgroups; supports YAML config and color themes.
- **Sorting**: `sort_key` for ordering elements in help outputs.
- **Type and Default Display**: Optional `show_types` and `show_defaults` flags.
- **Nargs Support**: Handles variable arguments/options (e.g., `*`, `+` for lists).
- **Boolean Handling**: Supports bool types with string-to-bool conversion.

## Advanced Features

### Folding
Keep large CLIs readable by folding groups:

```python
user_group = group(
    name="user",
    help="User management commands",
    fold=True,                    # Shows as "user [...]" in help tree
    commands=[greet_cmd, list_cmd],
)
```

Users can still explore the subtree with `myapp user --help`.

### Pluggability & Composition
Treeparse is highly composable — embed entire CLIs as subgroups:

```python
from treeparse import cli
from basic import app as basic_app
from demo import app as demo_app

super_app = cli(
    name="supertool",
    help="Combined CLI",
    subgroups=[basic_app, demo_app],   # Full CLIs reused!
)
```

See `examples/basic_super.py` for a live example.

Other pluggable features:

- **Color Themes**: `theme="mononeon"` (or `monochrome`, `red_white_blue`)
- **YAML Configuration**: `yml_config=Path("config.yml")` to override defaults
- **Shell Completions**: Optional `shtab` support via `[completions]` extra
- **Testing**: `CliRunner` for clean pytest integration

### Developer Validation Demo
Run `validation_error_demo.py` to explore rich error messages for name mismatches, type mismatches, and invalid defaults.

## Structure

- **`cli`**: Root (also reusable as a sub-CLI)
- **`group`**: Nested containers with optional `fold`
- **`command` / `chain`**: Executable actions
- **`argument`** & **`option`**: Parameters

Models are modularized; initialization in `__init__.py` handles forward references.

## Usage Example

From `examples/basic.py`:

```python
from treeparse import cli, command

def hello():
    print("Hello, world!")

app = cli(
    name="basic",
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

Run: `python examples/basic.py hello`

## Help Output

Tree-structured help prunes irrelevant branches while retaining context. Folding keeps deep hierarchies clean. Supports long help text wrapping.

## LLM Transparency

- **Rich Tree Format**: Visual, human/LLM-readable tree.
- **JSON Format**: Structured, parseable output for LLMs.

## Current Status

- Implemented: Model definitions, tree/JSON help, validation, nargs, bool support, **folding**, **pluggability** (composition, themes, YAML), `CliRunner`.
- Examples: `basic.py`, `demo.py` (complex), `list_demo.py`, `basic_super.py` (composition), `validation_error_demo.py`.
- Tests: Extensive pytest coverage (~87%) with dedicated runner tests and help-output snapshot tests.
- Tools: Ruff, pytest-cov.

## Recent Improvements (v0.2.x)

- **Correctness fixes**: inherited options now included in default-vs-choices validation; `option(required=True, default=X)` is caught at construction time; callback validation uses `inspect.unwrap()` so decorated functions are inspected correctly, and async callbacks are rejected with a clear error.
- **Enum type support**: `arg_type=MyEnum` automatically populates `choices` from enum member names and converts input strings via `MyEnum[s]`.
- **Help renderer extracted**: The 440-line help renderer now lives in `treeparse.utils.help_renderer` as an isolated, testable class. `cli.py` is ~375 lines (down from ~950).
- **Parser caching**: `build_parser()` and `get_max_depth()` cache their results after the first call; do not mutate a `cli` after first `run()`.
- **YAML config scope fixed**: `yml_config` overrides now apply to options on all subgroups and commands (not only root-level options); unrecognized config keys emit `warnings.warn`.

## License

MIT License.
