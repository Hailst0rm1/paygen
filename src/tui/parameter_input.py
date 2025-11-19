"""
Parameter Input Panel - Dynamic form generation for recipe parameters

Creates input forms based on recipe parameter definitions.
"""

from textual.widgets import Input, Label, Button, Checkbox, Static
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.validation import ValidationResult, Validator
from typing import Dict, Any, List, Optional

from src.core.recipe_loader import Recipe
from src.core.validator import ParameterValidator


class ParameterInputPanel(ScrollableContainer):
    """Panel for inputting recipe parameters."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.recipe = None
        self.validator = ParameterValidator()
        self.inputs = {}  # Store input widgets
        self.sub_recipe_checkboxes = {}  # Store sub-recipe checkboxes
    
    def compose(self):
        """Compose the parameter input panel."""
        yield Label("⚙️  Configure Parameters", id="param-panel-title")
        yield Static("Select a recipe to configure parameters", id="param-content")
    
    def show_recipe(self, recipe: Recipe):
        """
        Display parameter input form for recipe.
        
        Args:
            recipe: Recipe to show parameters for
        """
        self.recipe = recipe
        self.inputs.clear()
        self.sub_recipe_checkboxes.clear()
        
        # Build form
        form_widgets = []
        
        # Section: Required Parameters
        required = recipe.get_required_parameters()
        if required:
            form_widgets.append(Label("Required Parameters", classes="section-header"))
            
            for param in required:
                widget = self._create_parameter_input(param, required=True)
                form_widgets.append(widget)
        
        # Section: Optional Parameters
        optional = recipe.get_optional_parameters()
        if optional:
            form_widgets.append(Label("\nOptional Parameters", classes="section-header"))
            
            for param in optional:
                widget = self._create_parameter_input(param, required=False)
                form_widgets.append(widget)
        
        # Section: Sub-Recipes (if available)
        if recipe.sub_recipes:
            form_widgets.append(Label("\n🧩 Sub-Recipes (Select one or more)", classes="section-header"))
            
            for sub in recipe.sub_recipes:
                checkbox = self._create_sub_recipe_checkbox(sub)
                form_widgets.append(checkbox)
        
        # Generate button
        form_widgets.append(Label(""))  # Spacer
        form_widgets.append(Button("🚀 Generate Payload", id="generate-button", variant="success"))
        
        # Update content
        content = Vertical(*form_widgets, id="param-form")
        
        # Remove old content and add new
        self.query("#param-content").remove()
        self.mount(content)
    
    def _create_parameter_input(self, param: Dict[str, Any], required: bool) -> Horizontal:
        """Create input widget for a parameter."""
        name = param.get('name', 'unknown')
        param_type = param.get('type', 'string')
        description = param.get('description', '')
        default = param.get('default', '')
        
        # Create label
        label_text = f"{name}"
        if required:
            label_text += " *"
        label_text += f" ({param_type})"
        
        label = Label(label_text, classes="param-label")
        
        # Create input based on type
        if param_type == 'bool':
            input_widget = Checkbox(f"Enable {name}", value=bool(default))
        elif param_type == 'choice':
            # For choices, we'll use a simple input with placeholder showing options
            choices = param.get('choices', [])
            input_widget = Input(
                placeholder=f"Choose from: {', '.join(choices)}",
                value=str(default) if default else ""
            )
        else:
            # Standard input
            placeholder = description if description else f"Enter {param_type}"
            input_widget = Input(
                placeholder=placeholder,
                value=str(default) if default else ""
            )
        
        # Store input widget
        self.inputs[name] = {
            'widget': input_widget,
            'param': param,
            'required': required
        }
        
        # Create container
        container = Vertical(
            label,
            input_widget,
            Static(f"  {description}", classes="param-description") if description else Static(""),
            classes="param-input-group"
        )
        
        return container
    
    def _create_sub_recipe_checkbox(self, sub_recipe: Dict[str, Any]) -> Horizontal:
        """Create checkbox for sub-recipe selection."""
        name = sub_recipe.get('name', 'Unknown')
        description = sub_recipe.get('description', '')
        
        checkbox = Checkbox(f"{name}", value=False)
        
        # Store checkbox
        self.sub_recipe_checkboxes[name] = checkbox
        
        container = Vertical(
            checkbox,
            Static(f"  {description}", classes="sub-recipe-description") if description else Static(""),
            classes="sub-recipe-group"
        )
        
        return container
    
    def get_parameters(self) -> Dict[str, Any]:
        """
        Get current parameter values from inputs.
        
        Returns:
            Dictionary of parameter values
            
        Raises:
            ValueError: If validation fails
        """
        parameters = {}
        errors = []
        
        for name, input_data in self.inputs.items():
            widget = input_data['widget']
            param = input_data['param']
            required = input_data['required']
            
            # Get value
            if isinstance(widget, Checkbox):
                value = widget.value
            else:
                value = widget.value.strip()
            
            # Check required
            if required and not value:
                errors.append(f"Required parameter '{name}' is missing")
                continue
            
            # Skip empty optional parameters
            if not value:
                continue
            
            # Validate
            is_valid, error_msg = self.validator.validate_parameter(param, value)
            
            if not is_valid:
                errors.append(f"Parameter '{name}': {error_msg}")
                continue
            
            # Normalize and store
            normalized = self.validator.normalize_value(param, value)
            parameters[name] = normalized
        
        if errors:
            raise ValueError("Validation errors:\n  " + "\n  ".join(errors))
        
        return parameters
    
    def get_selected_sub_recipes(self) -> List[str]:
        """
        Get list of selected sub-recipe names.
        
        Returns:
            List of selected sub-recipe names
        """
        selected = []
        
        for name, checkbox in self.sub_recipe_checkboxes.items():
            if checkbox.value:
                selected.append(name)
        
        return selected
    
    def clear(self):
        """Clear the parameter input panel."""
        self.recipe = None
        self.inputs.clear()
        self.sub_recipe_checkboxes.clear()
        
        # Reset content
        try:
            self.query("#param-form").remove()
        except Exception:
            pass
        
        self.mount(Static("Select a recipe to configure parameters", id="param-content"))
