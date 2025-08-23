import sys
from pathlib import Path
import pytest
from examples.demo import main, cli


@pytest.fixture
def mock_argv():
    original = sys.argv
    yield
    sys.argv = original


def test_demo_help(mock_argv, capsys):
    sys.argv = ["demo.py", "--help"]
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Usage: demo.py [OPTIONS] COMMAND [ARGS]..." in captured.out


def test_demo_user_manage_help(mock_argv, capsys):
    sys.argv = ["demo.py", "user", "manage", "--help"]
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Manage user settings and permissions." in captured.out


def test_demo_invalid_command(mock_argv, capsys):
    sys.argv = ["demo.py", "invalid"]
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "invalid choice" in captured.out


def test_demo_execute_command(mock_argv):
    sys.argv = ["demo.py", "info"]
    main()  # Should execute without error
