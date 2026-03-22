#shellplot -t 0.02 -s 20 -w 125 -h 32 -d 1.8

# Complex CLI with groups, subcommands, arguments, and options
python examples/demo.py --help
clear

# Monokai theme — cargo-style build tool CLI
python examples/monokai_theme_demo.py --help
clear

python examples/monokai_theme_demo.py build --help
clear

# GitHub dark theme — gh-style repo/pr/issue CLI
python examples/github_theme_demo.py --help
clear

python examples/github_theme_demo.py pr --help
clear

# command chaining
python examples/chain_demo.py --help
clear

# CLI composition — super CLI embedding other CLIs as subgroups
python examples/basic_super.py --help
clear

# cli as json (LLM-friendly output)
python examples/basic.py -j
clear
