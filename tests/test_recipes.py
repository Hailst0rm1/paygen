#!/usr/bin/env python3
"""
Test recipe loading and validation

Tests that recipe YAML files can be loaded and validated correctly.
"""

import pytest
import tempfile
import shutil
import yaml
from pathlib import Path
from src.core.config import ConfigManager
from src.core.recipe_loader import RecipeLoader, Recipe
from src.core.recipe_manager import RecipeManager
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

    def test_recipe_version_count(self):
        """Test that recipes track version count."""
        recipe = Recipe(
            name='Test Recipe',
            category='Test',
            description='Test description',
            effectiveness='high',
            parameters=[],
            output={'type': 'command', 'command': 'echo test'},
            version_count=3
        )

        assert recipe.version_count == 3

    def test_recipe_default_version_count(self):
        """Test that recipes default to version_count=1."""
        recipe = Recipe(
            name='Test Recipe',
            category='Test',
            description='Test description',
            effectiveness='high',
            parameters=[],
            output={'type': 'command', 'command': 'echo test'}
        )

        assert recipe.version_count == 1


class TestRecipeManager:
    """Test recipe manager versioning and CRUD operations."""

    @pytest.fixture
    def tmp_recipes_dir(self, tmp_path):
        """Create a temporary recipes directory."""
        recipes_dir = tmp_path / "recipes"
        recipes_dir.mkdir()
        return recipes_dir

    @pytest.fixture
    def manager(self, tmp_recipes_dir):
        """Create a RecipeManager with a temp config."""
        config = ConfigManager()
        # Override the recipes_dir to use temp directory
        config.config['recipes_dir'] = str(tmp_recipes_dir)
        return RecipeManager(config)

    @pytest.fixture
    def sample_recipe_data(self):
        """Return a valid sample recipe data dict."""
        return {
            'meta': {
                'name': 'Test Recipe',
                'category': 'Test',
                'description': 'A test recipe',
                'effectiveness': 'medium'
            },
            'parameters': [
                {
                    'name': 'lhost',
                    'type': 'ip',
                    'description': 'Listener host',
                    'required': True
                }
            ],
            'preprocessing': [],
            'output': {
                'type': 'command',
                'command': 'echo {{ lhost }}'
            }
        }

    def test_reconstruct_v1_only(self, manager):
        """Test reconstructing a recipe with only V1."""
        versions = [
            {
                'version': 1,
                'comment': 'Initial',
                'timestamp': '2026-01-01T00:00:00',
                'original': {
                    'meta': {'name': 'Test', 'category': 'Cat', 'description': 'Desc', 'effectiveness': 'low'},
                    'parameters': [],
                    'output': {'type': 'command', 'command': 'echo hello'}
                }
            }
        ]
        result = manager.reconstruct_recipe(versions)
        assert result['meta']['name'] == 'Test'
        assert result['meta']['category'] == 'Cat'
        assert result['output']['command'] == 'echo hello'

    def test_reconstruct_with_changes(self, manager):
        """Test reconstructing a recipe with V1 + V2 changes."""
        versions = [
            {
                'version': 1,
                'comment': 'Initial',
                'original': {
                    'meta': {'name': 'Test', 'category': 'Cat', 'description': 'Desc', 'effectiveness': 'low'},
                    'parameters': [{'name': 'p1', 'type': 'string', 'description': 'Param 1', 'required': True}],
                    'output': {'type': 'command', 'command': 'echo hello'}
                }
            },
            {
                'version': 2,
                'comment': 'Updated description',
                'changes': {
                    'meta': {'description': 'Updated Desc'}
                }
            }
        ]
        result = manager.reconstruct_recipe(versions)
        assert result['meta']['description'] == 'Updated Desc'
        # Unchanged fields preserved
        assert result['meta']['name'] == 'Test'
        assert result['meta']['effectiveness'] == 'low'
        assert len(result['parameters']) == 1

    def test_reconstruct_up_to_version(self, manager):
        """Test reconstructing up to a specific version."""
        versions = [
            {
                'version': 1,
                'comment': 'Initial',
                'original': {
                    'meta': {'name': 'Test', 'category': 'Cat', 'description': 'V1', 'effectiveness': 'low'},
                    'parameters': [],
                    'output': {'type': 'command', 'command': 'echo v1'}
                }
            },
            {
                'version': 2,
                'comment': 'V2',
                'changes': {'meta': {'description': 'V2'}}
            },
            {
                'version': 3,
                'comment': 'V3',
                'changes': {'meta': {'description': 'V3'}}
            }
        ]
        # Reconstruct at V2
        result = manager.reconstruct_recipe(versions, up_to=2)
        assert result['meta']['description'] == 'V2'

        # Reconstruct at V1
        result = manager.reconstruct_recipe(versions, up_to=1)
        assert result['meta']['description'] == 'V1'

        # Reconstruct at V3 (latest)
        result = manager.reconstruct_recipe(versions, up_to=3)
        assert result['meta']['description'] == 'V3'

    def test_reconstruct_list_replacement(self, manager):
        """Test that list fields (parameters) are fully replaced in version changes."""
        versions = [
            {
                'version': 1,
                'comment': 'Initial',
                'original': {
                    'meta': {'name': 'Test', 'category': 'Cat', 'description': 'Desc', 'effectiveness': 'low'},
                    'parameters': [
                        {'name': 'p1', 'type': 'string', 'description': 'Param 1', 'required': True},
                        {'name': 'p2', 'type': 'port', 'description': 'Param 2', 'required': True}
                    ],
                    'output': {'type': 'command', 'command': 'echo test'}
                }
            },
            {
                'version': 2,
                'comment': 'Changed params',
                'changes': {
                    'parameters': [
                        {'name': 'p1', 'type': 'ip', 'description': 'Updated Param', 'required': True}
                    ]
                }
            }
        ]
        result = manager.reconstruct_recipe(versions)
        # Parameters should be fully replaced, not merged
        assert len(result['parameters']) == 1
        assert result['parameters'][0]['name'] == 'p1'
        assert result['parameters'][0]['type'] == 'ip'

    def test_compute_changes_dict_diff(self, manager):
        """Test computing minimal changes between two recipe states."""
        old = {
            'meta': {'name': 'Test', 'category': 'Cat', 'description': 'Old', 'effectiveness': 'low'},
            'parameters': [],
            'output': {'type': 'command', 'command': 'echo old'}
        }
        new = {
            'meta': {'name': 'Test', 'category': 'Cat', 'description': 'New', 'effectiveness': 'low'},
            'parameters': [],
            'output': {'type': 'command', 'command': 'echo new'}
        }
        changes = manager._compute_changes(old, new)
        # Only changed fields should be in changes
        assert 'meta' in changes
        assert changes['meta'] == {'description': 'New'}
        assert 'output' in changes
        assert changes['output'] == {'command': 'echo new'}
        # parameters didn't change
        assert 'parameters' not in changes

    def test_compute_changes_no_diff(self, manager):
        """Test that identical data produces empty changes."""
        data = {
            'meta': {'name': 'Test', 'category': 'Cat', 'description': 'Desc', 'effectiveness': 'low'},
            'parameters': [],
            'output': {'type': 'command', 'command': 'echo test'}
        }
        changes = manager._compute_changes(data, data)
        assert changes == {}

    def test_compute_changes_removed_key(self, manager):
        """Test that removed keys are set to None in changes."""
        old = {'meta': {'name': 'Test', 'extra': 'field'}}
        new = {'meta': {'name': 'Test'}}
        changes = manager._compute_changes(old, new)
        assert changes['meta']['extra'] is None

    def test_deep_merge_dict(self, manager):
        """Test deep merge of dicts."""
        base = {'meta': {'name': 'Test', 'category': 'Cat', 'description': 'Old'}}
        changes = {'meta': {'description': 'New'}}
        result = manager._deep_merge(base, changes)
        assert result['meta']['name'] == 'Test'
        assert result['meta']['category'] == 'Cat'
        assert result['meta']['description'] == 'New'

    def test_deep_merge_list_replacement(self, manager):
        """Test that deep merge fully replaces lists."""
        base = {'params': [{'a': 1}, {'b': 2}]}
        changes = {'params': [{'c': 3}]}
        result = manager._deep_merge(base, changes)
        assert len(result['params']) == 1
        assert result['params'][0] == {'c': 3}

    def test_deep_merge_none_removes_key(self, manager):
        """Test that None values remove keys during merge."""
        base = {'meta': {'name': 'Test', 'extra': 'field'}}
        changes = {'meta': {'extra': None}}
        result = manager._deep_merge(base, changes)
        assert 'extra' not in result['meta']

    def test_create_recipe(self, manager, sample_recipe_data, tmp_recipes_dir):
        """Test creating a new recipe file."""
        path = manager.create_recipe(sample_recipe_data, comment="Initial version")

        assert path.exists()

        # Read back and verify structure
        with open(path, 'r') as f:
            raw = yaml.safe_load(f)

        assert 'versions' in raw
        assert len(raw['versions']) == 1
        assert raw['versions'][0]['version'] == 1
        assert raw['versions'][0]['comment'] == 'Initial version'
        assert 'original' in raw['versions'][0]
        assert raw['versions'][0]['original']['meta']['name'] == 'Test Recipe'

    def test_create_recipe_invalid_data(self, manager):
        """Test that creating a recipe with invalid data raises ValidationError."""
        bad_data = {'parameters': [], 'output': {'type': 'command', 'command': 'test'}}
        with pytest.raises(ValidationError):
            manager.create_recipe(bad_data)

    def test_generate_filename(self, manager):
        """Test filename generation from recipe name."""
        assert manager._generate_filename("Basic Msfvenom Payload") == "basic_msfvenom_payload.yaml"
        assert manager._generate_filename("C# AES Injector") == "c_aes_injector.yaml"

    def test_load_versioned_recipe(self, manager, sample_recipe_data, tmp_recipes_dir):
        """Test loading a versioned recipe file."""
        path = manager.create_recipe(sample_recipe_data)

        data, version_count = manager.load_versioned_recipe(path)
        assert version_count == 1
        assert data['meta']['name'] == 'Test Recipe'
        assert data['meta']['category'] == 'Test'

    def test_load_legacy_recipe(self, manager, tmp_recipes_dir):
        """Test loading a legacy (non-versioned) recipe file."""
        legacy_data = {
            'meta': {'name': 'Legacy', 'category': 'Test', 'description': 'Old', 'effectiveness': 'low'},
            'parameters': [],
            'output': {'type': 'command', 'command': 'echo legacy'}
        }
        legacy_path = tmp_recipes_dir / "legacy.yaml"
        with open(legacy_path, 'w') as f:
            yaml.dump(legacy_data, f)

        data, version_count = manager.load_versioned_recipe(legacy_path)
        assert version_count == 1
        assert data['meta']['name'] == 'Legacy'

    def test_reconstruct_empty_versions(self, manager):
        """Test reconstructing from empty versions list."""
        result = manager.reconstruct_recipe([])
        assert result == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
