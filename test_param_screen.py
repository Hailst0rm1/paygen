#!/usr/bin/env python3
"""Test the parameter configuration screen"""

from src.core.config import get_config
from src.core.recipe_loader import RecipeLoader
from src.tui.app import PaygenApp

# Load config and recipes
config = get_config()
loader = RecipeLoader(config)
recipes = loader.load_all_recipes()

print(f"Loaded {len(recipes)} recipes")
print(f"Recipe 0: {recipes[0].name}")
print(f"Parameters: {len(recipes[0].parameters)}")

# Create app
app = PaygenApp(config=config, recipes=recipes)

# Set selected recipe
app.selected_recipe = recipes[0]

print(f"Selected recipe: {app.selected_recipe.name}")
print("Ready to test")
