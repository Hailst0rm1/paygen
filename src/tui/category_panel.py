"""
Category and Recipe Panel

Left panel showing categories and recipes sorted by effectiveness.
"""

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static, Tree, Input
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding

from .colors import get_effectiveness_badge, get_effectiveness_color, MOCHA


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
    
    CategoryPanel Input {
        background: """ + MOCHA['surface0'] + """;
        border: solid """ + MOCHA['surface1'] + """;
        color: """ + MOCHA['text'] + """;
        padding: 0 1;
        margin: 0 1;
    }
    
    CategoryPanel Input:focus {
        border: solid """ + MOCHA['blue'] + """;
    }
    
    CategoryPanel Tree {
        background: #1e1e2e;
        padding: 1;
    }
    
    CategoryPanel Tree > .tree--label {
        text-overflow: ellipsis;
        overflow: hidden;
        width: 100%;
    }
    
    CategoryPanel Tree > .tree--cursor {
        color: """ + MOCHA['text'] + """;
    }
    """
    
    BINDINGS = [
        Binding("/", "focus_search", "Search", show=False),
        Binding("escape", "clear_search", "Clear Search", show=False),
    ]
    
    selected_recipe = reactive(None)
    search_query = reactive("")
    
    def __init__(self, recipes=None, **kwargs):
        """
        Initialize the category panel.
        
        Args:
            recipes: List of Recipe objects
        """
        super().__init__(**kwargs)
        self.recipes = recipes or []
        self.recipe_tree = None
        self.search_input = None
    
    def compose(self) -> ComposeResult:
        """Compose the panel widgets."""
        yield Static("Categories & Recipes", classes="panel-title")
        
        # Search input
        search = Input(placeholder="Search recipes... (press /)", id="recipe-search")
        self.search_input = search
        yield search
        
        # Create tree for categories and recipes
        tree = Tree("Recipes", id="recipe-tree")
        tree.show_root = False
        self.recipe_tree = tree
        
        yield tree
    
    def on_mount(self) -> None:
        """Populate the tree when mounted."""
        self.populate_tree()
    
    def populate_tree(self, filter_query: str = "") -> None:
        """Populate the recipe tree with categories and recipes.
        
        Args:
            filter_query: Optional search query to filter recipes
        """
        if not self.recipe_tree:
            return
        
        # Clear existing tree
        self.recipe_tree.clear()
        
        # Filter recipes by search query if provided
        filtered_recipes = self.recipes
        if filter_query:
            query_lower = filter_query.lower()
            filtered_recipes = [
                r for r in self.recipes 
                if query_lower in r.name.lower()
            ]
        
        # Group recipes by category
        categories = {}
        for recipe in filtered_recipes:
            category = recipe.category or "Misc"
            if category not in categories:
                categories[category] = []
            categories[category].append(recipe)
        
        # Sort categories alphabetically, but always put "Misc" second to last and "Examples" last
        category_names = sorted(categories.keys())
        
        # Remove special categories from sorted list
        if "Misc" in category_names:
            category_names.remove("Misc")
        if "Examples" in category_names:
            category_names.remove("Examples")
        
        # Add special categories at the end in the desired order
        if "Misc" in categories:
            category_names.append("Misc")
        if "Examples" in categories:
            category_names.append("Examples")
        
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
                # Truncate long names to fit in the panel (max ~40 chars)
                max_length = 40
                recipe_name = recipe.name
                if len(recipe_name) > max_length:
                    recipe_name = recipe_name[:max_length-3] + "..."
                # Escape brackets in recipe name FIRST to prevent markup conflicts
                escaped_name = recipe_name.replace('[', r'\[').replace(']', r'\]')
                # Get effectiveness color and apply it to the escaped name
                color = get_effectiveness_color(recipe.effectiveness)
                recipe_label = f"[{color}]{escaped_name}[/{color}]"
                
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
    
    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "recipe-search":
            self.search_query = event.value
            self.populate_tree(filter_query=event.value)
    
    def action_focus_search(self) -> None:
        """Focus the search input (/)."""
        if self.search_input:
            self.search_input.focus()
    
    def action_clear_search(self) -> None:
        """Clear search and refocus tree (Escape)."""
        if self.search_input and self.search_input.has_focus:
            self.search_input.value = ""
            self.search_query = ""
            self.populate_tree()
            if self.recipe_tree:
                self.recipe_tree.focus()


class RecipeSelected(Message):
    """Event emitted when a recipe is selected."""
    
    def __init__(self, recipe) -> None:
        super().__init__()
        self.recipe = recipe
