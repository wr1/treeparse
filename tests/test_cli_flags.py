"""Tests for flag=True option support."""

import sys

import pytest
from pydantic import ValidationError

from treeparse import cli, command, option
from treeparse.testing import cli_runner


def make_app(opts, callback):
    cmd = command(name="run", callback=callback, options=opts)
    return cli(name="test", commands=[cmd])


def test_flag_absent_is_false():
    captured = {}

    def callback(verbose: bool):
        captured["verbose"] = verbose

    app = make_app([option(flags=["--verbose"], flag=True)], callback)
    runner = cli_runner(app)
    result = runner.invoke(["run"])
    assert result.exit_code == 0
    assert captured["verbose"] is False


def test_flag_present_is_true():
    captured = {}

    def callback(verbose: bool):
        captured["verbose"] = verbose

    app = make_app([option(flags=["--verbose"], flag=True)], callback)
    runner = cli_runner(app)
    result = runner.invoke(["run", "--verbose"])
    assert result.exit_code == 0
    assert captured["verbose"] is True


def test_flag_short_alias():
    captured = {}

    def callback(verbose: bool):
        captured["verbose"] = verbose

    app = make_app([option(flags=["--verbose", "-v"], flag=True)], callback)
    runner = cli_runner(app)
    result = runner.invoke(["run", "-v"])
    assert result.exit_code == 0
    assert captured["verbose"] is True


def test_multiple_flags():
    captured = {}

    def callback(verbose: bool, dry_run: bool):
        captured["verbose"] = verbose
        captured["dry_run"] = dry_run

    app = make_app(
        [
            option(flags=["--verbose", "-v"], flag=True),
            option(flags=["--dry-run", "-n"], flag=True),
        ],
        callback,
    )
    runner = cli_runner(app)
    result = runner.invoke(["run", "--verbose"])
    assert result.exit_code == 0
    assert captured["verbose"] is True
    assert captured["dry_run"] is False


def test_flag_required_raises():
    with pytest.raises(ValidationError, match="incompatible with required=True"):
        option(flags=["--verbose"], flag=True, required=True)


def test_flag_nargs_raises():
    with pytest.raises(ValidationError, match="incompatible with nargs"):
        option(flags=["--verbose"], flag=True, nargs="+")


def test_flag_no_type_in_help(capsys):
    def callback(verbose: bool):
        pass

    app = make_app([option(flags=["--verbose"], flag=True, help="enable verbose output")], callback)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "--verbose" in captured.out
    # no ": bool" type annotation should appear for flags
    assert ": bool" not in captured.out
