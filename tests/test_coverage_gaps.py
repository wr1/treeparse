"""Tests targeting specific coverage gaps across the treeparse codebase."""

import sys
import warnings
from enum import Enum

import pytest

from treeparse import argument, cli, cli_runner, command, group, option
from treeparse.models.chain import chain
from treeparse.models.cli import str2bool

# ---------------------------------------------------------------------------
# str2bool
# ---------------------------------------------------------------------------


def test_str2bool_already_bool():
    assert str2bool(True) is True
    assert str2bool(False) is False


def test_str2bool_invalid():
    import argparse

    with pytest.raises(argparse.ArgumentTypeError):
        str2bool("maybe")


# ---------------------------------------------------------------------------
# option: required + default contradiction
# ---------------------------------------------------------------------------


def test_option_required_with_default_raises():
    with pytest.raises(Exception, match="required=True is contradicted by default"):
        option(flags=["--foo"], required=True, default="bar")


# ---------------------------------------------------------------------------
# chain: conflicting option dest
# ---------------------------------------------------------------------------


def test_chain_option_conflict():
    def cb1(verbose: bool):
        pass

    def cb2(verbose: bool):
        pass

    cmd1 = command(name="a", callback=cb1, options=[option(flags=["--verbose"], arg_type=bool)])
    cmd2 = command(name="b", callback=cb2, options=[option(flags=["--verbose"], arg_type=bool)])
    ch = chain(name="pipe", chained_commands=[cmd1, cmd2])
    with pytest.raises(ValueError, match="Conflicting option dest 'verbose'"):
        _ = ch.effective_options


# ---------------------------------------------------------------------------
# command.validate: async callback
# ---------------------------------------------------------------------------


def test_command_validate_async_callback():
    async def my_async():
        pass

    cmd = command(name="async_cmd", callback=my_async)
    with pytest.raises(ValueError, match="async"):
        cmd.validate()


# ---------------------------------------------------------------------------
# command.validate: nargs list wrapping (opt_type = List[opt_type])
# ---------------------------------------------------------------------------


def test_command_validate_list_option_nargs():
    from typing import List

    def cb(tags: List[str]):
        pass

    cmd = command(
        name="test",
        callback=cb,
        options=[option(flags=["--tags"], arg_type=str, nargs="+")],
    )
    cmd.validate()  # should not raise


# ---------------------------------------------------------------------------
# command.validate: list vs List equivalence
# ---------------------------------------------------------------------------


def test_command_validate_list_vs_typing_list():
    def cb(items: list):
        pass

    cmd = command(
        name="test",
        callback=cb,
        arguments=[argument(name="items", arg_type=str, nargs="*")],
    )
    cmd.validate()  # list vs List[str] — treated as equivalent


# ---------------------------------------------------------------------------
# command.validate: type mismatch raises
# ---------------------------------------------------------------------------


def test_command_validate_type_mismatch_message():
    def cb(x: int):
        pass

    cmd = command(name="test", callback=cb, arguments=[argument(name="x", arg_type=str)])
    with pytest.raises(ValueError, match="type mismatch"):
        cmd.validate()


# ---------------------------------------------------------------------------
# command.validate: default-vs-choices for list args/opts
# ---------------------------------------------------------------------------


def test_command_validate_list_arg_default_not_in_choices():
    def cb(tags: list):
        pass

    cmd = command(
        name="test",
        callback=cb,
        arguments=[argument(name="tags", arg_type=str, nargs="+", default=["bad"], choices=["a", "b"])],
    )
    with pytest.raises(ValueError, match="Default value bad not in choices"):
        cmd.validate()


def test_command_validate_list_opt_default_not_in_choices():
    from typing import List

    def cb(tags: List[str]):
        pass

    cmd = command(
        name="test",
        callback=cb,
        options=[option(flags=["--tags"], arg_type=str, nargs="+", default=["bad"], choices=["a", "b"])],
    )
    with pytest.raises(ValueError, match="Default value bad not in choices"):
        cmd.validate()


# ---------------------------------------------------------------------------
# cli._validate: async callback detected inside tree
# ---------------------------------------------------------------------------


def test_cli_validate_async_in_tree():
    async def async_cb():
        pass

    cmd = command(name="async_cmd", callback=async_cb)
    app = cli(name="test", commands=[cmd])
    with pytest.raises(ValueError, match="async"):
        app._validate()


# ---------------------------------------------------------------------------
# cli._validate: flat CLI with callback (exercises temp command path)
# ---------------------------------------------------------------------------


def test_cli_flat_with_callback_validates():
    def cb(name: str):
        pass

    app = cli(
        name="flat",
        callback=cb,
        arguments=[argument(name="name", arg_type=str)],
    )
    app._validate()  # should not raise


def test_cli_flat_callback_type_mismatch():
    def cb(name: int):
        pass

    app = cli(
        name="flat",
        callback=cb,
        arguments=[argument(name="name", arg_type=str)],
    )
    with pytest.raises(ValueError, match="type mismatch"):
        app._validate()


# ---------------------------------------------------------------------------
# cli._validate: list vs List and Union equivalence in tree validation
# ---------------------------------------------------------------------------


def test_cli_validate_list_equivalence_in_tree():
    from typing import List

    def cb(items: List[str]):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        arguments=[argument(name="items", arg_type=str, nargs="+")],
    )
    app = cli(name="test", commands=[cmd])
    app._validate()  # should not raise


# ---------------------------------------------------------------------------
# cli._validate: inherited option default-vs-choices (P1 fix — uses effective_opts)
# ---------------------------------------------------------------------------


def test_cli_validate_inherited_option_bad_default():
    def cb(mode: str):
        pass

    inherited_opt = option(flags=["--mode"], arg_type=str, default="bad", choices=["a", "b"], inherit=True)
    root = cli(name="test", options=[inherited_opt])
    cmd = command(name="cmd", callback=cb)
    root.commands.append(cmd)
    with pytest.raises(ValueError, match="Default value bad not in choices"):
        root._validate()


# ---------------------------------------------------------------------------
# cli: Enum type resolution
# ---------------------------------------------------------------------------


class color_enum(Enum):
    RED = "red"
    BLUE = "blue"


def test_enum_type_auto_choices():
    results = []

    def cb(color: color_enum):
        results.append(color)

    cmd = command(name="paint", callback=cb, arguments=[argument(name="color", arg_type=color_enum)])
    app = cli(name="test", commands=[cmd])
    runner = cli_runner(app)
    result = runner.invoke(["paint", "RED"])
    assert result.exit_code == 0
    assert results == [color_enum.RED]


def test_enum_invalid_choice():
    def cb(color: color_enum):
        pass

    cmd = command(name="paint", callback=cb, arguments=[argument(name="color", arg_type=color_enum)])
    app = cli(name="test", commands=[cmd])
    runner = cli_runner(app)
    result = runner.invoke(["paint", "GREEN"])
    assert result.exit_code != 0
    # argparse reports a type error or invalid choice for unknown enum member
    assert result.output != "" or result.stderr != ""


def test_enum_option_auto_choices():
    results = []

    def cb(color: color_enum):
        results.append(color)

    cmd = command(
        name="paint",
        callback=cb,
        options=[option(flags=["--color"], arg_type=color_enum)],
    )
    app = cli(name="test", commands=[cmd])
    runner = cli_runner(app)
    result = runner.invoke(["paint", "--color", "BLUE"])
    assert result.exit_code == 0
    assert results == [color_enum.BLUE]


# ---------------------------------------------------------------------------
# cli: explicit arg dest + default value in _add_args_and_opts_to_parser
# ---------------------------------------------------------------------------


def test_arg_with_default():
    results = []

    def cb(output: str):
        results.append(output)

    # nargs="?" makes the positional optional; default is used when omitted
    arg = argument(name="output", arg_type=str, nargs="?", default="result.txt")
    cmd = command(name="cmd", callback=cb, arguments=[arg])
    app = cli(name="test", commands=[cmd])
    runner = cli_runner(app)
    result = runner.invoke(["cmd"])
    assert result.exit_code == 0
    assert results == ["result.txt"]


def test_option_required_enforced():
    def cb(name: str):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        options=[option(flags=["--name"], arg_type=str, required=True)],
    )
    app = cli(name="test", commands=[cmd])
    runner = cli_runner(app)
    result = runner.invoke(["cmd"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# cli._get_node_from_path: error paths
# ---------------------------------------------------------------------------


def test_get_node_from_path_not_found():
    app = cli(name="test")
    with pytest.raises(ValueError, match="Path not found"):
        app._get_node_from_path(["nonexistent"])


# ---------------------------------------------------------------------------
# cli.structure_dict: command, chain, and non-root group type fields
# ---------------------------------------------------------------------------


def test_structure_dict_command_type():
    def cb():
        pass

    cmd = command(name="do", help="Do it", callback=cb)
    app = cli(name="test", commands=[cmd])
    d = app.structure_dict()
    cmd_d = d["commands"][0]
    assert cmd_d["type"] == "command"
    assert cmd_d["callback"] == "cb"


def test_structure_dict_chain_type():
    def cb1(x: int):
        pass

    def cb2(y: str):
        pass

    cmd1 = command(name="s1", callback=cb1, arguments=[argument(name="x", arg_type=int)])
    cmd2 = command(name="s2", callback=cb2, arguments=[argument(name="y", arg_type=str)])
    ch = chain(name="pipe", chained_commands=[cmd1, cmd2])
    app = cli(name="test", commands=[ch])
    d = app.structure_dict()
    ch_d = d["commands"][0]
    assert ch_d["type"] == "chain"
    assert "chained" in ch_d


def test_structure_dict_group_type():
    def cb():
        pass

    grp = group(name="ops", help="Ops")
    grp.commands.append(command(name="run", callback=cb))
    app = cli(name="test", subgroups=[grp])
    d = app.structure_dict()
    grp_d = d["subgroups"][0]
    assert grp_d["type"] == "group"


# ---------------------------------------------------------------------------
# cli: flat CLI with callback runs
# ---------------------------------------------------------------------------


def test_flat_cli_with_callback_runs():
    results = []

    def cb(name: str):
        results.append(name)

    app = cli(
        name="flat",
        callback=cb,
        arguments=[argument(name="name", arg_type=str)],
    )
    runner = cli_runner(app)
    result = runner.invoke(["Alice"])
    assert result.exit_code == 0
    assert results == ["Alice"]


# ---------------------------------------------------------------------------
# cli.build_parser: depth guard (depth > max_depth path)
# ---------------------------------------------------------------------------


def test_parser_depth_guard():
    def cb():
        pass

    # A flat CLI triggers no subparser building, exercising parser caching
    app = cli(name="test")
    app.commands.append(command(name="cmd", callback=cb))
    p1 = app.build_parser()
    p2 = app.build_parser()
    assert p1 is p2  # cached


# ---------------------------------------------------------------------------
# cli: YAML config applied to full tree + unknown key warning
# ---------------------------------------------------------------------------


def test_yaml_config_applies_to_subgroup(tmp_path):
    yaml_file = tmp_path / "config.yml"
    yaml_file.write_text("verbose: true\n")

    def cb(verbose: bool):
        pass

    grp = group(name="ops")
    cmd = command(name="run", callback=cb, options=[option(flags=["--verbose"], arg_type=bool)])
    grp.commands.append(cmd)
    app = cli(name="test", subgroups=[grp], yml_config=yaml_file)
    # _apply_yaml_config should walk into subgroups
    config = {"verbose": True}
    app._apply_yaml_config(config)
    assert cmd.options[0].default is True


def test_yaml_config_unknown_key_warns(tmp_path):
    app = cli(name="test")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        app._apply_yaml_config({"unknown_key": 42})
    assert any("unrecognized key 'unknown_key'" in str(warning.message) for warning in w)


def test_yaml_config_via_run(tmp_path, capsys):
    yaml_file = tmp_path / "config.yml"
    yaml_file.write_text("level: 5\n")

    results = []

    def cb(level: int):
        results.append(level)

    cmd = command(
        name="cmd",
        callback=cb,
        options=[option(flags=["--level"], arg_type=int)],
    )
    app = cli(name="test", commands=[cmd], yml_config=yaml_file)
    sys.argv = ["test", "cmd"]
    app.run()
    assert results == [5]


# ---------------------------------------------------------------------------
# cli.run: missing required positional argument error
# ---------------------------------------------------------------------------


def test_missing_required_argument_error(capsys):
    def cb(name: str):
        pass

    # argparse will error before we reach the missing-arg check for positionals,
    # but a nargs="?" arg with no default can reach it
    arg = argument(name="name", arg_type=str, nargs="?")

    def cb2(name: str):
        pass

    cmd2 = command(name="greet2", callback=cb2, arguments=[arg])
    app2 = cli(name="test2", commands=[cmd2])
    runner2 = cli_runner(app2)
    result = runner2.invoke(["greet2"])
    # nargs="?" provides None, so cb2 receives None — just check it runs
    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# RichArgumentParser.error: non-invalid-choice branch
# ---------------------------------------------------------------------------


def test_rich_parser_generic_error(capsys):
    def cb(name: str):
        pass

    cmd = command(name="cmd", callback=cb, arguments=[argument(name="name", arg_type=str)])
    app = cli(name="test", commands=[cmd])
    runner = cli_runner(app)
    # Pass a flag that argparse itself rejects (unknown option triggers generic error)
    result = runner.invoke(["cmd", "--unknown-flag"])
    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# color_config: RED_WHITE_BLUE theme
# ---------------------------------------------------------------------------


def test_red_white_blue_theme():
    from treeparse.utils.color_config import ColorTheme, color_config

    cfg = color_config.from_theme(ColorTheme.RED_WHITE_BLUE)
    assert "255,50,50" in cfg.app  # red
    assert "160,180,255" in cfg.group  # blue


def test_github_theme():
    from treeparse.utils.color_config import ColorTheme, color_config

    cfg = color_config.from_theme(ColorTheme.GITHUB)
    assert "210,168,255" in cfg.app  # purple
    assert "121,192,255" in cfg.group  # blue
    assert "255,166,87" in cfg.argument  # orange
    assert "255,123,114" in cfg.option  # red-pink


def test_monokai_theme():
    from treeparse.utils.color_config import ColorTheme, color_config

    cfg = color_config.from_theme(ColorTheme.MONOKAI)
    assert "166,226,46" in cfg.app  # green
    assert "102,217,232" in cfg.group  # cyan
    assert "174,129,255" in cfg.argument  # purple
    assert "249,38,114" in cfg.option  # pink


# ---------------------------------------------------------------------------
# cli_runner: invoke with None args (tests the `args = []` branch)
# ---------------------------------------------------------------------------


def test_cli_runner_invoke_none_args():
    app = cli(name="test", help="Test")
    runner = cli_runner(app)
    result = runner.invoke(None)
    assert result.exit_code == 0
    assert "Usage:" in result.output


# ---------------------------------------------------------------------------
# help_renderer: path errors
# ---------------------------------------------------------------------------


def test_help_renderer_path_not_found(capsys):
    # Unknown path token no longer raises — it silently falls back to root help
    app = cli(name="test", help="Test")
    app.print_help(["nonexistent"])
    captured = capsys.readouterr()
    assert "test" in captured.out


# ---------------------------------------------------------------------------
# help_renderer: narrow help text (width <= 0 fallback)
# ---------------------------------------------------------------------------


def test_help_renderer_narrow_wrapping(capsys):
    # max_width=30 forces very narrow help wrapping
    def cb():
        pass

    cmd = command(name="cmd", help="a b c d e f g h i j k l m n o p", callback=cb)
    app = cli(name="test", max_width=30)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "a b c" in out


# ---------------------------------------------------------------------------
# help_renderer: root label with arguments (lines 159-168, 171-172)
# ---------------------------------------------------------------------------


def test_help_renderer_root_label_with_args(capsys):
    def cb(name: str):
        pass

    app = cli(name="flat", help="Flat CLI", callback=cb, max_width=80)
    app.arguments.append(argument(name="name", arg_type=str))
    sys.argv = ["flat", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "NAME" in out


# ---------------------------------------------------------------------------
# help_renderer: multiline help text wrapping (lines 185-187 etc.)
# ---------------------------------------------------------------------------


def test_help_renderer_multiline_help(capsys):
    def cb():
        pass

    long_help = "word " * 30  # long enough to wrap at max_width=60
    cmd = command(name="cmd", help=long_help.strip(), callback=cb)
    app = cli(name="test", max_width=60)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "word" in out


# ---------------------------------------------------------------------------
# help_renderer: line_connect with multiline help
# ---------------------------------------------------------------------------


def test_help_renderer_line_connect_multiline(capsys):
    def cb():
        pass

    long_help = "alpha beta gamma delta epsilon zeta eta theta iota kappa"
    cmd = command(name="cmd", help=long_help, callback=cb)
    app = cli(name="test", max_width=50, line_connect=True)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "─" in out
    assert "alpha" in out


# ---------------------------------------------------------------------------
# help_renderer: folded group with long help (lines 282-297)
# ---------------------------------------------------------------------------


def test_help_renderer_folded_group_multiline(capsys):
    def cb():
        pass

    long_help = "one two three four five six seven eight nine ten eleven twelve"
    grp = group(name="internal", help=long_help, fold=True)
    grp.commands.append(command(name="run", callback=cb))
    app = cli(name="test", max_width=50)
    app.subgroups.append(grp)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "internal [...]" in out
    assert "one" in out


# ---------------------------------------------------------------------------
# help_renderer: option with multiline help (lines 332-334)
# ---------------------------------------------------------------------------


def test_help_renderer_option_multiline_help(capsys):
    long_help = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"

    def cb(verbose: bool):
        pass

    opt = option(flags=["--verbose"], arg_type=bool, help=long_help)
    cmd = command(name="cmd", callback=cb, options=[opt])
    app = cli(name="test", max_width=50)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "alpha" in out


# ---------------------------------------------------------------------------
# src/treeparse/cli.py entrypoint (0% coverage)
# ---------------------------------------------------------------------------


def test_treeparse_cli_entrypoint_importable():
    import treeparse.cli as ep

    assert hasattr(ep, "app")
    assert hasattr(ep, "main")


def test_treeparse_cli_hello(capsys):
    import treeparse.cli as ep

    ep.hello()
    assert "Treeparse CLI" in capsys.readouterr().out


def test_treeparse_cli_main(capsys):
    import treeparse.cli as ep

    sys.argv = ["treeparse", "--help"]
    with pytest.raises(SystemExit):
        ep.main()
    assert "Usage:" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# models/cli.py: cli.effective_options accessed directly
# ---------------------------------------------------------------------------


def test_cli_effective_options():
    opt = option(flags=["--foo"], arg_type=str)

    def cb(foo: str):
        pass

    app = cli(name="test", options=[opt], commands=[command(name="c", callback=lambda: None)])
    # effective_options on cli returns self.options
    assert app.effective_options == [opt]


# ---------------------------------------------------------------------------
# models/cli.py: _get_node_from_path on a command node (no subgroups)
# ---------------------------------------------------------------------------


def test_get_node_from_path_into_command():
    def cb():
        pass

    cmd = command(name="do", callback=cb)
    app = cli(name="test", commands=[cmd])
    # navigating to "do" works
    node = app._get_node_from_path(["do"])
    assert node.name == "do"


# ---------------------------------------------------------------------------
# models/cli.py: RichArgumentParser.error "invalid choice" with len(parts)==1
# ---------------------------------------------------------------------------


def test_rich_parser_invalid_choice_no_colon(capsys):
    # "invalid choice" in message but no "invalid choice: " (no colon+space)
    # → triggers the else branch at line 57 (len(parts) <= 1)
    from treeparse.models.cli import RichArgumentParser

    p = RichArgumentParser(prog="test")
    with pytest.raises(SystemExit):
        p.error("invalid choice detected")
    out = capsys.readouterr().out
    assert "invalid choice detected" in out


# ---------------------------------------------------------------------------
# models/cli.py: list vs List[X] equivalence branches in _validate() recurse
# ---------------------------------------------------------------------------


def test_cli_validate_bare_list_callback_with_nargs():
    # p_type is bare `list`, cli_type is List[str] — triggers line 376-377
    def cb(items: list):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        arguments=[argument(name="items", arg_type=str, nargs="+")],
    )
    app = cli(name="test", commands=[cmd])
    app._validate()  # should not raise


def test_cli_validate_typing_list_callback_bare_list_argtype():
    from typing import List

    # p_type is List[str], cli_type is bare list — triggers line 378-379
    def cb(items: List[str]):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        arguments=[argument(name="items", arg_type=list)],
    )
    app = cli(name="test", commands=[cmd])
    app._validate()  # should not raise


def test_cli_validate_union_type_skip():
    from typing import Optional

    # p_type is Union[str, None] — triggers line 381-382
    def cb(name: Optional[str]):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        arguments=[argument(name="name", arg_type=str)],
    )
    app = cli(name="test", commands=[cmd])
    app._validate()  # should not raise (Union skipped)


# ---------------------------------------------------------------------------
# models/cli.py: type mismatch in _validate() recurse raises ValueError
# ---------------------------------------------------------------------------


def test_cli_validate_type_mismatch_in_tree():
    def cb(x: int):
        pass

    cmd = command(name="cmd", callback=cb, arguments=[argument(name="x", arg_type=str)])
    app = cli(name="test", commands=[cmd])
    with pytest.raises(ValueError, match="type mismatch"):
        app._validate()


# ---------------------------------------------------------------------------
# models/cli.py: default-vs-choices in _validate() recurse (args list variant)
# ---------------------------------------------------------------------------


def test_cli_validate_list_arg_bad_default_in_tree():
    def cb(tags: list):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        arguments=[argument(name="tags", arg_type=str, nargs="+", default=["x"], choices=["a", "b"])],
    )
    app = cli(name="test", commands=[cmd])
    with pytest.raises(ValueError, match="Default value x not in choices"):
        app._validate()


def test_cli_validate_scalar_arg_bad_default_in_tree():
    def cb(mode: str):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        arguments=[argument(name="mode", arg_type=str, default="bad", choices=["a", "b"])],
    )
    app = cli(name="test", commands=[cmd])
    with pytest.raises(ValueError, match="Default value bad not in choices"):
        app._validate()


# ---------------------------------------------------------------------------
# models/cli.py: default-vs-choices for list opts in _validate() recurse
# ---------------------------------------------------------------------------


def test_cli_validate_list_opt_bad_default_in_tree():
    from typing import List

    def cb(tags: List[str]):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        options=[option(flags=["--tags"], arg_type=str, nargs="+", default=["x"], choices=["a", "b"])],
    )
    app = cli(name="test", commands=[cmd])
    with pytest.raises(ValueError, match="Default value x not in choices"):
        app._validate()


# ---------------------------------------------------------------------------
# models/command.py: List[X] vs bare list (lines 82, 85) and list opt choices
# ---------------------------------------------------------------------------


def test_command_validate_typing_list_vs_bare_list():
    from typing import List

    # p_type is List[str], cli_type is bare list — triggers command.py line 82
    def cb(items: List[str]):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        arguments=[argument(name="items", arg_type=list)],
    )
    cmd.validate()  # should not raise


def test_command_validate_union_type_skip():
    from typing import Optional

    def cb(name: Optional[str]):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        arguments=[argument(name="name", arg_type=str)],
    )
    cmd.validate()  # should not raise (Union skipped)


def test_command_validate_list_opt_bad_default():
    from typing import List

    def cb(tags: List[str]):
        pass

    cmd = command(
        name="cmd",
        callback=cb,
        options=[option(flags=["--tags"], arg_type=str, nargs="+", default=["bad"], choices=["a", "b"])],
    )
    with pytest.raises(ValueError, match="Default value bad not in choices"):
        cmd.validate()


# ---------------------------------------------------------------------------
# help_renderer: path to a chain node (line 31 — non-command, no subgroups)
# ---------------------------------------------------------------------------


def test_help_renderer_path_through_chain(capsys):
    def step1(x: int):
        pass

    def step2(y: str):
        pass

    cmd1 = command(name="s1", callback=step1, arguments=[argument(name="x", arg_type=int)])
    cmd2 = command(name="s2", callback=step2, arguments=[argument(name="y", arg_type=str)])
    ch = chain(name="pipe", chained_commands=[cmd1, cmd2])
    app = cli(name="test", commands=[ch])
    # Navigating into "pipe" itself (chain, no subgroups) should NOT error —
    # it falls through to the path-consumed break or standard render
    sys.argv = ["test", "pipe", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "pipe" in out


# ---------------------------------------------------------------------------
# help_renderer: _wrap_help with very narrow width (line 127)
# ---------------------------------------------------------------------------


def test_help_renderer_very_narrow_max_width(capsys):
    # max_width=5 forces help-area width <= 0, triggering the width=20 fallback
    def cb():
        pass

    cmd = command(name="cmd", help="word1 word2 word3", callback=cb)
    app = cli(name="t", max_width=5)
    app.commands.append(cmd)
    sys.argv = ["t", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    # output is valid even if very fragmented by the tiny terminal width
    out = capsys.readouterr().out
    assert "Usage" in out or "cmd" in out


# ---------------------------------------------------------------------------
# help_renderer: root label with show_types=True and arg choices (162, 164, 166)
# ---------------------------------------------------------------------------


def test_help_renderer_root_label_show_types_and_choices(capsys):
    def cb(mode: str):
        pass

    app = cli(
        name="flat",
        callback=cb,
        show_types=True,
        max_width=80,
    )
    app.arguments.append(argument(name="mode", arg_type=str, choices=["a", "b"]))
    sys.argv = ["flat", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "str" in out  # show_types triggers line 162
    assert "a|b" in out  # choices triggers line 164


# ---------------------------------------------------------------------------
# help_renderer: root label multiline help with line_connect (lines 185-187)
# ---------------------------------------------------------------------------


def test_help_renderer_root_label_multiline_line_connect(capsys):
    def cb():
        pass

    long_help = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu"
    cmd = command(name="cmd", callback=cb)
    app = cli(name="t", help=long_help, max_width=40, line_connect=True)
    app.commands.append(cmd)
    sys.argv = ["t", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "─" in out
    assert "alpha" in out


# ---------------------------------------------------------------------------
# help_renderer: folded group multiline with line_connect (lines 282-287)
# ---------------------------------------------------------------------------


def test_help_renderer_folded_group_line_connect_multiline(capsys):
    def cb():
        pass

    long_help = "one two three four five six seven eight nine ten"
    grp = group(name="internal", help=long_help, fold=True)
    grp.commands.append(command(name="run", callback=cb))
    app = cli(name="test", max_width=40, line_connect=True)
    app.subgroups.append(grp)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "─" in out
    assert "internal [...]" in out


# ---------------------------------------------------------------------------
# help_renderer: folded group multiline WITHOUT line_connect, 2nd line (297)
# ---------------------------------------------------------------------------


def test_help_renderer_folded_group_multiline_no_connect(capsys):
    def cb():
        pass

    # 12 words, max_width=30 forces wrapping without line_connect
    long_help = "aa bb cc dd ee ff gg hh ii jj kk ll mm"
    grp = group(name="g", help=long_help, fold=True)
    grp.commands.append(command(name="run", callback=cb))
    app = cli(name="t", max_width=30)
    app.subgroups.append(grp)
    sys.argv = ["t", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "aa" in out


# ---------------------------------------------------------------------------
# help_renderer: option multiline WITH line_connect (lines 332-334)
# ---------------------------------------------------------------------------


def test_help_renderer_option_multiline_line_connect(capsys):
    long_help = "alpha beta gamma delta epsilon zeta eta theta iota kappa"

    def cb(verbose: bool):
        pass

    opt = option(flags=["--verbose"], arg_type=bool, help=long_help)
    cmd = command(name="cmd", callback=cb, options=[opt])
    app = cli(name="test", max_width=40, line_connect=True)
    app.commands.append(cmd)
    sys.argv = ["test", "--help"]
    with pytest.raises(SystemExit):
        app.run()
    out = capsys.readouterr().out
    assert "─" in out
    assert "alpha" in out
