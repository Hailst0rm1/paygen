"""
Cross-platform compilation wrapper

Handles compilation of C, C#, and other source code payloads.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List


class CompilationError(Exception):
    """Raised when compilation fails."""
    pass


class Compiler:
    """Cross-platform payload compiler."""
    
    # Default compiler commands for different targets
    COMPILERS = {
        'windows_x64': {
            'c': 'x86_64-w64-mingw32-gcc',
            'cpp': 'x86_64-w64-mingw32-g++',
        },
        'windows_x86': {
            'c': 'i686-w64-mingw32-gcc',
            'cpp': 'i686-w64-mingw32-g++',
        },
        'linux_x64': {
            'c': 'gcc',
            'cpp': 'g++',
        },
        'csharp': {
            'exe': 'mcs',  # Mono C# compiler
            'dll': 'mcs',
        }
    }
    
    def __init__(self):
        """Initialize compiler."""
        self._check_available_compilers()
    
    def _check_available_compilers(self):
        """Check which compilers are available on the system."""
        self.available = {}
        
        # Check each compiler
        for target, compilers in self.COMPILERS.items():
            self.available[target] = {}
            for lang, cmd in compilers.items():
                # Extract just the command name
                cmd_name = cmd.split()[0] if ' ' in cmd else cmd
                self.available[target][lang] = shutil.which(cmd_name) is not None
    
    def is_available(self, target: str, language: str = 'c') -> bool:
        """
        Check if compiler is available for target and language.
        
        Args:
            target: Target platform (e.g., 'windows_x64')
            language: Source language (e.g., 'c', 'cpp', 'csharp')
            
        Returns:
            True if compiler is available
        """
        return self.available.get(target, {}).get(language, False)
    
    def compile(
        self,
        source_path: Path,
        output_path: Path,
        compile_command: Optional[str] = None,
        target: str = 'windows_x64',
        language: str = 'c',
        extra_flags: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compile source code to executable.
        
        Args:
            source_path: Path to source code file
            output_path: Path for output executable
            compile_command: Custom compile command (overrides defaults)
            target: Target platform
            language: Source language
            extra_flags: Additional compiler flags
            
        Returns:
            Dictionary with compilation results
            
        Raises:
            CompilationError: If compilation fails
        """
        if not source_path.exists():
            raise CompilationError(f"Source file not found: {source_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build compile command
        if compile_command:
            # Custom command - replace placeholders
            cmd = compile_command.format(
                source=str(source_path),
                output=str(output_path)
            )
        else:
            # Use default compiler
            if not self.is_available(target, language):
                raise CompilationError(
                    f"Compiler not available for {target}/{language}. "
                    f"Install {self.COMPILERS.get(target, {}).get(language, 'unknown')}"
                )
            
            compiler = self.COMPILERS[target][language]
            
            # Build command based on language
            if language in ['c', 'cpp']:
                cmd_parts = [compiler, str(source_path), '-o', str(output_path)]
                
                # Add common flags
                if target.startswith('windows'):
                    cmd_parts.extend(['-s', '-O2'])  # Strip and optimize
                
                if extra_flags:
                    cmd_parts.extend(extra_flags)
                
                cmd = ' '.join(cmd_parts)
            
            elif language == 'csharp':
                cmd_parts = [compiler, str(source_path), '-out:' + str(output_path)]
                
                if extra_flags:
                    cmd_parts.extend(extra_flags)
                
                cmd = ' '.join(cmd_parts)
            
            else:
                raise CompilationError(f"Unsupported language: {language}")
        
        # Execute compilation
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode != 0:
                raise CompilationError(
                    f"Compilation failed with exit code {result.returncode}\n"
                    f"STDOUT: {result.stdout}\n"
                    f"STDERR: {result.stderr}"
                )
            
            # Verify output was created
            if not output_path.exists():
                raise CompilationError("Compilation succeeded but output file not found")
            
            return {
                'success': True,
                'output_path': output_path,
                'output_size': output_path.stat().st_size,
                'command': cmd,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        
        except subprocess.TimeoutExpired:
            raise CompilationError("Compilation timed out after 60 seconds")
        except Exception as e:
            raise CompilationError(f"Compilation error: {e}")
    
    def get_missing_compilers(self) -> List[str]:
        """
        Get list of missing compilers.
        
        Returns:
            List of missing compiler names
        """
        missing = []
        for target, compilers in self.COMPILERS.items():
            for lang, cmd in compilers.items():
                cmd_name = cmd.split()[0] if ' ' in cmd else cmd
                if not self.available.get(target, {}).get(lang, False):
                    missing.append(f"{cmd_name} (for {target}/{lang})")
        
        return list(set(missing))  # Remove duplicates
