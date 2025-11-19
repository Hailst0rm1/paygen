"""
Template rendering utilities

Handles Jinja2 template rendering for both source code and command generation.
"""

from pathlib import Path
from typing import Dict, Any
from jinja2 import Template, Environment, FileSystemLoader, TemplateError


class TemplateRenderer:
    """Render Jinja2 templates with parameters."""
    
    def __init__(self, template_dirs: list = None):
        """
        Initialize template renderer.
        
        Args:
            template_dirs: List of directories to search for templates
        """
        self.template_dirs = template_dirs or []
        
        # Create Jinja2 environment
        if template_dirs:
            self.env = Environment(
                loader=FileSystemLoader(template_dirs),
                trim_blocks=True,
                lstrip_blocks=True,
                keep_trailing_newline=True
            )
        else:
            self.env = None
    
    def render_file(self, template_path: Path, parameters: Dict[str, Any]) -> str:
        """
        Render a template file.
        
        Args:
            template_path: Path to template file
            parameters: Template variables
            
        Returns:
            Rendered template content
            
        Raises:
            TemplateError: If rendering fails
        """
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        try:
            template_content = template_path.read_text()
            return self.render_string(template_content, parameters)
        except Exception as e:
            raise TemplateError(f"Failed to render template {template_path}: {e}")
    
    def render_string(self, template_string: str, parameters: Dict[str, Any]) -> str:
        """
        Render a template string.
        
        Args:
            template_string: Template content as string
            parameters: Template variables
            
        Returns:
            Rendered content
            
        Raises:
            TemplateError: If rendering fails
        """
        try:
            template = Template(template_string)
            return template.render(**parameters)
        except Exception as e:
            raise TemplateError(f"Template rendering failed: {e}")
    
    def render_command(self, command_template: str, parameters: Dict[str, Any]) -> str:
        """
        Render a command template (for command-based recipes).
        
        Args:
            command_template: Command template string with Jinja2 syntax
            parameters: Command parameters
            
        Returns:
            Rendered command ready to execute
            
        Raises:
            TemplateError: If rendering fails
        """
        return self.render_string(command_template, parameters)
    
    def add_template_dir(self, directory: Path):
        """
        Add a directory to template search path.
        
        Args:
            directory: Directory to add
        """
        if directory not in self.template_dirs:
            self.template_dirs.append(directory)
            
            # Recreate environment with updated dirs
            self.env = Environment(
                loader=FileSystemLoader(self.template_dirs),
                trim_blocks=True,
                lstrip_blocks=True,
                keep_trailing_newline=True
            )
