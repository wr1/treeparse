# Design: `default` subcommand for treeparse groups

Date: 2026-06-03
Status: Approved (brainstorming)
Repos affected: `treeparse` (feature), `anno` (first consumer)

## Problem

A treeparse `group` compiles to an argparse subparser: the first token after the
group name *must* match a child command name, or argparse errors. This makes it
impossible to express a "noun verb-optional" CLI like `anno ink <name>` where
`ink` is a group with sibling commands (`fig`, `screen`) — the `<name>` token
collides with subcommand dispatch.

Concretely, `anno` has `ink new` / `ink open` and `mind new` / `mind open` pairs
that are near-duplicates. We want the common case (`anno ink foo`, `anno ink`) to
"just work" while keeping the other verbs (`fig`, `screen`) as explicit
subcommands.

## Feature: `group(default=...)`

### Public API

Add one optional field to the `group` model (inherited by `cli`):

```python
group(name="ink", default="open", commands=[open_cmd, fig_cmd, screen_cmd])
```

- `default` is the **name of a direct child command** of that group.
- It must not name a subgroup (only commands can receive the routed token/args).
- `None` (the default) preserves today's behavior exactly.

### Semantics

When dispatching at a group that has `default` set, treeparse inspects the next
token in `argv`:

| Next token                         | Behavior                                            |
|------------------------------------|-----------------------------------------------------|
| matches a child command/subgroup   | normal dispatch — **explicit always wins**          |
| missing (bare group)               | inject `default`; default command runs with no positional |
| starts with `-` (option/flag)      | inject `default` before it; flag applies to default command |
| unknown bare word                  | inject `default`; the word becomes default command's positional |

Examples (with `ink` default `open`, where `open`'s `name` arg is `nargs="?"`):

```
anno ink              -> anno ink open            # name=None
anno ink foo          -> anno ink open foo        # name="foo"
anno ink -d /tmp      -> anno ink open -d /tmp    # flag flows to open
anno ink fig x.png    -> anno ink fig x.png       # fig is a known subcommand; wins
```

### Implementation — argv pre-dispatch rewrite

The hook lives in `cli.run()`, **before** `parser.parse_args()`. A helper walks
`argv` against the command tree from the root: at each node that is a group with
`default` set, if the next token is not the display-name of any child
(command or subgroup), splice `group.default` into `argv` at that index, then
continue walking into the (now-named) child. Recurses so nested groups each
resolve independently.

Rationale for this approach over alternatives:

- **argparse-native** (optional `add_subparsers` + a positional on the group
  parser): argparse cannot cleanly arbitrate a single token between an optional
  subparser action and a positional `nargs="?"` at the same level — ambiguous
  and fragile.
- **custom argparse action/subclass**: more machinery for the same result.

The rewrite is localized (~15 lines, only `run()` + one helper), and leaves the
existing build/parse/validate/dispatch path untouched. `--help`, `--hv`,
`--json`, and `--version` already short-circuit earlier in `run()`, so they are
unaffected by the rewrite.

### Validation

In `_validate()` (or `build_parser()`): if a group has `default` set, assert it
names an existing **child command**. Otherwise raise a `ValueError` in the same
style treeparse already uses for malformed CLI definitions (e.g.
`"group 'ink': default 'opn' does not match any child command"`).

### Help rendering

Annotate the group's help line so the default is discoverable in the tree, e.g.:

```
├── ink ··········· Annotate figures with Inkscape. … (default: open)
```

Implemented in the tree renderer where the group row is built; gated on
`default is not None`.

### Tests

New `tests/test_cli_default_command.py`:

1. explicit subcommand still wins (`ink fig x` → `fig`)
2. unknown bare token routes to default with token as arg (`ink foo` → `open foo`)
3. bare group routes to default (`ink` → `open` with no positional)
4. leading-`-` token routes to default, flag applies (`ink -d /tmp` → `open -d /tmp`)
5. unknown `default` name raises `ValueError` at build/validate
6. nested groups each resolve their own default independently
7. group with no `default` is unchanged (regression guard)

## Consumer: `anno` wiring

After the feature ships in treeparse (version bump + release), update `anno`:

- **`ink` group** → `default="open"`. Make `cmd_ink_open`'s `name` optional
  (`nargs="?"`, default `None`) and convert it to **find-or-create**:
  - name given + file exists → open it
  - name given + missing → create a blank SVG with that name, then open
  - no name → timestamped scratch (`fig_YYYYmmdd_HHMMSS.svg`)
  - **Remove `cmd_ink_new` and the `ink new` command** — `open` absorbs it.
- **`mind` group** → `default="open"`. `mind open` already creates-if-missing via
  `_resolve_open_target` mode `"new"`; just make its `name` optional so bare
  `anno mind` yields a scratch map. **Remove `cmd_mind_new` and `mind new`.**
- **`para` group** → unchanged. `para new` takes a filesystem path and `para open`
  does a log lookup; their arguments mean different things, so no default and no
  consolidation.
- **Docs/abbrevations**: update `README.md` "Daily workflow" and "Commands"
  sections (`anno ink new` → `anno ink`, `anno mind new topic` → `anno mind topic`),
  regenerate `help.svg`, and review `scripts/shorthand.fish` (the `ani`/`anm`
  abbreviations still work; only the `new`-suffixed usages in prose change).

### Behavior change / trade-off (accepted)

Dropping `new` removes the "refuse to clobber an existing name" guard and the
strict "Not found" error on a typo'd `open`. Find-or-create means a mistyped name
silently creates a new empty annotation instead of erroring. This was explicitly
accepted in favor of the ergonomic single-verb flow.

## Out of scope

- No group-level `callback` (the "group-as-command" model) — rejected in favor of
  the lighter default-subcommand model.
- No change to `para`.
- No change to chains, options inheritance, or YAML config handling.

## Rollout order

1. treeparse: implement `default`, tests, validation, help rendering.
2. treeparse: bump version (0.2.8 → 0.3.0, new feature), release (PyPI), so
   `anno` can depend on it.
3. anno: bump `treeparse>=0.3.0`, wire `ink`/`mind`, remove `new`, update docs +
   `help.svg`.
