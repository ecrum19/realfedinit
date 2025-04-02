#!/usr/bin/env bash

SESSION="experiments"
COMMAND="./experiment-automation.sh"

# Check if the screen session exists by looking for its name in the list.
if screen -list | grep -q "\.${SESSION}"; then
    echo "Session ${SESSION} exists. Resuming and executing the command."
    # Send the command followed by a newline to the session.
    screen -S "$SESSION" -X stuff "$COMMAND$(printf \\r)"
    # Optionally, reattach to the session so you can see the output.
    screen -r "$SESSION"
else
    echo "Session ${SESSION} does not exist. Creating a new one with the command."
    # Create a new detached session and run the command.
    screen -dmS "$SESSION" bash -c "$COMMAND"
fi