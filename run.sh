#!/bin/bash

# Output file
OUTPUT_FILE="help_output.txt"

# Clear the output file
> "$OUTPUT_FILE"

# List of help commands to run
COMMANDS=(
    "--help"
    "user --help"
    "user manage --help"
    "user manage permissions --help"
    "user manage permissions set --help"
    "user manage permissions set add --help"
    "info --help"
    "project --help"
    "user add --help"
    "user list --help"
    "user manage remove-role --help"
    "user manage set-role --help"
)

for cmd in "${COMMANDS[@]}"; do
    echo "=== Running: python examples/demo.py $cmd ===" >> "$OUTPUT_FILE"
    python examples/demo.py $cmd >> "$OUTPUT_FILE" 2>&1
    printf "\n" >> "$OUTPUT_FILE"
done

echo "Help outputs saved to $OUTPUT_FILE"

