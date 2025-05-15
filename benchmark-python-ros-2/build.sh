#!/bin/bash

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install pip-tools
pip install pip-tools

# Install dependencies
pip install -r requirements.in

# Generate requirements.txt
pip-compile requirements.in > requirements.txt

# Run the main script
python main.py 