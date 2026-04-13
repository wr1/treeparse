"""Snapshot tests for help renderer output.

These tests lock in the exact text output of the help renderer.
Run with `pytest --snapshot-update` (or delete the expected strings) to regenerate.
All comparisons use ANSI-stripped plain text via non-TTY stdout capture.
"""

import contextlib
import re
import sys
from io import StringIO

import pytest

from treeparse import argument, cli, command, group, option
from treeparse.models.chain import chain


def strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def run_help(app: cli, path: list = None) -> str:
    if path is None:
        path = []
    out = StringIO()
    sys.argv = [app.name] + path + ["--help"]
    try:
        with contextlib.redirect_stdout(out):
            app.run()
    except SystemExit:
        pass
    return strip_ansi(out.getvalue())


# --- fixtures ---


@pytest.fixture
def flat_app():
    def greet(name: str):
        pass

    app = cli(name="myapp", help="My application", max_width=80)
    app.commands.append(
        command(
            name="greet",
            help="Greet someone",
            callback=greet,
            arguments=[argument(name="name", arg_type=str)],
        )
    )
    return app


@pytest.fixture
def single_group_app():
    def cmd_a():
        pass

    def cmd_b(x: int):
        pass

    grp = group(name="ops", help="Operations group")
    grp.commands.append(command(name="run", help="Run it", callback=cmd_a))
    grp.commands.append(
        command(
            name="build",
            help="Build it",
            callback=cmd_b,
            arguments=[argument(name="x", arg_type=int)],
        )
    )
    app = cli(name="myapp", help="My application", max_width=80)
    app.subgroups.append(grp)
    return app


@pytest.fixture
def option_app():
    def do_thing(verbose: bool):
        pass

    opt = option(flags=["--verbose", "-v"], arg_type=bool, help="Verbose mode")
    cmd = command(name="thing", help="Do a thing", callback=do_thing, options=[opt])
    app = cli(name="myapp", help="My CLI", max_width=80)
    app.commands.append(cmd)
    return app


@pytest.fixture
def show_types_defaults_app():
    def process(name: str, count: int):
        pass

    opt = option(flags=["--count", "-c"], arg_type=int, default=5, help="Count")
    cmd = command(
        name="proc",
        help="Process",
        callback=process,
        arguments=[argument(name="name", arg_type=str)],
        options=[opt],
    )
    app = cli(name="myapp", help="My CLI", max_width=80, show_types=True, show_defaults=True)
    app.commands.append(cmd)
    return app


@pytest.fixture
def folded_group_app():
    def cmd_a():
        pass

    def cmd_b():
        pass

    grp = group(name="internal", help="Internal group", fold=True)
    grp.commands.append(command(name="run", help="Run", callback=cmd_a))
    grp.commands.append(command(name="clean", help="Clean", callback=cmd_b))
    app = cli(name="myapp", help="My CLI", max_width=80)
    app.subgroups.append(grp)
    return app


@pytest.fixture
def chain_app():
    def step1(x: int):
        pass

    def step2(y: str):
        pass

    cmd1 = command(name="step1", callback=step1, arguments=[argument(name="x", arg_type=int)])
    cmd2 = command(name="step2", callback=step2, arguments=[argument(name="y", arg_type=str)])
    ch = chain(name="pipe", help="Pipeline", chained_commands=[cmd1, cmd2])
    app = cli(name="myapp", help="Pipeline CLI", max_width=80)
    app.commands.append(ch)
    return app


@pytest.fixture
def nested_app():
    def leaf():
        pass

    inner = group(name="inner", help="Inner group")
    inner.commands.append(command(name="leaf", help="Leaf cmd", callback=leaf))
    outer = group(name="outer", help="Outer group")
    outer.subgroups.append(inner)
    app = cli(name="myapp", help="Nested CLI", max_width=80)
    app.subgroups.append(outer)
    return app


# --- snapshot tests ---


def test_flat_cli_help(flat_app):
    expected = (
        "Usage: myapp ...  (--json, -j, --help, -h, --hv)\n"
        "Description: My application\n"
        "myapp                 My application\n"
        "└── greet <NAME, str> Greet someone\n"
    )
    assert run_help(flat_app) == expected


def test_single_group_help(single_group_app):
    expected = (
        "Usage: myapp ...  (--json, -j, --help, -h, --hv)\n"
        "Description: My application\n"
        "myapp                  My application\n"
        "└── ops                Operations group\n"
        "    ├── run            Run it\n"
        "    └── build <X, int> Build it\n"
    )
    assert run_help(single_group_app) == expected


def test_option_help(option_app):
    expected = (
        "Usage: myapp ...  (--json, -j, --help, -h, --hv)\n"
        "Description: My CLI\n"
        "myapp                       My CLI\n"
        "└── thing                   Do a thing\n"
        "    └── --verbose, -v: bool Verbose mode\n"
    )
    assert run_help(option_app) == expected


def test_show_types_and_defaults(show_types_defaults_app):
    expected = (
        "Usage: myapp ...  (--json, -j, --help, -h, --hv)\n"
        "Description: My CLI\n"
        "myapp                    My CLI\n"
        "└── proc <NAME, str>     Process\n"
        "    └── --count, -c: int Count (default: 5)\n"
    )
    assert run_help(show_types_defaults_app) == expected


def test_folded_group_help(folded_group_app):
    expected = (
        "Usage: myapp ...  (--json, -j, --help, -h, --hv)\n"
        "Description: My CLI\n"
        "myapp              My CLI\n"
        "└── internal [...] Internal group\n"
    )
    assert run_help(folded_group_app) == expected


def test_chain_help(chain_app):
    expected = (
        "Usage: myapp ...  (--json, -j, --help, -h, --hv)\n"
        "Description: Pipeline CLI\n"
        "myapp                      Pipeline CLI\n"
        "└── pipe <X, int> <Y, str> Pipeline\n"
    )
    assert run_help(chain_app) == expected


def test_nested_root_help(nested_app):
    expected = (
        "Usage: myapp ...  (--json, -j, --help, -h, --hv)\n"
        "Description: Nested CLI\n"
        "myapp            Nested CLI\n"
        "└── outer        Outer group\n"
        "    └── inner    Inner group\n"
        "        └── leaf Leaf cmd\n"
    )
    assert run_help(nested_app) == expected


def test_nested_path_help(nested_app):
    expected = (
        "Usage: myapp outer ...  (--json, -j, --help, -h, --hv)\n"
        "Description: Outer group\n"
        "myapp            Nested CLI\n"
        "└── outer        Outer group\n"
        "    └── inner    Inner group\n"
        "        └── leaf Leaf cmd\n"
    )
    assert run_help(nested_app, ["outer"]) == expected
