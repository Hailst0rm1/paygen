#!/usr/bin/env python3
"""Test parameter validation functionality"""

from src.core.validator import ParameterValidator, ValidationError

validator = ParameterValidator()

# Test IP validation
print("Testing IP validation:")
test_ips = [
    ("192.168.1.1", True),
    ("10.0.0.1", True),
    ("::1", True),
    ("2001:db8::1", True),
    ("999.999.999.999", False),
    ("not-an-ip", False),
    ("", False),
]

for ip, should_pass in test_ips:
    try:
        validator.validate_ip(ip)
        result = "✓ PASS" if should_pass else "✗ FAIL (should have failed)"
    except ValidationError as e:
        result = "✗ FAIL (should have passed)" if should_pass else f"✓ PASS: {e}"
    print(f"  {ip:20s} - {result}")

print("\nTesting port validation:")
test_ports = [
    ("80", True),
    ("443", True),
    ("8080", True),
    ("65535", True),
    ("1", True),
    ("0", False),
    ("65536", False),
    ("-1", False),
    ("abc", False),
]

for port, should_pass in test_ports:
    try:
        validator.validate_port(port)
        result = "✓ PASS" if should_pass else "✗ FAIL (should have failed)"
    except ValidationError as e:
        result = "✗ FAIL (should have passed)" if should_pass else f"✓ PASS: {e}"
    print(f"  {port:10s} - {result}")

print("\nTesting hex validation:")
test_hex = [
    ("deadbeef", True),
    ("CAFEBABE", True),
    ("0123456789abcdef", True),
    ("xyz", False),
    ("12 34", False),
    ("0x1234", False),
]

for hex_val, should_pass in test_hex:
    try:
        validator.validate_hex(hex_val)
        result = "✓ PASS" if should_pass else "✗ FAIL (should have failed)"
    except ValidationError as e:
        result = "✗ FAIL (should have passed)" if should_pass else f"✓ PASS: {e}"
    print(f"  {hex_val:20s} - {result}")

print("\nTesting path validation:")
test_paths = [
    ("/home/user/file.txt", True),
    ("~/Documents", True),
    ("./relative/path", True),
    ("C:\\Windows\\System32", True),
]

for path, should_pass in test_paths:
    try:
        validator.validate_path(path)
        result = "✓ PASS" if should_pass else "✗ FAIL (should have failed)"
    except ValidationError as e:
        result = "✗ FAIL (should have passed)" if should_pass else f"✓ PASS: {e}"
    print(f"  {path:30s} - {result}")

print("\nValidation tests complete!")
