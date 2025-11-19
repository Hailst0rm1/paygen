"""
Parameter Validator - Validate user input for recipe parameters

Supports validation for: ip, port, string, file, path, hex, bool, choice, integer
"""

import ipaddress
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class ValidationError(Exception):
    """Exception raised when parameter validation fails."""
    pass


class ParameterValidator:
    """Validates recipe parameters based on their type and constraints."""
    
    @staticmethod
    def validate_parameter(param_def: Dict, value: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate a parameter value against its definition.
        
        Args:
            param_def: Parameter definition dictionary from recipe
            value: Value to validate
        
        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is None
        """
        param_name = param_def.get('name', 'unknown')
        param_type = param_def.get('type', 'string')
        required = param_def.get('required', False)
        
        # Check if value is provided for required parameter
        if required and (value is None or value == ''):
            return False, f"Parameter '{param_name}' is required"
        
        # If not required and no value provided, it's valid
        if not required and (value is None or value == ''):
            return True, None
        
        # Validate based on type
        validator_method = getattr(
            ParameterValidator,
            f'_validate_{param_type}',
            ParameterValidator._validate_string
        )
        
        try:
            validator_method(param_def, value)
            return True, None
        except ValidationError as e:
            return False, str(e)
    
    @staticmethod
    def _validate_ip(param_def: Dict, value: str) -> None:
        """Validate IPv4 address."""
        param_name = param_def.get('name', 'ip')
        validation = param_def.get('validation', 'ipv4')
        
        try:
            if validation == 'ipv4':
                ipaddress.IPv4Address(value)
            elif validation == 'ipv6':
                ipaddress.IPv6Address(value)
            else:
                # Accept both IPv4 and IPv6
                ipaddress.ip_address(value)
        except ValueError:
            raise ValidationError(f"Invalid IP address for '{param_name}': {value}")
    
    @staticmethod
    def _validate_port(param_def: Dict, value: Any) -> None:
        """Validate port number (1-65535)."""
        param_name = param_def.get('name', 'port')
        
        try:
            port = int(value)
            if not (1 <= port <= 65535):
                raise ValidationError(
                    f"Port '{param_name}' must be between 1 and 65535, got {port}"
                )
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid port number for '{param_name}': {value}")
    
    @staticmethod
    def _validate_string(param_def: Dict, value: str) -> None:
        """Validate string parameter."""
        # Strings are generally always valid, but we can add constraints
        if not isinstance(value, str):
            param_name = param_def.get('name', 'string')
            raise ValidationError(f"Parameter '{param_name}' must be a string")
    
    @staticmethod
    def _validate_file(param_def: Dict, value: str) -> None:
        """Validate file path exists."""
        param_name = param_def.get('name', 'file')
        file_path = Path(value)
        
        if not file_path.exists():
            raise ValidationError(f"File not found for '{param_name}': {value}")
        
        if not file_path.is_file():
            raise ValidationError(f"Path is not a file for '{param_name}': {value}")
    
    @staticmethod
    def _validate_path(param_def: Dict, value: str) -> None:
        """Validate directory path."""
        param_name = param_def.get('name', 'path')
        dir_path = Path(value)
        
        # Create directory if it doesn't exist
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise ValidationError(
                    f"Cannot create directory for '{param_name}': {value} ({e})"
                )
        
        if not dir_path.is_dir():
            raise ValidationError(f"Path is not a directory for '{param_name}': {value}")
    
    @staticmethod
    def _validate_hex(param_def: Dict, value: str) -> None:
        """Validate hexadecimal string."""
        param_name = param_def.get('name', 'hex')
        
        # Remove common hex prefixes if present
        cleaned_value = value.strip().lower()
        if cleaned_value.startswith('0x'):
            cleaned_value = cleaned_value[2:]
        
        # Check if valid hex
        if not re.match(r'^[0-9a-f]+$', cleaned_value):
            raise ValidationError(
                f"Invalid hexadecimal value for '{param_name}': {value}"
            )
    
    @staticmethod
    def _validate_bool(param_def: Dict, value: Any) -> None:
        """Validate boolean parameter."""
        param_name = param_def.get('name', 'bool')
        
        if isinstance(value, bool):
            return
        
        # Accept common boolean representations
        if isinstance(value, str):
            if value.lower() in ('true', 'yes', '1', 'on'):
                return
            if value.lower() in ('false', 'no', '0', 'off'):
                return
        
        raise ValidationError(
            f"Invalid boolean value for '{param_name}': {value} "
            "(expected: true/false, yes/no, 1/0, on/off)"
        )
    
    @staticmethod
    def _validate_choice(param_def: Dict, value: str) -> None:
        """Validate value is one of allowed choices."""
        param_name = param_def.get('name', 'choice')
        choices = param_def.get('choices', [])
        
        if not choices:
            raise ValidationError(f"No choices defined for '{param_name}'")
        
        if value not in choices:
            raise ValidationError(
                f"Invalid choice for '{param_name}': {value}. "
                f"Valid options: {', '.join(choices)}"
            )
    
    @staticmethod
    def _validate_integer(param_def: Dict, value: Any) -> None:
        """Validate integer parameter with optional range."""
        param_name = param_def.get('name', 'integer')
        range_spec = param_def.get('range')
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid integer for '{param_name}': {value}")
        
        # Check range if specified
        if range_spec and len(range_spec) == 2:
            min_val, max_val = range_spec
            if not (min_val <= int_value <= max_val):
                raise ValidationError(
                    f"Integer '{param_name}' must be between {min_val} and {max_val}, "
                    f"got {int_value}"
                )
    
    @staticmethod
    def normalize_value(param_def: Dict, value: Any) -> Any:
        """
        Normalize a parameter value to its proper type.
        
        Args:
            param_def: Parameter definition
            value: Raw value
        
        Returns:
            Normalized value
        """
        param_type = param_def.get('type', 'string')
        
        if value is None or value == '':
            # Use default if available
            return param_def.get('default')
        
        # Type conversions
        if param_type == 'bool':
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 'on')
            return bool(value)
        
        elif param_type == 'integer':
            return int(value)
        
        elif param_type == 'port':
            return int(value)
        
        elif param_type == 'hex':
            # Remove 0x prefix if present
            if isinstance(value, str) and value.lower().startswith('0x'):
                return value[2:]
            return value
        
        elif param_type == 'path':
            # Convert to absolute path
            return str(Path(value).resolve())
        
        elif param_type == 'file':
            # Convert to absolute path
            return str(Path(value).resolve())
        
        # Default: return as string
        return str(value)
    
    @staticmethod
    def validate_all_parameters(param_defs: List[Dict], values: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate all parameters and return errors.
        
        Args:
            param_defs: List of parameter definitions
            values: Dictionary of parameter values
        
        Returns:
            Dictionary mapping parameter names to error messages
            Empty dict if all valid
        """
        errors = {}
        
        for param_def in param_defs:
            param_name = param_def.get('name')
            value = values.get(param_name)
            
            is_valid, error = ParameterValidator.validate_parameter(param_def, value)
            if not is_valid:
                errors[param_name] = error
        
        return errors
