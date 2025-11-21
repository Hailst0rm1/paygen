"""
Category and Recipe Panel

Left panel showing categories and recipes sorted by effectiveness.
"""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static, Tree
from textual.reactive import reactive
from textual.message import Message

from .colors import get_effectiveness_badge, MOCHA


class CategoryPanel(ScrollableContainer):
    """Left panel displaying categories and recipes."""
    
    DEFAULT_CSS = """
    CategoryPanel {
        width: 30%;
        border: solid """ + MOCHA['surface1'] + """;
        background: #1e1e2e;
        padding: 0;
    }
    
    CategoryPanel:focus-within {
        border: double """ + MOCHA['blue'] + """;
    }
    
    CategoryPanel .panel-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: #1e1e2e;
        padding: 1;
        dock: top;
    }
    
    CategoryPanel Tree {
        background: #1e1e2e;
        padding: 1;
    }
    
    CategoryPanel Tree > .tree--label {
        color: """ + MOCHA['text'] + """;
        text-overflow: ellipsis;
        overflow: hidden;
        width: 100%;
    }
    
    CategoryPanel Tree > .tree--cursor {
        color: """ + MOCHA['text'] + """;
    }
    """
    
    selected_recipe = reactive(None)
    
    def __init__(self, recipes=None, **kwargs):
        """
        Initialize the category panel.
        
        Args:
            recipes: List of Recipe objects
        """
        super().__init__(**kwargs)
        self.recipes = recipes or []
        self.recipe_tree = None
    
    def compose(self) -> ComposeResult:
        """Compose the panel widgets."""
        yield Static("Categories & Recipes", classes="panel-title")
        
        # Create tree for categories and recipes
        tree = Tree("Recipes", id="recipe-tree")
        tree.show_root = False
        self.recipe_tree = tree
        
        yield tree
    
    def on_mount(self) -> None:
        """Populate the tree when mounted."""
        self.populate_tree()
    
    def populate_tree(self) -> None:
        """Populate the recipe tree with categories and recipes."""
        if not self.recipe_tree:
            return
        
        # Clear existing tree
        self.recipe_tree.clear()
        
        # Group recipes by category
        categories = {}
        for recipe in self.recipes:
            category = recipe.category or "Misc"
            if category not in categories:
                categories[category] = []
            categories[category].append(recipe)
        
        # Sort categories alphabetically, but always put "Misc" at the end
        category_names = sorted(categories.keys())
        if "Misc" in category_names:
            category_names.remove("Misc")
            category_names.append("Misc")
        
        for category in category_names:
            # Add category node
            category_recipes = categories[category]
            category_node = self.recipe_tree.root.add(
                f"[bold {MOCHA['lavender']}]📁 {category}[/] ({len(category_recipes)})",
                data={"type": "category", "name": category}
            )
            
            # Sort recipes by effectiveness (high -> medium -> low) then alphabetically
            sorted_recipes = sorted(
                category_recipes,
                key=lambda r: (-r.effectiveness_level, r.name.lower())
            )
            
            # Add recipe nodes
            for recipe in sorted_recipes:
                badge = get_effectiveness_badge(recipe.effectiveness)
                # Truncate long names to fit in the panel (max ~35 chars with badge)
                max_length = 35
                recipe_name = recipe.name
                if len(recipe_name) > max_length:
                    recipe_name = recipe_name[:max_length-3] + "..."
                recipe_label = f"{badge} {recipe_name}"
                
                category_node.add_leaf(
                    recipe_label,
                    data={"type": "recipe", "recipe": recipe}
                )
        
        # Expand all categories by default
        self.recipe_tree.root.expand_all()
    
    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle tree node highlight (arrow key navigation)."""
        node_data = event.node.data
        
        if node_data and node_data.get("type") == "recipe":
            recipe = node_data.get("recipe")
            self.selected_recipe = recipe
            
            # Post message to parent app to update other panels
            self.post_message(RecipeSelected(recipe))
    
    def watch_selected_recipe(self, recipe) -> None:
        """React to selected recipe changes."""
        if recipe:
            self.app.selected_recipe = recipe


class RecipeSelected(Message):
    """Event emitted when a recipe is selected."""
    
    def __init__(self, recipe) -> None:
        super().__init__()
        self.recipe = recipe
