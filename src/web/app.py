"""
Flask Web Application for Paygen

Provides a web-based GUI for payload generation while reusing
all core functionality from the TUI version.
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
from typing import Dict, Any, Optional
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


def load_amsi_bypasses():
    """Load AMSI bypass methods from templates/amsi_bypasses directory
    
    Returns:
        Dict mapping bypass names to their code content
    """
    bypasses = {}
    amsi_dir = config.templates_dir / 'amsi_bypasses'
    
    if not amsi_dir.exists():
        return bypasses
    
    for bypass_file in amsi_dir.glob('*.ps1'):
        # Convert filename to display name (remove extension, replace _ with space)
        name = bypass_file.stem.replace('_', ' ')
        
        try:
            with open(bypass_file, 'r') as f:
                code = f.read().strip()
                bypasses[name] = code
        except Exception as e:
            print(f"Warning: Failed to load AMSI bypass {bypass_file}: {e}", file=sys.stderr)
    
    return bypasses


def inject_amsi_bypass_launch_instructions(launch_instructions: str, bypass_method: str) -> str:
    """Inject AMSI bypass into launch instructions
    
    Args:
        launch_instructions: Markdown text containing PowerShell code blocks
        bypass_method: Name of the bypass method to use
        
    Returns:
        Modified launch instructions with AMSI bypass injected
    """
    if not launch_instructions:
        return launch_instructions
    
    # Load bypass code
    amsi_dir = config.templates_dir / 'amsi_bypasses'
    bypass_file = amsi_dir / f"{bypass_method.replace(' ', '_')}.ps1"
    
    if not bypass_file.exists():
        return launch_instructions
    
    try:
        with open(bypass_file, 'r') as f:
            bypass_code = f.read().strip()
    except:
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


def obfuscate_powershell_in_launch_instructions(launch_instructions: str, level: str) -> tuple:
    """Obfuscate PowerShell code blocks in launch instructions
    
    Args:
        launch_instructions: Markdown text containing PowerShell code blocks
        level: Obfuscation level ('high', 'medium', 'low')
        
    Returns:
        Tuple of (modified_instructions, commands_executed)
    """
    if not launch_instructions:
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
            # Define obfuscation levels
            levels = []
            if level == 'high':
                levels = ['high', 'medium', 'low']
            elif level == 'medium':
                levels = ['medium', 'low']
            else:
                levels = ['low']
            
            # Try each level with failover
            for current_level in levels:
                # Generate random values
                rand_hex_bytes = random.randint(8, 32)
                rand_hex_length = rand_hex_bytes * 2
                rand_hex = ''.join(random.choices('0123456789abcdef', k=rand_hex_length))
                rand_stringdict = random.randint(0, 100)
                rand_deadcode = random.randint(0, 100)
                rand_seed = random.randint(0 if current_level != 'high' else 1, 10000)
                
                # Build command based on level
                if current_level == 'high':
                    command = (
                        f'psobf -i "{tmp_in_path}" -o "{tmp_out_path}" -q -level 5 '
                        f'-pipeline "iden,strenc,stringdict,numenc,fmt,cf,dead,frag" '
                        f'-iden obf -strenc xor -strkey {rand_hex} '
                        f'-stringdict {rand_stringdict} -numenc -fmt jitter -cf-opaque '
                        f'-deadcode {rand_deadcode} -frag profile=medium -seed {rand_seed}'
                    )
                elif current_level == 'medium':
                    command = (
                        f'psobf -i "{tmp_in_path}" -o "{tmp_out_path}" -q -level 3 '
                        f'-pipeline "iden,strenc,stringdict,numenc,fmt,cf,dead,frag" '
                        f'-strenc xor -strkey {rand_hex} -stringdict {rand_stringdict} '
                        f'-deadcode {rand_deadcode} -fmt jitter -frag profile=medium '
                        f'-seed {rand_seed}'
                    )
                else:
                    command = (
                        f'psobf -i "{tmp_in_path}" -o "{tmp_out_path}" '
                        f'-level 2 -seed {rand_seed}'
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
            
            # All levels failed, return original
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


def init_app():
    """Initialize the Flask application with paygen configuration"""
    global config, recipe_loader, recipes, history_manager
    
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


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                          show_build_debug=config.show_build_debug if config else False)


@app.route('/api/amsi-bypasses')
def get_amsi_bypasses():
    """Get available AMSI bypass methods"""
    bypasses = load_amsi_bypasses()
    # Return as list of names for dropdown
    return jsonify({'bypasses': sorted(bypasses.keys())})


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
    
    # Validate parameters
    validator = ParameterValidator()
    validated_params = {}
    
    try:
        for param_def in recipe_obj.parameters:
            param_name = param_def.get('name')
            value = parameters.get(param_name)
            
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
            
            # Build payload
            recipe_dict = recipe_obj.to_dict()
            success, output_file, steps = builder.build(recipe_dict, validated_params)
            
            with build_locks[session_id]:
                if success:
                    build_sessions[session_id]['status'] = 'success'
                    build_sessions[session_id]['output_file'] = output_file
                    
                    # Process launch instructions
                    final_launch_instructions = recipe_obj.launch_instructions
                    
                    # Step 1: Insert AMSI bypass if requested (BEFORE obfuscation)
                    if (build_options.get('amsi_bypass_launch', False) and 
                        recipe_obj.launch_instructions):
                        amsi_method = build_options.get('amsi_bypass_launch_method', '')
                        
                        if amsi_method:
                            # Add AMSI bypass step
                            amsi_step = {
                                'name': f'Inserting AMSI bypass in launch instructions ({amsi_method})',
                                'type': 'amsi_bypass',
                                'status': 'success',
                                'output': f"AMSI bypass '{amsi_method}' injected into launch instructions",
                                'error': ''
                            }
                            build_sessions[session_id]['steps'].append(amsi_step)
                            
                            # Inject bypass
                            final_launch_instructions = inject_amsi_bypass_launch_instructions(
                                final_launch_instructions,
                                amsi_method
                            )
                    
                    # Step 2: Obfuscate PowerShell if requested
                    if (build_options.get('obfuscate_launch_ps', False) and 
                        final_launch_instructions):
                        obf_level = build_options.get('obfuscate_launch_ps_level', 'low')
                        
                        # Add obfuscation step to build session
                        obf_step = {
                            'name': f'Obfuscating launch instructions ({obf_level.upper()} level)',
                            'type': 'obfuscation',
                            'status': 'running',
                            'output': f'Obfuscating PowerShell code blocks in launch instructions',
                            'error': ''
                        }
                        build_sessions[session_id]['steps'].append(obf_step)
                        
                        # Perform obfuscation
                        final_launch_instructions, commands = obfuscate_powershell_in_launch_instructions(
                            recipe_obj.launch_instructions, 
                            obf_level
                        )
                        
                        # Update step status with commands
                        commands_output = '\n\n'.join([f'Command: {cmd}' for cmd in commands]) if commands else 'No PowerShell code blocks found'
                        obf_step['status'] = 'success'
                        obf_step['output'] = f'{commands_output}\n\nSuccessfully obfuscated PowerShell code blocks ({obf_level.upper()} level)'
                    
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
