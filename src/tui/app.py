"""
Paygen TUI Application

Main Textual application for the Paygen payload generation tool.
"""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label, Button
from textual.binding import Binding

from src.core.recipe_loader import RecipeLoader
from src.core.payload_builder import PayloadBuilder, PayloadBuildError
from src.tui.menu import MenuPanel
from src.tui.recipe_detail import RecipeDetailPanel
from src.tui.parameter_input import ParameterInputPanel
from src.tui.build_results import BuildResultsPanel


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
    
    ParameterInputPanel {
        width: 60%;
        border: solid $success;
        padding: 1;
    }
    
    BuildResultsPanel {
        width: 60%;
        border: solid $warning;
        padding: 1;
    }
    
    .param-label {
        text-style: bold;
        margin-top: 1;
    }
    
    .param-description {
        color: $text-muted;
        margin-bottom: 1;
    }
    
    .section-header {
        text-style: bold;
        color: $accent;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    .param-input-group {
        margin-bottom: 1;
    }
    
    .sub-recipe-group {
        margin-left: 2;
        margin-bottom: 1;
    }
    
    .sub-recipe-description {
        color: $text-muted;
        margin-left: 4;
    }
    
    #generate-button {
        width: 100%;
        margin-top: 2;
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
        Binding("g", "generate", "Generate Payload"),
    ]
    
    def __init__(self):
        super().__init__()
        self.menu_panel = None
        self.detail_panel = None
        self.param_panel = None
        self.results_panel = None
        self.current_recipe = None
        self.current_view = "detail"  # detail | params | results
        
        # Load recipes and initialize builder
        project_root = Path(__file__).parent.parent.parent
        recipes_dir = project_root / "recipes"
        self.recipe_loader = RecipeLoader(recipes_dir)
        self.recipes = self.recipe_loader.load_all_recipes()
        self.payload_builder = PayloadBuilder(project_root)
    
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
            
            # Right panels - Details, Parameters, Results (switch between them)
            with Vertical(id="right-panel-container"):
                self.detail_panel = RecipeDetailPanel()
                yield self.detail_panel
                
                self.param_panel = ParameterInputPanel()
                self.param_panel.display = False  # Hidden initially
                yield self.param_panel
                
                self.results_panel = BuildResultsPanel()
                self.results_panel.display = False  # Hidden initially
                yield self.results_panel
        
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
        self.current_recipe = message.recipe
        self._show_detail_view()
        self.detail_panel.show_recipe(message.recipe)
        self.notify(f"Viewing: {message.recipe.name}", timeout=2)
    
    def _show_detail_view(self):
        """Show recipe detail panel."""
        self.current_view = "detail"
        self.detail_panel.display = True
        self.param_panel.display = False
        self.results_panel.display = False
    
    def _show_params_view(self):
        """Show parameter input panel."""
        if not self.current_recipe:
            self.notify("No recipe selected", severity="warning")
            return
        
        self.current_view = "params"
        self.detail_panel.display = False
        self.param_panel.display = True
        self.results_panel.display = False
        
        self.param_panel.show_recipe(self.current_recipe)
    
    def _show_results_view(self):
        """Show build results panel."""
        self.current_view = "results"
        self.detail_panel.display = False
        self.param_panel.display = False
        self.results_panel.display = True
    
    def action_generate(self) -> None:
        """Switch to parameter input view or trigger generation."""
        if self.current_view == "detail":
            # Switch to params view
            self._show_params_view()
        elif self.current_view == "params":
            # Trigger generation
            self._generate_payload()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "generate-button":
            self._generate_payload()
    
    def _generate_payload(self) -> None:
        """Generate payload from current recipe and parameters."""
        if not self.current_recipe:
            self.notify("No recipe selected", severity="error")
            return
        
        try:
            # Get parameters from input panel
            parameters = self.param_panel.get_parameters()
            selected_subs = self.param_panel.get_selected_sub_recipes()
            
            # Validate sub-recipes
            if self.current_recipe.sub_recipes and not selected_subs:
                self.notify(
                    "Warning: No sub-recipes selected. At least one sub-recipe is recommended.",
                    severity="warning",
                    timeout=5
                )
            
            # Show results panel with progress
            self._show_results_view()
            self.results_panel.show_progress(f"Building {self.current_recipe.name}...")
            
            # Build payload (this might take a while)
            result = self.payload_builder.build(
                recipe=self.current_recipe,
                parameters=parameters,
                selected_sub_recipes=selected_subs
            )
            
            # Show success
            self.results_panel.show_success(result)
            self.notify(
                f"✅ Payload generated: {result['output_path']}",
                severity="information",
                timeout=5
            )
        
        except ValueError as e:
            # Validation error
            self.notify(str(e), severity="error", timeout=10)
        
        except PayloadBuildError as e:
            # Build error
            self._show_results_view()
            self.results_panel.show_error(str(e))
            self.notify("❌ Build failed - see results panel", severity="error", timeout=5)
        
        except Exception as e:
            # Unexpected error
            self._show_results_view()
            self.results_panel.show_error(f"Unexpected error: {str(e)}")
            self.notify("❌ Unexpected error occurred", severity="error", timeout=5)
    
    def action_help(self) -> None:
        """Show help screen."""
        self.notify(
            "Navigation:\n"
            "• ↑/↓: Navigate lists\n"
            "• Enter: Select item\n"
            "• g: Configure & Generate Payload\n"
            "• Esc: Go back\n"
            "• q: Quit\n"
            "• ?: Show this help",
            title="Help",
            timeout=10
        )
    
    def action_back(self) -> None:
        """Go back to previous view."""
        if self.current_view == "params":
            # Go back to detail view
            self._show_detail_view()
        elif self.current_view == "results":
            # Go back to params view
            self._show_params_view()
        elif self.menu_panel and self.menu_panel.current_view == "recipes":
            # Go back to tactics view
            self.menu_panel.show_tactics()
            self.detail_panel.clear()
            self._show_detail_view()


def run_app():
    """Run the Paygen TUI application."""
    app = PaygenApp()
    app.run()


if __name__ == "__main__":
    run_app()
