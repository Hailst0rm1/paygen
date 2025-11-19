"""
Recipe Detail Panel - Display recipe information

Shows description, MITRE info, effectiveness, artifacts, and parameters.
"""

from textual.widgets import Static, Label
from textual.containers import Vertical, ScrollableContainer
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

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
        
        # Build the detail view
        details = []
        
        # Header with name and type
        type_str = "Template-Based" if recipe.is_template_based() else "Command-Based"
        type_icon = "📝" if recipe.is_template_based() else "⚙️"
        details.append(f"# {type_icon} {recipe.name}")
        details.append(f"*{type_str} Recipe*\n")
        
        # Effectiveness badge
        effectiveness_colors = {
            'high': 'green',
            'medium': 'yellow',
            'low': 'red'
        }
        color = effectiveness_colors.get(recipe.effectiveness.lower(), 'white')
        details.append(f"**Effectiveness:** [{color}]{recipe.effectiveness.upper()}[/{color}]\n")
        
        # MITRE ATT&CK Information
        details.append("## 🎯 MITRE ATT&CK")
        details.append(f"**Tactic:** {recipe.mitre_tactic}")
        details.append(f"**Technique:** {recipe.mitre_technique}\n")
        
        # Description
        details.append("## 📋 Description")
        details.append(recipe.description.strip())
        details.append("")
        
        # Artifacts
        if recipe.artifacts:
            details.append("## 🔍 Artifacts & Detection")
            details.append("*What defenders will see:*")
            for artifact in recipe.artifacts:
                details.append(f"- {artifact}")
            details.append("")
        
        # Dependencies (for command-based recipes)
        if recipe.is_command_based() and hasattr(recipe, 'dependencies'):
            if recipe.dependencies:
                details.append("## ⚙️  Dependencies")
                for dep in recipe.dependencies:
                    tool = dep.get('tool', 'Unknown')
                    hint = dep.get('install_hint', 'No installation hint')
                    details.append(f"- **{tool}**")
                    details.append(f"  {hint}")
                details.append("")
        
        # Parameters
        if recipe.parameters:
            details.append("## 📝 Parameters")
            
            required = recipe.get_required_parameters()
            optional = recipe.get_optional_parameters()
            
            if required:
                details.append("### Required")
                for param in required:
                    name = param.get('name', 'unknown')
                    param_type = param.get('type', 'string')
                    desc = param.get('description', '')
                    default = param.get('default', '')
                    
                    details.append(f"- **{name}** (`{param_type}`)")
                    details.append(f"  {desc}")
                    if default:
                        details.append(f"  *Default: {default}*")
                details.append("")
            
            if optional:
                details.append("### Optional")
                for param in optional:
                    name = param.get('name', 'unknown')
                    param_type = param.get('type', 'string')
                    desc = param.get('description', '')
                    default = param.get('default', '')
                    
                    details.append(f"- **{name}** (`{param_type}`)")
                    details.append(f"  {desc}")
                    if default:
                        details.append(f"  *Default: {default}*")
                details.append("")
        
        # Sub-recipes
        if recipe.sub_recipes:
            details.append("## 🧩 Available Sub-Recipes")
            details.append("*Modular components that can be combined:*")
            for sub in recipe.sub_recipes:
                sub_name = sub.get('name', 'Unknown')
                sub_desc = sub.get('description', '')
                details.append(f"- **{sub_name}**")
                if sub_desc:
                    details.append(f"  {sub_desc}")
            details.append("")
        
        # Launch instructions
        if recipe.launch_instructions:
            details.append("## 🚀 Launch Instructions")
            details.append("```")
            details.append(recipe.launch_instructions.strip())
            details.append("```")
        
        # Update the content
        content_text = "\n".join(details)
        self.content.update(content_text)
        
        # Update title
        self.title_label.update(f"📖 {recipe.name}")
    
    def clear(self):
        """Clear the detail panel."""
        self.current_recipe = None
        self.title_label.update("📖 Recipe Details")
        self.content.update("Select a recipe to view details")
