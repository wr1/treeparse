"""Demo of the MONOKAI color theme.

Run:
    python examples/monokai_theme_demo.py --help
    python examples/monokai_theme_demo.py build --help
    python examples/monokai_theme_demo.py run --help
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "src"))
from treeparse import argument, cli, command, group, option

# --- callbacks ---


def build_compile(target: str, release: bool, jobs: int):
    print(f"Compiling target={target!r} release={release} jobs={jobs}")


def build_clean(all: bool):
    print(f"Cleaning build artifacts all={all}")


def build_check(fix: bool):
    print(f"Checking code fix={fix}")


def run_exec(binary: str, args: str):
    print(f"Running {binary!r} with args={args!r}")


def run_test(filter: str, no_capture: bool):
    print(f"Testing filter={filter!r} no_capture={no_capture}")


def run_bench(filter: str):
    print(f"Benchmarking filter={filter!r}")


def fmt_check(check: bool):
    print(f"Formatting check={check}")


def doc_open(open: bool):
    print(f"Docs open={open}")


# --- structure ---

build = group(name="build", help="Compile and verify the project.")
build.commands.append(
    command(
        name="compile",
        help="Compile the project.",
        callback=build_compile,
        arguments=[argument(name="target", arg_type=str, help="Build target name")],
        options=[
            option(flags=["--release"], arg_type=bool, default=False, help="Build with optimizations"),
            option(flags=["--jobs", "-j"], arg_type=int, default=4, help="Number of parallel jobs"),
        ],
    )
)
build.commands.append(
    command(
        name="clean",
        help="Remove build artifacts.",
        callback=build_clean,
        options=[option(flags=["--all"], arg_type=bool, default=False, help="Remove all generated files")],
    )
)
build.commands.append(
    command(
        name="check",
        help="Analyze code without producing output.",
        callback=build_check,
        options=[option(flags=["--fix"], arg_type=bool, default=False, help="Auto-fix lint warnings")],
    )
)

run = group(name="run", help="Execute binaries and tests.")
run.commands.append(
    command(
        name="exec",
        help="Run a compiled binary.",
        callback=run_exec,
        arguments=[argument(name="binary", arg_type=str, help="Binary to execute")],
        options=[option(flags=["--args", "-a"], arg_type=str, default="", help="Arguments to pass through")],
    )
)
run.commands.append(
    command(
        name="test",
        help="Run the test suite.",
        callback=run_test,
        options=[
            option(flags=["--filter", "-f"], arg_type=str, default="", help="Only run tests matching filter"),
            option(flags=["--no-capture"], arg_type=bool, default=False, help="Show test output inline"),
        ],
    )
)
run.commands.append(
    command(
        name="bench",
        help="Run benchmarks.",
        callback=run_bench,
        options=[option(flags=["--filter", "-f"], arg_type=str, default="", help="Only run benches matching filter")],
    )
)

extras = group(name="tools", help="Code quality and documentation tools.")
extras.commands.append(
    command(
        name="fmt",
        help="Format source code.",
        callback=fmt_check,
        options=[
            option(flags=["--check"], arg_type=bool, default=False, help="Check formatting without writing changes")
        ],
    )
)
extras.commands.append(
    command(
        name="doc",
        help="Generate and view documentation.",
        callback=doc_open,
        options=[option(flags=["--open"], arg_type=bool, default=False, help="Open docs in browser")],
    )
)

app = cli(
    name="cargo",
    help="Monokai-themed build tool CLI — compile, test, run, and document your project.",
    theme="monokai",
    show_types=True,
    show_defaults=True,
    line_connect=True,
    max_width=110,
    subgroups=[build, run, extras],
)


def main():
    app.run()


if __name__ == "__main__":
    main()
