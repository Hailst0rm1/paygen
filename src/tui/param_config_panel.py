"""
Parameter Configuration Popup

Popup widget for configuring recipe parameters before generation.
"""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal, Vertical
from textual.widgets import Static, Input, Button, Select, Checkbox
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message

from .colors import MOCHA, get_effectiveness_badge
from ..core.validator import ParameterValidator, ValidationError


class ParameterConfigPopup(Widget):
    """Popup widget for configuring recipe parameters."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Cancel", show=False),
        Binding("q", "dismiss", "Cancel", show=False),
    ]
    
    DEFAULT_CSS = """
    ParameterConfigPopup {
        width: 70;
        height: auto;
        max-height: 80%;
        border: thick """ + MOCHA['blue'] + """;
        background: """ + MOCHA['base'] + """;
        layer: overlay;
    }
    
    ParameterConfigPopup .panel-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: #1e1e2e;
        padding: 0 1;
        text-align: center;
        dock: top;
    }
    
    ParameterConfigPopup #params-scroll {
        height: auto;
        max-height: 25;
        border: none;
        background: #1e1e2e;
        padding: 0 1;
    }
    
    ParameterConfigPopup .param-label {
        color: """ + MOCHA['text'] + """;
        padding: 0 1;
        margin-top: 0;
    }
    
    ParameterConfigPopup .param-required {
        color: """ + MOCHA['red'] + """;
    }
    
    ParameterConfigPopup .param-description {
        color: """ + MOCHA['subtext0'] + """;
        padding: 0 1;
        text-style: italic;
    }
    
    ParameterConfigPopup Input {
        margin: 0 1;
        background: #1e1e2e;
        border: solid """ + MOCHA['surface2'] + """;
    }
    
    ParameterConfigPopup Input:focus {
        border: solid """ + MOCHA['blue'] + """;
    }
    
    ParameterConfigPopup Select {
        margin: 0 1;
        background: #1e1e2e;
        border: solid """ + MOCHA['surface2'] + """;
    }
    
    ParameterConfigPopup Select:focus {
        border: solid """ + MOCHA['blue'] + """;
    }
    
    ParameterConfigPopup Checkbox {
        margin: 0 1;
        background: #1e1e2e;
    }
    
    ParameterConfigPopup .error-message {
        color: """ + MOCHA['red'] + """;
        padding: 0 1;
    }
    
    ParameterConfigPopup .button-container {
        height: auto;
        align: center middle;
        padding: 0 1;
        margin-top: 0;
        dock: bottom;
    }
    
    ParameterConfigPopup Button {
        margin: 0 1;
        min-width: 12;
        height: 1;
        text-style: bold;
        border: none !important;
        border-top: none !important;
        border-bottom: none !important;
    }
    
    ParameterConfigPopup Button#generate-btn {
        background: #a6e3a1 !important;
        color: #1e1e2e !important;
    }
    
    ParameterConfigPopup Button#generate-btn:focus {
        background: #94e2d5 !important;
        color: #1e1e2e !important;
        background-tint: transparent 0% !important;
    }
    
    ParameterConfigPopup Button#generate-btn:hover {
        background: #94e2d5 !important;
        color: #1e1e2e !important;
    }
    
    ParameterConfigPopup Button#generate-btn.-active {
        background: #94e2d5 !important;
        color: #1e1e2e !important;
        tint: transparent 0% !important;
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
    
    def __init__(self, recipe=None, config=None, prefill_params=None, **kwargs):
        """
        Initialize parameter configuration panel.
        
        Args:
            recipe: Recipe object to configure
            config: Configuration object for resolving defaults
            prefill_params: Optional dict of parameter values to pre-fill
        """
        super().__init__(**kwargs)
        self.recipe = recipe
        self.config = config
        self.prefill_params = prefill_params or {}
        self.validator = ParameterValidator()
        self.param_values = {}
        self.param_errors = {}
        
        # Build options with defaults from config
        self.remove_comments = config.remove_comments if config else True
        self.strip_binaries = config.strip_binaries if config else True
        self.remove_console_output = True  # Default to removing console output
    
    def compose(self) -> ComposeResult:
        """Compose the configuration popup."""
        if not self.recipe:
            yield Static("No recipe selected", classes="panel-title")
            return
        
        yield Static(f"Configure: {self.recipe.name}", classes="panel-title")
        
        with VerticalScroll(id="params-scroll"):
            # Parameter options section
            yield Static("[bold]Parameter Options[/bold]", classes="param-label", markup=True)
            yield Static("")  # Spacer
            
            # Generate parameter inputs based on recipe parameters
            for param in self.recipe.parameters:
                for widget in self._create_parameter_widgets(param):
                    yield widget
            
            # Add build options section
            yield Static("")  # Spacer
            yield Static("")  # Extra spacer
            yield Static("[bold]Build Options[/bold]", classes="param-label", markup=True)
            yield Static("")  # Spacer below title
            
            # Only show "remove comments" option for template-based recipes
            output_type = self.recipe.output.get('type', 'template')
            if output_type == 'template':
                yield Static("Strip comments and empty lines before compilation", classes="param-description")
                yield Checkbox(
                    "Remove comments from source code",
                    value=self.remove_comments,
                    id="build-remove-comments"
                )
                yield Static("")  # Spacer
                
                yield Static("Remove console output statements (e.g., Console.WriteLine, printf)", classes="param-description")
                yield Checkbox(
                    "Remove console output",
                    value=self.remove_console_output,
                    id="build-remove-console"
                )
                yield Static("")  # Spacer
            
            yield Static("Remove debug symbols and metadata from compiled binaries", classes="param-description")
            yield Checkbox(
                "Strip binary metadata",
                value=self.strip_binaries,
                id="build-strip-binaries"
            )
        
        yield Static("")  # Spacer before buttons
        with Horizontal(classes="button-container"):
            yield Button("Generate", variant="primary", id="generate-btn")
    
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
        
        # Check if we have a prefilled value
        if name in self.prefill_params:
            default = self.prefill_params[name]
        else:
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
        if not widget_id:
            return
        
        # Handle build options
        if widget_id == "build-remove-comments":
            self.remove_comments = event.value
            return
        elif widget_id == "build-remove-console":
            self.remove_console_output = event.value
            return
        elif widget_id == "build-strip-binaries":
            self.strip_binaries = event.value
            return
        
        # Handle parameter checkboxes
        if widget_id.startswith("param-"):
            param_name = widget_id[6:]
            self.param_values[param_name] = event.value
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "generate-btn":
            self._handle_generate()
    
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
        
        # All validation passed, send message with parameters and build options
        result = {
            'parameters': self.param_values,
            'build_options': {
                'remove_comments': self.remove_comments,
                'remove_console_output': self.remove_console_output,
                'strip_binaries': self.strip_binaries
            }
        }
        self.post_message(self.GenerateRequested(result))
    
    def action_dismiss(self) -> None:
        """Dismiss the popup without generating."""
        self.remove()
    
    def on_mount(self) -> None:
        """Called when popup is mounted - focus the first input."""
        try:
            # Try to focus the first input field
            inputs = self.query(Input)
            if inputs:
                inputs.first().focus()
        except:
            pass
    
    def update_recipe(self, recipe):
        """Update the panel with a new recipe."""
        self.recipe = recipe
        self.param_values = {}
        self.param_errors = {}
        
        # Trigger recompose
        self.refresh(layout=True)
