"""
Compilation utilities for Paygen

Handles compilation of source code to binaries using various compilers.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from jinja2 import Template


class CompilationError(Exception):
    """Raised when compilation fails"""
    pass


class Compiler:
    """Handles source code compilation"""
    
    def compile(
        self,
        source_file: Path,
        compiler: str,
        flags: List[str],
        variables: Dict[str, any] = None
    ) -> Tuple[bool, str, str]:
        """
        Compile source code to binary
        
        Args:
            source_file: Path to source code file
            compiler: Compiler command (e.g., 'mcs', 'gcc')
            flags: List of compiler flags (may contain Jinja2 templates)
            variables: Variables for Jinja2 template rendering in flags
            
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        if variables is None:
            variables = {}
        
        # Render compiler flags with Jinja2
        rendered_flags = []
        for flag in flags:
            template = Template(flag)
            rendered_flag = template.render(**variables)
            rendered_flags.append(rendered_flag)
        
        # Build command
        command = [compiler] + rendered_flags + [str(source_file)]
        
        try:
            # Execute compilation
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Compilation timed out after 5 minutes"
        except FileNotFoundError:
            return False, "", f"Compiler '{compiler}' not found. Please install it."
        except Exception as e:
            return False, "", f"Compilation error: {str(e)}"
    
    def get_compiler_for_language(self, language: str) -> Optional[str]:
        """
        Get default compiler for a language
        
        Args:
            language: Programming language (e.g., 'cs', 'c', 'cpp')
            
        Returns:
            Default compiler command or None
        """
        compilers = {
            'cs': 'mcs',  # Mono C# compiler
            'c': 'gcc',
            'cpp': 'g++',
            'go': 'go build',
            'rust': 'rustc'
        }
        return compilers.get(language.lower())
    
    def detect_language(self, source_file: Path) -> Optional[str]:
        """
        Detect programming language from file extension
        
        Args:
            source_file: Path to source file
            
        Returns:
            Language identifier or None
        """
        extension_map = {
            '.cs': 'cs',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cxx': 'cpp',
            '.cc': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.ps1': 'powershell',
            '.py': 'python'
        }
        return extension_map.get(source_file.suffix.lower())
