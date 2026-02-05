"""
Shellcode configuration loader for Paygen

Loads and validates shellcode generation methods from shellcodes.yaml
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .validator import ParameterValidator, ValidationError


@dataclass
class ShellcodeConfig:
    """Represents a shellcode generation method configuration"""
    
    name: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    shellcode: str = ""
    listener: Optional[str] = None
    
    def get_parameter(self, name: str) -> Optional[Dict[str, Any]]:
        """Get parameter definition by name
        
        Args:
            name: Parameter name
            
        Returns:
            Parameter definition or None
        """
        for param in self.parameters:
            if param.get('name') == name:
                return param
        return None
    
    def get_required_parameters(self) -> List[Dict[str, Any]]:
        """Get list of required parameters"""
        return [p for p in self.parameters if p.get('required', False)]
    
    def get_optional_parameters(self) -> List[Dict[str, Any]]:
        """Get list of optional parameters"""
        return [p for p in self.parameters if not p.get('required', False)]


class ShellcodeLoader:
    """Loads and manages shellcode configurations from YAML"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize shellcode loader
        
        Args:
            config_path: Path to shellcodes.yaml file
        """
        self.config_path = config_path
        self.shellcodes: Dict[str, ShellcodeConfig] = {}
        
        if config_path and config_path.exists():
            self.load_shellcodes()
    
    def load_shellcodes(self) -> Dict[str, ShellcodeConfig]:
        """Load all shellcode configurations from YAML file
        
        Returns:
            Dictionary mapping shellcode names to ShellcodeConfig objects
            
        Raises:
            ValidationError: If validation fails
        """
        if not self.config_path or not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                return {}
            
            if not isinstance(data, list):
                raise ValidationError("Shellcodes file must contain a list of shellcode configurations")
            
            self.shellcodes = {}
            
            for idx, shellcode_data in enumerate(data):
                # Validate shellcode configuration
                self._validate_shellcode_config(shellcode_data, idx)
                
                # Create ShellcodeConfig object
                name = shellcode_data['name']
                shellcode_config = ShellcodeConfig(
                    name=name,
                    parameters=shellcode_data.get('parameters', []),
                    shellcode=shellcode_data.get('shellcode', ''),
                    listener=shellcode_data.get('listener')
                )
                
                self.shellcodes[name] = shellcode_config
            
            return self.shellcodes
            
        except yaml.YAMLError as e:
            raise ValidationError(f"YAML parsing error in shellcodes file: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to load shellcodes configuration: {e}")
    
    def _validate_shellcode_config(self, config: Dict[str, Any], index: int) -> None:
        """Validate a single shellcode configuration
        
        Args:
            config: Shellcode configuration dictionary
            index: Index in the list (for error reporting)
            
        Raises:
            ValidationError: If validation fails
        """
        # Required fields
        if 'name' not in config:
            raise ValidationError(f"Shellcode configuration at index {index} missing 'name' field")
        
        if 'shellcode' not in config:
            raise ValidationError(f"Shellcode configuration '{config['name']}' missing 'shellcode' field")
        
        # Validate parameters if present
        if 'parameters' in config:
            if not isinstance(config['parameters'], list):
                raise ValidationError(f"Shellcode '{config['name']}' parameters must be a list")
            
            param_names = set()
            for param in config['parameters']:
                # Check required parameter fields
                required_fields = ['name', 'type', 'description', 'required']
                for field in required_fields:
                    if field not in param:
                        raise ValidationError(
                            f"Shellcode '{config['name']}' parameter missing required field: {field}"
                        )
                
                # Check for duplicate parameter names
                param_name = param['name']
                if param_name in param_names:
                    raise ValidationError(f"Shellcode '{config['name']}' has duplicate parameter: {param_name}")
                param_names.add(param_name)
                
                # Validate parameter type is supported
                param_type = param['type']
                valid_types = ['string', 'ip', 'port', 'path', 'file', 'hex', 'bool', 'integer', 'choice', 'option']
                if param_type not in valid_types:
                    raise ValidationError(
                        f"Shellcode '{config['name']}' parameter '{param_name}' has invalid type '{param_type}'. "
                        f"Valid types: {valid_types}"
                    )
                
                # Validate option type has options list
                if param_type == 'option' and 'options' not in param:
                    raise ValidationError(
                        f"Shellcode '{config['name']}' option parameter '{param_name}' missing 'options' field"
                    )
                
                # Validate choice parameters have choices
                if param_type == 'choice' and 'choices' not in param:
                    raise ValidationError(
                        f"Shellcode '{config['name']}' choice parameter '{param_name}' missing 'choices' field"
                    )
        
        # Validate listener is a string if present
        if 'listener' in config and not isinstance(config['listener'], str):
            raise ValidationError(f"Shellcode '{config['name']}' listener must be a string")
    
    def get_shellcode(self, name: str) -> Optional[ShellcodeConfig]:
        """Get shellcode configuration by name
        
        Args:
            name: Shellcode name
            
        Returns:
            ShellcodeConfig object or None if not found
        """
        return self.shellcodes.get(name)
    
    def get_all_shellcodes(self) -> Dict[str, ShellcodeConfig]:
        """Get all loaded shellcode configurations
        
        Returns:
            Dictionary of shellcode configurations
        """
        return self.shellcodes
    
    def get_shellcode_names(self) -> List[str]:
        """Get list of all shellcode names
        
        Returns:
            List of shellcode names
        """
        return list(self.shellcodes.keys())
