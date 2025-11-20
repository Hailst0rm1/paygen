"""
Paygen TUI Application

Main Textual application for the Paygen payload generation framework.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer
from textual.binding import Binding

from .colors import MOCHA
from .category_panel import CategoryPanel, RecipeSelected
from .recipe_panel import RecipePanel
from .code_panel import CodePanel
from .help_screen import HelpScreen
from .param_config_screen import ParameterConfigScreen


class PaygenApp(App):
    """Main Paygen TUI application."""
    
    # Enable transparency
    ENABLE_COMMAND_PALETTE = False
    
    CSS = """
    Screen {
        background: transparent;
    }
    
    Header {
        background: transparent;
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
    }
    
    Footer {
        background: """ + MOCHA['surface0'] + """;
        color: """ + MOCHA['text'] + """;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("g", "generate", "Generate", show=True),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("h", "focus_left", "Left", show=False),
        Binding("l", "focus_right", "Right", show=False),
    ]
    
    TITLE = "PAYGEN - Payload Generation Framework"
    SUB_TITLE = "Recipes: 0 | Categories: 0"
    
    def __init__(self, config=None, recipes=None):
        """
        Initialize the Paygen TUI application.
        
        Args:
            config: Configuration object
            recipes: List of loaded recipes
        """
        super().__init__()
        self.config = config
        self.recipes = recipes or []
        self.selected_recipe = None
    
    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        
        with Horizontal():
            # Left panel: Categories & Recipes
            yield CategoryPanel(recipes=self.recipes, id="category-panel")
            
            # Middle panel: Recipe Metadata
            yield RecipePanel(id="recipe-panel")
            
            # Right panel: Code Preview
            yield CodePanel(config=self.config, id="code-panel")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.update_recipe_count()
        
        # Auto-focus the category panel on startup
        category_panel = self.query_one("#category-panel", CategoryPanel)
        category_panel.focus()
        
        # Focus the tree widget within the category panel
        try:
            tree = category_panel.query_one("#recipe-tree")
            tree.focus()
        except:
            pass
    
    def on_recipe_selected(self, message: RecipeSelected) -> None:
        """Handle recipe selection from category panel."""
        self.selected_recipe = message.recipe
        
        # Update middle and right panels
        recipe_panel = self.query_one("#recipe-panel", RecipePanel)
        recipe_panel.selected_recipe = message.recipe
        
        code_panel = self.query_one("#code-panel", CodePanel)
        code_panel.selected_recipe = message.recipe
    
    def update_recipe_count(self) -> None:
        """Update the subtitle with recipe and category counts."""
        recipe_count = len(self.recipes)
        
        # Count unique categories
        categories = set()
        for recipe in self.recipes:
            categories.add(recipe.category)
        
        category_count = len(categories)
        self.sub_title = f"Recipes: {recipe_count} | Categories: {category_count}"
    
    def action_help(self) -> None:
        """Show help dialog."""
        self.push_screen(HelpScreen())
    
    def action_cursor_down(self) -> None:
        """Move cursor down in focused panel."""
        focused = self.focused
        if focused and hasattr(focused, 'action_cursor_down'):
            focused.action_cursor_down()
    
    def action_cursor_up(self) -> None:
        """Move cursor up in focused panel."""
        focused = self.focused
        if hasattr(focused, 'action_cursor_up'):
            focused.action_cursor_up()
    
    def action_focus_left(self) -> None:
        """Focus the panel to the left."""
        # Cycle through panels: code -> recipe -> category -> code
        focused_id = self.focused.id if self.focused else None
        
        if focused_id == "code-panel":
            self.query_one("#recipe-panel").focus()
        elif focused_id == "recipe-panel":
            category_panel = self.query_one("#category-panel", CategoryPanel)
            category_panel.focus()
            # Also focus the tree within the category panel
            try:
                tree = category_panel.query_one("#recipe-tree")
                tree.focus()
            except:
                pass
        elif focused_id == "category-panel" or focused_id == "recipe-tree":
            self.query_one("#code-panel").focus()
        else:
            category_panel = self.query_one("#category-panel", CategoryPanel)
            category_panel.focus()
            try:
                tree = category_panel.query_one("#recipe-tree")
                tree.focus()
            except:
                pass
    
    def action_focus_right(self) -> None:
        """Focus the panel to the right."""
        # Cycle through panels: category -> recipe -> code -> category
        focused_id = self.focused.id if self.focused else None
        
        if focused_id == "category-panel" or focused_id == "recipe-tree":
            self.query_one("#recipe-panel").focus()
        elif focused_id == "recipe-panel":
            self.query_one("#code-panel").focus()
        elif focused_id == "code-panel":
            category_panel = self.query_one("#category-panel", CategoryPanel)
            category_panel.focus()
            # Also focus the tree within the category panel
            try:
                tree = category_panel.query_one("#recipe-tree")
                tree.focus()
            except:
                pass
        else:
            category_panel = self.query_one("#category-panel", CategoryPanel)
            category_panel.focus()
            try:
                tree = category_panel.query_one("#recipe-tree")
                tree.focus()
            except:
                pass
    
    def action_generate(self) -> None:
        """Generate payload from selected recipe."""
        if self.selected_recipe:
            # Open parameter configuration screen
            def handle_params(params):
                """Handle parameters returned from config screen."""
                if params is not None:
                    # Show configured parameters for verification
                    param_summary = "\n".join([f"  • {k}: {v}" for k, v in params.items()])
                    self.notify(
                        f"Parameters configured for [bold]{self.selected_recipe.name}[/bold]:\n{param_summary}\n\n"
                        f"[dim]Build system will be implemented in Phase 5[/dim]",
                        title="✓ Configuration Complete",
                        severity="information",
                        timeout=8
                    )
            
            self.push_screen(
                ParameterConfigScreen(self.selected_recipe, config=self.config),
                handle_params
            )
        else:
            self.notify("No recipe selected", title="Generate", severity="warning")
    
    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui(config=None, recipes=None):
    """
    Run the Paygen TUI application.
    
    Args:
        config: Configuration object
        recipes: List of loaded recipes
    """
    app = PaygenApp(config=config, recipes=recipes)
    # Run without mouse support to allow terminal text selection
    # Users can select and copy text using their terminal's selection (Shift+mouse or terminal-specific shortcuts)
    app.run(mouse=False)
