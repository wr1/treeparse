"""Example replicating the chain execution issue."""

from treeparse import cli, command, argument, chain

calls = []

def cb1(a: int):
    calls.append(("cb1", a))

def cb2(b: str):
    calls.append(("cb2", b))

cmd1 = command(
    name="cmd1", callback=cb1, arguments=[argument(name="a", arg_type=int)]
)
cmd2 = command(
    name="cmd2", callback=cb2, arguments=[argument(name="b", arg_type=str)]
)
chain_obj = chain(name="chain", chained_commands=[cmd1, cmd2])
app = cli(name="test", commands=[chain_obj])

if __name__ == "__main__":
    import sys
    sys.argv = ["test", "chain", "42", "hello"]
    app.run()
    print(calls)  # Should print [('cb1', 42), ('cb2', 'hello')]
