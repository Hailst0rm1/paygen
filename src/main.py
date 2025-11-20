"""Paygen - Payload Generation Framework

Entry point for the application.
"""

import sys
from pathlib import Path

from .core.config import get_config
from .core.recipe_loader import RecipeLoader
from .tui.app import run_tui


def main():
    """Main entry point"""
    # Initialize configuration
    try:
        config = get_config()
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}", file=sys.stderr)
        return 1
    
    # Load recipes
    try:
        loader = RecipeLoader(config)
        recipes = loader.load_all_recipes()
    except Exception as e:
        print(f"✗ Failed to load recipes: {e}", file=sys.stderr)
        return 1
    
    # Launch TUI
    try:
        run_tui(config=config, recipes=recipes)
    except Exception as e:
        print(f"✗ TUI error: {e}", file=sys.stderr)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
