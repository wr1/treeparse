[![ci](https://github.com/wr1/treeparse/actions/workflows/ci.yml/badge.svg)](https://github.com/wr1/treeparse/actions/workflows/ci.yml)
[![Version](https://img.shields.io/github/v/release/wr1/treeparse)](https://github.com/wr1/treeparse/releases)
[![PyPI](https://img.shields.io/pypi/v/treeparse)](https://pypi.org/project/treeparse/)
![Python](https://img.shields.io/badge/python-3.8+-blue)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

# Treeparse

**CLI framework for building LLM skill toolboxes.**

Build individual tools, plug them into a toolbox CLI, run `toolbox --json > skill.md`. The LLM reads it once and can use every command.

## Workflow

**1. Build tool 1**

```python
# ink.py
ink = cli(name="ink", help="Annotate figures with Inkscape.")
ink.commands.append(command(
    name="new", help="Open a new blank SVG.", callback=new,
    arguments=[argument(name="name", arg_type=str)],
    options=[option(flags=["--notes-dir", "-d"], arg_type=str, default="notes/draw")],
))
```

**2. Build tool 2**

```python
# mind.py
mind = cli(name="mind", help="Build mind maps in Minder.")
mind.commands.append(command(
    name="create", help="Create a new mind map.", callback=create,
    arguments=[argument(name="title", arg_type=str)],
))
```

**3. Plug into a toolbox**

```python
# toolbox.py
from treeparse import cli
from ink import ink
from mind import mind

toolbox = cli(name="toolbox", help="Creative toolbox.", subgroups=[ink, mind])

if __name__ == "__main__":
    toolbox.run()
```

**4. Teach the LLM**

```
toolbox --json > skill.md
```

```
toolbox --help
```

```
toolbox                      Creative toolbox.
├── ink                      Annotate figures with Inkscape.
│   └── new <NAME>           Open a new blank SVG.
│       └── --notes-dir, -d  Directory to save SVGs (default: notes/draw)
└── mind                     Build mind maps in Minder.
    └── create <TITLE>       Create a new mind map.
```

![Demo](docs/assets/demos.gif)

## Built-in flags

| Flag | Output |
|------|--------|
| `--help`, `-h` | Rich tree, branch-pruned per subcommand |
| `--json`, `-j` | Full CLI structure as JSON |
| `--version`, `-V` | Auto-detected from package metadata, or set with `version=` on `cli` |

## Installation

```
pip install treeparse
```

## Models

```python
from treeparse import cli, command, group, argument, option
from treeparse.models.chain import chain
```

| Model | Purpose |
|-------|---------|
| `cli` | Root — reusable as a subgroup in another `cli` |
| `group` | Namespace with optional `fold=True` to collapse in help |
| `command` | Executable action with a callback |
| `chain` | Runs multiple commands in sequence |
| `argument` | Positional — `<ARG>` required, `[ARG]` optional (`nargs="?"`/`"*"`) |
| `option` | Named flag, with optional inheritance to child commands |

## More

- **Folding**: `group(fold=True)` collapses to `group [...]` — drill in with `toolbox ink --help`
- **Inheritance**: `option(inherit=True)` propagates to all child commands
- **Validation**: callback param names and types checked against CLI definition at startup
- **YAML config**: `cli(yml_config=Path("config.yml"))` overrides defaults at runtime
- **Themes**: `theme="github"` / `"monokai"` / `"mononeon"` / `"monochrome"`
- **Testing**: `CliRunner` for pytest integration

## License

MIT
