"""Comprehensive tests for the CliRunner testing framework."""

from treeparse import argument, cli, cli_runner, command


def test_cli_runner_success_with_args():
    """Test normal command execution with arguments and output capture."""
    calls = []

    def greet(name: str):
        calls.append(name)
        print(f"Hello {name}!")

    cmd = command(
        name="greet",
        callback=greet,
        arguments=[argument(name="name", arg_type=str)],
    )
    app = cli(name="testcli", commands=[cmd])
    runner = cli_runner(app)

    result = runner.invoke(["greet", "World"])

    assert result.exit_code == 0
    assert "Hello World!" in result.output
    assert calls == ["World"]


def test_cli_runner_help_output():
    """Test that --help produces the rich tree help and exits 0."""
    app = cli(name="testcli", help="Test CLI for runner")
    runner = cli_runner(app)

    result = runner.invoke(["--help"])

    assert result.exit_code == 0
    assert "Usage: testcli" in result.output
    assert "Test CLI for runner" in result.output


def test_cli_runner_json_output():
    """Test --json flag returns valid JSON structure."""
    app = cli(name="testcli", help="JSON test")
    runner = cli_runner(app)

    result = runner.invoke(["--json"])

    assert result.exit_code == 0
    assert '"name": "testcli"' in result.output
    assert '"type": "cli"' in result.output


def test_cli_runner_invalid_choice():
    """Test invalid subcommand shows rich error and non-zero exit."""

    def dummy():
        pass

    cmd = command(name="hello", callback=dummy)
    app = cli(name="testcli", commands=[cmd])
    runner = cli_runner(app)

    result = runner.invoke(["invalid-cmd"])

    assert result.exit_code != 0
    assert "invalid choice" in result.output.lower()


def test_cli_runner_callback_exception():
    """Test that exceptions in callbacks are captured in stderr with exit 1."""

    def crash():
        raise RuntimeError("Boom from callback")

    cmd = command(name="crash", callback=crash)
    app = cli(name="testcli", commands=[cmd])
    runner = cli_runner(app)

    result = runner.invoke(["crash"])

    assert result.exit_code == 1
    assert "Boom from callback" in result.stderr


def test_cli_runner_validation_error():
    """Test that CLI definition validation errors are captured (name/type mismatch etc.)."""

    def bad(name: str, missing: int):
        pass

    cmd = command(
        name="bad",
        callback=bad,
        arguments=[argument(name="name", arg_type=str)],
    )
    app = cli(name="testcli", commands=[cmd])
    runner = cli_runner(app)

    result = runner.invoke(["bad", "Alice"])

    assert result.exit_code != 0
    assert "parameter name mismatch" in result.output.lower()
    assert "missing" in result.output.lower()


def test_cli_runner_no_args_shows_help():
    """Test root call with no args falls back to help (as in real CLI)."""
    app = cli(name="testcli", help="Root help demo")
    runner = cli_runner(app)

    result = runner.invoke([])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "Root help demo" in result.output


def test_cli_runner_chain_execution():
    """Test chain commands work correctly with runner."""
    calls = []

    def step1(x: int):
        calls.append(("step1", x))

    def step2(y: str):
        calls.append(("step2", y))

    cmd1 = command(name="step1", callback=step1, arguments=[argument(name="x", arg_type=int)])
    cmd2 = command(name="step2", callback=step2, arguments=[argument(name="y", arg_type=str)])
    from treeparse import chain

    chain_cmd = chain(name="pipe", chained_commands=[cmd1, cmd2])
    app = cli(name="testcli", commands=[chain_cmd])
    runner = cli_runner(app)

    result = runner.invoke(["pipe", "42", "hello"])

    assert result.exit_code == 0
    assert calls == [("step1", 42), ("step2", "hello")]
