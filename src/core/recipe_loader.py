"""
Recipe Loader - Load and parse YAML recipe files

Handles both template-based and command-based recipes.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import yaml


class RecipeLoadError(Exception):
    """Exception raised when recipe loading fails."""
    pass


class Recipe:
    """Represents a loaded recipe with all its metadata and configuration."""
    
    def __init__(self, data: Dict, file_path: Path):
        """
        Initialize a Recipe from parsed YAML data.
        
        Args:
            data: Parsed YAML dictionary
            file_path: Path to the recipe YAML file
        """
        self.file_path = file_path
        self.data = data
        
        # Required fields for all recipe types
        self.recipe_type = data.get('recipe_type', 'template')
        self.name = data['name']
        self.description = data.get('description', '')
        self.effectiveness = data.get('effectiveness', 'medium')
        
        # MITRE ATT&CK mapping
        mitre = data.get('mitre', {})
        self.mitre_tactic = mitre.get('tactic', '')
        self.mitre_technique = mitre.get('technique', '')
        
        # Artifacts and parameters
        self.artifacts = data.get('artifacts', [])
        self.parameters = data.get('parameters', [])
        self.sub_recipes = data.get('sub_recipes', [])
        self.output = data.get('output', {})
        self.launch_instructions = data.get('launch_instructions', '')
        
        # Type-specific fields
        if self.recipe_type == 'template':
            self.compile_command = self.output.get('compile_command')
        elif self.recipe_type == 'command':
            self.dependencies = data.get('dependencies', [])
            self.generation_command = data.get('generation_command', '')
    
    def get_tactic_id(self) -> str:
        """Extract MITRE tactic ID (e.g., 'TA0005') from tactic string."""
        if ' - ' in self.mitre_tactic:
            return self.mitre_tactic.split(' - ')[0].strip()
        return self.mitre_tactic
    
    def get_tactic_name(self) -> str:
        """Extract MITRE tactic name from tactic string."""
        if ' - ' in self.mitre_tactic:
            return self.mitre_tactic.split(' - ')[1].strip()
        return self.mitre_tactic
    
    def get_required_parameters(self) -> List[Dict]:
        """Get list of required parameters."""
        return [p for p in self.parameters if p.get('required', False)]
    
    def get_optional_parameters(self) -> List[Dict]:
        """Get list of optional parameters."""
        return [p for p in self.parameters if not p.get('required', False)]
    
    def is_template_based(self) -> bool:
        """Check if this is a template-based recipe."""
        return self.recipe_type == 'template'
    
    def is_command_based(self) -> bool:
        """Check if this is a command-based recipe."""
        return self.recipe_type == 'command'
    
    def __repr__(self) -> str:
        return f"Recipe(name='{self.name}', type='{self.recipe_type}', effectiveness='{self.effectiveness}')"


class RecipeLoader:
    """Loads and manages recipes from YAML files."""
    
    def __init__(self, recipes_dir: Union[str, Path]):
        """
        Initialize the recipe loader.
        
        Args:
            recipes_dir: Path to the recipes directory
        """
        self.recipes_dir = Path(recipes_dir)
        if not self.recipes_dir.exists():
            raise RecipeLoadError(f"Recipes directory not found: {self.recipes_dir}")
        
        self.recipes: List[Recipe] = []
        self._recipes_by_tactic: Dict[str, List[Recipe]] = {}
    
    def load_all_recipes(self) -> List[Recipe]:
        """
        Load all recipes from the recipes directory.
        
        Returns:
            List of loaded Recipe objects
        
        Raises:
            RecipeLoadError: If recipe loading fails
        """
        self.recipes = []
        
        # Walk through all MITRE tactic directories
        for tactic_dir in self.recipes_dir.iterdir():
            if not tactic_dir.is_dir():
                continue
            
            # Load all YAML files in this tactic directory
            for recipe_file in tactic_dir.glob('*.yaml'):
                try:
                    recipe = self.load_recipe(recipe_file)
                    self.recipes.append(recipe)
                except Exception as e:
                    print(f"Warning: Failed to load {recipe_file}: {e}")
        
        # Build index by tactic
        self._index_by_tactic()
        
        return self.recipes
    
    def load_recipe(self, file_path: Union[str, Path]) -> Recipe:
        """
        Load a single recipe from a YAML file.
        
        Args:
            file_path: Path to the recipe YAML file
        
        Returns:
            Recipe object
        
        Raises:
            RecipeLoadError: If recipe loading or validation fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise RecipeLoadError(f"Recipe file not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RecipeLoadError(f"Invalid YAML in {file_path}: {e}")
        
        # Validate required fields
        if not data:
            raise RecipeLoadError(f"Empty recipe file: {file_path}")
        
        if 'name' not in data:
            raise RecipeLoadError(f"Recipe missing 'name' field: {file_path}")
        
        return Recipe(data, file_path)
    
    def _index_by_tactic(self) -> None:
        """Build an index of recipes organized by MITRE tactic."""
        self._recipes_by_tactic = {}
        
        for recipe in self.recipes:
            tactic_id = recipe.get_tactic_id()
            if tactic_id not in self._recipes_by_tactic:
                self._recipes_by_tactic[tactic_id] = []
            self._recipes_by_tactic[tactic_id].append(recipe)
    
    def get_recipes_by_tactic(self, tactic_id: Optional[str] = None) -> Dict[str, List[Recipe]]:
        """
        Get recipes organized by MITRE tactic.
        
        Args:
            tactic_id: Optional tactic ID to filter by (e.g., 'TA0005')
        
        Returns:
            Dictionary mapping tactic IDs to lists of recipes
        """
        if tactic_id:
            return {tactic_id: self._recipes_by_tactic.get(tactic_id, [])}
        return self._recipes_by_tactic
    
    def get_sorted_recipes(self, recipes: List[Recipe]) -> List[Recipe]:
        """
        Sort recipes by effectiveness (high -> medium -> low) then alphabetically.
        
        Args:
            recipes: List of recipes to sort
        
        Returns:
            Sorted list of recipes
        """
        effectiveness_order = {'high': 0, 'medium': 1, 'low': 2}
        
        return sorted(
            recipes,
            key=lambda r: (
                effectiveness_order.get(r.effectiveness.lower(), 3),
                r.name.lower()
            )
        )
    
    def search_recipes(self, query: str) -> List[Recipe]:
        """
        Search recipes by name, description, or MITRE technique.
        
        Args:
            query: Search query string
        
        Returns:
            List of matching recipes
        """
        query_lower = query.lower()
        matches = []
        
        for recipe in self.recipes:
            if (query_lower in recipe.name.lower() or
                query_lower in recipe.description.lower() or
                query_lower in recipe.mitre_technique.lower()):
                matches.append(recipe)
        
        return matches
    
    def get_recipe_count(self) -> int:
        """Get total number of loaded recipes."""
        return len(self.recipes)
    
    def get_tactic_list(self) -> List[str]:
        """Get list of all MITRE tactics present in loaded recipes."""
        return sorted(self._recipes_by_tactic.keys())
