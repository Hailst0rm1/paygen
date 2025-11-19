"""
Menu Widget - MITRE Tactic and Recipe Selection

Displays tactics and recipes with effectiveness-based sorting.
"""

from typing import Optional, List
from textual.widgets import ListView, ListItem, Label, Static
from textual.containers import Vertical
from textual.message import Message

from src.core.recipe_loader import Recipe


class RecipeListItem(ListItem):
    """A list item representing a recipe."""
    
    def __init__(self, recipe: Recipe, **kwargs):
        super().__init__(**kwargs)
        self.recipe = recipe
        
        # Color coding for effectiveness
        effectiveness_colors = {
            'high': 'green',
            'medium': 'yellow',
            'low': 'red'
        }
        color = effectiveness_colors.get(recipe.effectiveness.lower(), 'white')
        
        # Recipe type indicator
        type_icon = "📝" if recipe.is_template_based() else "⚙️"
        
        # Format the label
        label_text = (
            f"[{color}][{recipe.effectiveness.upper():^6}][/{color}] "
            f"{type_icon} {recipe.name}"
        )
        
        self.label = Label(label_text, markup=True)
    
    def compose(self):
        yield self.label


class TacticListItem(ListItem):
    """A list item representing a MITRE tactic."""
    
    def __init__(self, tactic_id: str, tactic_name: str, count: int, **kwargs):
        super().__init__(**kwargs)
        self.tactic_id = tactic_id
        self.tactic_name = tactic_name
        self.count = count
        
        label_text = f"🎯 {tactic_id} - {tactic_name} ({count})"
        self.label = Label(label_text)
    
    def compose(self):
        yield self.label


class MenuPanel(Vertical):
    """Main menu panel for tactic and recipe navigation."""
    
    class TacticSelected(Message):
        """Message sent when a tactic is selected."""
        def __init__(self, tactic_id: str, tactic_name: str):
            super().__init__()
            self.tactic_id = tactic_id
            self.tactic_name = tactic_name
    
    class RecipeSelected(Message):
        """Message sent when a recipe is selected."""
        def __init__(self, recipe: Recipe):
            super().__init__()
            self.recipe = recipe
    
    def __init__(self, recipe_loader, **kwargs):
        super().__init__(**kwargs)
        self.recipe_loader = recipe_loader
        self.current_view = "tactics"  # "tactics" or "recipes"
        self.current_tactic_id = None
        self.tactics_list = None
        self.recipes_list = None
    
    def compose(self):
        """Compose the menu panel."""
        self.title_label = Label("📋 Select MITRE Tactic", id="menu-panel-title")
        yield self.title_label
        
        # Create tactics list
        self.tactics_list = ListView(id="tactics-list")
        self.populate_tactics()
        yield self.tactics_list
        
        # Create recipes list (initially hidden)
        self.recipes_list = ListView(id="recipes-list")
        self.recipes_list.display = False
        yield self.recipes_list
    
    def populate_tactics(self):
        """Populate the tactics list."""
        self.tactics_list.clear()
        
        tactics_dict = self.recipe_loader.get_recipes_by_tactic()
        
        # MITRE tactic names mapping
        tactic_names = {
            'TA0001': 'Initial Access',
            'TA0002': 'Execution',
            'TA0003': 'Persistence',
            'TA0004': 'Privilege Escalation',
            'TA0005': 'Defense Evasion',
            'TA0006': 'Credential Access',
            'TA0007': 'Discovery',
            'TA0008': 'Lateral Movement',
            'TA0009': 'Collection',
            'TA0010': 'Exfiltration',
            'TA0011': 'Command and Control',
        }
        
        for tactic_id in sorted(tactics_dict.keys()):
            recipes = tactics_dict[tactic_id]
            tactic_name = tactic_names.get(tactic_id, tactic_id)
            
            item = TacticListItem(tactic_id, tactic_name, len(recipes))
            self.tactics_list.append(item)
    
    def populate_recipes(self, tactic_id: str):
        """Populate the recipes list for a specific tactic."""
        self.recipes_list.clear()
        
        recipes_dict = self.recipe_loader.get_recipes_by_tactic(tactic_id)
        recipes = recipes_dict.get(tactic_id, [])
        
        # Sort by effectiveness and name
        sorted_recipes = self.recipe_loader.get_sorted_recipes(recipes)
        
        for recipe in sorted_recipes:
            item = RecipeListItem(recipe)
            self.recipes_list.append(item)
    
    def show_tactics(self):
        """Show the tactics list."""
        self.current_view = "tactics"
        self.title_label.update("📋 Select MITRE Tactic")
        self.tactics_list.display = True
        self.recipes_list.display = False
        self.tactics_list.focus()
    
    def show_recipes(self, tactic_id: str, tactic_name: str):
        """Show the recipes list for a tactic."""
        self.current_view = "recipes"
        self.current_tactic_id = tactic_id
        self.title_label.update(f"📋 {tactic_id} - {tactic_name}\n[Press Esc to go back]")
        
        self.populate_recipes(tactic_id)
        
        self.tactics_list.display = False
        self.recipes_list.display = True
        self.recipes_list.focus()
    
    def on_list_view_selected(self, event: ListView.Selected):
        """Handle list item selection."""
        if self.current_view == "tactics":
            # Tactic selected
            item = event.item
            if isinstance(item, TacticListItem):
                self.show_recipes(item.tactic_id, item.tactic_name)
                self.post_message(self.TacticSelected(item.tactic_id, item.tactic_name))
        
        elif self.current_view == "recipes":
            # Recipe selected
            item = event.item
            if isinstance(item, RecipeListItem):
                self.post_message(self.RecipeSelected(item.recipe))
    
    def on_key(self, event):
        """Handle key presses."""
        if event.key == "escape" and self.current_view == "recipes":
            self.show_tactics()
            event.prevent_default()
