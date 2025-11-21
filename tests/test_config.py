#!/usr/bin/env python3
"""
Test configuration management

Tests configuration loading, validation, and path resolution.
"""

import pytest
from pathlib import Path
from src.core.config import ConfigManager


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def test_config_creation(self):
        """Test that config can be created."""
        config = ConfigManager()
        assert config is not None
    
    def test_default_paths_exist(self):
        """Test that default paths are set."""
        config = ConfigManager()
        
        assert config.recipes_dir is not None
        assert config.templates_dir is not None
        assert config.preprocessors_dir is not None
        assert config.output_dir is not None
    
    def test_paths_are_pathlib_paths(self):
        """Test that paths are pathlib.Path objects."""
        config = ConfigManager()
        
        assert isinstance(config.recipes_dir, Path)
        assert isinstance(config.templates_dir, Path)
        assert isinstance(config.preprocessors_dir, Path)
        assert isinstance(config.output_dir, Path)
    
    def test_recipes_dir_exists(self):
        """Test that recipes directory exists."""
        config = ConfigManager()
        assert config.recipes_dir.exists(), \
            f"Recipes directory should exist: {config.recipes_dir}"
    
    def test_templates_dir_exists(self):
        """Test that templates directory exists."""
        config = ConfigManager()
        assert config.templates_dir.exists(), \
            f"Templates directory should exist: {config.templates_dir}"
    
    def test_preprocessors_dir_exists(self):
        """Test that preprocessors directory exists."""
        config = ConfigManager()
        assert config.preprocessors_dir.exists(), \
            f"Preprocessors directory should exist: {config.preprocessors_dir}"
    
    def test_config_get_method(self):
        """Test config.get() method."""
        config = ConfigManager()
        
        # Test getting existing key
        output_dir = config.get('output_dir')
        assert output_dir is not None
        
        # Test getting non-existent key with default
        result = config.get('nonexistent', 'default_value')
        assert result == 'default_value'
    
    def test_keep_source_files_setting(self):
        """Test keep_source_files configuration."""
        config = ConfigManager()
        
        # Should have a value (True or False)
        keep_source = config.keep_source_files
        assert isinstance(keep_source, bool)
    
    def test_show_build_debug_setting(self):
        """Test show_build_debug configuration."""
        config = ConfigManager()
        
        # Should have a value (True or False)
        show_debug = config.show_build_debug
        assert isinstance(show_debug, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
