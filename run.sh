#!/usr/bin/env bash
# Test script for Paygen TUI

echo "Testing Paygen TUI..."
echo "Note: Run this in a Nix development shell: nix develop ~/.nixos#python"
echo ""

cd "$(dirname "$0")"
python3 src/main.py
