"""Tests for group(default=...) — routing to a default subcommand when the
next token is not a known child command."""

import pytest

from treeparse import argument, cli, command, group, option
from treeparse.testing import cli_runner


def _build_app(default="open"):
    """A CLI with an `ink` group: an `open` (optional name) + a `fig` (required
    file) command. Callbacks record what they received in `calls`."""
    calls = []

    def cmd_open(name=None, notes_dir="default"):
        calls.append(("open", name, notes_dir))

    def cmd_fig(file):
        calls.append(("fig", file))

    notes_opt = option(flags=["--notes-dir", "-d"], dest="notes_dir", arg_type=str, default="default")
    ink = group(
        name="ink",
        help="Inkscape annotations.",
        default=default,
        commands=[
            command(
                name="open",
                callback=cmd_open,
                arguments=[argument(name="name", arg_type=str, nargs="?", default=None)],
                options=[notes_opt],
            ),
            command(
                name="fig",
                callback=cmd_fig,
                arguments=[argument(name="file", arg_type=str)],
            ),
        ],
    )
    app = cli(name="anno", help="test", subgroups=[ink])
    return app, calls


def test_explicit_subcommand_wins():
    app, calls = _build_app()
    cli_runner(app).invoke(["ink", "fig", "diagram.png"])
    assert calls == [("fig", "diagram.png")]


def test_unknown_token_routes_to_default_as_arg():
    app, calls = _build_app()
    cli_runner(app).invoke(["ink", "foo"])
    assert calls == [("open", "foo", "default")]


def test_bare_group_routes_to_default():
    app, calls = _build_app()
    cli_runner(app).invoke(["ink"])
    assert calls == [("open", None, "default")]


def test_leading_dash_token_routes_to_default_with_flag():
    app, calls = _build_app()
    cli_runner(app).invoke(["ink", "-d", "/tmp"])
    assert calls == [("open", None, "/tmp")]


def test_unknown_default_name_raises():
    app, _ = _build_app(default="nonexistent")
    with pytest.raises(ValueError, match="default"):
        app.build_parser()


def test_no_default_is_unchanged():
    app, calls = _build_app(default=None)
    # No default: a bare group should not dispatch a command (prints help, exit 0).
    result = cli_runner(app).invoke(["ink"])
    assert calls == []
    assert result.exit_code == 0


def test_help_shows_default_annotation():
    app, _ = _build_app()
    result = cli_runner(app).invoke(["--help"])
    assert "(default: open)" in result.output


def test_help_omits_annotation_without_default():
    app, _ = _build_app(default=None)
    result = cli_runner(app).invoke(["--help"])
    # options still render "(default: default)"; only the group annotation is gone
    assert "(default: open)" not in result.output


def test_nested_subgroup_default_resolves():
    """Walking descends through named groups; a subgroup's own default fires."""
    calls = []

    def leaf(name=None):
        calls.append(("show", name))

    inner = group(
        name="inner",
        default="show",
        commands=[
            command(
                name="show", callback=leaf, arguments=[argument(name="name", arg_type=str, nargs="?", default=None)]
            )
        ],
    )
    outer = group(name="outer", subgroups=[inner])  # outer itself has no default
    app = cli(name="app", subgroups=[outer])
    cli_runner(app).invoke(["outer", "inner", "bar"])
    assert calls == [("show", "bar")]
