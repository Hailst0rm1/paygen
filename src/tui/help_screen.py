"""
Help Screen

Modal dialog showing keybindings and usage information.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, VerticalScroll
from textual.widgets import Static, Markdown, Button
from textual.binding import Binding

from .colors import MOCHA


class HelpScreen(ModalScreen):
    """Modal screen displaying help information."""
    
    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
    }
    
    HelpScreen > Container {
        width: 80;
        height: auto;
        max-height: 90%;
        background: """ + MOCHA['base'] + """;
        border: thick """ + MOCHA['blue'] + """;
    }
    
    HelpScreen .help-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: """ + MOCHA['surface0'] + """;
        padding: 1;
        text-align: center;
    }
    
    HelpScreen Markdown {
        padding: 1 2;
        background: """ + MOCHA['base'] + """;
        color: """ + MOCHA['text'] + """;
    }
    
    HelpScreen Button {
        margin: 1 2;
    }
    """
    
    BINDINGS = [
        Binding("escape", "dismiss", "Close", show=False),
        Binding("q", "dismiss", "Close", show=False),
    ]
    
    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        with Container():
            yield Static("Paygen Help", classes="help-title")
            
            with VerticalScroll():
                yield Markdown("""
# Keybindings

## Navigation
- **j** / **k** - Move down/up in focused panel
- **h** / **l** - Switch to left/right panel
- **Tab** - Next panel
- **Shift+Tab** - Previous panel
- **Enter** - Select item / Expand category
- **/** - Focus search (in Categories panel)
- **Escape** - Clear search / Return to tree

## Scrolling (Recipe & Code Panels)
- **j** / **k** - Scroll line by line
- **Ctrl+d** / **Ctrl+u** - Page down/up
- **gg** - Jump to top
- **G** - Jump to bottom

## Actions
- **Ctrl+G** - Generate payload from selected recipe
- **Ctrl+H** - View build history
- **Ctrl+R** - Refresh recipes from disk
- **Ctrl+F** - Toggle fullscreen (code panel)
- **?** - Show this help
- **Ctrl+Q** - Quit application

# Usage

1. **Browse Categories** - Use j/k to navigate categories in the left panel
2. **Select Recipe** - Navigate with arrow keys to view details (no Enter needed)
3. **View Details** - Middle panel shows recipe metadata, MITRE ATT&CK info
4. **Preview Code** - Right panel displays template source or command
5. **Generate** - Press 'Ctrl+G' to configure parameters and generate payload

# Recipe Information

**Effectiveness Ratings:**
- **[HIGH]** - Advanced evasion, low detection rate
- **[MEDIUM]** - Moderate evasion, moderate detection rate
- **[LOW]** - Basic technique, higher detection rate

**Parameters:**
- **\\*** - Required parameter
- Others are optional with defaults
                """)
            
            yield Button("Close", variant="primary", id="close-button")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        self.dismiss()
    
    def action_dismiss(self) -> None:
        """Dismiss the help screen."""
        self.dismiss()
