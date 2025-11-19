"""
Cryptographic utilities for payload preprocessing

Provides XOR, AES encryption, base64 encoding, and compression.
"""

import base64
import gzip
import os
from typing import Union, Tuple
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class CryptoUtils:
    """Cryptographic operations for payload obfuscation."""
    
    @staticmethod
    def xor_encrypt(data: bytes, key: Union[bytes, str]) -> bytes:
        """
        XOR encrypt data with a key.
        
        Args:
            data: Data to encrypt
            key: Encryption key (bytes or hex string)
            
        Returns:
            Encrypted data
        """
        if isinstance(key, str):
            key = bytes.fromhex(key)
        
        # Repeat key to match data length
        key_repeated = (key * (len(data) // len(key) + 1))[:len(data)]
        
        # XOR each byte
        encrypted = bytes(a ^ b for a, b in zip(data, key_repeated))
        return encrypted
    
    @staticmethod
    def xor_decrypt(data: bytes, key: Union[bytes, str]) -> bytes:
        """
        XOR decrypt data (same as encrypt due to XOR properties).
        
        Args:
            data: Data to decrypt
            key: Decryption key (bytes or hex string)
            
        Returns:
            Decrypted data
        """
        return CryptoUtils.xor_encrypt(data, key)
    
    @staticmethod
    def aes_encrypt(data: bytes, key: Union[bytes, str] = None) -> Tuple[bytes, bytes, bytes]:
        """
        AES-256-CBC encrypt data.
        
        Args:
            data: Data to encrypt
            key: 32-byte key (bytes or hex string). If None, generates random key.
            
        Returns:
            Tuple of (encrypted_data, key, iv)
        """
        if key is None:
            key = os.urandom(32)  # 256-bit key
        elif isinstance(key, str):
            key = bytes.fromhex(key)
        
        if len(key) != 32:
            raise ValueError("AES-256 requires a 32-byte key")
        
        # Generate random IV
        iv = os.urandom(16)
        
        # Create cipher and encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted = cipher.encrypt(pad(data, AES.block_size))
        
        return encrypted, key, iv
    
    @staticmethod
    def aes_decrypt(data: bytes, key: Union[bytes, str], iv: bytes) -> bytes:
        """
        AES-256-CBC decrypt data.
        
        Args:
            data: Encrypted data
            key: 32-byte key (bytes or hex string)
            iv: 16-byte initialization vector
            
        Returns:
            Decrypted data
        """
        if isinstance(key, str):
            key = bytes.fromhex(key)
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(data), AES.block_size)
        
        return decrypted
    
    @staticmethod
    def base64_encode(data: bytes) -> str:
        """
        Base64 encode data.
        
        Args:
            data: Data to encode
            
        Returns:
            Base64 encoded string
        """
        return base64.b64encode(data).decode('ascii')
    
    @staticmethod
    def base64_decode(data: str) -> bytes:
        """
        Base64 decode data.
        
        Args:
            data: Base64 encoded string
            
        Returns:
            Decoded bytes
        """
        return base64.b64decode(data)
    
    @staticmethod
    def compress(data: bytes, level: int = 9) -> bytes:
        """
        Gzip compress data.
        
        Args:
            data: Data to compress
            level: Compression level (0-9, default 9)
            
        Returns:
            Compressed data
        """
        return gzip.compress(data, compresslevel=level)
    
    @staticmethod
    def decompress(data: bytes) -> bytes:
        """
        Gzip decompress data.
        
        Args:
            data: Compressed data
            
        Returns:
            Decompressed data
        """
        return gzip.decompress(data)
    
    @staticmethod
    def generate_random_key(length: int = 32) -> str:
        """
        Generate a random hex key.
        
        Args:
            length: Key length in bytes (default 32 for AES-256)
            
        Returns:
            Hex string of random bytes
        """
        return os.urandom(length).hex()
    
    @staticmethod
    def bytes_to_c_array(data: bytes, var_name: str = "shellcode") -> str:
        """
        Convert bytes to C array format.
        
        Args:
            data: Binary data
            var_name: Variable name for C array
            
        Returns:
            C array declaration as string
        """
        hex_bytes = ', '.join(f'0x{b:02x}' for b in data)
        return f"unsigned char {var_name}[] = {{ {hex_bytes} }};"
    
    @staticmethod
    def bytes_to_csharp_array(data: bytes, var_name: str = "shellcode") -> str:
        """
        Convert bytes to C# array format.
        
        Args:
            data: Binary data
            var_name: Variable name for C# array
            
        Returns:
            C# array declaration as string
        """
        hex_bytes = ', '.join(f'0x{b:02x}' for b in data)
        return f"byte[] {var_name} = new byte[] {{ {hex_bytes} }};"
    
    @staticmethod
    def bytes_to_powershell_array(data: bytes, var_name: str = "$shellcode") -> str:
        """
        Convert bytes to PowerShell array format.
        
        Args:
            data: Binary data
            var_name: Variable name for PowerShell array
            
        Returns:
            PowerShell array declaration as string
        """
        hex_bytes = ','.join(f'0x{b:02x}' for b in data)
        return f"{var_name} = @({hex_bytes})"
