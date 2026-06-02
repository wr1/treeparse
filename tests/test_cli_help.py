import os
import sys

import pytest

from treeparse import argument, cli, command, option


def test_cli_help_output(capsys):
    app = cli(name="test", help="Test CLI")
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "Usage: test ...  (--json, -j, --help, -h, --hv)" in captured.out


def test_show_types(capsys):
    app = cli(name="test", show_types=True)
    arg = argument(name="arg", arg_type=int)
    opt = option(flags=["--opt"], arg_type=str)

    def callback(arg: int, opt: str):
        pass

    cmd = command(name="cmd", arguments=[arg], options=[opt], callback=callback)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "<ARG, int>" in captured.out
    assert "--opt: str" in captured.out


def test_show_defaults(capsys):
    app = cli(name="test", show_defaults=True)
    opt = option(flags=["--opt"], arg_type=str, default="default_value")

    def callback(opt: str):
        pass

    cmd = command(name="cmd", options=[opt], callback=callback)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "(default: default_value)" in captured.out


def test_show_defaults_option_home_abbreviated(capsys):
    home_subdir = os.path.join(os.path.expanduser("~"), "myproject", "data")
    app = cli(name="test", show_defaults=True)
    opt = option(flags=["--target"], arg_type=str, default=home_subdir)

    def callback(target: str):
        pass

    cmd = command(name="cmd", options=[opt], callback=callback)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "(default: ~/myproject/data)" in captured.out
    assert os.path.expanduser("~") not in captured.out


def test_show_defaults_argument_home_abbreviated(capsys):
    home_subdir = os.path.join(os.path.expanduser("~"), "myproject")
    app = cli(name="test", show_defaults=True)
    arg = argument(name="path", arg_type=str, nargs="?", default=home_subdir)

    def callback(path: str):
        pass

    cmd = command(name="cmd", arguments=[arg], callback=callback)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "=~/myproject]" in captured.out
    assert os.path.expanduser("~") not in captured.out


def test_show_defaults_non_home_path_unchanged(capsys):
    app = cli(name="test", show_defaults=True)
    opt = option(flags=["--target"], arg_type=str, default="/etc/config")

    def callback(target: str):
        pass

    cmd = command(name="cmd", options=[opt], callback=callback)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "(default: /etc/config)" in captured.out


def test_cli_json_output(capsys):
    app = cli(name="test", help="Test CLI")
    sys.argv = ["test", "--json"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    json_output = captured.out.strip()
    try:
        import json

        data = json.loads(json_output)
    except json.JSONDecodeError:
        pytest.fail("Output is not valid JSON")
    assert data["name"] == "test"
    assert data["help"] == "Test CLI"
    assert data["type"] == "cli"


def test_line_connect(capsys):
    app = cli(name="test", help="Test CLI with line connect", line_connect=True)

    def callback():
        pass

    cmd = command(name="cmd", help="A command with help", callback=callback)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "─" in captured.out  # Check for connector lines
    assert "A command with help" in captured.out


def test_line_connect_option(capsys):
    app = cli(name="test", line_connect=True)

    def callback(opt: str):
        pass

    opt = option(flags=["--opt"], arg_type=str, help="An option with help")
    cmd = command(name="cmd", options=[opt], callback=callback)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "─" in captured.out  # Check for connector in option
    assert "An option with help" in captured.out
