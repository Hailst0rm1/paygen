"""
Payload Builder Orchestrator

Manages the complete payload generation process including preprocessing,
template rendering, and compilation.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
from jinja2 import Template, Environment
import base64


# Custom Jinja2 environment with base64 filter
def create_jinja_env():
    """Create Jinja2 environment with custom filters"""
    env = Environment()
    
    # Add base64 encode filter for bytes
    def b64encode_filter(value):
        if isinstance(value, bytes):
            return base64.b64encode(value).decode('ascii')
        return value
    
    env.filters['b64'] = b64encode_filter
    return env

JINJA_ENV = create_jinja_env()

from .compiler import Compiler
from .config import ConfigManager


class BuildStep:
    """Represents a single build step"""
    def __init__(self, name: str, step_type: str):
        self.name = name
        self.type = step_type
        self.status = "pending"  # pending, running, success, failed
        self.output = ""
        self.error = ""


class PayloadBuilder:
    """Orchestrates payload generation from recipes"""
    
    def __init__(self, config: ConfigManager):
        """
        Initialize payload builder
        
        Args:
            config: ConfigManager instance
        """
        self.config = config
        self.compiler = Compiler()
        self.variables = {}
        self.steps: List[BuildStep] = []
        self.progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable[[BuildStep], None]):
        """
        Set callback for build progress updates
        
        Args:
            callback: Function called with BuildStep on each step update
        """
        self.progress_callback = callback
    
    def _update_step(self, step: BuildStep):
        """Update step and notify callback"""
        if self.progress_callback:
            self.progress_callback(step)
    
    def build(self, recipe: dict, parameters: Dict[str, any]) -> Tuple[bool, str, List[BuildStep]]:
        """
        Build payload from recipe
        
        Args:
            recipe: Recipe dictionary loaded from YAML
            parameters: User-provided parameters
            
        Returns:
            Tuple of (success: bool, output_file: str, steps: List[BuildStep])
        """
        self.steps = []
        self.variables = parameters.copy()
        
        # Add config to variables for template rendering
        self.variables['config'] = {
            'output_dir': str(self.config.output_dir),
            'recipes_dir': str(self.config.recipes_dir),
            'payloads_dir': str(self.config.payloads_dir),
            'preprocessors_dir': str(self.config.preprocessors_dir)
        }
        
        try:
            # Step 1: Run preprocessing
            if 'preprocessing' in recipe and recipe['preprocessing']:
                for i, preproc_step in enumerate(recipe['preprocessing'], 1):
                    step = BuildStep(
                        f"Preprocessing {i}/{len(recipe['preprocessing'])}: {preproc_step.get('name', 'Unknown')}",
                        preproc_step.get('type', 'unknown')
                    )
                    self.steps.append(step)
                    
                    success, output, error = self._run_preprocessing_step(preproc_step)
                    if not success:
                        step.status = "failed"
                        step.error = error
                        self._update_step(step)
                        return False, "", self.steps
                    
                    step.status = "success"
                    step.output = output
                    self._update_step(step)
                    
                    # Store output in variables
                    if 'output_var' in preproc_step:
                        # Try to parse JSON output from scripts
                        if preproc_step.get('type') == 'script':
                            try:
                                parsed = json.loads(output)
                                self.variables[preproc_step['output_var']] = parsed
                            except (json.JSONDecodeError, TypeError):
                                # Not JSON, store as-is (plain string or bytes)
                                self.variables[preproc_step['output_var']] = output
                        else:
                            # Command output - store as-is (usually bytes)
                            self.variables[preproc_step['output_var']] = output
            
            # Step 2: Generate payload
            output_config = recipe.get('output', {})
            output_type = output_config.get('type', 'template')
            
            if output_type == 'template':
                return self._build_template_payload(recipe, output_config)
            elif output_type == 'command':
                return self._build_command_payload(recipe, output_config)
            else:
                return False, "", self.steps
                
        except Exception as e:
            error_step = BuildStep("Build Error", "error")
            error_step.status = "failed"
            error_step.error = str(e)
            self.steps.append(error_step)
            self._update_step(error_step)
            return False, "", self.steps
    
    def _run_preprocessing_step(self, step_config: dict) -> Tuple[bool, str, str]:
        """
        Run a single preprocessing step
        
        Args:
            step_config: Preprocessing step configuration from recipe
            
        Returns:
            Tuple of (success: bool, output: str, error: str)
        """
        step_type = step_config.get('type')
        
        if step_type == 'command':
            return self._run_command_preprocessing(step_config)
        elif step_type == 'script':
            return self._run_script_preprocessing(step_config)
        else:
            return False, "", f"Unknown preprocessing type: {step_type}"
    
    def _run_command_preprocessing(self, step_config: dict) -> Tuple[bool, str, str]:
        """
        Run command-based preprocessing
        
        Args:
            step_config: Step configuration
            
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        command_template = step_config.get('command', '')
        
        # Render command with current variables
        template = JINJA_ENV.from_string(command_template)
        command = template.render(**self.variables)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=False,  # Don't decode as text - keep as bytes
                timeout=300
            )
            
            success = result.returncode == 0
            # Return bytes as-is for stdout, decode stderr for error messages
            stdout = result.stdout  # Keep as bytes
            stderr = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            return False, b"", "Command timed out after 5 minutes"
        except Exception as e:
            return False, b"", f"Command execution error: {str(e)}"
    
    def _run_script_preprocessing(self, step_config: dict) -> Tuple[bool, str, str]:
        """
        Run script-based preprocessing
        
        Args:
            step_config: Step configuration
            
        Returns:
            Tuple of (success: bool, stdout: str, stderr: str)
        """
        script_path = step_config.get('script', '')
        args_config = step_config.get('args', {})
        
        # Resolve script path
        full_script_path = self.config.preprocessors_dir / script_path
        
        if not full_script_path.exists():
            return False, "", f"Script not found: {full_script_path}"
        
        # Render arguments with current variables
        rendered_args = {}
        for key, value_template in args_config.items():
            if isinstance(value_template, str):
                # Use Jinja2 to render the template with all variables
                template = JINJA_ENV.from_string(value_template)
                try:
                    rendered_value = template.render(**self.variables)
                    rendered_args[key] = rendered_value
                except Exception as e:
                    # If rendering fails, use as-is
                    rendered_args[key] = value_template
            else:
                rendered_args[key] = value_template
        
        # Pass arguments as JSON to stdin
        try:
            result = subprocess.run(
                ['python3', str(full_script_path)],
                input=json.dumps(rendered_args),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            success = result.returncode == 0
            # Include both stdout and stderr in error output for better debugging
            if not success and not result.stderr:
                stderr = result.stdout if result.stdout else "Script failed with no error output"
            else:
                stderr = result.stderr
            return success, result.stdout, stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Script timed out after 5 minutes"
        except Exception as e:
            return False, "", f"Script execution error: {str(e)}"
    
    def _build_template_payload(self, recipe: dict, output_config: dict) -> Tuple[bool, str, List[BuildStep]]:
        """
        Build payload from template
        
        Args:
            recipe: Recipe dictionary
            output_config: Output configuration from recipe
            
        Returns:
            Tuple of (success: bool, output_file: str, steps: List[BuildStep])
        """
        # Step: Render template
        step = BuildStep("Rendering template", "template")
        self.steps.append(step)
        step.status = "running"
        self._update_step(step)
        
        template_path = output_config.get('template', '')
        full_template_path = self.config.payloads_dir / template_path
        
        if not full_template_path.exists():
            step.status = "failed"
            step.error = f"Template not found: {full_template_path}"
            self._update_step(step)
            return False, "", self.steps
        
        try:
            # Read and render template
            with open(full_template_path, 'r') as f:
                template_content = f.read()
            
            template = JINJA_ENV.from_string(template_content)
            rendered_code = template.render(**self.variables)
            
            # Determine output paths
            output_path = Path(self.variables.get('output_path', self.config.output_dir))
            output_file = self.variables.get('output_file', 'payload')
            
            # Create output directory if it doesn't exist
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save rendered source code
            source_file = output_path / f"{Path(output_file).stem}{full_template_path.suffix}"
            with open(source_file, 'w') as f:
                f.write(rendered_code)
            
            step.status = "success"
            step.output = f"Template rendered to {source_file}"
            self._update_step(step)
            
            # Step: Compile if needed
            compile_config = output_config.get('compile', {})
            if compile_config.get('enabled', False):
                compile_step = BuildStep("Compiling", "compile")
                self.steps.append(compile_step)
                compile_step.status = "running"
                self._update_step(compile_step)
                
                command = compile_config.get('command')
                if not command:
                    compile_step.status = "failed"
                    compile_step.error = "No compilation command specified"
                    self._update_step(compile_step)
                    return False, "", self.steps
                
                success, stdout, stderr = self.compiler.compile(
                    source_file,
                    command,
                    self.variables
                )
                
                if not success:
                    compile_step.status = "failed"
                    compile_step.error = stderr
                    compile_step.output = stdout
                    self._update_step(compile_step)
                    return False, "", self.steps
                
                compile_step.status = "success"
                compile_step.output = stdout
                self._update_step(compile_step)
                
                # Remove source file if keep_source_files is False
                if not self.config.keep_source_files:
                    source_file.unlink()
                
                # The compiled output file path (from output_path and output_file parameters)
                final_output = output_path / output_file
                
                # Verify the output file exists
                if not final_output.exists():
                    # Try to find what file was actually created
                    possible_files = list(output_path.glob(f"{Path(output_file).stem}*"))
                    if possible_files:
                        final_output = possible_files[0]
                    else:
                        compile_step.status = "failed"
                        compile_step.error = f"Expected output file not found: {final_output}"
                        self._update_step(compile_step)
                        return False, "", self.steps
                
                return True, str(final_output), self.steps
            else:
                # No compilation, source file is the output
                return True, str(source_file), self.steps
                
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            self._update_step(step)
            return False, "", self.steps
    
    def _build_command_payload(self, recipe: dict, output_config: dict) -> Tuple[bool, str, List[BuildStep]]:
        """
        Build payload using command execution
        
        Args:
            recipe: Recipe dictionary
            output_config: Output configuration from recipe
            
        Returns:
            Tuple of (success: bool, output_file: str, steps: List[BuildStep])
        """
        step = BuildStep("Executing command", "command")
        self.steps.append(step)
        step.status = "running"
        self._update_step(step)
        
        command_template = output_config.get('command', '')
        
        # Render command with variables
        template = JINJA_ENV.from_string(command_template)
        command = template.render(**self.variables)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                step.status = "success"
                step.output = result.stdout
                self._update_step(step)
                
                # Determine output file from parameters
                output_path = Path(self.variables.get('output_path', self.config.output_dir))
                output_file = self.variables.get('output_file', 'payload')
                full_output = output_path / output_file
                
                return True, str(full_output), self.steps
            else:
                step.status = "failed"
                step.error = result.stderr
                step.output = result.stdout
                self._update_step(step)
                return False, "", self.steps
                
        except subprocess.TimeoutExpired:
            step.status = "failed"
            step.error = "Command timed out after 5 minutes"
            self._update_step(step)
            return False, "", self.steps
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            self._update_step(step)
            return False, "", self.steps
