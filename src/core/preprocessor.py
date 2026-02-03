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
from src.core.shellcode_loader import ShellcodeLoader


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
        
        # Load shellcode configurations
        self.shellcode_loader = None
        try:
            shellcodes_path = config.shellcodes_config
            if shellcodes_path.exists():
                self.shellcode_loader = ShellcodeLoader(shellcodes_path)
        except Exception as e:
            print(f"Warning: Failed to load shellcodes configuration: {e}")
    
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
                elif step_type == 'shellcode':
                    self._execute_shellcode(step)
                else:
                    raise PreprocessingError(f"Unknown preprocessing type: {step_type}")
            except PreprocessingError:
                raise
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
    
    def _execute_shellcode(self, step: Dict[str, Any]) -> None:
        """
        Execute a shellcode generation preprocessing step.
        
        Args:
            step: Shellcode step definition with 'output_var' and selected shellcode name in variables
        """
        output_var = step.get('output_var')
        
        if not output_var:
            raise PreprocessingError("Shellcode preprocessing step missing 'output_var'")
        
        if not self.shellcode_loader:
            raise PreprocessingError("Shellcode loader not initialized. Check shellcodes_config in configuration.")
        
        # Get the selected shellcode name from variables
        # The web UI should have set this as '<step_name>_selected'
        step_name = step.get('name', 'shellcode')
        shellcode_selection_var = f"{output_var}_shellcode_name"
        
        selected_shellcode_name = self.variables.get(shellcode_selection_var)
        if not selected_shellcode_name:
            raise PreprocessingError(
                f"No shellcode selected. Expected variable '{shellcode_selection_var}' to contain shellcode name."
            )
        
        # Get the shellcode configuration
        shellcode_config = self.shellcode_loader.get_shellcode(selected_shellcode_name)
        if not shellcode_config:
            raise PreprocessingError(f"Shellcode configuration not found: {selected_shellcode_name}")
        
        # Store the shellcode config for later use (e.g., for listener generation)
        self.variables[f"{output_var}_shellcode_config"] = {
            'name': shellcode_config.name,
            'listener': shellcode_config.listener
        }
        
        # Render the shellcode command with current variables (Jinja2)
        command_template = shellcode_config.shellcode
        rendered_command = Template(command_template).render(**self.variables)
        
        # Execute command
        try:
            result = subprocess.run(
                rendered_command,
                shell=True,
                capture_output=True,
                text=False,  # Get bytes output for shellcode
                check=True
            )
            
            # Store output in variables (as bytes for shellcode)
            self.variables[output_var] = result.stdout
            
        except subprocess.CalledProcessError as e:
            raise PreprocessingError(
                f"Shellcode generation command failed with exit code {e.returncode}\n"
                f"Command: {rendered_command}\n"
                f"Stdout: {e.stdout.decode('utf-8', errors='replace') if e.stdout else '(empty)'}\n"
                f"Stderr: {e.stderr.decode('utf-8', errors='replace') if e.stderr else '(empty)'}"
            )


class PreprocessingError(Exception):
    """Exception raised when preprocessing fails."""
    pass
