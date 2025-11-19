"""
Recipe Detail Panel - Display recipe information

Shows description, MITRE info, effectiveness, artifacts, and parameters.
"""

from textual.widgets import Static, Label
from textual.containers import Vertical, ScrollableContainer
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.console import Group

from src.core.recipe_loader import Recipe


class RecipeDetailPanel(ScrollableContainer):
    """Panel displaying detailed recipe information."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_recipe = None
    
    def compose(self):
        """Compose the detail panel."""
        self.title_label = Label("📖 Recipe Details", id="detail-panel-title")
        yield self.title_label
        
        self.content = Static("Select a recipe to view details", id="detail-content")
        yield self.content
    
    def show_recipe(self, recipe: Recipe):
        """Display recipe details."""
        self.current_recipe = recipe
        
        # Build the detail view with Rich renderables
        renderables = []
        
        # Header with name and type
        type_str = "Template-Based" if recipe.is_template_based() else "Command-Based"
        type_icon = "📝" if recipe.is_template_based() else "⚙️"
        
        header = Text()
        header.append(f"{type_icon} {recipe.name}\n", style="bold cyan")
        header.append(f"{type_str} Recipe\n", style="italic")
        renderables.append(header)
        
        # Effectiveness badge
        effectiveness_colors = {
            'high': 'green',
            'medium': 'yellow',
            'low': 'red'
        }
        color = effectiveness_colors.get(recipe.effectiveness.lower(), 'white')
        
        effectiveness = Text()
        effectiveness.append("Effectiveness: ", style="bold")
        effectiveness.append(recipe.effectiveness.upper(), style=f"bold {color}")
        renderables.append(effectiveness)
        renderables.append(Text())
        
        # MITRE ATT&CK Information as markdown
        mitre_md = f"""## 🎯 MITRE ATT&CK
**Tactic:** {recipe.mitre_tactic}
**Technique:** {recipe.mitre_technique}
"""
        renderables.append(Markdown(mitre_md))
        
        # Description as markdown
        desc_md = f"""## 📋 Description
{recipe.description.strip()}
"""
        renderables.append(Markdown(desc_md))
        
        # Artifacts
        if recipe.artifacts:
            artifacts_md = "## 🔍 Artifacts & Detection\n*What defenders will see:*\n"
            for artifact in recipe.artifacts:
                artifacts_md += f"- {artifact}\n"
            renderables.append(Markdown(artifacts_md))
        
        # Dependencies (for command-based recipes)
        if recipe.is_command_based() and hasattr(recipe, 'dependencies'):
            if recipe.dependencies:
                deps_md = "## ⚙️  Dependencies\n"
                for dep in recipe.dependencies:
                    tool = dep.get('tool', 'Unknown')
                    hint = dep.get('install_hint', 'No installation hint')
                    deps_md += f"- **{tool}**\n"
                    deps_md += f"  {hint}\n"
                renderables.append(Markdown(deps_md))
        
        # Parameters
        if recipe.parameters:
            params_md = "## 📝 Parameters\n"
            
            required = recipe.get_required_parameters()
            optional = recipe.get_optional_parameters()
            
            if required:
                params_md += "### Required\n"
                for param in required:
                    name = param.get('name', 'unknown')
                    param_type = param.get('type', 'string')
                    desc = param.get('description', '')
                    default = param.get('default', '')
                    
                    params_md += f"- **{name}** (`{param_type}`)\n"
                    params_md += f"  {desc}\n"
                    if default:
                        params_md += f"  *Default: {default}*\n"
                params_md += "\n"
            
            if optional:
                params_md += "### Optional\n"
                for param in optional:
                    name = param.get('name', 'unknown')
                    param_type = param.get('type', 'string')
                    desc = param.get('description', '')
                    default = param.get('default', '')
                    
                    params_md += f"- **{name}** (`{param_type}`)\n"
                    params_md += f"  {desc}\n"
                    if default:
                        params_md += f"  *Default: {default}*\n"
                params_md += "\n"
            
            renderables.append(Markdown(params_md))
        
        # Sub-recipes
        if recipe.sub_recipes:
            subs_md = "## 🧩 Available Sub-Recipes\n*Modular components that can be combined:*\n"
            for sub in recipe.sub_recipes:
                sub_name = sub.get('name', 'Unknown')
                sub_desc = sub.get('description', '')
                subs_md += f"- **{sub_name}**\n"
                if sub_desc:
                    subs_md += f"  {sub_desc}\n"
            renderables.append(Markdown(subs_md))
        
        # Launch instructions
        if recipe.launch_instructions:
            launch_md = f"""## 🚀 Launch Instructions
```
{recipe.launch_instructions.strip()}
```
"""
            renderables.append(Markdown(launch_md))
        
        # Update the content with group of renderables
        content_group = Group(*renderables)
        self.content.update(content_group)
        
        # Update title
        self.title_label.update(f"📖 {recipe.name}")
    
    def clear(self):
        """Clear the detail panel."""
        self.current_recipe = None
        self.title_label.update("📖 Recipe Details")
        self.content.update("Select a recipe to view details")
