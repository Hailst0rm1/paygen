"""Paygen - Payload Generation Framework

Entry point for the application.
"""

import sys
from pathlib import Path

from .core.config import get_config
from .core.recipe_loader import RecipeLoader


def main():
    """Main entry point"""
    print("╔═══════════════════════════════════════════════════╗")
    print("║  PAYGEN - Payload Generation Framework v2.0      ║")
    print("║  Template-based payload generation with TUI       ║")
    print("╚═══════════════════════════════════════════════════╝")
    print()
    
    # Initialize configuration
    try:
        config = get_config()
        print(f"✓ Configuration loaded from {config.config_path}")
        print(f"  - Recipes directory: {config.recipes_dir}")
        print(f"  - Payloads directory: {config.payloads_dir}")
        print(f"  - Preprocessors directory: {config.preprocessors_dir}")
        print(f"  - Output directory: {config.output_dir}")
        print(f"  - Theme: {config.theme}")
        print()
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return 1
    
    # Load recipes
    try:
        loader = RecipeLoader(config)
        recipes = loader.load_all_recipes()
        
        print(f"✓ Loaded {loader.get_recipe_count()} recipes from {loader.get_category_count()} categories")
        
        if recipes:
            print("\nCategories:")
            for category in loader.get_categories():
                category_recipes = loader.get_recipes_by_category(category)
                print(f"  • {category} ({len(category_recipes)} recipes)")
        else:
            print("\n⚠ No recipes found. Add recipe YAML files to the recipes directory.")
        print()
        
    except Exception as e:
        print(f"✗ Failed to load recipes: {e}")
        return 1
    
    print("Phase 1 core infrastructure is complete!")
    print("\nNext steps:")
    print("  1. Add recipe YAML files to the recipes directory")
    print("  2. Add payload templates to the payloads directory")
    print("  3. Implement TUI (Phase 3)")
    print("  4. Implement preprocessing system (Phase 2)")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
