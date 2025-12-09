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


@app.route('/api/recipes')
def get_recipes():
    """Get all recipes organized by category"""
    # Organize recipes by category
    categories = {}
    for recipe in recipes:
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
        'total_recipes': len(recipes),
        'total_categories': len(categories)
    })


@app.route('/api/recipe/<category>/<name>')
def get_recipe(category, name):
    """Get a specific recipe by category and name"""
    for recipe in recipes:
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
    for recipe in recipes:
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
    
    # Find recipe
    recipe_obj = None
    for r in recipes:
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
        'steps': [],
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
            
            builder = PayloadBuilder(temp_config)
            
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
                    build_sessions[session_id]['launch_instructions'] = recipe_obj.launch_instructions
                    
                    # Add to history
                    if history_manager:
                        history_manager.add_entry(
                            recipe_name=recipe_obj.name,
                            success=True,
                            output_file=output_file,
                            parameters=validated_params,
                            launch_instructions=recipe_obj.launch_instructions or "",
                            build_steps=[{
                                'name': s.name,
                                'type': s.type,
                                'status': s.status
                            } for s in steps]
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
                                'status': s.status
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
