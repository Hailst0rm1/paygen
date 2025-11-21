"""Template rendering utilities using Jinja2"""

from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template, TemplateError

from ..core.config import get_config


class TemplateRenderer:
    """Renders Jinja2 templates with parameters and preprocessing outputs"""
    
    def __init__(self, config=None):
        """Initialize template renderer
        
        Args:
            config: Optional ConfigManager instance
        """
        self.config = config or get_config()
        
        # Set up Jinja2 environment for file-based templates
        self.env = Environment(
            loader=FileSystemLoader(str(self.config.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
    
    def render_template_file(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a template file with given context
        
        Args:
            template_path: Path to template file (relative to templates_dir)
            context: Dictionary of variables to pass to template
            
        Returns:
            Rendered template string
            
        Raises:
            TemplateError: If template rendering fails
        """
        try:
            template = self.env.get_template(template_path)
            return template.render(**context)
        except TemplateError as e:
            raise TemplateError(f"Failed to render template {template_path}: {e}")
    
    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string with given context
        
        Args:
            template_string: Template string
            context: Dictionary of variables to pass to template
            
        Returns:
            Rendered string
            
        Raises:
            TemplateError: If template rendering fails
        """
        try:
            template = Template(template_string)
            return template.render(**context)
        except TemplateError as e:
            raise TemplateError(f"Failed to render template string: {e}")
    
    def render_command(self, command_template: str, context: Dict[str, Any]) -> str:
        """Render a command template with given context
        
        This is a convenience wrapper for render_string() for command templates.
        
        Args:
            command_template: Command template string
            context: Dictionary of variables to pass to template
            
        Returns:
            Rendered command string
        """
        return self.render_string(command_template, context)
    
    def prepare_context(self, parameters: Dict[str, Any], 
                       preprocessing_outputs: Optional[Dict[str, Any]] = None,
                       config_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare template context from parameters and preprocessing outputs
        
        Args:
            parameters: User-provided parameter values
            preprocessing_outputs: Output variables from preprocessing steps
            config_vars: Additional config variables to include
            
        Returns:
            Complete context dictionary for template rendering
        """
        context = {}
        
        # Add user parameters
        context.update(parameters)
        
        # Add preprocessing outputs
        if preprocessing_outputs:
            context.update(preprocessing_outputs)
        
        # Add config variables with 'config.' prefix
        if config_vars:
            context['config'] = config_vars
        else:
            # Add default config values
            context['config'] = {
                'output_dir': str(self.config.output_dir),
                'templates_dir': str(self.config.templates_dir),
                'preprocessors_dir': str(self.config.preprocessors_dir),
            }
        
        return context
    
    def validate_template_syntax(self, template_path: str) -> bool:
        """Validate template syntax without rendering
        
        Args:
            template_path: Path to template file
            
        Returns:
            True if valid
            
        Raises:
            TemplateError: If syntax is invalid
        """
        try:
            self.env.get_template(template_path)
            return True
        except TemplateError as e:
            raise TemplateError(f"Template syntax error in {template_path}: {e}")
