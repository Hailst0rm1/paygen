"""
Paygen TUI Application

Main Textual application for the Paygen payload generation tool.
"""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label
from textual.binding import Binding

from src.core.recipe_loader import RecipeLoader
from src.tui.menu import MenuPanel
from src.tui.recipe_detail import RecipeDetailPanel


class PaygenApp(App):
    """Main Paygen TUI application."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    .title {
        content-align: center middle;
        text-style: bold;
        color: $accent;
        height: 3;
        background: $primary;
    }
    
    .stats {
        height: 3;
        background: $panel;
        padding: 1;
    }
    
    .main-container {
        height: 1fr;
    }
    
    MenuPanel {
        width: 40%;
        border: solid $primary;
        padding: 1;
    }
    
    RecipeDetailPanel {
        width: 60%;
        border: solid $accent;
        padding: 1;
    }
    
    #menu-panel-title {
        text-style: bold;
        background: $primary-darken-2;
        padding: 1;
        margin-bottom: 1;
    }
    
    #detail-panel-title {
        text-style: bold;
        background: $accent-darken-2;
        padding: 1;
        margin-bottom: 1;
    }
    
    #detail-content {
        padding: 1;
    }
    
    ListView {
        height: 1fr;
    }
    
    ListItem {
        padding: 1;
    }
    
    ListItem:hover {
        background: $primary-darken-1;
    }
    
    ListItem.-selected {
        background: $accent;
    }
    """
    
    TITLE = "Paygen - Payload Generation Framework"
    SUB_TITLE = "MITRE ATT&CK Integrated Payload Generation"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("?", "help", "Help"),
        Binding("escape", "back", "Back"),
    ]
    
    def __init__(self):
        super().__init__()
        self.menu_panel = None
        self.detail_panel = None
        
        # Load recipes immediately
        recipes_dir = Path(__file__).parent.parent.parent / "recipes"
        self.recipe_loader = RecipeLoader(recipes_dir)
        self.recipes = self.recipe_loader.load_all_recipes()
    
    def on_mount(self) -> None:
        """Initialize the application when mounted."""
        # Update stats and show notification
        self.update_stats()
        self.notify(
            f"Loaded {len(self.recipes)} recipes successfully!",
            severity="information",
            timeout=3
        )
    
    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        
        # Title bar
        yield Static(
            "🎯 PAYGEN - Payload Generation Framework\n"
            "MITRE ATT&CK Integrated | Effectiveness Ratings | Modular Sub-Recipes",
            classes="title"
        )
        
        # Stats bar
        self.stats_label = Label("Loading...", classes="stats")
        yield self.stats_label
        
        # Main content area
        with Horizontal(classes="main-container"):
            # Left panel - Menu
            self.menu_panel = MenuPanel(self.recipe_loader)
            yield self.menu_panel
            
            # Right panel - Details
            self.detail_panel = RecipeDetailPanel()
            yield self.detail_panel
        
        yield Footer()
    
    def update_stats(self) -> None:
        """Update the statistics display."""
        if self.recipe_loader:
            total_recipes = self.recipe_loader.get_recipe_count()
            tactics_count = len(self.recipe_loader.get_tactic_list())
            
            template_count = sum(1 for r in self.recipes if r.is_template_based())
            command_count = sum(1 for r in self.recipes if r.is_command_based())
            
            self.stats_label.update(
                f"📊 Total Recipes: {total_recipes} | "
                f"🎯 Tactics: {tactics_count} | "
                f"📝 Template: {template_count} | "
                f"⚙️  Command: {command_count}"
            )
    
    def on_menu_panel_tactic_selected(self, message: MenuPanel.TacticSelected) -> None:
        """Handle tactic selection."""
        self.detail_panel.clear()
        self.notify(f"Selected: {message.tactic_id} - {message.tactic_name}", timeout=2)
    
    def on_menu_panel_recipe_selected(self, message: MenuPanel.RecipeSelected) -> None:
        """Handle recipe selection."""
        self.detail_panel.show_recipe(message.recipe)
        self.notify(f"Viewing: {message.recipe.name}", timeout=2)
    
    def action_help(self) -> None:
        """Show help screen."""
        self.notify(
            "Navigation:\n"
            "• ↑/↓: Navigate lists\n"
            "• Enter: Select item\n"
            "• Esc: Go back\n"
            "• q: Quit\n"
            "• ?: Show this help",
            title="Help",
            timeout=10
        )
    
    def action_back(self) -> None:
        """Go back to previous view."""
        if self.menu_panel and self.menu_panel.current_view == "recipes":
            self.menu_panel.show_tactics()
            self.detail_panel.clear()


def run_app():
    """Run the Paygen TUI application."""
    app = PaygenApp()
    app.run()


if __name__ == "__main__":
    run_app()
