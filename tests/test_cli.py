import pytest
import sys
from io import StringIO
from treeparse import Cli, Group, Command, Argument, Option
from rich.console import Console

def test_cli_build_parser():
    cli = Cli(name="test", help="Test CLI")
    parser = cli.build_parser()
    assert parser.prog == "test"

def test_cli_validation_error(capsys):
    def callback(arg1: int):
        pass
    cmd = Command(name="test", callback=callback, arguments=[Argument(name="arg2", arg_type=int)])
    cli = Cli(name="test", commands=[cmd])
    with pytest.raises(SystemExit):
        cli.run()
    captured = capsys.readouterr()
    assert "name mismatch" in captured.out

def test_cli_help_output(capsys):
    cli = Cli(name="test", help="Test CLI")
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        cli.run()
    captured = capsys.readouterr()
    assert "Usage: test [OPTIONS] COMMAND [ARGS]..." in captured.out

def test_cli_with_command():
    called = [False]
    def callback():
        called[0] = True
    cmd = Command(name="cmd", callback=callback)
    cli = Cli(name="test", commands=[cmd])
    sys.argv = ["test", "cmd"]
    cli.run()
    assert called[0]

def test_show_types(capsys):
    cli = Cli(name="test", show_types=True)
    arg = Argument(name="arg", arg_type=int)
    opt = Option(flags=["--opt"], arg_type=str)
    def callback(arg: int, opt: str):
        pass
    cmd = Command(name="cmd", arguments=[arg], options=[opt], callback=callback)
    cli.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        cli.run()
    captured = capsys.readouterr()
    assert "[ARG,int]" in captured.out
    assert "--opt: str" in captured.out

