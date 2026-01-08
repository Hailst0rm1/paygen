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
    
    def __init__(self, config: ConfigManager, build_options: dict = None):
        """
        Initialize payload builder
        
        Args:
            config: ConfigManager instance
            build_options: Optional dict with remove_comments and strip_binaries flags
        """
        self.config = config
        self.compiler = Compiler()
        self.variables = {}
        self.steps: List[BuildStep] = []
        self.progress_callback: Optional[Callable] = None
        
        # Build options - override config defaults if provided
        self.build_options = build_options or {}
        self.remove_comments = self.build_options.get('remove_comments', config.remove_comments)
        self.strip_binaries = self.build_options.get('strip_binaries', config.strip_binaries)
    
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
            'templates_dir': str(self.config.templates_dir),
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
                            # Command output - decode bytes to string if possible, otherwise base64 encode
                            if isinstance(output, bytes):
                                try:
                                    # Try to decode as UTF-8 text (for file paths, JSON, etc.)
                                    decoded = output.decode('utf-8').strip()
                                    self.variables[preproc_step['output_var']] = decoded
                                except UnicodeDecodeError:
                                    # Binary data (shellcode, etc.) - base64 encode for safe template passing
                                    import base64
                                    self.variables[preproc_step['output_var']] = base64.b64encode(output).decode('ascii')
                            else:
                                self.variables[preproc_step['output_var']] = output.strip() if isinstance(output, str) else output
            
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
        full_template_path = self.config.templates_dir / template_path
        
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
            
            # Remove comments if configured
            if self.remove_comments:
                comment_step = BuildStep("Removing comments", "preprocessing")
                self.steps.append(comment_step)
                comment_step.status = "running"
                self._update_step(comment_step)
                
                rendered_code = self._remove_comments(rendered_code, full_template_path.suffix)
                
                comment_step.status = "success"
                comment_step.output = "Comments removed from source code"
                self._update_step(comment_step)
            
            # Remove console output if configured
            if self.build_options.get('remove_console_output', False):
                console_step = BuildStep("Removing console output", "preprocessing")
                self.steps.append(console_step)
                console_step.status = "running"
                self._update_step(console_step)
                
                rendered_code = self._remove_console_output(rendered_code, full_template_path.suffix)
                
                console_step.status = "success"
                console_step.output = "Console output statements removed"
                self._update_step(console_step)
            
            # Determine output paths - render templates
            output_path_template = self.variables.get('output_path', str(self.config.output_dir))
            output_file_template = self.variables.get('output_file', 'payload')
            
            output_path = Path(JINJA_ENV.from_string(str(output_path_template)).render(**self.variables))
            output_file = JINJA_ENV.from_string(str(output_file_template)).render(**self.variables)
            
            # Create output directory if it doesn't exist
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Save rendered source code
            source_file = output_path / f"{Path(output_file).stem}{full_template_path.suffix}"
            with open(source_file, 'w') as f:
                f.write(rendered_code)
            
            step.status = "success"
            step.output = f"Template rendered to {source_file}"
            self._update_step(step)
            
            # Step: Insert AMSI bypass if enabled (BEFORE obfuscation)
            if (full_template_path.suffix.lower() == '.ps1' and 
                self.build_options.get('ps_amsi_bypass', False)):
                
                amsi_method = self.build_options.get('ps_amsi_method', '')
                if amsi_method:
                    amsi_step = BuildStep(f"Inserting AMSI bypass ({amsi_method})", "amsi_bypass")
                    self.steps.append(amsi_step)
                    amsi_step.status = "running"
                    self._update_step(amsi_step)
                    
                    success = self._insert_amsi_bypass_template(source_file, amsi_method)
                    
                    if success:
                        amsi_step.status = "success"
                        amsi_step.output = f"AMSI bypass '{amsi_method}' inserted at beginning of script"
                        self._update_step(amsi_step)
                    else:
                        amsi_step.status = "failed"
                        amsi_step.error = f"Failed to insert AMSI bypass"
                        self._update_step(amsi_step)
            
            # Step: PowerShell obfuscation if enabled
            if (full_template_path.suffix.lower() == '.ps1' and 
                self.build_options.get('ps_obfuscate', False)):
                
                obf_level = self.build_options.get('ps_obfuscate_level', 'high')
                obf_success, obf_file = self._obfuscate_powershell(
                    source_file, 
                    output_path, 
                    output_file,
                    obf_level
                )
                
                if obf_success:
                    # Update source_file to point to the obfuscated version
                    source_file = Path(obf_file)
                # If obfuscation fails, continue with non-obfuscated version
            
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
                
                # Strip binaries if configured
                if self.strip_binaries:
                    # The compiled output file path (from output_path and output_file parameters)
                    final_output = output_path / output_file
                    if final_output.exists():
                        strip_step = BuildStep("Stripping binary", "strip")
                        self.steps.append(strip_step)
                        strip_step.status = "running"
                        self._update_step(strip_step)
                        
                        success = self._strip_binary(final_output)
                        if success:
                            strip_step.status = "success"
                            strip_step.output = f"Stripped metadata from {final_output.name}"
                        else:
                            strip_step.status = "warning"
                            strip_step.output = "Strip command not available or failed"
                        self._update_step(strip_step)
                
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
                output_path_template = self.variables.get('output_path', str(self.config.output_dir))
                output_file_template = self.variables.get('output_file', 'payload')
                
                # Render templates
                output_path = Path(JINJA_ENV.from_string(str(output_path_template)).render(**self.variables))
                output_file = JINJA_ENV.from_string(str(output_file_template)).render(**self.variables)
                
                full_output = output_path / output_file
                
                # Strip binaries if configured and file exists
                if self.strip_binaries and full_output.exists():
                    strip_step = BuildStep("Stripping binary", "strip")
                    self.steps.append(strip_step)
                    strip_step.status = "running"
                    self._update_step(strip_step)
                    
                    success = self._strip_binary(full_output)
                    if success:
                        strip_step.status = "success"
                        strip_step.output = f"Stripped metadata from {full_output.name}"
                    else:
                        strip_step.status = "warning"
                        strip_step.output = "Strip command not available or failed"
                    self._update_step(strip_step)
                
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
    
    def _remove_comments(self, code: str, file_extension: str) -> str:
        """Remove comments from source code based on file type
        
        Args:
            code: Source code string
            file_extension: File extension (e.g., '.cs', '.c', '.py')
            
        Returns:
            Code with comments removed and cleaned up
        """
        import re
        
        # C-style comments (C, C++, C#, Java, JavaScript)
        if file_extension in ['.c', '.cpp', '.cs', '.h', '.hpp', '.java', '.js']:
            # Remove single-line comments (only lines that start with //)
            code = re.sub(r'^\s*//.*?$', '', code, flags=re.MULTILINE)
            # Remove multi-line comments
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        
        # Python comments
        elif file_extension in ['.py']:
            # Remove single-line comments (only lines that start with #)
            code = re.sub(r'^\s*#.*?$', '', code, flags=re.MULTILINE)
        
        # PowerShell comments
        elif file_extension in ['.ps1']:
            # Remove multi-line comments first (both PowerShell <# #> and C# /* */)
            code = re.sub(r'<#.*?#>', '', code, flags=re.DOTALL)
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            # Then remove single-line comments (only lines that start with # or //)
            code = re.sub(r'^\s*#.*?$', '', code, flags=re.MULTILINE)
            code = re.sub(r'^\s*//.*?$', '', code, flags=re.MULTILINE)
        
        # VBA comments (Visual Basic for Applications)
        elif file_extension in ['.vba', '.vbs', '.bas']:
            # Remove single-line comments (') - only at start of line or after whitespace
            # This prevents removing single quotes inside strings
            code = re.sub(r"^\s*'.*?$", '', code, flags=re.MULTILINE)
        
        # Remove trailing whitespace from each line
        code = re.sub(r'[ \t]+$', '', code, flags=re.MULTILINE)
        
        # Clean up blank lines: collapse 3+ consecutive newlines into 2 (keeping max 1 blank line)
        code = re.sub(r'\n{3,}', '\n\n', code)
        
        return code
    
    def _remove_console_output(self, code: str, file_extension: str) -> str:
        """Remove console output statements from source code
        
        Args:
            code: Source code string
            file_extension: File extension (e.g., '.cs', '.c', '.py')
            
        Returns:
            Code with console output removed
        """
        import re
        
        # C# - Remove Console.WriteLine, Console.Write, etc.
        if file_extension in ['.cs']:
            # Remove entire Console.WriteLine/Write lines
            # Use a pattern that matches the statement and removes just the content, not the line structure
            lines = code.split('\n')
            filtered_lines = []
            for line in lines:
                # Check if line contains a Console output statement
                if re.match(r'^\s*Console\.(WriteLine|Write|Error\.WriteLine)', line.strip()):
                    # Skip this line (effectively removing it)
                    continue
                filtered_lines.append(line)
            code = '\n'.join(filtered_lines)
        
        # C/C++ - Remove printf, fprintf, puts, etc.
        elif file_extension in ['.c', '.cpp', '.h', '.hpp']:
            lines = code.split('\n')
            filtered_lines = []
            for line in lines:
                if re.match(r'^\s*(printf|fprintf|puts|fputs)\s*\(', line.strip()):
                    continue
                filtered_lines.append(line)
            code = '\n'.join(filtered_lines)
        
        # Python - Remove print statements
        elif file_extension in ['.py']:
            lines = code.split('\n')
            filtered_lines = []
            for line in lines:
                if re.match(r'^\s*print\s*\(', line.strip()):
                    continue
                filtered_lines.append(line)
            code = '\n'.join(filtered_lines)
        
        # PowerShell - Remove Write-Host, Write-Verbose, Write-Debug (but NOT Write-Output as it's used for returns)
        elif file_extension in ['.ps1']:
            lines = code.split('\n')
            filtered_lines = []
            for line in lines:
                if re.match(r'^\s*(Write-Host|Write-Verbose|Write-Debug|Write-Information|echo)\s+', line.strip()):
                    continue
                filtered_lines.append(line)
            code = '\n'.join(filtered_lines)
        
        # Clean up excessive blank lines (keep max 1 blank line)
        code = re.sub(r'\n{3,}', '\n\n', code)
        
        return code
    
    def _strip_binary(self, binary_path: Path) -> bool:
        """Strip debug symbols and metadata from compiled binary
        
        Args:
            binary_path: Path to binary file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use strip command if available (Linux/Unix)
            result = subprocess.run(
                ['strip', '--strip-all', str(binary_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except FileNotFoundError:
            # strip command not available
            return False
        except Exception:
            return False
    
    def _obfuscate_powershell(self, source_file: Path, output_path: Path, 
                              output_file: str, level: str) -> Tuple[bool, str]:
        """Obfuscate PowerShell script using psobf with failover
        
        Args:
            source_file: Path to the source PowerShell file
            output_path: Directory for output files
            output_file: Desired output filename
            level: Obfuscation level ('high', 'medium', 'low')
            
        Returns:
            Tuple of (success: bool, output_file_path: str)
        """
        import random
        import string
        
        # Prepare temp and final file paths
        temp_file = source_file  # Input file
        final_file = output_path / output_file
        
        # Define obfuscation levels in order of priority
        levels = []
        if level == 'high':
            levels = ['high', 'medium', 'low']
        elif level == 'medium':
            levels = ['medium', 'low']
        else:
            levels = ['low']
        
        # Try each level with failover
        for current_level in levels:
            step_name = f"Obfuscating PowerShell ({current_level.upper()} level)"
            obf_step = BuildStep(step_name, "obfuscation")
            self.steps.append(obf_step)
            obf_step.status = "running"
            self._update_step(obf_step)
            
            # Generate random values for command
            # Hex key must be even length (2 hex chars = 1 byte), so 8-32 bytes = 16-64 hex chars
            rand_hex_bytes = random.randint(8, 32)
            rand_hex_length = rand_hex_bytes * 2  # Ensure even length
            rand_hex = ''.join(random.choices('0123456789abcdef', k=rand_hex_length))
            rand_stringdict = random.randint(0, 100)
            rand_deadcode = random.randint(0, 100)
            rand_seed = random.randint(0 if current_level != 'high' else 1, 10000)
            
            # Build command based on level
            if current_level == 'high':
                command = (
                    f'psobf -i "{temp_file}" -o "{final_file}" -q -level 5 '
                    f'-pipeline "iden,strenc,stringdict,numenc,fmt,cf,dead,frag" '
                    f'-iden obf -strenc xor -strkey {rand_hex} '
                    f'-stringdict {rand_stringdict} -numenc -fmt jitter -cf-opaque '
                    f'-deadcode {rand_deadcode} -frag profile=medium -seed {rand_seed}'
                )
            elif current_level == 'medium':
                command = (
                    f'psobf -i "{temp_file}" -o "{final_file}" -q -level 3 '
                    f'-pipeline "iden,strenc,stringdict,numenc,fmt,cf,dead,frag" '
                    f'-strenc xor -strkey {rand_hex} -stringdict {rand_stringdict} '
                    f'-deadcode {rand_deadcode} -fmt jitter -frag profile=medium '
                    f'-seed {rand_seed}'
                )
            else:  # low
                command = (
                    f'psobf -i "{temp_file}" -o "{final_file}" '
                    f'-level 2 -seed {rand_seed}'
                )
            
            obf_step.output = f"Running: {command}"
            self._update_step(obf_step)
            
            try:
                # Execute psobf command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                # Check if obfuscation was successful
                if result.returncode == 0 and final_file.exists():
                    obf_step.status = "success"
                    obf_step.output = f"Command: {command}\n\nPowerShell obfuscation successful ({current_level} level)"
                    self._update_step(obf_step)
                    return True, str(final_file)
                else:
                    # Obfuscation failed, log the error
                    error_msg = result.stderr if result.stderr else result.stdout
                    obf_step.status = "failed"
                    obf_step.error = f"Obfuscation failed: {error_msg}"
                    self._update_step(obf_step)
                    
                    # If this isn't the last level, continue to next level
                    if current_level != levels[-1]:
                        continue
                    
            except subprocess.TimeoutExpired:
                obf_step.status = "failed"
                obf_step.error = f"Obfuscation timed out at {current_level} level"
                self._update_step(obf_step)
                
                # Try next level
                if current_level != levels[-1]:
                    continue
                    
            except Exception as e:
                obf_step.status = "failed"
                obf_step.error = f"Obfuscation error: {str(e)}"
                self._update_step(obf_step)
                
                # Try next level
                if current_level != levels[-1]:
                    continue
        
        # All levels failed, add warning step and continue without obfuscation
        warning_step = BuildStep("Obfuscation skipped", "warning")
        self.steps.append(warning_step)
        warning_step.status = "success"
        warning_step.output = "All obfuscation levels failed, continuing with non-obfuscated script"
        self._update_step(warning_step)
        
        # Copy the original file to final destination
        import shutil
        shutil.copy2(temp_file, final_file)
        
        return True, str(final_file)
    
    def _insert_amsi_bypass_template(self, ps1_file: Path, bypass_method: str) -> bool:
        """Insert AMSI bypass at the beginning of a PowerShell template
        
        Args:
            ps1_file: Path to the PowerShell file
            bypass_method: Name of the bypass method to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load bypass code
            amsi_dir = self.config.templates_dir / 'amsi_bypasses'
            bypass_file = amsi_dir / f"{bypass_method.replace(' ', '_')}.ps1"
            
            if not bypass_file.exists():
                return False
            
            with open(bypass_file, 'r') as f:
                bypass_code = f.read().strip()
            
            # Read existing file
            with open(ps1_file, 'r') as f:
                original_code = f.read()
            
            # Insert bypass at the beginning
            modified_code = f"{bypass_code}\n\n{original_code}"
            
            # Write back
            with open(ps1_file, 'w') as f:
                f.write(modified_code)
            
            return True
            
        except Exception as e:
            return False
