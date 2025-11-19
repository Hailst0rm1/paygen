#!/usr/bin/env python3
"""
Paygen - Main Entry Point

Launches the TUI application for payload generation.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for Paygen."""
    try:
        # Import TUI app
        from src.tui.app import run_app
        
        # Run the application
        run_app()
        return 0
    except ImportError as e:
        print("Paygen - Payload Generation Framework")
        print("=" * 40)
        print(f"\n[!] Missing dependency: {e}")
        print("[*] Install dependencies: pip install -r requirements.txt")
        print("[*] Or use Nix: nix develop")
        return 1
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
