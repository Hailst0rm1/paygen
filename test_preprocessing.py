#!/usr/bin/env python3
"""
Test script for the preprocessing system.

Tests command execution, script execution, and output variable management.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.config import ConfigManager
from src.core.preprocessor import PreprocessingOrchestrator, PreprocessingError


def test_command_execution():
    """Test command-based preprocessing."""
    print("=" * 60)
    print("TEST 1: Command Execution")
    print("=" * 60)
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    # Test simple echo command
    preprocessing_steps = [
        {
            'type': 'command',
            'name': 'echo_test',
            'command': 'echo "Hello from command"',
            'output_var': 'echo_result'
        }
    ]
    
    parameters = {}
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters)
        print(f"✓ Command executed successfully")
        print(f"  Output: {result.get('echo_result')}")
        print()
        return True
    except PreprocessingError as e:
        print(f"✗ Command execution failed: {e}")
        print()
        return False


def test_script_execution():
    """Test script-based preprocessing."""
    print("=" * 60)
    print("TEST 2: Script Execution (XOR Encryption)")
    print("=" * 60)
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    # Test XOR encryption script
    test_data = "Hello, World!"
    
    preprocessing_steps = [
        {
            'type': 'script',
            'name': 'xor_encryption',
            'script': 'xor_encrypt.py',
            'args': {
                'shellcode': test_data,
                'key': 'auto'
            },
            'output_var': 'encrypted_data'
        }
    ]
    
    parameters = {}
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters)
        print(f"✓ Script executed successfully")
        encrypted = result.get('encrypted_data')
        if isinstance(encrypted, dict):
            print(f"  Encrypted size: {encrypted.get('size')} bytes")
            print(f"  Key (hex): {encrypted.get('key_hex')}")
        else:
            print(f"  Output: {encrypted}")
        print()
        return True
    except PreprocessingError as e:
        print(f"✗ Script execution failed: {e}")
        print()
        return False


def test_caesar_cipher():
    """Test Caesar cipher preprocessor."""
    print("=" * 60)
    print("TEST 3: Caesar Cipher")
    print("=" * 60)
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    test_data = "Attack at dawn!"
    
    preprocessing_steps = [
        {
            'type': 'script',
            'name': 'caesar_encrypt',
            'script': 'caesar_cipher.py',
            'args': {
                'data': test_data,
                'shift': 13,
                'decrypt': False
            },
            'output_var': 'caesar_result'
        }
    ]
    
    parameters = {}
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters)
        print(f"✓ Caesar cipher executed successfully")
        caesar_data = result.get('caesar_result')
        if isinstance(caesar_data, dict):
            print(f"  Shift: {caesar_data.get('shift')}")
            print(f"  Size: {caesar_data.get('size')} bytes")
        else:
            print(f"  Output: {caesar_data}")
        print()
        return True
    except PreprocessingError as e:
        print(f"✗ Caesar cipher failed: {e}")
        print()
        return False


def test_chained_preprocessing():
    """Test multiple preprocessing steps chained together."""
    print("=" * 60)
    print("TEST 4: Chained Preprocessing (Base64 → Compress)")
    print("=" * 60)
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    test_data = "This is a test payload that will be encoded and compressed. " * 10
    
    preprocessing_steps = [
        {
            'type': 'script',
            'name': 'base64_encode',
            'script': 'base64_encode.py',
            'args': {
                'data': test_data,
                'format': 'json'
            },
            'output_var': 'encoded_data'
        },
        {
            'type': 'script',
            'name': 'compress',
            'script': 'compress.py',
            'args': {
                'data': '{{ encoded_data.encoded }}',  # Reference previous output
                'level': 9
            },
            'output_var': 'compressed_data'
        }
    ]
    
    parameters = {}
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters)
        print(f"✓ Chained preprocessing executed successfully")
        
        encoded = result.get('encoded_data')
        compressed = result.get('compressed_data')
        
        if isinstance(encoded, dict):
            print(f"  Step 1 (Base64): {encoded.get('original_size')} → {encoded.get('size')} bytes")
        
        if isinstance(compressed, dict):
            print(f"  Step 2 (Compress): {compressed.get('original_size')} → {compressed.get('compressed_size')} bytes")
            print(f"  Compression ratio: {compressed.get('compression_ratio')}")
        
        print()
        return True
    except PreprocessingError as e:
        print(f"✗ Chained preprocessing failed: {e}")
        print()
        return False


def test_variable_substitution():
    """Test Jinja2 variable substitution in preprocessing."""
    print("=" * 60)
    print("TEST 5: Variable Substitution")
    print("=" * 60)
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    preprocessing_steps = [
        {
            'type': 'command',
            'name': 'echo_with_params',
            'command': 'echo "LHOST={{ lhost }} LPORT={{ lport }}"',
            'output_var': 'params_echo'
        }
    ]
    
    parameters = {
        'lhost': '192.168.1.100',
        'lport': 4444
    }
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters)
        print(f"✓ Variable substitution successful")
        print(f"  Output: {result.get('params_echo')}")
        print()
        return True
    except PreprocessingError as e:
        print(f"✗ Variable substitution failed: {e}")
        print()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "PAYGEN PREPROCESSING SYSTEM TESTS" + " " * 15 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    tests = [
        ("Command Execution", test_command_execution),
        ("Script Execution (XOR)", test_script_execution),
        ("Caesar Cipher", test_caesar_cipher),
        ("Chained Preprocessing", test_chained_preprocessing),
        ("Variable Substitution", test_variable_substitution),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"✗ Test '{name}' crashed: {e}")
            results.append(False)
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    for i, (name, _) in enumerate(tests):
        status = "✓ PASS" if results[i] else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
