#!/usr/bin/env python3
"""
Phase 4 Integration Test

Test the parameter configuration screen integration with the app.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.config import get_config
from src.core.recipe_loader import RecipeLoader

def main():
    """Run integration tests."""
    print("=" * 70)
    print("Phase 4 Integration Test")
    print("=" * 70)
    
    # Load configuration
    print("\n[1/4] Loading configuration...")
    config = get_config()
    print(f"  ✓ Config loaded")
    print(f"    - Recipes dir: {config.recipes_dir}")
    print(f"    - Payloads dir: {config.payloads_dir}")
    print(f"    - Output dir: {config.output_dir}")
    print(f"    - Theme: {config.get('theme', 'default')}")
    
    # Load recipes
    print("\n[2/4] Loading recipes...")
    loader = RecipeLoader(config)
    recipes = loader.load_all_recipes()
    print(f"  ✓ Loaded {len(recipes)} recipes")
    
    for recipe in recipes:
        print(f"    - {recipe.name}")
        print(f"      Category: {recipe.category}")
        print(f"      Parameters: {len(recipe.parameters)}")
        
        # Show parameter details
        for i, param in enumerate(recipe.parameters, 1):
            name = param.get('name', 'unknown')
            ptype = param.get('type', 'string')
            required = param.get('required', False)
            default = param.get('default', '')
            req_marker = "*" if required else " "
            print(f"        {i}. [{req_marker}] {name} ({ptype}) = {default}")
    
    # Test parameter resolution
    print("\n[3/4] Testing parameter default resolution...")
    test_recipe = recipes[0] if recipes else None
    
    if test_recipe:
        print(f"  Testing with: {test_recipe.name}")
        for param in test_recipe.parameters:
            name = param.get('name')
            default = param.get('default', '')
            
            # Check if it's a config placeholder
            if isinstance(default, str) and default.startswith('{config.'):
                config_key = default[8:-1]
                resolved = getattr(config, config_key, default)
                print(f"    ✓ {name}: '{default}' → '{resolved}'")
            else:
                print(f"    • {name}: {default}")
    
    # Test validation
    print("\n[4/4] Testing parameter validation...")
    from src.core.validator import ParameterValidator, ValidationError
    validator = ParameterValidator()
    
    test_cases = [
        ("IP", "192.168.1.1", validator.validate_ip, True),
        ("IP", "invalid", validator.validate_ip, False),
        ("Port", "4444", validator.validate_port, True),
        ("Port", "99999", validator.validate_port, False),
        ("Hex", "deadbeef", validator.validate_hex, True),
        ("Hex", "xyz123", validator.validate_hex, False),
    ]
    
    for label, value, func, should_pass in test_cases:
        try:
            func(value)
            result = "✓" if should_pass else "✗ (should fail)"
        except ValidationError:
            result = "✗ (should pass)" if should_pass else "✓"
        print(f"    {result} {label:6s} {value:15s}")
    
    print("\n" + "=" * 70)
    print("Integration test complete!")
    print("\nNow run: python -m src.main")
    print("Then press 'g' on a recipe to test parameter configuration.")
    print("=" * 70)

if __name__ == "__main__":
    main()
