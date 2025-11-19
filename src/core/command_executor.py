"""
Command execution engine for command-based recipes

Handles dependency checking and command execution for external tools.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


class CommandExecutionError(Exception):
    """Raised when command execution fails."""
    pass


class DependencyError(Exception):
    """Raised when a required dependency is missing."""
    pass


class CommandExecutor:
    """Execute command-based recipes with dependency validation."""
    
    def __init__(self):
        """Initialize command executor."""
        self.dependency_cache = {}
    
    def check_dependency(self, dependency: Dict[str, Any]) -> bool:
        """
        Check if a dependency is available.
        
        Args:
            dependency: Dependency definition from recipe
            
        Returns:
            True if dependency is available
        """
        tool_name = dependency.get('tool', 'unknown')
        
        # Check cache first
        if tool_name in self.dependency_cache:
            return self.dependency_cache[tool_name]
        
        # Get check command
        check_cmd = dependency.get('check_command')
        
        if not check_cmd:
            # Default: check if tool is in PATH
            is_available = shutil.which(tool_name) is not None
        else:
            # Run custom check command
            try:
                result = subprocess.run(
                    check_cmd,
                    shell=True,
                    capture_output=True,
                    timeout=5
                )
                is_available = result.returncode == 0
            except Exception:
                is_available = False
        
        # Cache result
        self.dependency_cache[tool_name] = is_available
        return is_available
    
    def check_all_dependencies(self, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check all dependencies for a recipe.
        
        Args:
            dependencies: List of dependency definitions
            
        Returns:
            Dictionary with check results
        """
        results = {
            'all_satisfied': True,
            'missing': [],
            'available': []
        }
        
        for dep in dependencies:
            tool_name = dep.get('tool', 'unknown')
            is_available = self.check_dependency(dep)
            
            if is_available:
                results['available'].append(tool_name)
            else:
                results['all_satisfied'] = False
                results['missing'].append({
                    'tool': tool_name,
                    'install_hint': dep.get('install_hint', 'No installation hint provided')
                })
        
        return results
    
    def execute_command(
        self,
        command: str,
        working_dir: Optional[Path] = None,
        timeout: int = 300,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a command and capture output.
        
        Args:
            command: Command to execute
            working_dir: Working directory for command execution
            timeout: Command timeout in seconds (default 300)
            env: Environment variables
            
        Returns:
            Dictionary with execution results
            
        Raises:
            CommandExecutionError: If execution fails
        """
        try:
            # Set working directory
            cwd = str(working_dir) if working_dir else None
            
            # Execute command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout,
                env=env
            )
            
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': command
            }
        
        except subprocess.TimeoutExpired:
            raise CommandExecutionError(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise CommandExecutionError(f"Command execution failed: {e}")
    
    def validate_and_execute(
        self,
        command: str,
        dependencies: List[Dict[str, Any]],
        working_dir: Optional[Path] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Validate dependencies and execute command.
        
        Args:
            command: Command to execute
            dependencies: List of required dependencies
            working_dir: Working directory
            timeout: Command timeout in seconds
            
        Returns:
            Dictionary with execution results
            
        Raises:
            DependencyError: If dependencies are missing
            CommandExecutionError: If execution fails
        """
        # Check dependencies
        dep_results = self.check_all_dependencies(dependencies)
        
        if not dep_results['all_satisfied']:
            missing_info = []
            for missing in dep_results['missing']:
                missing_info.append(
                    f"  - {missing['tool']}: {missing['install_hint']}"
                )
            
            raise DependencyError(
                f"Missing required dependencies:\n" + "\n".join(missing_info)
            )
        
        # Execute command
        return self.execute_command(command, working_dir, timeout)
    
    def clear_cache(self):
        """Clear dependency check cache."""
        self.dependency_cache.clear()
