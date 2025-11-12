"""Example app with two arguments: mesh and anba."""

from treeparse import cli, command, argument


def run_command(mesh: str, anba: str):
    """Run command with mesh and anba arguments."""
    print(f"Mesh: {mesh}, Anba: {anba}")


app = cli(
    name="mesh_anba_example",
    help="Example CLI with mesh and anba arguments.",
    commands=[
        command(
            name="run",
            help="Execute with mesh and anba.",
            callback=run_command,
            arguments=[
                argument(name="mesh", arg_type=str, help="The mesh argument."),
                argument(name="anba", arg_type=str, help="The anba argument."),
            ],
        )
    ],
)


def main():
    """Run the CLI application."""
    app.run()


if __name__ == "__main__":
    main()
