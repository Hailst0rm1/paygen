#!/usr/bin/env python3
"""
Test recipe loading and validation

Tests that recipe YAML files can be loaded and validated correctly.
"""

import pytest
from pathlib import Path
from src.core.config import ConfigManager
from src.core.recipe_loader import RecipeLoader, Recipe
from src.core.validator import RecipeValidator, ValidationError


class TestRecipeLoading:
    """Test recipe loading functionality."""
    
    @pytest.fixture
    def config(self):
        """Get config manager."""
        return ConfigManager()
    
    @pytest.fixture
    def loader(self, config):
        """Get recipe loader."""
        return RecipeLoader(config)
    
    def test_load_all_recipes(self, loader):
        """Test loading all recipes from recipes directory."""
        recipes = loader.load_all_recipes()
        assert len(recipes) > 0, "Should load at least one recipe"
    
    def test_recipe_structure(self, loader):
        """Test that loaded recipes have correct structure."""
        recipes = loader.load_all_recipes()
        
        for recipe in recipes:
            # Check required fields
            assert recipe.name, "Recipe should have name"
            assert recipe.category, "Recipe should have category"
            assert recipe.description, "Recipe should have description"
            assert recipe.effectiveness in ['low', 'medium', 'high'], \
                "Recipe should have valid effectiveness"
            
            # Check parameters
            assert isinstance(recipe.parameters, list), "Parameters should be a list"
            
            # Check output config
            assert isinstance(recipe.output, dict), "Output should be a dict"
            assert 'type' in recipe.output, "Output should have type"
            assert recipe.output['type'] in ['template', 'command'], \
                "Output type should be template or command"
    
    def test_get_categories(self, loader):
        """Test getting list of categories."""
        loader.load_all_recipes()
        categories = loader.get_categories()
        
        assert isinstance(categories, list), "Categories should be a list"
        assert len(categories) > 0, "Should have at least one category"
    
    def test_get_recipes_by_category(self, loader):
        """Test getting recipes by category."""
        loader.load_all_recipes()
        categories = loader.get_categories()
        
        for category in categories:
            recipes = loader.get_recipes_by_category(category)
            assert isinstance(recipes, list), "Should return list of recipes"
            
            # All recipes should belong to the category
            for recipe in recipes:
                assert recipe.category == category


class TestRecipeValidation:
    """Test recipe YAML validation."""
    
    def test_valid_recipe_structure(self):
        """Test validation of valid recipe structure."""
        recipe_data = {
            'meta': {
                'name': 'Test Recipe',
                'category': 'Test',
                'description': 'Test description',
                'effectiveness': 'high'
            },
            'parameters': [
                {
                    'name': 'lhost',
                    'type': 'ip',
                    'description': 'Test param',
                    'required': True
                }
            ],
            'output': {
                'type': 'command',
                'command': 'echo test'
            }
        }
        
        # Should not raise exception
        assert RecipeValidator.validate_recipe(recipe_data)
    
    def test_missing_meta_section(self):
        """Test that missing meta section raises error."""
        recipe_data = {
            'parameters': [],
            'output': {'type': 'command', 'command': 'test'}
        }
        
        with pytest.raises(ValidationError, match="missing 'meta' section"):
            RecipeValidator.validate_recipe(recipe_data)
    
    def test_missing_parameters_section(self):
        """Test that missing parameters section raises error."""
        recipe_data = {
            'meta': {
                'name': 'Test',
                'category': 'Test',
                'description': 'Test',
                'effectiveness': 'high'
            },
            'output': {'type': 'command', 'command': 'test'}
        }
        
        with pytest.raises(ValidationError, match="missing 'parameters' section"):
            RecipeValidator.validate_recipe(recipe_data)
    
    def test_invalid_effectiveness(self):
        """Test that invalid effectiveness raises error."""
        recipe_data = {
            'meta': {
                'name': 'Test',
                'category': 'Test',
                'description': 'Test',
                'effectiveness': 'super-high'  # Invalid
            },
            'parameters': [],
            'output': {'type': 'command', 'command': 'test'}
        }
        
        with pytest.raises(ValidationError, match="Invalid effectiveness"):
            RecipeValidator.validate_recipe(recipe_data)
    
    def test_invalid_output_type(self):
        """Test that invalid output type raises error."""
        recipe_data = {
            'meta': {
                'name': 'Test',
                'category': 'Test',
                'description': 'Test',
                'effectiveness': 'high'
            },
            'parameters': [],
            'output': {'type': 'invalid-type'}  # Invalid
        }
        
        with pytest.raises(ValidationError, match="Invalid output type"):
            RecipeValidator.validate_recipe(recipe_data)


class TestRecipeParameters:
    """Test recipe parameter handling."""
    
    @pytest.fixture
    def recipe_with_params(self):
        """Create a test recipe with parameters."""
        from src.core.recipe_loader import Recipe
        return Recipe(
            name="Test Recipe",
            category="Test",
            description="Test",
            effectiveness="high",
            parameters=[
                {
                    'name': 'lhost',
                    'type': 'ip',
                    'description': 'Listener host',
                    'required': True
                },
                {
                    'name': 'lport',
                    'type': 'port',
                    'description': 'Listener port',
                    'required': True,
                    'default': 4444
                },
                {
                    'name': 'optional_param',
                    'type': 'string',
                    'description': 'Optional parameter',
                    'required': False,
                    'default': 'default_value'
                }
            ],
            output={'type': 'command', 'command': 'echo test'}
        )
    
    def test_get_required_parameters(self, recipe_with_params):
        """Test getting required parameters."""
        required = recipe_with_params.get_required_parameters()
        
        assert len(required) == 2, "Should have 2 required parameters"
        assert all(p.get('required') for p in required), "All should be required"
    
    def test_get_optional_parameters(self, recipe_with_params):
        """Test getting optional parameters."""
        optional = recipe_with_params.get_optional_parameters()
        
        assert len(optional) == 1, "Should have 1 optional parameter"
        assert not optional[0].get('required'), "Should not be required"
    
    def test_get_parameter_by_name(self, recipe_with_params):
        """Test getting parameter by name."""
        param = recipe_with_params.get_parameter('lhost')
        
        assert param is not None, "Should find parameter"
        assert param['name'] == 'lhost'
        assert param['type'] == 'ip'
    
    def test_recipe_with_platform(self):
        """Test that recipes can have optional platform field."""
        recipe = Recipe(
            name='Test Recipe',
            category='Test',
            description='Test description',
            effectiveness='high',
            platform='Windows',
            parameters=[],
            output={'type': 'command', 'command': 'echo test'}
        )
        
        assert recipe.platform == 'Windows'
    
    def test_recipe_without_platform(self):
        """Test that recipes without platform field work correctly."""
        recipe = Recipe(
            name='Test Recipe',
            category='Test',
            description='Test description',
            effectiveness='high',
            parameters=[],
            output={'type': 'command', 'command': 'echo test'}
        )
        
        assert recipe.platform is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
