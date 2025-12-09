"""Configuration management for Paygen"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages Paygen configuration from ~/.config/paygen/config.yaml"""
    
    DEFAULT_CONFIG = {
        'recipes_dir': '~/Documents/Tools/paygen/recipes',
        'templates_dir': '~/Documents/Tools/paygen/templates',
        'preprocessors_dir': '~/Documents/Tools/paygen/preprocessors',
        'output_dir': '~/Documents/Tools/paygen/output',
        'theme': 'catppuccin_mocha',
        'transparent_background': True,
        'keep_source_files': False,
        'show_build_debug': False,
        'remove_comments': True,
        'strip_binaries': True,
        'web_host': '0.0.0.0',
        'web_port': 1337,
        'web_debug': False
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager
        
        Args:
            config_path: Optional custom config path. Defaults to ~/.config/paygen/config.yaml
        """
        if config_path:
            self.config_path = Path(config_path).expanduser()
        else:
            self.config_path = Path.home() / '.config' / 'paygen' / 'config.yaml'
        
        self.config = self._load_or_create_config()
        self._validate_paths()
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load existing config or create default one"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f) or {}
                # Merge with defaults to ensure all keys exist
                return {**self.DEFAULT_CONFIG, **config}
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create config file with defaults
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_config(self.DEFAULT_CONFIG)
            print(f"Created default configuration at {self.config_path}")
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def _validate_paths(self) -> None:
        """Validate and expand paths in configuration"""
        path_keys = ['recipes_dir', 'templates_dir', 'preprocessors_dir', 'output_dir']
        
        for key in path_keys:
            if key in self.config:
                # Expand ~ and environment variables
                path = Path(self.config[key]).expanduser()
                self.config[key] = str(path.absolute())
                
                # Create directory if it doesn't exist (except output_dir which may be created later)
                if not path.exists() and key != 'output_dir':
                    print(f"Warning: {key} path does not exist: {path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save to file
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        self._save_config(self.config)
    
    def get_path(self, key: str) -> Path:
        """Get path from configuration as Path object
        
        Args:
            key: Configuration key for path
            
        Returns:
            Path object
        """
        path_str = self.get(key)
        if path_str:
            return Path(path_str).expanduser().absolute()
        raise ValueError(f"Path configuration '{key}' not found")
    
    @property
    def recipes_dir(self) -> Path:
        """Get recipes directory path"""
        return self.get_path('recipes_dir')
    
    @property
    def templates_dir(self) -> Path:
        """Get templates directory path"""
        return self.get_path('templates_dir')
    
    @property
    def preprocessors_dir(self) -> Path:
        """Get preprocessors directory path"""
        return self.get_path('preprocessors_dir')
    
    @property
    def output_dir(self) -> Path:
        """Get output directory path"""
        return self.get_path('output_dir')
    
    @property
    def theme(self) -> str:
        """Get theme name"""
        return self.get('theme', 'catppuccin_mocha')
    
    @property
    def transparent_background(self) -> bool:
        """Get transparent background setting"""
        return self.get('transparent_background', True)
    
    @property
    def keep_source_files(self) -> bool:
        """Get keep source files setting"""
        return self.get('keep_source_files', False)
    
    @property
    def show_build_debug(self) -> bool:
        """Get show build debug setting"""
        return self.get('show_build_debug', False)
    
    @property
    def remove_comments(self) -> bool:
        """Get remove comments setting"""
        return self.get('remove_comments', True)
    
    @property
    def strip_binaries(self) -> bool:
        """Get strip binaries setting"""
        return self.get('strip_binaries', True)
    
    @property
    def web_host(self) -> str:
        """Get web server host"""
        return self.get('web_host', '0.0.0.0')
    
    @property
    def web_port(self) -> int:
        """Get web server port"""
        return self.get('web_port', 1337)
    
    @property
    def web_debug(self) -> bool:
        """Get web server debug mode"""
        return self.get('web_debug', False)


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """Get or create global configuration instance
    
    Args:
        config_path: Optional custom config path
        
    Returns:
        ConfigManager instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager(config_path)
    return _config_instance
