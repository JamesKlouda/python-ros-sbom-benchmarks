#!/bin/bash

# Exit on error
set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install pip-tools
pip install pip-tools

# Compile requirements.txt from requirements.in
pip-compile requirements.in

# Install dependencies
pip install -r requirements.txt

# Install playwright browsers
playwright install

# Run the benchmark
python main.py

# Deactivate virtual environment
deactivate 