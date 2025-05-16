#!/bin/bash
set -e

# Echo all commands
set -x

# Forward all signals to the Python process
trap 'kill -TERM $PID' TERM INT

# Start the Python application in the background
python3 -u /app/src/app.py &
PID=$!

# Wait for the Python process to exit
wait $PID

# Exit with the same code
exit $? 