#!/usr/bin/env python3
"""
Recipe validation and workflow test.

Tests that recipe YAML files are valid and that the preprocessing
workflows produce the expected C# code output.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.config import ConfigManager
from src.core.recipe_loader import RecipeLoader
from src.core.validator import RecipeValidator
from src.core.preprocessor import PreprocessingOrchestrator
import base64


def test_recipe_loading():
    """Test that recipe YAML files can be loaded and validated."""
    print("=" * 70)
    print("TEST 1: Recipe Loading & Validation")
    print("=" * 70)
    
    config = ConfigManager()
    loader = RecipeLoader(config)
    
    # Try to load all recipes
    recipes = loader.load_all_recipes()
    
    print(f"✓ Loaded {len(recipes)} recipe(s)")
    
    for recipe in recipes:
        print(f"\n  Recipe: {recipe.name}")
        print(f"  Category: {recipe.category}")
        print(f"  Effectiveness: {recipe.effectiveness}")
        print(f"  Parameters: {len(recipe.parameters)}")
        print(f"  Preprocessing steps: {len(recipe.preprocessing)}")
        print(f"  Output type: {recipe.output.get('type')}")
    
    print()
    return len(recipes) > 0, recipes


def test_aes_recipe_workflow():
    """Test AES recipe preprocessing workflow (without msfvenom)."""
    print("=" * 70)
    print("TEST 2: AES Recipe Workflow Simulation")
    print("=" * 70)
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    # Simulate msfvenom output with test shellcode
    test_shellcode = bytes([
        0xfc, 0x48, 0x83, 0xe4, 0xf0, 0xe8, 0xcc, 0x00, 0x00, 0x00, 0x41, 0x51, 0x41, 0x50, 0x52,
        0x51, 0x56, 0x48, 0x31, 0xd2, 0x65, 0x48, 0x8b, 0x52, 0x60, 0x48, 0x8b, 0x52, 0x18, 0x48
    ])
    
    # Simulate the preprocessing steps from the AES recipe
    # (skipping the msfvenom command step)
    preprocessing_steps = [
        # Step 2: Base64 encode the shellcode
        {
            'type': 'script',
            'name': 'base64_encode_shellcode',
            'script': 'base64_encode.py',
            'args': {
                'data': test_shellcode.decode('latin-1'),  # Simulate raw bytes
                'format': 'string'
            },
            'output_var': 'shellcode_b64'
        },
        # Step 3: AES encrypt
        {
            'type': 'script',
            'name': 'aes_encryption',
            'script': 'aes_encrypt.py',
            'args': {
                'data': '{{ shellcode_b64 }}',
                'key': 'auto',
                'iv': 'auto'
            },
            'output_var': 'aes_result'
        },
        # Step 4: Format encrypted payload as C#
        {
            'type': 'script',
            'name': 'format_encrypted_payload',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ aes_result.encrypted }}',
                'var_name': 'encryptedShellcode',
                'bytes_per_line': 15
            },
            'output_var': 'csharp_shellcode'
        },
        # Step 5: Format AES key as C#
        {
            'type': 'script',
            'name': 'format_aes_key',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ aes_result.key }}',
                'var_name': 'aesKey',
                'bytes_per_line': 16
            },
            'output_var': 'csharp_key'
        },
        # Step 6: Format AES IV as C#
        {
            'type': 'script',
            'name': 'format_aes_iv',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ aes_result.iv }}',
                'var_name': 'aesIV',
                'bytes_per_line': 16
            },
            'output_var': 'csharp_iv'
        }
    ]
    
    parameters = {}
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters)
        
        print("✓ AES recipe workflow completed successfully\n")
        
        # Verify all expected outputs are present
        required_outputs = ['shellcode_b64', 'aes_result', 'csharp_shellcode', 'csharp_key', 'csharp_iv']
        for output in required_outputs:
            if output not in result:
                print(f"  ✗ Missing output: {output}")
                return False
        
        print("  ✓ All preprocessing outputs generated")
        
        # Check C# code format
        csharp_key = result['csharp_key']
        csharp_iv = result['csharp_iv']
        csharp_shellcode = result['csharp_shellcode']
        
        # Validate C# syntax
        if 'byte[] aesKey = new byte[32]' in csharp_key:
            print("  ✓ AES key formatted correctly (32 bytes)")
        else:
            print("  ✗ AES key format incorrect")
            return False
        
        if 'byte[] aesIV = new byte[16]' in csharp_iv:
            print("  ✓ AES IV formatted correctly (16 bytes)")
        else:
            print("  ✗ AES IV format incorrect")
            return False
        
        if 'byte[] encryptedShellcode = new byte[' in csharp_shellcode:
            print("  ✓ Encrypted shellcode formatted correctly")
        else:
            print("  ✗ Encrypted shellcode format incorrect")
            return False
        
        print("\n  Preview of generated C# code:")
        print("  " + "-" * 66)
        print("  " + csharp_key.split('\n')[0])
        print("  " + csharp_key.split('\n')[1][:68] + "...")
        print("  " + "-" * 66)
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ AES recipe workflow failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_xor_recipe_workflow():
    """Test XOR recipe preprocessing workflow."""
    print("=" * 70)
    print("TEST 3: XOR Recipe Workflow Simulation")
    print("=" * 70)
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    # Test shellcode
    test_shellcode = bytes([
        0xfc, 0x48, 0x83, 0xe4, 0xf0, 0xe8, 0xcc, 0x00, 0x00, 0x00, 0x41, 0x51, 0x41, 0x50, 0x52,
        0x51, 0x56, 0x48, 0x31, 0xd2
    ])
    
    # Simulate XOR recipe preprocessing (without msfvenom)
    preprocessing_steps = [
        # Step 2: Base64 encode
        {
            'type': 'script',
            'name': 'encode_b64',
            'script': 'base64_encode.py',
            'args': {
                'data': test_shellcode.decode('latin-1')
            },
            'output_var': 'shellcode_b64'
        },
        # Step 3: XOR encrypt with key 0xfa
        {
            'type': 'script',
            'name': 'xor_encryption',
            'script': 'xor_encrypt.py',
            'args': {
                'data': '{{ shellcode_b64 }}',
                'key': 'fa'
            },
            'output_var': 'xor_result'
        },
        # Step 4: Format as C# byte array
        {
            'type': 'script',
            'name': 'format_payload',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ xor_result.encrypted }}',
                'var_name': 'buf',
                'bytes_per_line': 15
            },
            'output_var': 'csharp_payload'
        }
    ]
    
    parameters = {
        'xor_key': 'fa'
    }
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters)
        
        print("✓ XOR recipe workflow completed successfully\n")
        
        # Verify outputs
        required_outputs = ['shellcode_b64', 'xor_result', 'csharp_payload']
        for output in required_outputs:
            if output not in result:
                print(f"  ✗ Missing output: {output}")
                return False
        
        print("  ✓ All preprocessing outputs generated")
        
        # Check C# code format
        csharp_payload = result['csharp_payload']
        
        if 'byte[] buf = new byte[' in csharp_payload:
            print("  ✓ XOR payload formatted correctly")
        else:
            print("  ✗ XOR payload format incorrect")
            return False
        
        # Verify XOR key is correct
        xor_result = result['xor_result']
        if isinstance(xor_result, dict) and xor_result.get('key_hex') == 'fa':
            print("  ✓ XOR key is 0xfa (as expected)")
        else:
            print("  ✗ XOR key incorrect")
            return False
        
        print("\n  Preview of generated C# code:")
        print("  " + "-" * 66)
        print("  " + csharp_payload.split('\n')[0])
        print("  " + csharp_payload.split('\n')[1][:68] + "...")
        print("  " + "-" * 66)
        print()
        
        # Test decoding
        print("  Testing XOR decode logic:")
        encrypted_b64 = xor_result['encrypted']
        encrypted_bytes = base64.b64decode(encrypted_b64)
        
        # Decode with XOR
        decoded = bytes(b ^ 0xfa for b in encrypted_bytes)
        
        if decoded == test_shellcode:
            print("  ✓ XOR decode verified - matches original shellcode!")
        else:
            print("  ✗ XOR decode failed - doesn't match original")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ XOR recipe workflow failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_template_rendering():
    """Test that templates can be read and have correct placeholders."""
    print("=" * 70)
    print("TEST 4: Template File Validation")
    print("=" * 70)
    
    config = ConfigManager()
    
    templates = [
        ('AES Injector', Path(config.payloads_dir) / 'process_injection' / 'aes_injector.cs'),
        ('XOR Injector', Path(config.payloads_dir) / 'shellcode_injection' / 'xor_injector.cs')
    ]
    
    all_valid = True
    
    for name, template_path in templates:
        if not template_path.exists():
            print(f"  ✗ {name} template not found: {template_path}")
            all_valid = False
            continue
        
        content = template_path.read_text()
        
        # Check for Jinja2 placeholders
        if name == 'AES Injector':
            required_placeholders = ['{{ csharp_key }}', '{{ csharp_iv }}', '{{ csharp_shellcode }}']
        else:  # XOR Injector
            required_placeholders = ['{{ csharp_payload }}']
        
        missing = []
        for placeholder in required_placeholders:
            if placeholder not in content:
                missing.append(placeholder)
        
        if missing:
            print(f"  ✗ {name}: Missing placeholders: {missing}")
            all_valid = False
        else:
            print(f"  ✓ {name}: All placeholders present")
    
    print()
    return all_valid


def main():
    """Run all recipe tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "PAYGEN RECIPE VALIDATION TESTS" + " " * 20 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    results = []
    
    # Test 1: Load recipes
    success, recipes = test_recipe_loading()
    results.append(("Recipe Loading", success))
    
    # Test 2: AES workflow
    results.append(("AES Recipe Workflow", test_aes_recipe_workflow()))
    
    # Test 3: XOR workflow
    results.append(("XOR Recipe Workflow", test_xor_recipe_workflow()))
    
    # Test 4: Template validation
    results.append(("Template Validation", test_template_rendering()))
    
    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 All recipe tests passed! Recipes are ready to use.")
        print("\nNext steps:")
        print("  1. Phase 3: Build the TUI to use these recipes")
        print("  2. Phase 4: Implement payload builder with compilation")
        print("  3. Test with real msfvenom on a Windows VM")
        return 0
    else:
        print("❌ Some recipe tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
