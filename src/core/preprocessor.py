"""
Preprocessing orchestrator for payload generation.

Executes preprocessing steps (commands and scripts) and manages output variables.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List
from jinja2 import Template

from src.core.config import ConfigManager


class PreprocessingOrchestrator:
    """Orchestrates preprocessing steps for payload generation."""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize the preprocessing orchestrator.
        
        Args:
            config: ConfigManager instance for accessing paths
        """
        self.config = config
        self.variables: Dict[str, Any] = {}
    
    def execute(self, preprocessing_steps: List[Dict[str, Any]], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute all preprocessing steps in order.
        
        Args:
            preprocessing_steps: List of preprocessing step definitions from recipe
            parameters: User-provided parameters from recipe
        
        Returns:
            Dictionary of all variables (parameters + preprocessing outputs)
        
        Raises:
            PreprocessingError: If any preprocessing step fails
        """
        # Start with user parameters
        self.variables = parameters.copy()
        
        # Execute each preprocessing step
        for step in preprocessing_steps:
            step_type = step.get('type')
            step_name = step.get('name', 'unnamed')
            
            try:
                if step_type == 'command':
                    self._execute_command(step)
                elif step_type == 'script':
                    self._execute_script(step)
                else:
                    raise PreprocessingError(f"Unknown preprocessing type: {step_type}")
            except Exception as e:
                raise PreprocessingError(f"Preprocessing step '{step_name}' failed: {str(e)}")
        
        return self.variables
    
    def _execute_command(self, step: Dict[str, Any]) -> None:
        """
        Execute a command-based preprocessing step.
        
        Args:
            step: Command step definition with 'command' and 'output_var'
        """
        command_template = step.get('command', '')
        output_var = step.get('output_var')
        
        if not output_var:
            raise PreprocessingError("Command preprocessing step missing 'output_var'")
        
        # Render command with current variables (Jinja2)
        rendered_command = Template(command_template).render(**self.variables)
        
        # Execute command
        try:
            result = subprocess.run(
                rendered_command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Store output in variables
            self.variables[output_var] = result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            raise PreprocessingError(
                f"Command failed with exit code {e.returncode}\n"
                f"Command: {rendered_command}\n"
                f"Error: {e.stderr}"
            )
    
    def _execute_script(self, step: Dict[str, Any]) -> None:
        """
        Execute a script-based preprocessing step.
        
        Args:
            step: Script step definition with 'script', 'args', and 'output_var'
        """
        script_path = step.get('script', '')
        args = step.get('args', {})
        output_var = step.get('output_var')
        
        if not output_var:
            raise PreprocessingError("Script preprocessing step missing 'output_var'")
        
        # Resolve script path (relative to preprocessors_dir)
        full_script_path = Path(self.config.preprocessors_dir) / script_path
        
        if not full_script_path.exists():
            raise PreprocessingError(f"Preprocessor script not found: {full_script_path}")
        
        # Render arguments with current variables (Jinja2)
        rendered_args = {}
        for key, value in args.items():
            if isinstance(value, str):
                rendered_args[key] = Template(value).render(**self.variables)
            else:
                rendered_args[key] = value
        
        # Execute script with JSON input
        try:
            result = subprocess.run(
                ['python3', str(full_script_path)],
                input=json.dumps(rendered_args),
                capture_output=True,
                text=True,
                check=True
            )
            
            # Store output in variables
            output = result.stdout.strip()
            
            # Try to parse as JSON first, fall back to raw string
            try:
                self.variables[output_var] = json.loads(output)
            except json.JSONDecodeError:
                self.variables[output_var] = output
                
        except subprocess.CalledProcessError as e:
            raise PreprocessingError(
                f"Script failed with exit code {e.returncode}\n"
                f"Script: {full_script_path}\n"
                f"Error: {e.stderr}"
            )
        except FileNotFoundError:
            raise PreprocessingError(f"Python interpreter not found. Is python3 installed?")


class PreprocessingError(Exception):
    """Exception raised when preprocessing fails."""
    pass
