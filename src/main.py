"""Paygen - Payload Generation Framework

Web interface entry point.
"""

import sys

from .web.app import run_web_app


def main():
    """Main entry point for paygen"""
    try:
        run_web_app()
    except KeyboardInterrupt:
        print("\n\nShutting down Paygen...")
        return 0
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
