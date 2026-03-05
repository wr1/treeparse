"""Validation error demonstration CLI.

This example deliberately contains common mistakes in CLI definitions
(name mismatch, type mismatch, invalid default vs choices).

Run it to explore the rich red error messages produced by treeparse validation.

Usage examples:
  uv run validation_error_demo bad-name Alice     # → name mismatch error
  uv run validation_error_demo bad-type 42        # → type mismatch error
  uv run validation_error_demo bad-choice         # → invalid default error
"""

from treeparse import cli, command, argument, option


def callback_with_missing_param(name: str, age: int):
    """Callback expects 'age' but it is not defined in the CLI."""
    print(f"Hello {name}, you are {age} years old.")


def callback_type_mismatch(count: int):
    """Callback expects int, but we will define the argument as str."""
    print(f"Count: {count}")


def callback_bad_default(level: int):
    """Callback expects int. Default=5 is NOT in choices=[1,2,3]."""
    print(f"Level set to {level}")


# Intentionally broken commands – validation will catch these at runtime
app = cli(
    name="validation_error_demo",
    help="Showcase of rich validation errors for bad CLI definitions.",
    commands=[
        # 1. Parameter name mismatch
        command(
            name="bad-name",
            help="Missing parameter in CLI definition",
            callback=callback_with_missing_param,
            arguments=[argument(name="name", arg_type=str)],
            # 'age' is missing → will raise ValueError about parameter name mismatch
        ),
        # 2. Type mismatch
        command(
            name="bad-type",
            help="Argument type mismatch",
            callback=callback_type_mismatch,
            arguments=[argument(name="count", arg_type=str)],  # str vs int
            # Will raise "Parameter type mismatch"
        ),
        # 3. Default value not in choices
        command(
            name="bad-choice",
            help="Invalid default against choices",
            callback=callback_bad_default,
            options=[
                option(
                    flags=["--level", "-l"],
                    arg_type=int,
                    choices=[1, 2, 3],
                    default=5,  # invalid default
                    help="Level to set",
                )
            ],
            # Will raise "Default value 5 not in choices [1, 2, 3]"
        ),
    ],
)


def main():
    """Run the demo (will immediately show a validation error)."""
    app.run()


if __name__ == "__main__":
    main()
