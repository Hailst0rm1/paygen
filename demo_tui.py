#!/usr/bin/env python3
"""
Quick demo/test script for the Paygen TUI

Run this to test the TUI with the example recipes.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.main import main

if __name__ == '__main__':
    print("=" * 60)
    print("PAYGEN TUI DEMO")
    print("=" * 60)
    print()
    print("Keybindings:")
    print("  j/k       - Navigate up/down")
    print("  h/l       - Switch panels left/right")
    print("  Tab       - Next panel")
    print("  Enter     - Select/Expand")
    print("  g         - Generate (not yet implemented)")
    print("  ?         - Help")
    print("  q         - Quit")
    print()
    print("=" * 60)
    print()
    input("Press Enter to launch the TUI...")
    
    sys.exit(main())
