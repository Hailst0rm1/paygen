"""Recipe and parameter validation for Paygen"""

import re
import ipaddress
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class ParameterValidator:
    """Validates recipe parameters"""
    
    @staticmethod
    def validate_ip(value: str) -> bool:
        """Validate IP address (IPv4 or IPv6)
        
        Args:
            value: IP address string
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If invalid
        """
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            raise ValidationError(f"Invalid IP address: {value}")
    
    @staticmethod
    def validate_port(value: Union[int, str]) -> bool:
        """Validate port number (1-65535)
        
        Args:
            value: Port number
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If invalid
        """
        try:
            port = int(value)
            if 1 <= port <= 65535:
                return True
            raise ValidationError(f"Port must be between 1 and 65535, got {port}")
        except ValueError:
            raise ValidationError(f"Invalid port number: {value}")
    
    @staticmethod
    def validate_string(value: str) -> bool:
        """Validate string parameter
        
        Args:
            value: String value
            
        Returns:
            True if valid
        """
        return isinstance(value, str)
    
    @staticmethod
    def validate_file(value: str) -> bool:
        """Validate file path exists
        
        Args:
            value: File path
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If file doesn't exist
        """
        path = Path(value).expanduser()
        if path.is_file():
            return True
        raise ValidationError(f"File not found: {value}")
    
    @staticmethod
    def validate_path(value: str) -> bool:
        """Validate directory path
        
        Args:
            value: Directory path
            
        Returns:
            True if valid
        """
        # Just validate it's a valid path format, don't check existence
        try:
            Path(value).expanduser()
            return True
        except Exception as e:
            raise ValidationError(f"Invalid path: {value} - {e}")
    
    @staticmethod
    def validate_hex(value: str) -> bool:
        """Validate hexadecimal string
        
        Args:
            value: Hex string
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If invalid hex
        """
        if re.match(r'^[0-9a-fA-F]+$', value):
            return True
        raise ValidationError(f"Invalid hexadecimal string: {value}")
    
    @staticmethod
    def validate_bool(value: Union[bool, str]) -> bool:
        """Validate boolean value
        
        Args:
            value: Boolean or string representation
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If invalid
        """
        if isinstance(value, bool):
            return True
        if isinstance(value, str) and value.lower() in ('true', 'false', 'yes', 'no', '1', '0'):
            return True
        raise ValidationError(f"Invalid boolean value: {value}")
    
    @staticmethod
    def validate_choice(value: str, choices: List[str]) -> bool:
        """Validate value is in allowed choices
        
        Args:
            value: Value to check
            choices: List of allowed values
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If not in choices
        """
        if value in choices:
            return True
        raise ValidationError(f"Value '{value}' not in allowed choices: {choices}")
    
    @staticmethod
    def validate_integer(value: Union[int, str], range_min: Optional[int] = None, 
                        range_max: Optional[int] = None) -> bool:
        """Validate integer with optional range
        
        Args:
            value: Integer value
            range_min: Minimum value (inclusive)
            range_max: Maximum value (inclusive)
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If invalid
        """
        try:
            num = int(value)
            if range_min is not None and num < range_min:
                raise ValidationError(f"Value {num} is less than minimum {range_min}")
            if range_max is not None and num > range_max:
                raise ValidationError(f"Value {num} is greater than maximum {range_max}")
            return True
        except ValueError:
            raise ValidationError(f"Invalid integer: {value}")
    
    @classmethod
    def validate_parameter(cls, param_def: Dict[str, Any], value: Any) -> bool:
        """Validate a parameter value against its definition
        
        Args:
            param_def: Parameter definition from recipe
            value: Value to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        param_type = param_def.get('type', 'string')
        
        # Handle empty values for non-required parameters
        if not param_def.get('required', False) and (value is None or value == ''):
            return True
        
        # Required parameter must have value
        if param_def.get('required', False) and (value is None or value == ''):
            raise ValidationError(f"Required parameter '{param_def.get('name')}' is missing")
        
        # Type-specific validation
        validators = {
            'ip': cls.validate_ip,
            'port': cls.validate_port,
            'string': cls.validate_string,
            'file': cls.validate_file,
            'path': cls.validate_path,
            'hex': cls.validate_hex,
            'bool': cls.validate_bool,
            'integer': lambda v: cls.validate_integer(
                v, 
                param_def.get('range', [None, None])[0] if 'range' in param_def else None,
                param_def.get('range', [None, None])[1] if 'range' in param_def else None
            ),
            'choice': lambda v: cls.validate_choice(v, param_def.get('choices', []))
        }
        
        validator = validators.get(param_type)
        if validator:
            return validator(value)
        
        # Unknown type, just accept it
        return True


class RecipeValidator:
    """Validates recipe YAML structure"""
    
    REQUIRED_META_FIELDS = ['name', 'category', 'description', 'effectiveness']
    REQUIRED_MITRE_FIELDS = ['tactic', 'technique']
    REQUIRED_PARAM_FIELDS = ['name', 'type', 'description', 'required']
    REQUIRED_OUTPUT_FIELDS = ['type']
    
    VALID_EFFECTIVENESS = ['low', 'medium', 'high']
    VALID_OUTPUT_TYPES = ['template', 'command']
    VALID_PREPROCESSING_TYPES = ['command', 'script', 'option', 'shellcode']
    
    @classmethod
    def validate_recipe(cls, recipe_data: Dict[str, Any]) -> bool:
        """Validate complete recipe structure
        
        Args:
            recipe_data: Recipe dictionary from YAML
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate top-level structure
        if 'meta' not in recipe_data:
            raise ValidationError("Recipe missing 'meta' section")
        if 'parameters' not in recipe_data:
            raise ValidationError("Recipe missing 'parameters' section")
        if 'output' not in recipe_data:
            raise ValidationError("Recipe missing 'output' section")
        
        # Validate meta section
        cls._validate_meta(recipe_data['meta'])
        
        # Validate parameters
        cls._validate_parameters(recipe_data['parameters'])
        
        # Validate preprocessing (optional)
        if 'preprocessing' in recipe_data:
            cls._validate_preprocessing(recipe_data['preprocessing'])
        
        # Validate output
        cls._validate_output(recipe_data['output'])
        
        return True
    
    @classmethod
    def _validate_meta(cls, meta: Dict[str, Any]) -> bool:
        """Validate meta section"""
        for field in cls.REQUIRED_META_FIELDS:
            if field not in meta:
                raise ValidationError(f"Meta section missing required field: {field}")
        
        # Validate effectiveness
        if meta['effectiveness'] not in cls.VALID_EFFECTIVENESS:
            raise ValidationError(
                f"Invalid effectiveness '{meta['effectiveness']}'. "
                f"Must be one of: {cls.VALID_EFFECTIVENESS}"
            )
        
        # Validate MITRE (optional but if present must be valid)
        if 'mitre' in meta:
            for field in cls.REQUIRED_MITRE_FIELDS:
                if field not in meta['mitre']:
                    raise ValidationError(f"MITRE section missing required field: {field}")
        
        return True
    
    @classmethod
    def _validate_parameters(cls, parameters: List[Dict[str, Any]]) -> bool:
        """Validate parameters section"""
        if not isinstance(parameters, list):
            raise ValidationError("Parameters must be a list")
        
        param_names = set()
        for param in parameters:
            # Check required fields (except 'required' which may be conditional)
            required_fields = ['name', 'type', 'description']
            for field in required_fields:
                if field not in param:
                    raise ValidationError(f"Parameter missing required field: {field}")
            
            # 'required' field must exist OR 'required_for' field must exist
            if 'required' not in param and 'required_for' not in param:
                raise ValidationError(f"Parameter '{param['name']}' must have either 'required' or 'required_for' field")
            
            # Check for duplicate names
            name = param['name']
            if name in param_names:
                raise ValidationError(f"Duplicate parameter name: {name}")
            param_names.add(name)
            
            # Validate choice parameters have choices
            if param['type'] == 'choice' and 'choices' not in param:
                raise ValidationError(f"Choice parameter '{name}' missing 'choices' field")
        
        return True
    
    @classmethod
    def _validate_preprocessing(cls, preprocessing: List[Dict[str, Any]]) -> bool:
        """Validate preprocessing section"""
        if not isinstance(preprocessing, list):
            raise ValidationError("Preprocessing must be a list")
        
        for i, step in enumerate(preprocessing):
            if 'type' not in step:
                raise ValidationError(f"Preprocessing step {i} missing 'type' field")
            
            step_type = step['type']
            if step_type not in cls.VALID_PREPROCESSING_TYPES:
                raise ValidationError(
                    f"Invalid preprocessing type '{step_type}'. "
                    f"Must be one of: {cls.VALID_PREPROCESSING_TYPES}"
                )
            
            # Validate option type (container for multiple options)
            if step_type == 'option':
                if 'name' not in step:
                    raise ValidationError(f"Option preprocessing step {i} missing 'name' field")
                if 'options' not in step:
                    raise ValidationError(f"Option preprocessing step {i} missing 'options' field")
                if not isinstance(step['options'], list):
                    raise ValidationError(f"Option preprocessing step {i} 'options' must be a list")
                if len(step['options']) == 0:
                    raise ValidationError(f"Option preprocessing step {i} must have at least one option")
                
                # Validate each nested option
                for j, option in enumerate(step['options']):
                    if 'type' not in option:
                        raise ValidationError(f"Option {j} in preprocessing step {i} missing 'type' field")
                    if 'name' not in option:
                        raise ValidationError(f"Option {j} in preprocessing step {i} missing 'name' field")
                    if 'output_var' not in option:
                        raise ValidationError(f"Option {j} in preprocessing step {i} missing 'output_var' field")
                    
                    option_type = option['type']
                    if option_type == 'command' and 'command' not in option:
                        raise ValidationError(f"Command option {j} in step {i} missing 'command' field")
                    if option_type == 'script' and 'script' not in option:
                        raise ValidationError(f"Script option {j} in step {i} missing 'script' field")
            
            # Validate shellcode type
            elif step_type == 'shellcode':
                if 'name' not in step:
                    raise ValidationError(f"Shellcode preprocessing step {i} missing 'name' field")
                if 'output_var' not in step:
                    raise ValidationError(f"Shellcode preprocessing step {i} missing 'output_var' field")
            
            # Validate regular command/script types
            elif step_type in ['command', 'script']:
                if 'output_var' not in step:
                    raise ValidationError(f"Preprocessing step {i} missing 'output_var' field")
                
                if step_type == 'command' and 'command' not in step:
                    raise ValidationError(f"Command preprocessing step {i} missing 'command' field")
                
                if step_type == 'script' and 'script' not in step:
                    raise ValidationError(f"Script preprocessing step {i} missing 'script' field")
        
        return True
    
    @classmethod
    def _validate_output(cls, output: Dict[str, Any]) -> bool:
        """Validate output section"""
        for field in cls.REQUIRED_OUTPUT_FIELDS:
            if field not in output:
                raise ValidationError(f"Output section missing required field: {field}")
        
        output_type = output['type']
        if output_type not in cls.VALID_OUTPUT_TYPES:
            raise ValidationError(
                f"Invalid output type '{output_type}'. "
                f"Must be one of: {cls.VALID_OUTPUT_TYPES}"
            )
        
        if output_type == 'template' and 'template' not in output:
            raise ValidationError("Template output missing 'template' field")
        
        if output_type == 'command' and 'command' not in output:
            raise ValidationError("Command output missing 'command' field")
        
        return True
