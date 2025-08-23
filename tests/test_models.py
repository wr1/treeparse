import pytest
from treeparse.models import argument, option, command, group


def test_argument_model():
    arg = argument(name="test", arg_type=int, help="Test arg")
    assert arg.name == "test"
    assert arg.arg_type == int


def test_option_model():
    opt = option(flags=["--test", "-t"], arg_type=str, help="Test option")
    assert opt.flags == ["--test", "-t"]
    assert opt.arg_type == str


def test_command_validation_success():
    def callback(arg1: int, opt1: str):
        pass

    cmd = command(
        name="test",
        callback=callback,
        arguments=[argument(name="arg1", arg_type=int)],
        options=[option(flags=["--opt1"], arg_type=str)],
    )
    cmd.validate()  # Should not raise


def test_command_validation_name_mismatch():
    def callback(arg1: int, opt2: str):
        pass

    cmd = command(
        name="test",
        callback=callback,
        arguments=[argument(name="arg1", arg_type=int)],
        options=[option(flags=["--opt1"], arg_type=str)],
    )
    with pytest.raises(ValueError) as exc:
        cmd.validate()
    assert "name mismatch" in str(exc.value)


def test_command_validation_type_mismatch():
    def callback(arg1: str):
        pass

    cmd = command(
        name="test", callback=callback, arguments=[argument(name="arg1", arg_type=int)]
    )
    with pytest.raises(ValueError) as exc:
        cmd.validate()
    assert "type mismatch" in str(exc.value)


def test_group_model():
    grp = group(name="test", subgroups=[], commands=[])
    assert grp.name == "test"
