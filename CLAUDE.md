# Project Rules for Treeparse

- Use **snake_case** for everything, including class names (e.g. `my_class`, `rich_argument_parser`, never `MyClass` or `CamelCase`).
  The core models (`cli`, `command`, `group`, `argument`, `option`, `chain`) already follow this convention.
- Keep example code exemplary: no builtin shadowing (`id`, `filter`, `all`, `input`, `open`, `check`, `fix`, etc.), correct type hints (`str | None = None` + `from __future__ import annotations`), no `sys.path` hacks in committed files.
- Run `ruff check --fix && ruff format` and the full test suite (`uv run pytest`) before opening PRs.
- Examples live in `examples/` as **living documentation**; they are not packaged or installed via `pip install treeparse`. See README "Examples" section for the supported dev workflow (`uv run --with-editable .`).

# See also
- The review at /tmp/grok-review-4571233e.md (and its summary) for the concrete issues that drove the 2026-05 hygiene + packaging cleanup.