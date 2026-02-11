#!/usr/bin/env python3
"""
Test script to verify conditional block processing in ps-features.yaml
"""
import re

def process_conditional_blocks(code: str, variables: dict) -> str:
    """Process conditional blocks in the format {{ if varname }}content{{ fi }}
    
    If the variable is empty or None, the entire block (including content) is removed.
    If the variable has a value, the block markers are removed and content is kept.
    
    Args:
        code: Template code with conditional blocks
        variables: Dictionary of variable names to their values
        
    Returns:
        Processed code with conditional blocks handled
    """
    # Pattern to match {{ if varname }}...{{ fi }}
    pattern = r'\{\{\s*if\s+(\w+)\s*\}\}(.*?)\{\{\s*fi\s*\}\}'
    
    def replace_conditional(match):
        var_name = match.group(1)
        content = match.group(2)
        
        # Check if variable exists and has a value
        var_value = variables.get(var_name, '')
        
        if var_value:
            # Variable has value, keep the content
            return content
        else:
            # Variable is empty/None, remove the entire block
            return ''
    
    # Process all conditional blocks
    result = re.sub(pattern, replace_conditional, code, flags=re.DOTALL)
    return result


# Test cases
print("="*60)
print("Testing conditional block processing")
print("="*60)

# Test 1: args has value
print("\nTest 1: WITH arguments")
print("-" * 40)
template1 = 'mimikatz {{ if args }}"{{ args }}"{{ fi }} "privilege::debug"'
variables1 = {'args': 'sekurlsa::logonpasswords'}
result1 = process_conditional_blocks(template1, variables1)
result1 = result1.replace('{{ args }}', variables1['args'])
print(f"Template: {template1}")
print(f"Args: {variables1['args']}")
print(f"Result: {result1}")
print(f"Expected: mimikatz \"sekurlsa::logonpasswords\" \"privilege::debug\"")

# Test 2: args is empty
print("\nTest 2: WITHOUT arguments (empty string)")
print("-" * 40)
template2 = 'mimikatz {{ if args }}"{{ args }}"{{ fi }} "privilege::debug"'
variables2 = {'args': ''}
result2 = process_conditional_blocks(template2, variables2)
result2 = result2.replace('{{ args }}', variables2['args'])
print(f"Template: {template2}")
print(f"Args: (empty)")
print(f"Result: {result2}")
print(f"Expected: mimikatz \"privilege::debug\"")

# Test 3: Multiple conditional blocks
print("\nTest 3: Multiple conditional blocks")
print("-" * 40)
template3 = 'tool {{ if args }}--args "{{ args }}"{{ fi }} {{ if namespace }}--namespace {{ namespace }}{{ fi }} --always'
variables3a = {'args': 'myarg', 'namespace': 'MyNS'}
result3a = process_conditional_blocks(template3, variables3a)
result3a = result3a.replace('{{ args }}', variables3a.get('args', ''))
result3a = result3a.replace('{{ namespace }}', variables3a.get('namespace', ''))
print(f"Template: {template3}")
print(f"With both values:")
print(f"  Result: {result3a}")
print(f"  Expected: tool --args \"myarg\" --namespace MyNS --always")

variables3b = {'args': '', 'namespace': ''}
result3b = process_conditional_blocks(template3, variables3b)
result3b = result3b.replace('{{ args }}', variables3b.get('args', ''))
result3b = result3b.replace('{{ namespace }}', variables3b.get('namespace', ''))
print(f"Without values:")
print(f"  Result: {result3b}")
print(f"  Expected: tool --always")

# Test 4: Nested content with quotes
print("\nTest 4: Complex quoting scenario")
print("-" * 40)
template4 = '& "$env:TEMP\\tool.exe" {{ if args }}"{{ args }}"{{ fi }} "privilege::debug"'
variables4a = {'args': 'sekurlsa::logonpasswords'}
result4a = process_conditional_blocks(template4, variables4a)
result4a = result4a.replace('{{ args }}', variables4a['args'])
print(f"Template: {template4}")
print(f"With args:")
print(f"  Result: {result4a}")
print(f"  Expected: & \"$env:TEMP\\tool.exe\" \"sekurlsa::logonpasswords\" \"privilege::debug\"")

variables4b = {'args': ''}
result4b = process_conditional_blocks(template4, variables4b)
result4b = result4b.replace('{{ args }}', variables4b.get('args', ''))
print(f"Without args:")
print(f"  Result: {result4b}")
print(f"  Expected: & \"$env:TEMP\\tool.exe\" \"privilege::debug\"")

print("\n" + "="*60)
print("All tests completed!")
print("="*60)
