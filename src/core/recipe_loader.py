"""Recipe loader for Paygen"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict

from .validator import RecipeValidator, ValidationError
from .config import get_config


@dataclass
class Recipe:
    """Represents a loaded recipe"""
    
    # Recipe metadata
    name: str
    category: str
    description: str
    effectiveness: str  # low, medium, high
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    launch_instructions: Optional[str] = None
    
    # Recipe configuration
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    preprocessing: List[Dict[str, Any]] = field(default_factory=list)
    output: Dict[str, Any] = field(default_factory=dict)
    
    # File metadata
    file_path: Optional[Path] = None
    
    @property
    def effectiveness_level(self) -> int:
        """Get numeric effectiveness level for sorting"""
        levels = {'high': 3, 'medium': 2, 'low': 1}
        return levels.get(self.effectiveness.lower(), 0)
    
    @property
    def is_template_based(self) -> bool:
        """Check if recipe uses templates"""
        return self.output.get('type') == 'template'
    
    @property
    def is_command_based(self) -> bool:
        """Check if recipe uses commands"""
        return self.output.get('type') == 'command'
    
    def get_parameter(self, name: str) -> Optional[Dict[str, Any]]:
        """Get parameter definition by name
        
        Args:
            name: Parameter name
            
        Returns:
            Parameter definition or None
        """
        for param in self.parameters:
            if param.get('name') == name:
                return param
        return None
    
    def get_required_parameters(self) -> List[Dict[str, Any]]:
        """Get list of required parameters"""
        return [p for p in self.parameters if p.get('required', False)]
    
    def get_optional_parameters(self) -> List[Dict[str, Any]]:
        """Get list of optional parameters"""
        return [p for p in self.parameters if not p.get('required', False)]
    
    def get_conditional_parameters(self) -> List[Dict[str, Any]]:
        """Get list of parameters that are conditionally required
        
        Returns:
            List of parameters with 'required-for' field
        """
        return [p for p in self.parameters if 'required-for' in p]
    
    def get_preprocessing_options(self) -> List[Dict[str, Any]]:
        """Get list of preprocessing steps that are option types
        
        Returns:
            List of preprocessing steps with type='option'
        """
        return [p for p in self.preprocessing if p.get('type') == 'option']
    
    def to_dict(self) -> dict:
        """Convert recipe to dictionary
        
        Returns:
            Dictionary representation of recipe
        """
        data = asdict(self)
        # Remove file_path as it's not needed in dict form
        if 'file_path' in data:
            del data['file_path']
        return data


class RecipeLoader:
    """Loads and manages recipes from YAML files"""
    
    def __init__(self, config=None):
        """Initialize recipe loader
        
        Args:
            config: Optional ConfigManager instance
        """
        self.config = config or get_config()
        self.recipes: List[Recipe] = []
        self.recipes_by_category: Dict[str, List[Recipe]] = {}
    
    def load_all_recipes(self) -> List[Recipe]:
        """Load all recipes from recipes directory
        
        Returns:
            List of loaded Recipe objects
        """
        recipes_dir = self.config.recipes_dir
        
        if not recipes_dir.exists():
            print(f"Warning: Recipes directory not found: {recipes_dir}")
            return []
        
        self.recipes = []
        
        # Find all YAML files recursively
        yaml_files = list(recipes_dir.rglob('*.yaml')) + list(recipes_dir.rglob('*.yml'))
        
        for yaml_file in yaml_files:
            try:
                recipe = self.load_recipe(yaml_file)
                if recipe:
                    self.recipes.append(recipe)
            except Exception as e:
                print(f"Warning: Failed to load recipe {yaml_file}: {e}")
        
        # Build category index
        self._build_category_index()
        
        return self.recipes
    
    def load_recipe(self, file_path: Path) -> Optional[Recipe]:
        """Load a single recipe from YAML file
        
        Args:
            file_path: Path to recipe YAML file
            
        Returns:
            Recipe object or None if validation fails
        """
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if not data:
                print(f"Warning: Empty recipe file: {file_path}")
                return None
            
            # Validate recipe structure
            RecipeValidator.validate_recipe(data)
            
            # Extract meta information
            meta = data['meta']
            mitre = meta.get('mitre', {})
            
            # Create Recipe object
            recipe = Recipe(
                name=meta['name'],
                category=meta.get('category', 'Misc'),
                description=meta['description'],
                effectiveness=meta['effectiveness'],
                mitre_tactic=mitre.get('tactic'),
                mitre_technique=mitre.get('technique'),
                artifacts=meta.get('artifacts', []),
                launch_instructions=data.get('output', {}).get('launch_instructions'),
                parameters=data.get('parameters', []),
                preprocessing=data.get('preprocessing', []),
                output=data.get('output', {}),
                file_path=file_path
            )
            
            return recipe
            
        except ValidationError as e:
            print(f"Validation error in {file_path}: {e}")
            return None
        except yaml.YAMLError as e:
            print(f"YAML parsing error in {file_path}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error loading {file_path}: {e}")
            return None
    
    def _build_category_index(self) -> None:
        """Build index of recipes by category"""
        self.recipes_by_category = {}
        
        for recipe in self.recipes:
            category = recipe.category
            if category not in self.recipes_by_category:
                self.recipes_by_category[category] = []
            self.recipes_by_category[category].append(recipe)
        
        # Sort recipes within each category by effectiveness (high to low) then name
        for category in self.recipes_by_category:
            self.recipes_by_category[category].sort(
                key=lambda r: (-r.effectiveness_level, r.name.lower())
            )
    
    def get_categories(self) -> List[str]:
        """Get list of all categories, sorted alphabetically
        
        Returns:
            Sorted list of category names
        """
        return sorted(self.recipes_by_category.keys())
    
    def get_recipes_by_category(self, category: str) -> List[Recipe]:
        """Get all recipes in a category
        
        Args:
            category: Category name
            
        Returns:
            List of recipes in category
        """
        return self.recipes_by_category.get(category, [])
    
    def get_recipe_by_name(self, name: str) -> Optional[Recipe]:
        """Get recipe by name
        
        Args:
            name: Recipe name
            
        Returns:
            Recipe object or None
        """
        for recipe in self.recipes:
            if recipe.name == name:
                return recipe
        return None
    
    def search_recipes(self, query: str) -> List[Recipe]:
        """Search recipes by name, description, or category
        
        Args:
            query: Search query
            
        Returns:
            List of matching recipes
        """
        query_lower = query.lower()
        results = []
        
        for recipe in self.recipes:
            if (query_lower in recipe.name.lower() or
                query_lower in recipe.description.lower() or
                query_lower in recipe.category.lower()):
                results.append(recipe)
        
        # Sort by effectiveness then name
        results.sort(key=lambda r: (-r.effectiveness_level, r.name.lower()))
        
        return results
    
    def get_recipe_count(self) -> int:
        """Get total number of loaded recipes
        
        Returns:
            Recipe count
        """
        return len(self.recipes)
    
    def get_category_count(self) -> int:
        """Get total number of categories
        
        Returns:
            Category count
        """
        return len(self.recipes_by_category)
