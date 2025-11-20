"""
Code Preview Panel

Right panel displaying template source code or command with syntax highlighting.
"""

from pathlib import Path
from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from textual.reactive import reactive
from textual.binding import Binding
from rich.syntax import Syntax

from .colors import MOCHA


class CodePanel(VerticalScroll):
    """Right panel displaying code preview."""
    
    BINDINGS = [
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
        Binding("g", "scroll_home", "Top", show=False, key_display="gg"),
        Binding("G", "scroll_end", "Bottom", show=False),
    ]
    
    def action_scroll_down(self) -> None:
        """Scroll down faster (5 lines at a time)."""
        self.scroll_relative(y=5, animate=False)
    
    def action_scroll_up(self) -> None:
        """Scroll up faster (5 lines at a time)."""
        self.scroll_relative(y=-5, animate=False)
    
    DEFAULT_CSS = """
    CodePanel {
        width: 35%;
        border: solid """ + MOCHA['surface1'] + """;
        background: #1e1e2e;
        padding: 0;
    }
    
    CodePanel:focus-within {
        border: double """ + MOCHA['blue'] + """;
    }
    
    CodePanel .panel-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: #1e1e2e;
        padding: 1;
        dock: top;
    }
    
    CodePanel .code-content {
        padding: 1;
        color: """ + MOCHA['text'] + """;
    }
    """
    
    selected_recipe = reactive(None)
    
    def __init__(self, config=None, **kwargs):
        """
        Initialize the code panel.
        
        Args:
            config: Configuration object for resolving paths
        """
        super().__init__(**kwargs)
        self.config = config
    
    def compose(self) -> ComposeResult:
        """Compose the panel widgets."""
        yield Static("Code Preview", classes="panel-title")
        yield Static("Select a recipe to view code", classes="code-content", id="code-content")
    
    def watch_selected_recipe(self, recipe) -> None:
        """Update panel when recipe selection changes."""
        if recipe:
            self.update_code_display(recipe)
        else:
            content_widget = self.query_one("#code-content", Static)
            content_widget.update("Select a recipe to view code")
    
    def update_code_display(self, recipe) -> None:
        """Display code preview."""
        content_widget = self.query_one("#code-content", Static)
        
        if recipe.is_template_based:
            # Show template source code
            template_path = recipe.output.get('template')
            if template_path and self.config:
                # Template path should be relative to payloads_dir
                # e.g., "process_injection/aes_injector.cs"
                full_path = Path(self.config.payloads_dir) / template_path
                
                if full_path.exists():
                    try:
                        code = full_path.read_text()
                        
                        # Determine lexer based on file extension
                        ext = full_path.suffix.lower()
                        lexer_map = {
                            '.cs': 'csharp',
                            '.py': 'python',
                            '.ps1': 'powershell',
                            '.c': 'c',
                            '.cpp': 'cpp',
                            '.sh': 'bash',
                            '.go': 'go',
                            '.rs': 'rust',
                        }
                        lexer = lexer_map.get(ext, 'text')
                        
                        # Create syntax highlighted code
                        syntax = Syntax(
                            code,
                            lexer,
                            theme="monokai",  # Close to Catppuccin Mocha
                            line_numbers=True,
                            word_wrap=False,
                            background_color="#1e1e2e"
                        )
                        
                        content_widget.update(syntax)
                    except Exception as e:
                        content_widget.update(f"[{MOCHA['red']}]Error reading template: {e}[/{MOCHA['red']}]")
                else:
                    content_widget.update(f"[{MOCHA['peach']}]Template file not found: {full_path}[/{MOCHA['peach']}]")
            else:
                content_widget.update(f"[{MOCHA['peach']}]No template specified[/{MOCHA['peach']}]")
        
        elif recipe.is_command_based:
            # Show command
            command = recipe.output.get('command', '')
            if command:
                # Syntax highlight as bash
                syntax = Syntax(
                    command,
                    "bash",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True,
                    background_color="#1e1e2e"
                )
                content_widget.update(syntax)
            else:
                content_widget.update(f"[{MOCHA['peach']}]No command specified[/{MOCHA['peach']}]")
        
        else:
            content_widget.update(f"[{MOCHA['peach']}]Unknown output type[/{MOCHA['peach']}]")
