#!/usr/bin/env bash
# Test script for Paygen TUI

echo "Testing Paygen TUI..."
echo "Note: Ensure dependencies are installed (pip install -r requirements.txt)"
echo "      Or run in Nix shell: nix develop ~/.nixos#python"
echo ""

cd "$(dirname "$0")" || exit
python3 paygen.py
