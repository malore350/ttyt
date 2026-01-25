#!/bin/bash
set -e

echo "Installing ttyt..."

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

CONFIG_DIR="$HOME/.ttyt"
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Creating configuration directory at $CONFIG_DIR..."
    mkdir -p "$CONFIG_DIR"
fi

echo "Installing package..."
python3 -m pip install .

echo "--------------------------------------------------"
echo "Installation successful!"
echo "You can now run 'ttyt' from your terminal."
echo "Configuration is stored in $CONFIG_DIR"
echo "--------------------------------------------------"
