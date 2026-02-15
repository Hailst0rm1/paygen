L#!/usr/bin/env python3
"""
Standalone Manual Recipe Format Tester

Usage:
    python test_recipe.py <recipe_file.yaml>

This script validates a recipe file and shows detailed information about its structure.
No external dependencies required (except PyYAML).
"""

import sys
import re
import ipaddress
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class RecipeValidator:
    """Validates recipe YAML structure"""
    
    # Valid top-level fields in a recipe
    VALID_TOP_LEVEL_FIELDS = ['meta', 'parameters', 'preprocessing', 'output']
    
    # Valid fields in each section
    VALID_META_FIELDS = ['name', 'category', 'description', 'effectiveness', 'platform', 'mitre', 'artifacts']
    VALID_MITRE_FIELDS = ['tactic', 'technique']
    VALID_PARAMETER_FIELDS = ['name', 'type', 'description', 'required', 'required_for', 'default', 'choices', 'range']
    VALID_PREPROCESSING_FIELDS = ['type', 'name', 'output_var', 'command', 'script', 'options']
    VALID_OUTPUT_FIELDS = ['type', 'template', 'command', 'compile', 'launch_instructions', 'filename']
    VALID_COMPILE_FIELDS = ['enable', 'compiler', 'command']
    
    REQUIRED_FIELDS = ['meta', 'parameters', 'output']
    VALID_OUTPUT_TYPES = ['template', 'command']
    VALID_PARAM_TYPES = ['string', 'int', 'ip', 'port', 'path', 'hex', 'choice']
    VALID_PREPROCESSING_TYPES = ['script', 'option', 'shellcode', 'command']
    VALID_EFFECTIVENESS = ['low', 'medium', 'high']
    VALID_PLATFORMS = ['Windows', 'Linux', 'macOS']
    
    @classmethod
    def validate_recipe(cls, recipe_data: Dict[str, Any]) -> bool:
        """Validate complete recipe structure
        
        Args:
            recipe_data: Recipe dictionary from YAML
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails with all collected errors
        """
        errors = []
        
        # Check for unknown top-level fields
        for field in recipe_data.keys():
            if field not in cls.VALID_TOP_LEVEL_FIELDS:
                # Check if it's a common misplaced field
                if field in ['launch_instructions', 'compile', 'filename', 'template', 'command']:
                    errors.append(
                        f"Field '{field}' is misplaced. It should be under the 'output' section, not at top level"
                    )
                else:
                    errors.append(
                        f"Unknown top-level field '{field}'. Valid fields are: {', '.join(cls.VALID_TOP_LEVEL_FIELDS)}"
                    )
        
        # Check required top-level fields
        missing = [f for f in cls.REQUIRED_FIELDS if f not in recipe_data]
        if missing:
            errors.append(f"Missing required top-level fields: {', '.join(missing)}")
            # If critical fields are missing, raise immediately
            if errors:
                raise ValidationError('\n  • '.join(['Found validation errors:'] + errors))
        
        # Validate each section and collect errors
        errors.extend(cls._validate_meta(recipe_data.get('meta', {})))
        errors.extend(cls._validate_parameters(recipe_data.get('parameters', [])))
        
        if 'preprocessing' in recipe_data:
            errors.extend(cls._validate_preprocessing(recipe_data['preprocessing']))
        
        errors.extend(cls._validate_output(recipe_data.get('output', {})))
        
        # Raise all collected errors
        if errors:
            raise ValidationError('\n  • '.join(['Found validation errors:'] + errors))
        
        return True
    
    @classmethod
    def _validate_meta(cls, meta: Dict[str, Any]) -> List[str]:
        """Validate meta section - returns list of errors"""
        errors = []
        
        if not isinstance(meta, dict):
            errors.append("'meta' must be a dictionary")
            return errors
        
        # Check for unknown fields
        for field in meta.keys():
            if field not in cls.VALID_META_FIELDS:
                errors.append(
                    f"meta: Unknown field '{field}'. Valid fields are: {', '.join(cls.VALID_META_FIELDS)}"
                )
        
        required = ['name', 'category', 'description', 'effectiveness']
        missing = [f for f in required if f not in meta]
        if missing:
            errors.append(f"meta: Missing required fields: {', '.join(missing)}")
        
        if 'name' in meta and (not meta['name'] or not isinstance(meta['name'], str)):
            errors.append("meta.name must be a non-empty string")
        
        if 'description' in meta and (not meta['description'] or not isinstance(meta['description'], str)):
            errors.append("meta.description must be a non-empty string")
        
        # Validate effectiveness
        if 'effectiveness' in meta and meta['effectiveness'] not in cls.VALID_EFFECTIVENESS:
            errors.append(
                f"meta.effectiveness: Invalid value '{meta['effectiveness']}'. "
                f"Must be one of: {', '.join(cls.VALID_EFFECTIVENESS)}"
            )
        
        # Validate platform if present
        if 'platform' in meta and meta['platform'] not in cls.VALID_PLATFORMS:
            errors.append(
                f"meta.platform: Invalid value '{meta['platform']}'. "
                f"Must be one of: {', '.join(cls.VALID_PLATFORMS)}"
            )
        
        # Validate MITRE section if present
        if 'mitre' in meta:
            if not isinstance(meta['mitre'], dict):
                errors.append("meta.mitre must be a dictionary")
            else:
                # Check for unknown MITRE fields
                for field in meta['mitre'].keys():
                    if field not in cls.VALID_MITRE_FIELDS:
                        errors.append(
                            f"meta.mitre: Unknown field '{field}'. Valid fields are: {', '.join(cls.VALID_MITRE_FIELDS)}"
                        )
                
                required_mitre = ['tactic', 'technique']
                missing_mitre = [f for f in required_mitre if f not in meta['mitre']]
                if missing_mitre:
                    errors.append(f"meta.mitre: Missing required fields: {', '.join(missing_mitre)}")
        
        return errors
    
    @classmethod
    def _validate_parameters(cls, parameters: List[Dict[str, Any]]) -> List[str]:
        """Validate parameters section - returns list of errors"""
        errors = []
        
        if not isinstance(parameters, list):
            errors.append("'parameters' must be a list")
            return errors
        
        if not parameters:
            errors.append("At least one parameter must be defined")
            return errors
        
        param_names = set()
        for i, param in enumerate(parameters):
            if not isinstance(param, dict):
                errors.append(f"Parameter {i}: Must be a dictionary")
                continue
            
            # Check for unknown fields
            for field in param.keys():
                if field not in cls.VALID_PARAMETER_FIELDS:
                    errors.append(
                        f"Parameter {i}: Unknown field '{field}'. Valid fields are: {', '.join(cls.VALID_PARAMETER_FIELDS)}"
                    )
            
            if 'name' not in param:
                errors.append(f"Parameter {i}: Missing 'name' field")
                continue
            
            name = param['name']
            if name in param_names:
                errors.append(f"Duplicate parameter name: '{name}'")
            param_names.add(name)
            
            if 'type' not in param:
                errors.append(f"Parameter '{name}': Missing 'type' field")
                continue
            
            param_type = param['type']
            if param_type not in cls.VALID_PARAM_TYPES:
                errors.append(
                    f"Parameter '{name}': Invalid type '{param_type}'. "
                    f"Must be one of: {', '.join(cls.VALID_PARAM_TYPES)}"
                )
            
            # Validate description is present
            if 'description' not in param:
                errors.append(f"Parameter '{name}': Missing 'description' field")
            
            # Validate required field exists (or required_for)
            if 'required' not in param and 'required_for' not in param:
                errors.append(f"Parameter '{name}': Must have either 'required' or 'required_for' field")
            
            # Validate choice type has options
            if param_type == 'choice' and 'choices' not in param:
                errors.append(f"Parameter '{name}': 'choice' type requires 'choices' field")
        
        return errors
    
    @classmethod
    def _validate_preprocessing(cls, preprocessing: List[Dict[str, Any]]) -> List[str]:
        """Validate preprocessing section
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not isinstance(preprocessing, list):
            return ["'preprocessing' must be a list"]
        
        for i, step in enumerate(preprocessing):
            if not isinstance(step, dict):
                errors.append(f"Preprocessing step {i}: Must be a dictionary")
                continue
            
            # Check for unknown fields
            for field in step.keys():
                if field not in cls.VALID_PREPROCESSING_FIELDS:
                    errors.append(
                        f"Preprocessing step {i}: Unknown field '{field}'. Valid fields are: {', '.join(cls.VALID_PREPROCESSING_FIELDS)}"
                    )
            
            if 'type' not in step:
                errors.append(f"Preprocessing step {i}: Missing 'type' field")
                continue
            
            step_type = step['type']
            if step_type not in cls.VALID_PREPROCESSING_TYPES:
                errors.append(
                    f"Preprocessing step {i}: Invalid type '{step_type}'. "
                    f"Must be one of: {', '.join(cls.VALID_PREPROCESSING_TYPES)}"
                )
                continue
            
            # Validate script type
            if step_type == 'script':
                if 'name' not in step:
                    errors.append(f"Preprocessing step {i}: 'script' type requires 'name' field")
                if 'script' not in step:
                    errors.append(f"Preprocessing step {i}: 'script' type requires 'script' field")
                if 'output_var' not in step:
                    errors.append(f"Preprocessing step {i}: 'script' type requires 'output_var' field")
            
            # Validate command type
            elif step_type == 'command':
                if 'command' not in step:
                    errors.append(f"Preprocessing step {i}: 'command' type requires 'command' field")
                if 'output_var' not in step:
                    errors.append(f"Preprocessing step {i}: 'command' type requires 'output_var' field")
            
            # Validate option type
            elif step_type == 'option':
                if 'name' not in step:
                    errors.append(f"Preprocessing step {i}: 'option' type requires 'name' field")
                if 'options' not in step or not isinstance(step['options'], list):
                    errors.append(f"Preprocessing step {i}: 'option' type requires 'options' list")
                elif len(step['options']) == 0:
                    errors.append(f"Preprocessing step {i}: must have at least one option")
            
            # Validate shellcode type
            elif step_type == 'shellcode':
                if 'name' not in step:
                    errors.append(f"Preprocessing step {i}: 'shellcode' type requires 'name' field")
                if 'output_var' not in step:
                    errors.append(f"Preprocessing step {i}: 'shellcode' type requires 'output_var' field")
        
        return errors
    
    @classmethod
    def _validate_output(cls, output: Dict[str, Any]) -> List[str]:
        """Validate output section
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not isinstance(output, dict):
            return ["'output' must be a dictionary"]
        
        # Check for unknown fields in output
        for field in output.keys():
            if field not in cls.VALID_OUTPUT_FIELDS:
                errors.append(
                    f"output: Unknown field '{field}'. Valid fields are: {', '.join(cls.VALID_OUTPUT_FIELDS)}"
                )
        
        if 'type' not in output:
            errors.append("output: Missing 'type' field")
            return errors
        
        output_type = output['type']
        if output_type not in cls.VALID_OUTPUT_TYPES:
            errors.append(
                f"output: Invalid type '{output_type}'. "
                f"Must be one of: {', '.join(cls.VALID_OUTPUT_TYPES)}"
            )
        
        # Template type requires template field
        if output_type == 'template':
            if 'template' not in output:
                errors.append("output: 'template' type requires 'template' field")
        
        # Command type requires command field
        elif output_type == 'command':
            if 'command' not in output:
                errors.append("output: 'command' type requires 'command' field")
        
        # Validate compile section if present
        if 'compile' in output:
            compile_cfg = output['compile']
            if not isinstance(compile_cfg, dict):
                errors.append("output.compile must be a dictionary")
            else:
                # Check for unknown fields in compile section
                for field in compile_cfg.keys():
                    if field not in cls.VALID_COMPILE_FIELDS:
                        errors.append(
                            f"output.compile: Unknown field '{field}'. Valid fields are: {', '.join(cls.VALID_COMPILE_FIELDS)}"
                        )
                
                # Only require command if compilation is enabled (default is enabled if not specified)
                compile_enabled = compile_cfg.get('enable', True)
                if compile_enabled and 'command' not in compile_cfg:
                    errors.append("output.compile: Missing 'command' field when compile.enable is true")
        
        return errors


def test_recipe_format(recipe_path: str):
    """Test and validate a recipe file format
    
    Args:
        recipe_path: Path to the recipe YAML file
    """
    recipe_file = Path(recipe_path)
    
    print("="*70)
    print(f"Testing Recipe: {recipe_file.name}")
    print("="*70)
    
    # Check if file exists
    if not recipe_file.exists():
        print(f"❌ ERROR: File not found: {recipe_path}")
        return False
    
    try:
        # Load the YAML file
        print("\n📄 Loading YAML file...")
        with open(recipe_file, 'r') as f:
            recipe_data = yaml.safe_load(f)
        print("✓ YAML file loaded successfully")
        
        # Display basic structure
        print(f"\n📋 Recipe Structure:")
        print(f"   - Name: {recipe_data.get('meta', {}).get('name', 'N/A')}")
        print(f"   - Description: {recipe_data.get('meta', {}).get('description', 'N/A')}")
        print(f"   - Language: {recipe_data.get('meta', {}).get('language', 'N/A')}")
        print(f"   - Parameters: {len(recipe_data.get('parameters', []))} defined")
        print(f"   - Preprocessing steps: {len(recipe_data.get('preprocessing', []))}")
        print(f"   - Output: {recipe_data.get('output', {}).get('type', 'N/A')}")
        
        # Validate the recipe structure
        print("\n🔍 Validating recipe structure...")
        RecipeValidator.validate_recipe(recipe_data)
        print("✓ Recipe structure is valid!")
        
        # Show parameters
        if recipe_data.get('parameters'):
            print(f"\n📝 Parameters ({len(recipe_data['parameters'])}):")
            for param in recipe_data['parameters']:
                name = param.get('name', 'unnamed')
                param_type = param.get('type', 'unknown')
                required = '(required)' if param.get('required', True) else '(optional)'
                default = f" [default: {param.get('default')}]" if 'default' in param else ''
                print(f"   - {name}: {param_type} {required}{default}")
        
        # Show preprocessing steps
        if recipe_data.get('preprocessing'):
            print(f"\n⚙️  Preprocessing Steps ({len(recipe_data['preprocessing'])}):")
            for i, step in enumerate(recipe_data['preprocessing'], 1):
                step_type = step.get('type', 'unknown')
                step_name = step.get('name', f'step_{i}')
                print(f"   {i}. {step_name} ({step_type})")
        
        # Show output configuration
        print(f"\n📤 Output Configuration:")
        output = recipe_data.get('output', {})
        print(f"   - Type: {output.get('type', 'N/A')}")
        if output.get('type') == 'template':
            template_path = output.get('template', 'N/A')
            print(f"   - Template: {template_path}")
        elif output.get('type') == 'command':
            command = output.get('command', 'N/A')
            print(f"   - Command: {command[:60]}...")
        
        if output.get('compile'):
            compile_cfg = output['compile']
            print(f"   - Compilation:")
            print(f"     • Compiler: {compile_cfg.get('compiler', 'N/A')}")
            command_preview = str(compile_cfg.get('command', 'N/A'))[:60]
            print(f"     • Command: {command_preview}...")
        
        print("\n" + "="*70)
        print("✅ RECIPE FORMAT IS VALID!")
        print("="*70)
        return True
        
    except ValidationError as e:
        print(f"\n❌ VALIDATION ERROR:")
        print(f"   {str(e)}")
        return False
        
    except yaml.YAMLError as e:
        print(f"\n❌ YAML PARSING ERROR:")
        print(f"   {str(e)}")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python test_recipe.py <recipe_file.yaml>")
        print("\nExamples:")
        print("  python test_recipe.py recipes/basic_msfvenom_payload.yaml")
        print("  python test_recipe.py recipes/shellcode_example.yaml")
        print("  python test_recipe.py my_custom_recipe.yaml")
        sys.exit(1)
    
    recipe_path = sys.argv[1]
    success = test_recipe_format(recipe_path)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
