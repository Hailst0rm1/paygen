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
from .param_config_panel import ParameterConfigPopup
from .build_progress_popup import BuildProgressPopup
from .history_popup import HistoryPopup
from ..core.payload_builder import PayloadBuilder
from ..core.history import HistoryManager


class PaygenApp(App):
    """Main Paygen TUI application."""
    
    # Enable transparency
    ENABLE_COMMAND_PALETTE = False
    
    # Disable default focus tint
    design = None  # Use default design but we'll override focus colors
    
    CSS = """
    Screen {
        background: #1e1e2e;
    }
    
    Header {
        background: #1e1e2e;
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
    }
    
    Footer {
        background: #1e1e2e;
        color: """ + MOCHA['text'] + """;
    }
    
    *:focus {
        background-tint: transparent 0%;
    }
    
    Button:focus {
        background: """ + MOCHA['green'] + """;
    }
    
    Button.default:focus {
        background: """ + MOCHA['surface2'] + """;
    }
    
    ParameterConfigPopup {
    }
    
    BuildProgressPopup {
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("?", "help", "Help", show=True),
        Binding("g", "generate", "Generate", show=True),
        Binding("shift+h", "history", "History", show=True),
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
        
        # Initialize history manager
        if config:
            history_file = config.config_path.parent / "history.json"
            self.history = HistoryManager(history_file)
        else:
            self.history = None
    
    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        
        with Horizontal(id="main-container"):
            # Left panel: Categories & Recipes (or Recipe Details in generation mode)
            yield CategoryPanel(recipes=self.recipes, id="category-panel")
            
            # Middle panel: Recipe Metadata (or Parameter Config in generation mode)
            yield RecipePanel(id="recipe-panel")
            
            # Right panel: Code Preview (or Build Output in generation mode)
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
    
    def check_action(self, action: str, parameters: tuple) -> bool | None:
        """Check if an action should be enabled/visible."""
        return True
    
    def _get_bindings(self):
        """Get bindings with dynamic descriptions based on mode."""
        return self.BINDINGS
    
    @property
    def active_bindings(self):
        """Get the active bindings for the current state."""
        return self._get_bindings()
    
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
        focused = self.focused
        focused_id = focused.id if focused else None
        
        # Get the parent panel if focused widget is a child
        parent_panel_id = None
        if focused:
            for ancestor in focused.ancestors:
                if ancestor.id in ["code-panel", "recipe-panel", "category-panel"]:
                    parent_panel_id = ancestor.id
                    break
        
        # Use parent panel ID if found, otherwise use focused_id
        panel_id = parent_panel_id or focused_id
        
        # Browse mode: category-panel, recipe-panel, code-panel
        if panel_id == "code-panel":
            self.query_one("#recipe-panel").focus()
        elif panel_id == "recipe-panel":
            category_panel = self.query_one("#category-panel", CategoryPanel)
            category_panel.focus()
            try:
                tree = category_panel.query_one("#recipe-tree")
                tree.focus()
            except:
                pass
        elif panel_id == "category-panel" or panel_id == "recipe-tree":
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
        focused = self.focused
        focused_id = focused.id if focused else None
        
        # Get the parent panel if focused widget is a child
        parent_panel_id = None
        if focused:
            for ancestor in focused.ancestors:
                if ancestor.id in ["code-panel", "recipe-panel", "category-panel"]:
                    parent_panel_id = ancestor.id
                    break
        
        # Use parent panel ID if found, otherwise use focused_id
        panel_id = parent_panel_id or focused_id
        
        # Browse mode: category-panel, recipe-panel, code-panel
        if panel_id == "category-panel" or panel_id == "recipe-tree":
            self.query_one("#recipe-panel").focus()
        elif panel_id == "recipe-panel":
            self.query_one("#code-panel").focus()
        elif panel_id == "code-panel":
            category_panel = self.query_one("#category-panel", CategoryPanel)
            category_panel.focus()
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
    
    def action_generate(self, prefill_params: dict = None) -> None:
        """
        Generate payload from selected recipe - show parameter configuration popup.
        
        Args:
            prefill_params: Optional dict of parameter values to pre-fill
        """
        if not self.selected_recipe:
            self.notify("No recipe selected", title="Generate", severity="warning")
            return
        
        # Create popup widget
        popup = ParameterConfigPopup(
            recipe=self.selected_recipe,
            config=self.config,
            prefill_params=prefill_params
        )
        
        # Calculate center position
        popup_width = 70 + 4  # width + thick border
        popup_height = 30  # estimate for auto-height popup
        screen_width = self.size.width
        screen_height = self.size.height
        
        left_offset = (screen_width - popup_width) // 2
        top_offset = (screen_height - popup_height) // 2
        
        popup.styles.offset = (left_offset, top_offset)
        
        # Mount popup
        self.mount(popup)
    
    def on_parameter_config_popup_generate_requested(self, message: ParameterConfigPopup.GenerateRequested) -> None:
        """Handle generate request from parameter popup."""
        # Get the popup widget from the message
        popup = message._sender
        
        # Remove popup
        if popup:
            popup.remove()
        
        # Start build process
        self._start_build(message.params)
    
    def _start_build(self, params: dict) -> None:
        """
        Start the payload build process.
        
        Args:
            params: Build parameters from user
        """
        if not self.selected_recipe:
            return
        
        # Create build progress popup
        progress_popup = BuildProgressPopup(
            recipe_name=self.selected_recipe.name,
            show_debug=self.config.show_build_debug
        )
        
        # Calculate center position
        popup_width = 70 + 4  # width + thick border
        popup_height = 30 + 4  # height + thick border
        screen_width = self.size.width
        screen_height = self.size.height
        
        left_offset = (screen_width - popup_width) // 2
        top_offset = (screen_height - popup_height) // 2
        
        progress_popup.styles.offset = (left_offset, top_offset)
        
        # Mount popup
        self.mount(progress_popup)
        
        # Create payload builder
        builder = PayloadBuilder(self.config)
        
        # Set progress callback to update popup
        def on_progress(step):
            self.call_from_thread(progress_popup.update_step, step)
        
        builder.set_progress_callback(on_progress)
        
        # Run build in background
        recipe_dict = self.selected_recipe.to_dict()
        
        # Store current recipe name and params for history
        current_recipe_name = self.selected_recipe.name
        current_params = params.copy()
        
        def build_task():
            """Worker function for build process"""
            # Run build (this is blocking but runs in a thread)
            success, output_file, steps = builder.build(recipe_dict, params)
            
            # Render launch instructions with build variables
            launch_instructions = recipe_dict.get('launch_instructions', '')
            if launch_instructions and success:
                from jinja2 import Template
                # Get all variables used in the build
                all_vars = params.copy()
                all_vars['output_file'] = output_file
                # Render the launch instructions
                try:
                    template = Template(launch_instructions)
                    launch_instructions = template.render(**all_vars)
                except Exception as e:
                    launch_instructions = f"Error rendering launch instructions: {e}\n\n{launch_instructions}"
            
            # Save to history
            if self.history:
                # Convert build steps to simple dict format for JSON serialization
                build_steps_data = []
                for step in steps:
                    build_steps_data.append({
                        'name': step.name,
                        'type': step.type,
                        'status': step.status,
                        'output': str(step.output)[:500] if step.output else '',  # Truncate long output
                        'error': str(step.error)[:500] if step.error else ''
                    })
                
                self.history.add_entry(
                    recipe_name=current_recipe_name,
                    success=success,
                    output_file=output_file,
                    parameters=current_params,
                    launch_instructions=launch_instructions,
                    build_steps=build_steps_data
                )
            
            # Update popup with completion status (call from thread)
            self.call_from_thread(
                progress_popup.set_complete,
                success,
                output_file,
                launch_instructions
            )
            
            return success, output_file
        
        # Run the task in a thread worker
        self.run_worker(build_task, thread=True, exclusive=False)
    
    def on_build_progress_popup_build_complete(
        self,
        message: BuildProgressPopup.BuildComplete
    ) -> None:
        """Handle build completion from progress popup."""
        if message.success:
            self.notify(
                f"Payload generated: {message.output_file}",
                title="Build Success",
                severity="information"
            )
        else:
            self.notify(
                "Build failed. See popup for details.",
                title="Build Failed",
                severity="error"
            )
    
    def action_history(self) -> None:
        """Show history popup"""
        if not self.history:
            self.notify("History not available", severity="warning")
            return
        
        # Create history popup
        popup = HistoryPopup(self.history)
        
        # Calculate center position
        popup_width = 90 + 4  # width + thick border
        popup_height = int(self.size.height * 0.8) + 4
        screen_width = self.size.width
        screen_height = self.size.height
        
        left_offset = (screen_width - popup_width) // 2
        top_offset = (screen_height - popup_height) // 2
        
        popup.styles.offset = (left_offset, top_offset)
        
        # Mount popup
        self.mount(popup)
    
    def on_history_popup_history_action(self, message: HistoryPopup.HistoryAction) -> None:
        """Handle history actions"""
        action = message.action
        entry = message.entry
        
        if action == "regenerate" and entry:
            # Find the recipe
            matching_recipes = [r for r in self.recipes if r.name == entry.recipe_name]
            if matching_recipes:
                self.selected_recipe = matching_recipes[0]
                
                # Update panels
                recipe_panel = self.query_one("#recipe-panel", RecipePanel)
                recipe_panel.selected_recipe = self.selected_recipe
                
                code_panel = self.query_one("#code-panel", CodePanel)
                code_panel.selected_recipe = self.selected_recipe
                
                # Open parameter config with pre-filled values
                self.action_generate(prefill_params=entry.parameters)
            else:
                self.notify(f"Recipe '{entry.recipe_name}' not found", severity="warning")
        
        elif action == "copy_launch" and entry:
            # Try to copy to clipboard using terminal escape sequences
            # This is a fallback - actual clipboard support varies by terminal
            try:
                import subprocess
                # Try xclip on Linux
                subprocess.run(
                    ['xclip', '-selection', 'clipboard'],
                    input=entry.launch_instructions.encode(),
                    check=True
                )
                self.notify("Launch instructions copied to clipboard", severity="information")
            except (FileNotFoundError, subprocess.CalledProcessError):
                # Fallback: just show notification
                self.notify(
                    "Copy not available. Use terminal selection to copy.",
                    severity="information"
                )
        
        elif action == "open_output" and entry:
            # Open directory in file manager
            import subprocess
            import os
            from pathlib import Path
            
            output_path = Path(entry.output_file)
            if output_path.exists():
                output_dir = output_path.parent
            else:
                output_dir = self.config.output_dir
            
            try:
                # Try xdg-open on Linux
                subprocess.run(['xdg-open', str(output_dir)], check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                self.notify(f"Output directory: {output_dir}", severity="information")
    
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
