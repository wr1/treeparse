"""Example replicating the group option inheritance issue."""

from treeparse import cli, command, argument, option, group

called = []

def callback(name: str, verbose: bool = False):
    called.append((name, verbose))

cmd = command(
    name="greet",
    callback=callback,
    arguments=[argument(name="name", arg_type=str)],
)
grp = group(
    name="user",
    commands=[cmd],
    options=[option(flags=["--verbose"], is_flag=True)],
)
app = cli(name="test", subgroups=[grp])

if __name__ == "__main__":
    import sys
    sys.argv = ["test", "user", "--verbose", "greet", "Alice"]
    app.run()
    print(called)  # Should print [('Alice', True)]
