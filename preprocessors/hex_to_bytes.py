#!/usr/bin/env python3
"""
Simple preprocessor to convert hex string to bytes
"""
import sys
import json


def hex_to_bytes(hex_string):
    """Convert hex string to bytes
    
    Args:
        hex_string: Hex string (with or without 0x prefix, spaces, or \\x)
    
    Returns:
        bytes object
    """
    # Remove common prefixes and separators
    hex_string = hex_string.replace('0x', '').replace('\\x', '').replace(' ', '').replace(',', '')
    
    try:
        return bytes.fromhex(hex_string)
    except ValueError as e:
        raise ValueError(f"Invalid hex string: {e}")


def main():
    # Read arguments from stdin as JSON
    input_data = sys.stdin.read()
    args = json.loads(input_data)
    
    hex_string = args.get('hex_string', '')
    
    if not hex_string:
        print(json.dumps({'error': 'No hex_string provided'}), file=sys.stderr)
        sys.exit(1)
    
    try:
        # Convert hex to bytes
        shellcode_bytes = hex_to_bytes(hex_string)
        
        # Output as raw bytes to stdout
        sys.stdout.buffer.write(shellcode_bytes)
        
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
