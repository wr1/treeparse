"""CLI testing helper/runner for treeparse.

Provides `CliRunner` to make testing CLIs simple and clean (no manual sys.argv hacks).
"""

import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from typing import List, Optional
from .models.cli import cli


class CliResult:
    """Result from invoking a CLI."""

    def __init__(self, exit_code: int = 0, output: str = "", stderr: str = ""):
        self.exit_code = exit_code
        self.output = output.strip()
        self.stderr = stderr.strip()


class CliRunner:
    """Runner for testing treeparse CLIs.

    Example usage:
        runner = CliRunner(app)
        result = runner.invoke(["command", "--flag", "value"])
        assert result.exit_code == 0
        assert "success" in result.output
    """

    def __init__(self, app: cli):
        self.app = app

    def invoke(self, args: Optional[List[str]] = None) -> CliResult:
        """Invoke the CLI with the given arguments and capture output/exit code."""
        if args is None:
            args = []
        original_argv = sys.argv[:]
        stdout = StringIO()
        stderr = StringIO()
        try:
            sys.argv = [self.app.name or "treeparse"] + args
            with redirect_stdout(stdout), redirect_stderr(stderr):
                try:
                    self.app.run()
                    exit_code = 0
                except SystemExit as e:
                    exit_code = e.code if isinstance(e.code, int) else 2
                except Exception as e:
                    # This branch now covered by test_cli_runner_validation_error + callback_exception
                    stderr.write(f"Unexpected error: {e}\n")
                    exit_code = 1
            return CliResult(exit_code, stdout.getvalue(), stderr.getvalue())
        finally:
            sys.argv = original_argv
