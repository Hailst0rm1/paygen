"""
Payload Builder - Main payload generation orchestrator

Coordinates preprocessing, template rendering, compilation, and command execution.
"""

import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.core.recipe_loader import Recipe
from src.core.preprocessor import Preprocessor, PreprocessingError
from src.core.compiler import Compiler, CompilationError
from src.core.command_executor import CommandExecutor, CommandExecutionError, DependencyError
from src.utils.templates import TemplateRenderer


class PayloadBuildError(Exception):
    """Raised when payload building fails."""
    pass


class PayloadBuilder:
    """Build payloads from recipes."""
    
    def __init__(self, project_root: Path):
        """
        Initialize payload builder.
        
        Args:
            project_root: Root directory of paygen project
        """
        self.project_root = project_root
        self.recipes_dir = project_root / "recipes"
        self.payloads_dir = project_root / "payloads"
        self.output_dir = project_root / "output"
        
        # Initialize components
        self.preprocessor = Preprocessor()
        self.compiler = Compiler()
        self.executor = CommandExecutor()
        self.renderer = TemplateRenderer(template_dirs=[str(self.payloads_dir)])
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
    
    def build(
        self,
        recipe: Recipe,
        parameters: Dict[str, Any],
        selected_sub_recipes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Build payload from recipe.
        
        Args:
            recipe: Recipe to build
            parameters: User-provided parameters
            selected_sub_recipes: List of selected sub-recipe names
            
        Returns:
            Dictionary with build results
            
        Raises:
            PayloadBuildError: If build fails
        """
        try:
            # Validate parameters
            self._validate_parameters(recipe, parameters)
            
            # Prepare output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = self._generate_output_filename(recipe, parameters, timestamp)
            output_path = self.output_dir / output_filename
            
            # Add output filename to parameters for template use
            parameters['output_filename'] = output_filename
            parameters['timestamp'] = timestamp
            parameters['output_dir'] = str(self.output_dir)
            
            # Build based on recipe type
            if recipe.is_template_based():
                result = self._build_template_based(
                    recipe,
                    parameters,
                    selected_sub_recipes or [],
                    output_path
                )
            else:
                result = self._build_command_based(
                    recipe,
                    parameters,
                    selected_sub_recipes or [],
                    output_path
                )
            
            # Generate launch instructions
            launch_instructions = self._generate_launch_instructions(recipe, parameters)
            result['launch_instructions'] = launch_instructions
            
            # Calculate file hash if output exists
            if output_path.exists():
                result['sha256'] = self._calculate_hash(output_path)
            
            return result
        
        except Exception as e:
            raise PayloadBuildError(f"Payload build failed: {e}")
    
    def _validate_parameters(self, recipe: Recipe, parameters: Dict[str, Any]):
        """Validate that all required parameters are provided."""
        required = recipe.get_required_parameters()
        
        missing = []
        for param in required:
            param_name = param.get('name')
            if param_name not in parameters or parameters[param_name] is None:
                missing.append(param_name)
        
        if missing:
            raise PayloadBuildError(
                f"Missing required parameters: {', '.join(missing)}"
            )
    
    def _generate_output_filename(
        self,
        recipe: Recipe,
        parameters: Dict[str, Any],
        timestamp: str
    ) -> str:
        """Generate output filename from pattern."""
        # Get pattern from recipe
        pattern = recipe.data.get('output', {}).get('filename_pattern', '')
        
        if not pattern:
            # Default pattern
            recipe_name = recipe.name.lower().replace(' ', '_')
            pattern = f"{recipe_name}_{timestamp}.bin"
        else:
            # Render pattern with parameters
            template_vars = {
                'recipe_name': recipe.name.lower().replace(' ', '_'),
                'timestamp': timestamp,
                **parameters
            }
            
            try:
                pattern = self.renderer.render_string(pattern, template_vars)
            except Exception:
                # Fallback to simple pattern
                pattern = f"{recipe.name.lower().replace(' ', '_')}_{timestamp}.bin"
        
        return pattern
    
    def _build_template_based(
        self,
        recipe: Recipe,
        parameters: Dict[str, Any],
        selected_sub_recipes: List[str],
        output_path: Path
    ) -> Dict[str, Any]:
        """Build template-based payload."""
        recipe_dir = self.recipes_dir / recipe.mitre_tactic.split(' - ')[0].lower()
        
        # Process sub-recipes
        processed_subs = []
        for sub_name in selected_sub_recipes:
            # Find sub-recipe definition
            sub_recipe = None
            for sub in recipe.sub_recipes:
                if sub.get('name') == sub_name:
                    sub_recipe = sub
                    break
            
            if not sub_recipe:
                continue
            
            # Process sub-recipe preprocessing
            preprocessing = sub_recipe.get('preprocessing', [])
            for preproc_op in preprocessing:
                processed = self.preprocessor.process(preproc_op, parameters, recipe_dir)
                processed_subs.append({
                    'name': sub_name,
                    'data': processed
                })
                
                # Add processed data to parameters for template use
                if preproc_op.get('type') == 'xor_encrypt':
                    parameters['encrypted_shellcode'] = self.preprocessor.crypto.bytes_to_c_array(
                        processed['data'], 'shellcode'
                    )
                elif preproc_op.get('type') == 'aes_encrypt':
                    parameters['encrypted_shellcode'] = self.preprocessor.crypto.bytes_to_c_array(
                        processed['data'], 'shellcode'
                    )
                    parameters['aes_iv'] = processed['iv_hex']
        
        # Get source template path
        source_template = None
        if selected_sub_recipes and recipe.sub_recipes:
            # Use first selected sub-recipe's template
            for sub in recipe.sub_recipes:
                if sub.get('name') == selected_sub_recipes[0]:
                    source_template = sub.get('source_template')
                    break
        
        if not source_template:
            raise PayloadBuildError("No source template specified")
        
        # Resolve template path
        template_path = self.project_root / source_template
        
        # Render template
        rendered_source = self.renderer.render_file(template_path, parameters)
        
        # Save rendered source to temp file
        temp_source = self.output_dir / f"temp_{output_path.stem}.c"
        temp_source.write_text(rendered_source)
        
        # Compile
        compile_cmd = recipe.data.get('output', {}).get('compile_command')
        
        try:
            compile_result = self.compiler.compile(
                source_path=temp_source,
                output_path=output_path,
                compile_command=compile_cmd
            )
            
            # Clean up temp source
            temp_source.unlink()
            
            return {
                'success': True,
                'type': 'template',
                'output_path': str(output_path),
                'output_size': compile_result['output_size'],
                'selected_sub_recipes': selected_sub_recipes,
                'compilation': compile_result
            }
        
        except CompilationError as e:
            # Keep temp source for debugging
            raise PayloadBuildError(f"Compilation failed: {e}\nSource saved to: {temp_source}")
    
    def _build_command_based(
        self,
        recipe: Recipe,
        parameters: Dict[str, Any],
        selected_sub_recipes: List[str],
        output_path: Path
    ) -> Dict[str, Any]:
        """Build command-based payload."""
        # Check dependencies
        dependencies = recipe.data.get('dependencies', [])
        
        if dependencies:
            try:
                dep_check = self.executor.check_all_dependencies(dependencies)
                if not dep_check['all_satisfied']:
                    missing_info = []
                    for missing in dep_check['missing']:
                        missing_info.append(
                            f"  {missing['tool']}: {missing['install_hint']}"
                        )
                    raise PayloadBuildError(
                        "Missing dependencies:\n" + "\n".join(missing_info)
                    )
            except DependencyError as e:
                raise PayloadBuildError(str(e))
        
        # Get generation command
        if selected_sub_recipes and recipe.sub_recipes:
            # Use sub-recipe command
            command_template = None
            for sub in recipe.sub_recipes:
                if sub.get('name') == selected_sub_recipes[0]:
                    command_template = sub.get('generation_command')
                    break
            
            if not command_template:
                command_template = recipe.data.get('generation_command')
        else:
            command_template = recipe.data.get('generation_command')
        
        if not command_template:
            raise PayloadBuildError("No generation command specified")
        
        # Render command with parameters
        try:
            command = self.renderer.render_command(command_template, parameters)
        except Exception as e:
            raise PayloadBuildError(f"Command rendering failed: {e}")
        
        # Execute command
        try:
            exec_result = self.executor.execute_command(
                command,
                working_dir=self.output_dir
            )
            
            if not exec_result['success']:
                raise PayloadBuildError(
                    f"Command execution failed:\n"
                    f"STDOUT: {exec_result['stdout']}\n"
                    f"STDERR: {exec_result['stderr']}"
                )
            
            # Check if output was created
            output_size = output_path.stat().st_size if output_path.exists() else 0
            
            return {
                'success': True,
                'type': 'command',
                'output_path': str(output_path),
                'output_size': output_size,
                'selected_sub_recipes': selected_sub_recipes,
                'execution': exec_result
            }
        
        except CommandExecutionError as e:
            raise PayloadBuildError(f"Command execution failed: {e}")
    
    def _generate_launch_instructions(
        self,
        recipe: Recipe,
        parameters: Dict[str, Any]
    ) -> str:
        """Generate launch instructions from recipe."""
        instructions = recipe.launch_instructions
        
        if not instructions:
            return "No launch instructions provided."
        
        # Render instructions with parameters
        try:
            return self.renderer.render_string(instructions, parameters)
        except Exception:
            return instructions  # Return as-is if rendering fails
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
