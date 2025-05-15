#!/bin/sh

# Exit on error
set -e

# Detect Python version
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD >/dev/null 2>&1; then
    echo "Error: python3 not found"
    exit 1
fi

# Create and activate virtualenv
echo "Creating virtual environment..."
$PYTHON_CMD -m venv .venv

# Detect OS for activation script
if [ "$(uname)" = "Darwin" ]; then
    # macOS
    ACTIVATE_SCRIPT=".venv/bin/activate"
else
    # Linux
    ACTIVATE_SCRIPT=".venv/bin/activate"
fi

# Activate virtualenv and install dependencies
echo "Installing dependencies..."
. $ACTIVATE_SCRIPT
pip install --upgrade pip
pip install pip-tools

# Generate requirements.txt from requirements.in
pip-compile requirements.in -o requirements.txt

# Install dependencies
pip install -r requirements.txt

# Run the main script to generate SBOM
echo "Generating SBOM..."
python main.py

echo "Build complete! SBOM generated as sbom-gold.json" 