"""
Recipe Metadata Panel

Middle panel displaying recipe details, MITRE ATT&CK info, and parameters.
"""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Static
from textual.reactive import reactive
from textual.binding import Binding

from .colors import get_effectiveness_badge, MOCHA


class RecipePanel(VerticalScroll):
    """Middle panel displaying recipe metadata."""
    
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
    RecipePanel {
        width: 35%;
        border: solid """ + MOCHA['surface1'] + """;
        background: #1e1e2e;
        padding: 0;
    }
    
    RecipePanel:focus-within {
        border: double """ + MOCHA['blue'] + """;
    }
    
    RecipePanel .panel-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: #1e1e2e;
        padding: 1;
        dock: top;
    }
    
    RecipePanel .recipe-content {
        padding: 1;
        color: """ + MOCHA['text'] + """;
    }
    
    RecipePanel .section-header {
        color: """ + MOCHA['lavender'] + """;
        text-style: bold;
        padding-top: 1;
    }
    
    RecipePanel .effectiveness-high {
        color: """ + MOCHA['green'] + """;
        text-style: bold;
    }
    
    RecipePanel .effectiveness-medium {
        color: """ + MOCHA['peach'] + """;
        text-style: bold;
    }
    
    RecipePanel .effectiveness-low {
        color: """ + MOCHA['overlay1'] + """;
        text-style: bold;
    }
    """
    
    selected_recipe = reactive(None)
    
    def compose(self) -> ComposeResult:
        """Compose the panel widgets."""
        yield Static("Recipe Details", classes="panel-title")
        yield Static("Select a recipe to view details", classes="recipe-content", id="recipe-content")
    
    def watch_selected_recipe(self, recipe) -> None:
        """Update panel when recipe selection changes."""
        if recipe:
            self.update_recipe_display(recipe)
        else:
            content_widget = self.query_one("#recipe-content", Static)
            content_widget.update("Select a recipe to view details")
    
    def update_recipe_display(self, recipe) -> None:
        """Display recipe metadata."""
        # Build the display content
        content = []
        
        # Name and category
        escaped_name = recipe.name.replace('[', r'\[').replace(']', r'\]')
        escaped_category = recipe.category.replace('[', r'\[').replace(']', r'\]')
        content.append(f"[bold {MOCHA['text']}]{escaped_name}[/bold {MOCHA['text']}]")
        content.append(f"[{MOCHA['subtext0']}]Category: {escaped_category}[/{MOCHA['subtext0']}]")
        content.append("")
        
        # Effectiveness
        badge = get_effectiveness_badge(recipe.effectiveness)
        content.append(f"[bold {MOCHA['lavender']}]Effectiveness:[/] {badge}")
        content.append("")
        
        # Description
        content.append(f"[bold {MOCHA['lavender']}]Description:[/]")
        # Wrap description lines
        for line in recipe.description.strip().split('\n'):
            escaped_line = line.replace('[', r'\[').replace(']', r'\]')
            content.append(f"[{MOCHA['subtext0']}]{escaped_line}[/{MOCHA['subtext0']}]")
        content.append("")
        
        # MITRE ATT&CK
        if recipe.mitre_tactic or recipe.mitre_technique:
            content.append(f"[bold {MOCHA['lavender']}]MITRE ATT&CK:[/]")
            if recipe.mitre_tactic:
                escaped_tactic = recipe.mitre_tactic.replace('[', r'\[').replace(']', r'\]')
                content.append(f"  [bold]Tactic:[/] [{MOCHA['teal']}]{escaped_tactic}[/{MOCHA['teal']}]")
            if recipe.mitre_technique:
                escaped_technique = recipe.mitre_technique.replace('[', r'\[').replace(']', r'\]')
                content.append(f"  [bold]Technique:[/] [{MOCHA['teal']}]{escaped_technique}[/{MOCHA['teal']}]")
            content.append("")
        
        # Artifacts
        if recipe.artifacts:
            content.append(f"[bold {MOCHA['lavender']}]Artifacts:[/]")
            for artifact in recipe.artifacts:
                escaped_artifact = artifact.replace('[', r'\[').replace(']', r'\]')
                content.append(f"  • [{MOCHA['peach']}]{escaped_artifact}[/{MOCHA['peach']}]")
            content.append("")
        
        # Parameters
        if recipe.parameters:
            content.append(f"[bold {MOCHA['lavender']}]Parameters:[/]")
            for param in recipe.parameters:
                name = param.get('name', 'unknown')
                param_type = param.get('type', 'string')
                required = param.get('required', False)
                default = param.get('default', '')
                description = param.get('description', '')
                
                req_marker = f"[{MOCHA['red']}]*[/{MOCHA['red']}]" if required else " "
                
                escaped_name = name.replace('[', r'\[').replace(']', r'\]')
                escaped_type = param_type.replace('[', r'\[').replace(']', r'\]')
                param_line = f"  {req_marker} [bold]{escaped_name}[/bold] ([{MOCHA['sky']}]{escaped_type}[/{MOCHA['sky']}])"
                if default:
                    escaped_default = str(default).replace('[', r'\[').replace(']', r'\]')
                    param_line += f" = [{MOCHA['yellow']}]{escaped_default}[/{MOCHA['yellow']}]"
                content.append(param_line)
                
                if description:
                    escaped_desc = description.replace('[', r'\[').replace(']', r'\]')
                    content.append(f"      [{MOCHA['subtext0']}]{escaped_desc}[/{MOCHA['subtext0']}]")
            content.append("")
        
        # Output type
        output_type = recipe.output.get('type', 'unknown')
        escaped_output_type = output_type.replace('[', r'\[').replace(']', r'\]')
        content.append(f"[bold {MOCHA['lavender']}]Output Type:[/] [{MOCHA['green']}]{escaped_output_type}[/{MOCHA['green']}]")
        
        # Compilation info
        if recipe.is_template_based:
            compile_info = recipe.output.get('compile', {})
            if compile_info.get('enabled'):
                # Extract compiler from command (first word of the command)
                command = compile_info.get('command', '')
                if command:
                    # Get first word (compiler executable)
                    compiler = command.split()[0] if command.split() else 'unknown'
                    escaped_compiler = compiler.replace('[', r'\[').replace(']', r'\]')
                    content.append(f"[bold {MOCHA['lavender']}]Compiler:[/] [{MOCHA['green']}]{escaped_compiler}[/{MOCHA['green']}]")
        
        # Launch instructions
        if recipe.launch_instructions:
            content.append("")
            content.append(f"[bold {MOCHA['lavender']}]Launch Instructions:[/]")
            # Split into lines and escape each one individually before wrapping in markup
            for line in recipe.launch_instructions.strip().split('\n'):
                # Escape special markup characters in the line content
                escaped_line = line.replace('[', r'\[').replace(']', r'\]')
                content.append(f"  [{MOCHA['subtext0']}]{escaped_line}[/{MOCHA['subtext0']}]")
        
        # Join and update
        display_text = "\n".join(content)
        content_widget = self.query_one("#recipe-content", Static)
        content_widget.update(display_text)
