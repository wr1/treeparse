import pytest
import sys
from treeparse import cli, command, argument, option


def test_cli_build_parser():
    app = cli(name="test", help="Test CLI")
    parser = app.build_parser()
    assert parser.prog == "test"


def test_cli_validation_error(capsys):
    def callback(arg1: int):
        pass

    cmd = command(
        name="test", callback=callback, arguments=[argument(name="arg2", arg_type=int)]
    )
    app = cli(name="test", commands=[cmd])
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "name mismatch" in captured.out


def test_cli_help_output(capsys):
    app = cli(name="test", help="Test CLI")
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    captured = capsys.readouterr()
    assert "Usage: test [OPTIONS] COMMAND [ARGS]..." in captured.out


def test_cli_with_command():
    called = [False]

    def callback():
        called[0] = True

    cmd = command(name="cmd", callback=callback)
    app = cli(name="test", commands=[cmd])
    sys.argv = ["test", "cmd"]
    app.run()
    assert called[0]


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
    assert "[ARG,int]" in captured.out
    assert "--opt: str" in captured.out
