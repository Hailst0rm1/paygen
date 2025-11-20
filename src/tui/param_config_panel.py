"""
Parameter Configuration Panel

Panel for configuring recipe parameters before generation (replaces middle panel).
"""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, Vertical
from textual.widgets import Static, Input, Button, Select, Checkbox
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message

from .colors import MOCHA, get_effectiveness_badge
from ..core.validator import ParameterValidator, ValidationError


class ParameterConfigPanel(Widget):
    """Panel for configuring recipe parameters."""
    
    DEFAULT_CSS = """
    ParameterConfigPanel {
        width: 35%;
        height: 100%;
        border: solid """ + MOCHA['surface1'] + """;
        background: #1e1e2e;
    }
    
    ParameterConfigPanel:focus-within {
        border: double """ + MOCHA['blue'] + """;
    }
    
    ParameterConfigPanel .panel-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: #1e1e2e;
        padding: 1;
        text-align: center;
        dock: top;
    }
    
    ParameterConfigPanel #params-scroll {
        height: 1fr;
        border: none;
        background: #1e1e2e;
        padding: 1;
    }
    
    ParameterConfigPanel .param-label {
        color: """ + MOCHA['text'] + """;
        padding: 0 1;
        margin-top: 1;
    }
    
    ParameterConfigPanel .param-required {
        color: """ + MOCHA['red'] + """;
    }
    
    ParameterConfigPanel .param-description {
        color: """ + MOCHA['subtext0'] + """;
        padding: 0 1;
        text-style: italic;
    }
    
    ParameterConfigPanel Input {
        margin: 0 1;
        background: #1e1e2e;
        border: solid """ + MOCHA['surface2'] + """;
    }
    
    ParameterConfigPanel Input:focus {
        border: solid """ + MOCHA['blue'] + """;
    }
    
    ParameterConfigPanel Select {
        margin: 0 1;
        background: #1e1e2e;
        border: solid """ + MOCHA['surface2'] + """;
    }
    
    ParameterConfigPanel Select:focus {
        border: solid """ + MOCHA['blue'] + """;
    }
    
    ParameterConfigPanel Checkbox {
        margin: 0 1;
        background: #1e1e2e;
    }
    
    ParameterConfigPanel .error-message {
        color: """ + MOCHA['red'] + """;
        padding: 0 1;
    }
    
    ParameterConfigPanel .button-container {
        height: auto;
        align: center middle;
        padding: 1;
        margin-top: 1;
        dock: bottom;
    }
    
    ParameterConfigPanel Button {
        margin: 0 2;
        min-width: 15;
    }
    
    ParameterConfigPanel Button.primary {
        background: """ + MOCHA['green'] + """;
        color: """ + MOCHA['base'] + """;
    }
    
    ParameterConfigPanel Button.primary:hover {
        background: """ + MOCHA['green'] + """;
    }
    
    ParameterConfigPanel Button.primary:focus {
        background: """ + MOCHA['green'] + """;
    }
    
    ParameterConfigPanel Button.default {
        background: """ + MOCHA['surface2'] + """;
        color: """ + MOCHA['text'] + """;
    }
    
    ParameterConfigPanel Button.default:hover {
        background: """ + MOCHA['surface2'] + """;
    }
    
    ParameterConfigPanel Button.default:focus {
        background: """ + MOCHA['surface2'] + """;
    }
    """
    
    class GenerateRequested(Message):
        """Message sent when user requests to generate payload."""
        def __init__(self, params: dict) -> None:
            super().__init__()
            self.params = params
    
    class CancelRequested(Message):
        """Message sent when user cancels parameter configuration."""
        pass
    
    def __init__(self, recipe=None, config=None, **kwargs):
        """
        Initialize parameter configuration panel.
        
        Args:
            recipe: Recipe object to configure
            config: Configuration object for resolving defaults
        """
        super().__init__(**kwargs)
        self.recipe = recipe
        self.config = config
        self.validator = ParameterValidator()
        self.param_values = {}
        self.param_errors = {}
    
    def compose(self) -> ComposeResult:
        """Compose the configuration panel."""
        if not self.recipe:
            yield Static("No recipe selected", classes="panel-title")
            return
        
        yield Static(f"Configure: {self.recipe.name}", classes="panel-title")
        
        with VerticalScroll(id="params-scroll"):
            # Generate parameter inputs based on recipe parameters
            for param in self.recipe.parameters:
                for widget in self._create_parameter_widgets(param):
                    yield widget
        
        with Horizontal(classes="button-container"):
            yield Button("Generate", variant="primary", id="generate-btn")
            yield Button("Cancel", variant="default", id="cancel-btn")
    
    def _create_parameter_widgets(self, param):
        """
        Create widgets for a single parameter.
        
        Args:
            param: Parameter definition dict
            
        Returns:
            List of widgets for this parameter
        """
        widgets = []
        
        name = param.get('name', 'unknown')
        param_type = param.get('type', 'string')
        description = param.get('description', '')
        required = param.get('required', False)
        default = param.get('default', '')
        
        # Resolve {config.*} placeholders in defaults
        if isinstance(default, str) and default.startswith('{config.'):
            config_key = default[8:-1]  # Extract key from {config.key}
            if self.config:
                default = str(getattr(self.config, config_key, default))
        
        # Store default value
        self.param_values[name] = default
        
        # Parameter label with required indicator
        req_marker = "[param-required]*[/param-required] " if required else ""
        label = f"{req_marker}[bold]{name}[/bold] ([{MOCHA['sky']}]{param_type}[/{MOCHA['sky']}])"
        
        widgets.append(Static(label, classes="param-label", markup=True))
        
        if description:
            widgets.append(Static(description, classes="param-description"))
        
        # Create input widget based on type
        if param_type == 'choice':
            choices = param.get('choices', [])
            options = [(choice, choice) for choice in choices]
            select = Select(options, value=default, id=f"param-{name}")
            widgets.append(select)
        
        elif param_type == 'bool':
            checkbox = Checkbox(value=bool(default), id=f"param-{name}")
            widgets.append(checkbox)
        
        elif param_type == 'integer':
            input_widget = Input(
                value=str(default),
                placeholder=f"Enter {param_type}",
                id=f"param-{name}"
            )
            widgets.append(input_widget)
        
        else:
            # Text input for string, ip, port, path, hex
            input_widget = Input(
                value=str(default) if default else "",
                placeholder=f"Enter {param_type}",
                id=f"param-{name}"
            )
            widgets.append(input_widget)
        
        # Placeholder for error messages
        widgets.append(Static("", classes="error-message", id=f"error-{name}"))
        
        return widgets
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes for real-time validation."""
        widget_id = event.input.id
        if not widget_id or not widget_id.startswith("param-"):
            return
        
        param_name = widget_id[6:]
        value = event.value
        
        self.param_values[param_name] = value
        
        # Find parameter definition
        param_def = None
        for param in self.recipe.parameters:
            if param.get('name') == param_name:
                param_def = param
                break
        
        if not param_def:
            return
        
        # Validate
        param_type = param_def.get('type', 'string')
        error = None
        
        try:
            if param_type == 'ip':
                if value:
                    try:
                        self.validator.validate_ip(value)
                    except ValidationError as e:
                        error = str(e)
            elif param_type == 'port':
                if value:
                    try:
                        self.validator.validate_port(value)
                    except ValidationError as e:
                        error = str(e)
            elif param_type == 'path':
                if value:
                    try:
                        self.validator.validate_path(value)
                    except ValidationError as e:
                        error = str(e)
            elif param_type == 'hex':
                if value:
                    try:
                        self.validator.validate_hex(value)
                    except ValidationError as e:
                        error = str(e)
            elif param_type == 'integer':
                if value:
                    int_val = int(value)
                    if 'min' in param_def and int_val < param_def['min']:
                        error = f"Must be at least {param_def['min']}"
                    if 'max' in param_def and int_val > param_def['max']:
                        error = f"Must be at most {param_def['max']}"
        except (ValueError, TypeError):
            if param_type in ['port', 'integer']:
                error = f"Must be a valid number"
        
        # Update error message
        error_widget = self.query_one(f"#error-{param_name}", Static)
        if error:
            error_widget.update(f"⚠ {error}")
            self.param_errors[param_name] = error
        else:
            error_widget.update("")
            self.param_errors.pop(param_name, None)
    
    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select changes."""
        widget_id = event.select.id
        if not widget_id or not widget_id.startswith("param-"):
            return
        
        param_name = widget_id[6:]
        self.param_values[param_name] = event.value
    
    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox changes."""
        widget_id = event.checkbox.id
        if not widget_id or not widget_id.startswith("param-"):
            return
        
        param_name = widget_id[6:]
        self.param_values[param_name] = event.value
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "generate-btn":
            self._handle_generate()
        elif event.button.id == "cancel-btn":
            self.post_message(self.CancelRequested())
    
    def _handle_generate(self) -> None:
        """Handle generate button press."""
        # Check for validation errors
        if self.param_errors:
            self.app.notify("Please fix validation errors", severity="error")
            return
        
        # Check required parameters
        for param in self.recipe.parameters:
            if param.get('required') and not self.param_values.get(param['name']):
                param_name = param['name']
                error_widget = self.query_one(f"#error-{param_name}", Static)
                error_widget.update("⚠ This field is required")
                self.app.notify("Please fill in all required fields", severity="error")
                return
        
        # All validation passed, send generate message
        self.post_message(self.GenerateRequested(self.param_values))
    
    def update_recipe(self, recipe):
        """Update the panel with a new recipe."""
        self.recipe = recipe
        self.param_values = {}
        self.param_errors = {}
        
        # Trigger recompose
        self.refresh(layout=True)
