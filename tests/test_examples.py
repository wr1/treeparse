import sys
import importlib.util
import os
import pytest

# Helper to import example modules
dir_path = os.path.join(os.path.dirname(__file__), '..', 'examples')

def import_example(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(dir_path, f'{name}.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

basic = import_example('basic')
demo = import_example('demo')
list_demo = import_example('list_demo')
choice_demo = import_example('choice_demo')
group_option_demo = import_example('group_option_demo')
group_arg_demo = import_example('group_arg_demo')
chain_demo = import_example('chain_demo')
theme_demo = import_example('theme_demo')


def test_basic_example(capsys):
    """Test the basic example CLI."""
    sys.argv = ["basic", "hello"]
    basic.main()
    captured = capsys.readouterr()
    assert "Hello, world!" in captured.out


def test_basic_example_group(capsys):
    """Test the basic example with subgroup."""
    sys.argv = ["basic", "example", "hello", "Alice"]
    basic.main()
    captured = capsys.readouterr()
    assert "Hello, Alice!" in captured.out


def test_demo_example_info(capsys):
    """Test the demo example info command."""
    sys.argv = ["demo", "info"]
    demo.main()
    # No output expected, just ensure no error


def test_demo_example_user_add(capsys):
    """Test the demo example user add command."""
    sys.argv = ["demo", "user", "add", "John"]
    demo.main()
    # No output expected


def test_list_demo_example(capsys):
    """Test the list_demo example."""
    sys.argv = ["list_demo", "echo", "hello", "world"]
    list_demo.main()
    # Logging output, but ensure no error


def test_choice_demo_example(capsys):
    """Test the choice_demo example."""
    sys.argv = ["choice_demo", "set-level", "--level", "3"]
    choice_demo.main()
    # No output expected


def test_group_option_demo_example(capsys):
    """Test the group_option_demo example."""
    sys.argv = ["group_option_demo", "user", "greet", "Alice"]
    group_option_demo.main()
    captured = capsys.readouterr()
    assert "Greeting Alice" in captured.out


def test_group_arg_demo_example(capsys):
    """Test the group_arg_demo example."""
    sys.argv = ["group_arg_demo", "user", "123", "add", "Bob"]
    group_arg_demo.main()
    captured = capsys.readouterr()
    assert "Adding user Bob with ID 123" in captured.out


def test_chain_demo_example(capsys):
    """Test the chain_demo example."""
    sys.argv = ["chain_demo", "pipeline", "42", "test"]
    chain_demo.main()
    captured = capsys.readouterr()
    assert "Called step1 with 42" in captured.out
    assert "Called step2 with test" in captured.out


def test_theme_demo_example(capsys):
    """Test the theme_demo example."""
    sys.argv = ["theme_demo", "hello"]
    theme_demo.main()
    captured = capsys.readouterr()
    assert "Hello, world!" in captured.out
