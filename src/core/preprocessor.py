"""
Preprocessing pipeline for payload transformations

Handles encryption, encoding, and compression of shellcode/payloads.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from src.utils.crypto import CryptoUtils


class PreprocessingError(Exception):
    """Raised when preprocessing fails."""
    pass


class Preprocessor:
    """Handle preprocessing operations on payload data."""
    
    def __init__(self):
        self.crypto = CryptoUtils()
    
    def process(
        self,
        operation: Dict[str, Any],
        parameters: Dict[str, Any],
        recipe_dir: Path
    ) -> Dict[str, Any]:
        """
        Execute a preprocessing operation.
        
        Args:
            operation: Preprocessing operation definition from recipe
            parameters: User-provided parameters
            recipe_dir: Recipe directory for resolving relative paths
            
        Returns:
            Dictionary with processed data and metadata
            
        Raises:
            PreprocessingError: If preprocessing fails
        """
        op_type = operation.get('type')
        
        if op_type == 'none':
            return self._process_none(operation, parameters, recipe_dir)
        elif op_type == 'xor_encrypt':
            return self._process_xor(operation, parameters, recipe_dir)
        elif op_type == 'aes_encrypt':
            return self._process_aes(operation, parameters, recipe_dir)
        elif op_type == 'base64_encode':
            return self._process_base64(operation, parameters, recipe_dir)
        elif op_type == 'compression':
            return self._process_compress(operation, parameters, recipe_dir)
        else:
            raise PreprocessingError(f"Unknown preprocessing type: {op_type}")
    
    def _load_input_file(self, input_param: str, parameters: Dict[str, Any], recipe_dir: Path) -> bytes:
        """
        Load input file from parameter.
        
        Args:
            input_param: Parameter name containing file path
            parameters: User parameters
            recipe_dir: Recipe directory for relative paths
            
        Returns:
            File contents as bytes
        """
        file_path = parameters.get(input_param)
        if not file_path:
            raise PreprocessingError(f"Missing input parameter: {input_param}")
        
        # Convert to Path and resolve
        path = Path(file_path)
        if not path.is_absolute():
            path = recipe_dir / path
        
        if not path.exists():
            raise PreprocessingError(f"Input file not found: {path}")
        
        try:
            return path.read_bytes()
        except Exception as e:
            raise PreprocessingError(f"Failed to read input file: {e}")
    
    def _process_none(
        self,
        operation: Dict[str, Any],
        parameters: Dict[str, Any],
        recipe_dir: Path
    ) -> Dict[str, Any]:
        """Process with no transformation."""
        input_param = operation.get('input')
        if input_param:
            data = self._load_input_file(input_param, parameters, recipe_dir)
        else:
            data = b""
        
        return {
            'type': 'none',
            'data': data,
            'encoding': 'raw'
        }
    
    def _process_xor(
        self,
        operation: Dict[str, Any],
        parameters: Dict[str, Any],
        recipe_dir: Path
    ) -> Dict[str, Any]:
        """Process XOR encryption."""
        # Load input data
        input_param = operation.get('input')
        data = self._load_input_file(input_param, parameters, recipe_dir)
        
        # Get or generate key
        key_param = operation.get('key')
        key = parameters.get(key_param)
        
        if not key:
            # Auto-generate key if not provided
            key = self.crypto.generate_random_key(length=16)  # 16-byte key for XOR
            parameters[key_param] = key  # Store back for template use
        
        # Encrypt
        encrypted = self.crypto.xor_encrypt(data, key)
        
        return {
            'type': 'xor_encrypt',
            'data': encrypted,
            'key': key,
            'key_bytes': bytes.fromhex(key),
            'encoding': 'raw',
            'original_size': len(data),
            'encrypted_size': len(encrypted)
        }
    
    def _process_aes(
        self,
        operation: Dict[str, Any],
        parameters: Dict[str, Any],
        recipe_dir: Path
    ) -> Dict[str, Any]:
        """Process AES-256-CBC encryption."""
        # Load input data
        input_param = operation.get('input')
        data = self._load_input_file(input_param, parameters, recipe_dir)
        
        # Get or generate key
        key_param = operation.get('key')
        key = parameters.get(key_param)
        
        if not key:
            # Auto-generate 256-bit key if not provided
            key = self.crypto.generate_random_key(length=32)
            parameters[key_param] = key  # Store back for template use
        
        # Encrypt
        encrypted, key_bytes, iv = self.crypto.aes_encrypt(data, key)
        
        return {
            'type': 'aes_encrypt',
            'data': encrypted,
            'key': key,
            'key_bytes': key_bytes,
            'iv': iv,
            'iv_hex': iv.hex(),
            'encoding': 'raw',
            'original_size': len(data),
            'encrypted_size': len(encrypted)
        }
    
    def _process_base64(
        self,
        operation: Dict[str, Any],
        parameters: Dict[str, Any],
        recipe_dir: Path
    ) -> Dict[str, Any]:
        """Process Base64 encoding."""
        # Load input data
        input_param = operation.get('input')
        data = self._load_input_file(input_param, parameters, recipe_dir)
        
        # Encode
        encoded = self.crypto.base64_encode(data)
        
        return {
            'type': 'base64_encode',
            'data': data,  # Keep raw data
            'encoded': encoded,
            'encoding': 'base64',
            'original_size': len(data),
            'encoded_size': len(encoded)
        }
    
    def _process_compress(
        self,
        operation: Dict[str, Any],
        parameters: Dict[str, Any],
        recipe_dir: Path
    ) -> Dict[str, Any]:
        """Process gzip compression."""
        # Load input data
        input_param = operation.get('input')
        data = self._load_input_file(input_param, parameters, recipe_dir)
        
        # Get compression level (default 9)
        level = operation.get('level', 9)
        
        # Compress
        compressed = self.crypto.compress(data, level)
        
        return {
            'type': 'compression',
            'data': compressed,
            'encoding': 'gzip',
            'original_size': len(data),
            'compressed_size': len(compressed),
            'compression_ratio': len(compressed) / len(data) if data else 0
        }
    
    def format_for_template(
        self,
        processed_data: Dict[str, Any],
        format_type: str = 'c'
    ) -> str:
        """
        Format processed data for use in templates.
        
        Args:
            processed_data: Result from process()
            format_type: Output format ('c', 'csharp', 'powershell')
            
        Returns:
            Formatted string for template injection
        """
        data = processed_data['data']
        
        if format_type == 'c':
            return self.crypto.bytes_to_c_array(data)
        elif format_type == 'csharp':
            return self.crypto.bytes_to_csharp_array(data)
        elif format_type == 'powershell':
            return self.crypto.bytes_to_powershell_array(data)
        else:
            raise PreprocessingError(f"Unknown format type: {format_type}")
