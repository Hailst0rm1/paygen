"""
Parameter Configuration Screen

Modal screen for configuring recipe parameters before generation.
"""

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll, Horizontal
from textual.widgets import Static, Input, Button, Select, Checkbox
from textual.screen import ModalScreen
from textual.binding import Binding
from textual.validation import Function, Integer

from .colors import MOCHA
from ..core.validator import ParameterValidator, ValidationError


class ParameterConfigScreen(ModalScreen):
    """Screen for configuring recipe parameters."""
    
    DEFAULT_CSS = """
    ParameterConfigScreen {
        align: center middle;
    }
    
    ParameterConfigScreen > Container {
        width: 80;
        height: auto;
        max-height: 90%;
        background: """ + MOCHA['base'] + """;
        border: double """ + MOCHA['blue'] + """;
    }
    
    ParameterConfigScreen .config-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: """ + MOCHA['surface0'] + """;
        padding: 1;
        text-align: center;
    }
    
    ParameterConfigScreen #params-scroll {
        height: auto;
        max-height: 30;
        border: solid """ + MOCHA['surface1'] + """;
        background: """ + MOCHA['base'] + """;
        padding: 1;
    }
    
    ParameterConfigScreen .param-label {
        color: """ + MOCHA['text'] + """;
        padding: 0 1;
        margin-top: 1;
    }
    
    ParameterConfigScreen .param-required {
        color: """ + MOCHA['red'] + """;
    }
    
    ParameterConfigScreen .param-description {
        color: """ + MOCHA['subtext0'] + """;
        padding: 0 1;
        text-style: italic;
    }
    
    ParameterConfigScreen Input {
        margin: 0 1;
        background: """ + MOCHA['surface0'] + """;
        border: solid """ + MOCHA['surface2'] + """;
    }
    
    ParameterConfigScreen Input:focus {
        border: solid """ + MOCHA['blue'] + """;
    }
    
    ParameterConfigScreen Select {
        margin: 0 1;
        background: """ + MOCHA['surface0'] + """;
        border: solid """ + MOCHA['surface2'] + """;
    }
    
    ParameterConfigScreen Select:focus {
        border: solid """ + MOCHA['blue'] + """;
    }
    
    ParameterConfigScreen Checkbox {
        margin: 0 1;
        background: """ + MOCHA['surface0'] + """;
    }
    
    ParameterConfigScreen .error-message {
        color: """ + MOCHA['red'] + """;
        padding: 0 1;
    }
    
    ParameterConfigScreen .button-container {
        height: auto;
        align: center middle;
        padding: 1;
        margin-top: 1;
    }
    
    ParameterConfigScreen Button {
        margin: 0 2;
        min-width: 15;
    }
    
    ParameterConfigScreen Button.primary {
        background: """ + MOCHA['green'] + """;
        color: """ + MOCHA['base'] + """;
    }
    
    ParameterConfigScreen Button.primary:hover {
        background: """ + MOCHA['teal'] + """;
    }
    
    ParameterConfigScreen Button.default {
        background: """ + MOCHA['surface2'] + """;
        color: """ + MOCHA['text'] + """;
    }
    
    ParameterConfigScreen Button.default:hover {
        background: """ + MOCHA['overlay0'] + """;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
        Binding("ctrl+g", "generate", "Generate", show=True),
        Binding("tab", "focus_next", "Next Field", show=False),
        Binding("shift+tab", "focus_previous", "Previous Field", show=False),
    ]
    
    def __init__(self, recipe, config=None):
        """
        Initialize parameter configuration screen.
        
        Args:
            recipe: Recipe object to configure
            config: Configuration object for resolving defaults
        """
        super().__init__()
        self.recipe = recipe
        self.config = config
        self.validator = ParameterValidator()
        self.param_values = {}
        self.param_errors = {}
        
        # Build options with defaults from config
        self.remove_comments = config.remove_comments if config else True
        self.strip_binaries = config.strip_binaries if config else True
    
    def compose(self) -> ComposeResult:
        """Compose the configuration screen."""
        with Container():
            yield Static(f"Configure: {self.recipe.name}", classes="config-title")
            
            with VerticalScroll(id="params-scroll"):
                # Generate parameter inputs based on recipe parameters
                for param in self.recipe.parameters:
                    # Compose parameter widgets inline
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
            
            yield Static("Remove debug symbols and metadata from compiled binaries", classes="param-description")
            yield Checkbox(
                "Strip binary metadata",
                value=self.strip_binaries,
                id="build-strip-binaries"
            )
        
        yield Static("")  # Spacer before buttons
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
            # Select widget expects tuples of (label, value)
            options = [(choice, choice) for choice in choices]
            select = Select(options, value=default, id=f"param-{name}")
            widgets.append(select)
        
        elif param_type == 'bool':
            checkbox = Checkbox(value=bool(default), id=f"param-{name}")
            widgets.append(checkbox)
        
        elif param_type == 'integer':
            # Integer input with validation
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
        # Extract parameter name from widget ID
        widget_id = event.input.id
        if not widget_id or not widget_id.startswith("param-"):
            return
        
        param_name = widget_id[6:]  # Remove "param-" prefix
        value = event.value
        
        # Store value
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
                    # Check range if specified
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
        elif event.button.id == "cancel-btn":
            self.dismiss(None)
    
    def _handle_generate(self) -> None:
        """Handle generate button press."""
        # Check for validation errors
        if self.param_errors:
            self.notify("Please fix validation errors", severity="error")
            return
        
        # Check required parameters
        for param in self.recipe.parameters:
            if param.get('required') and not self.param_values.get(param['name']):
                param_name = param['name']
                error_widget = self.query_one(f"#error-{param_name}", Static)
                error_widget.update("⚠ This field is required")
                self.notify("Please fill in all required fields", severity="error")
                return
        
        # All validation passed, return parameters and build options
        result = {
            'parameters': self.param_values,
            'build_options': {
                'remove_comments': self.remove_comments,
                'strip_binaries': self.strip_binaries
            }
        }
        self.dismiss(result)
    
    def action_cancel(self) -> None:
        """Cancel parameter configuration."""
        self.dismiss(None)
    
    def action_generate(self) -> None:
        """Generate action via keybinding."""
        self._handle_generate()
