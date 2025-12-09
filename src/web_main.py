"""Paygen Web Entry Point

Launch the web GUI for Paygen.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.web.app import run_web_app


def main():
    """Main entry point for paygen-web"""
    try:
        run_web_app()
    except KeyboardInterrupt:
        print("\n\nShutting down Paygen Web...")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
