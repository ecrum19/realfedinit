#!/usr/bin/env bash

SESSION="experiments"
COMMAND="./experiment-automation.sh"

# Check if the screen session exists by looking for its name in the list.
if screen -list | grep -q "\.${SESSION}"; then
    echo "Session '${SESSION}' exists. Resuming and running the experiment commands."
    # Send the command followed by a newline to the session.
    screen -S "$SESSION" -X exec "$COMMAND"
else
    echo "Session '${SESSION}' does not exist. Creating a new one and running the experiment commands."
    # Create a new detached session and run the command.
    screen -S "$SESSION" -d -m
    screen -S "$SESSION" -X exec "$COMMAND"
fi