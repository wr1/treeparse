# Run via: uv run --with-editable . python examples/flag_demo.py
# or after `pip install -e .[dev]`
from treeparse import argument, cli, command, option


def deploy(env: str, verbose: bool, dry_run: bool):
    if verbose:
        print(f"[verbose] deploying to environment: {env}")
        print(f"[verbose] dry_run={dry_run}")
    if dry_run:
        print(f"(dry run) would deploy to {env}")
    else:
        print(f"deploying to {env}")


def build(target: str, release: bool, verbose: bool):
    mode = "release" if release else "debug"
    if verbose:
        print(f"[verbose] building {target} in {mode} mode")
    print(f"built {target} ({mode})")


app = cli(
    name="flag-demo",
    help="Demo of boolean flag options (flag=True).",
    line_connect=True,
    max_width=100,
)

deploy_cmd = command(
    name="deploy",
    help="Deploy to an environment.",
    callback=deploy,
    arguments=[
        argument(name="env", arg_type=str, help="Target environment"),
    ],
    options=[
        option(flags=["--verbose", "-v"], flag=True, help="Enable verbose output"),
        option(flags=["--dry-run", "-n"], flag=True, help="Simulate without making changes"),
    ],
)

build_cmd = command(
    name="build",
    help="Build a target.",
    callback=build,
    arguments=[
        argument(name="target", arg_type=str, help="Build target"),
    ],
    options=[
        option(flags=["--release", "-r"], flag=True, help="Build in release mode"),
        option(flags=["--verbose", "-v"], flag=True, help="Enable verbose output"),
    ],
)

app.commands.append(deploy_cmd)
app.commands.append(build_cmd)


def main():
    app.run()


if __name__ == "__main__":
    main()
