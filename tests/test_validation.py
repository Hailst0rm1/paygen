#!/usr/bin/env python3
"""
Test parameter validation functionality

Tests all parameter types supported by Paygen's validator.
"""

import pytest
from src.core.validator import ParameterValidator, ValidationError


class TestIPValidation:
    """Test IP address validation."""
    
    def test_valid_ipv4(self):
        """Test valid IPv4 addresses."""
        validator = ParameterValidator()
        assert validator.validate_ip("192.168.1.1")
        assert validator.validate_ip("10.0.0.1")
        assert validator.validate_ip("127.0.0.1")
    
    def test_valid_ipv6(self):
        """Test valid IPv6 addresses."""
        validator = ParameterValidator()
        assert validator.validate_ip("::1")
        assert validator.validate_ip("2001:db8::1")
        assert validator.validate_ip("fe80::1")
    
    def test_invalid_ip(self):
        """Test invalid IP addresses."""
        validator = ParameterValidator()
        with pytest.raises(ValidationError):
            validator.validate_ip("999.999.999.999")
        with pytest.raises(ValidationError):
            validator.validate_ip("not-an-ip")
        with pytest.raises(ValidationError):
            validator.validate_ip("")


class TestPortValidation:
    """Test port number validation."""
    
    def test_valid_ports(self):
        """Test valid port numbers."""
        validator = ParameterValidator()
        assert validator.validate_port("80")
        assert validator.validate_port("443")
        assert validator.validate_port("8080")
        assert validator.validate_port("65535")
        assert validator.validate_port("1")
    
    def test_invalid_ports(self):
        """Test invalid port numbers."""
        validator = ParameterValidator()
        with pytest.raises(ValidationError):
            validator.validate_port("0")
        with pytest.raises(ValidationError):
            validator.validate_port("65536")
        with pytest.raises(ValidationError):
            validator.validate_port("-1")
        with pytest.raises(ValidationError):
            validator.validate_port("abc")


class TestHexValidation:
    """Test hexadecimal string validation."""
    
    def test_valid_hex(self):
        """Test valid hex strings."""
        validator = ParameterValidator()
        assert validator.validate_hex("deadbeef")
        assert validator.validate_hex("DEADBEEF")
        assert validator.validate_hex("0123456789abcdef")
        assert validator.validate_hex("ABCDEF")
    
    def test_invalid_hex(self):
        """Test invalid hex strings."""
        validator = ParameterValidator()
        with pytest.raises(ValidationError):
            validator.validate_hex("xyz")
        with pytest.raises(ValidationError):
            validator.validate_hex("dead beef")
        with pytest.raises(ValidationError):
            validator.validate_hex("0xdeadbeef")


class TestPathValidation:
    """Test path validation."""
    
    def test_valid_paths(self):
        """Test valid path formats."""
        validator = ParameterValidator()
        assert validator.validate_path("/tmp/test")
        assert validator.validate_path("./output")
        assert validator.validate_path("~/Documents")
        assert validator.validate_path("relative/path")


class TestBoolValidation:
    """Test boolean validation."""
    
    def test_valid_bool(self):
        """Test valid boolean values."""
        validator = ParameterValidator()
        assert validator.validate_bool(True)
        assert validator.validate_bool(False)
        assert validator.validate_bool("true")
        assert validator.validate_bool("false")
        assert validator.validate_bool("yes")
        assert validator.validate_bool("no")
        assert validator.validate_bool("1")
        assert validator.validate_bool("0")
    
    def test_invalid_bool(self):
        """Test invalid boolean values."""
        validator = ParameterValidator()
        with pytest.raises(ValidationError):
            validator.validate_bool("maybe")
        with pytest.raises(ValidationError):
            validator.validate_bool("2")


class TestChoiceValidation:
    """Test choice validation."""
    
    def test_valid_choice(self):
        """Test valid choices."""
        validator = ParameterValidator()
        choices = ["exe", "dll", "raw"]
        assert validator.validate_choice("exe", choices)
        assert validator.validate_choice("dll", choices)
        assert validator.validate_choice("raw", choices)
    
    def test_invalid_choice(self):
        """Test invalid choices."""
        validator = ParameterValidator()
        choices = ["exe", "dll", "raw"]
        with pytest.raises(ValidationError):
            validator.validate_choice("elf", choices)
        with pytest.raises(ValidationError):
            validator.validate_choice("", choices)


class TestIntegerValidation:
    """Test integer validation."""
    
    def test_valid_integer(self):
        """Test valid integers."""
        validator = ParameterValidator()
        assert validator.validate_integer("42")
        assert validator.validate_integer(42)
        assert validator.validate_integer("-10")
    
    def test_integer_with_range(self):
        """Test integer range validation."""
        validator = ParameterValidator()
        assert validator.validate_integer("5", range_min=1, range_max=10)
        assert validator.validate_integer(1, range_min=1, range_max=10)
        assert validator.validate_integer(10, range_min=1, range_max=10)
    
    def test_integer_out_of_range(self):
        """Test integer out of range."""
        validator = ParameterValidator()
        with pytest.raises(ValidationError):
            validator.validate_integer("0", range_min=1, range_max=10)
        with pytest.raises(ValidationError):
            validator.validate_integer("11", range_min=1, range_max=10)
    
    def test_invalid_integer(self):
        """Test invalid integers."""
        validator = ParameterValidator()
        with pytest.raises(ValidationError):
            validator.validate_integer("abc")
        with pytest.raises(ValidationError):
            validator.validate_integer("1.5")


class TestPlatformValidation:
    """Test platform validation in recipe metadata."""
    
    def test_valid_platforms(self):
        """Test valid platform values."""
        from src.core.validator import RecipeValidator
        
        # Recipe with valid Windows platform
        recipe_data = {
            'meta': {
                'name': 'Test Recipe',
                'category': 'Test',
                'description': 'Test description',
                'effectiveness': 'high',
                'platform': 'Windows'
            },
            'parameters': [],
            'output': {
                'type': 'command',
                'command': 'echo test'
            }
        }
        assert RecipeValidator.validate_recipe(recipe_data)
        
        # Test other valid platforms
        recipe_data['meta']['platform'] = 'Linux'
        assert RecipeValidator.validate_recipe(recipe_data)
        
        recipe_data['meta']['platform'] = 'macOS'
        assert RecipeValidator.validate_recipe(recipe_data)
    
    def test_platform_is_optional(self):
        """Test that platform field is optional."""
        from src.core.validator import RecipeValidator
        
        # Recipe without platform field should be valid
        recipe_data = {
            'meta': {
                'name': 'Test Recipe',
                'category': 'Test',
                'description': 'Test description',
                'effectiveness': 'high'
            },
            'parameters': [],
            'output': {
                'type': 'command',
                'command': 'echo test'
            }
        }
        assert RecipeValidator.validate_recipe(recipe_data)
    
    def test_invalid_platform(self):
        """Test invalid platform values."""
        from src.core.validator import RecipeValidator
        
        recipe_data = {
            'meta': {
                'name': 'Test Recipe',
                'category': 'Test',
                'description': 'Test description',
                'effectiveness': 'high',
                'platform': 'InvalidPlatform'
            },
            'parameters': [],
            'output': {
                'type': 'command',
                'command': 'echo test'
            }
        }
        with pytest.raises(ValidationError):
            RecipeValidator.validate_recipe(recipe_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
