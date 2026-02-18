"""Recipe CRUD and versioning manager for Paygen"""

import copy
import re
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import get_config
from .validator import RecipeValidator, ValidationError


class RecipeManager:
    """Manages recipe CRUD operations and in-file versioning"""

    def __init__(self, config=None):
        """Initialize recipe manager

        Args:
            config: Optional ConfigManager instance
        """
        self.config = config or get_config()

    def create_recipe(self, recipe_data: dict, comment: str = "Initial version") -> Path:
        """Create a new recipe file in versioned format

        Args:
            recipe_data: Recipe data with meta, parameters, preprocessing, output sections
            comment: Version comment

        Returns:
            Path to created recipe file

        Raises:
            ValidationError: If recipe data is invalid
        """
        # Validate the recipe data
        RecipeValidator.validate_recipe(recipe_data)

        # Determine category subdirectory
        category = recipe_data.get('meta', {}).get('category', 'Misc')
        category_dir = self.config.recipes_dir / self._sanitize_dirname(category)
        category_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        name = recipe_data['meta']['name']
        filename = self._generate_filename(name)
        file_path = category_dir / filename

        # Check for duplicate
        if file_path.exists():
            raise ValidationError(f"Recipe file already exists: {file_path}")

        # Build versioned structure
        versioned = {
            'versions': [
                {
                    'version': 1,
                    'comment': comment,
                    'timestamp': datetime.now().isoformat(timespec='seconds'),
                    'original': recipe_data
                }
            ]
        }

        self._write_yaml(file_path, versioned)
        return file_path

    def update_recipe(self, category: str, name: str, recipe_data: dict,
                      comment: str = "Updated") -> Path:
        """Update an existing recipe by appending a new version

        Args:
            category: Recipe category
            name: Recipe name
            recipe_data: Full updated recipe data
            comment: Version comment

        Returns:
            Path to updated recipe file

        Raises:
            ValidationError: If recipe data is invalid or recipe not found
        """
        # Validate the new data
        RecipeValidator.validate_recipe(recipe_data)

        file_path = self._find_recipe_file(category, name)
        if not file_path:
            raise ValidationError(f"Recipe not found: {category}/{name}")

        raw = self._read_yaml(file_path)
        versions = raw.get('versions', [])

        # Reconstruct current state
        current = self.reconstruct_recipe(versions)

        # Compute changes from current to new
        changes = self._compute_changes(current, recipe_data)

        if not changes:
            # No actual changes
            return file_path

        # Append new version
        new_version = {
            'version': len(versions) + 1,
            'comment': comment,
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'changes': changes
        }
        versions.append(new_version)

        self._write_yaml(file_path, {'versions': versions})
        return file_path

    def delete_recipe(self, category: str, name: str) -> bool:
        """Delete a recipe file

        Args:
            category: Recipe category
            name: Recipe name

        Returns:
            True if deleted successfully

        Raises:
            ValidationError: If recipe not found
        """
        file_path = self._find_recipe_file(category, name)
        if not file_path:
            raise ValidationError(f"Recipe not found: {category}/{name}")

        file_path.unlink()
        return True

    def get_recipe_raw(self, category: str, name: str) -> dict:
        """Get reconstructed current recipe data for editing

        Args:
            category: Recipe category
            name: Recipe name

        Returns:
            Reconstructed recipe data dict

        Raises:
            ValidationError: If recipe not found
        """
        file_path = self._find_recipe_file(category, name)
        if not file_path:
            raise ValidationError(f"Recipe not found: {category}/{name}")

        raw = self._read_yaml(file_path)
        versions = raw.get('versions', [])
        return self.reconstruct_recipe(versions)

    def get_versions(self, category: str, name: str) -> list:
        """Get version metadata list

        Args:
            category: Recipe category
            name: Recipe name

        Returns:
            List of version metadata dicts (version, comment, timestamp)

        Raises:
            ValidationError: If recipe not found
        """
        file_path = self._find_recipe_file(category, name)
        if not file_path:
            raise ValidationError(f"Recipe not found: {category}/{name}")

        raw = self._read_yaml(file_path)
        versions = raw.get('versions', [])

        return [
            {
                'version': v.get('version', i + 1),
                'comment': v.get('comment', ''),
                'timestamp': v.get('timestamp', '')
            }
            for i, v in enumerate(versions)
        ]

    def get_version_content(self, category: str, name: str, version: int) -> dict:
        """Reconstruct full recipe state at a given version

        Args:
            category: Recipe category
            name: Recipe name
            version: Version number to reconstruct to

        Returns:
            Reconstructed recipe data at that version

        Raises:
            ValidationError: If recipe or version not found
        """
        file_path = self._find_recipe_file(category, name)
        if not file_path:
            raise ValidationError(f"Recipe not found: {category}/{name}")

        raw = self._read_yaml(file_path)
        versions = raw.get('versions', [])

        if version < 1 or version > len(versions):
            raise ValidationError(f"Version {version} not found (have {len(versions)} versions)")

        return self.reconstruct_recipe(versions, up_to=version)

    def restore_version(self, category: str, name: str, version: int,
                        comment: str = "") -> Path:
        """Restore a previous version as new current by appending changes

        Args:
            category: Recipe category
            name: Recipe name
            version: Version to restore
            comment: Version comment

        Returns:
            Path to updated recipe file

        Raises:
            ValidationError: If recipe or version not found
        """
        file_path = self._find_recipe_file(category, name)
        if not file_path:
            raise ValidationError(f"Recipe not found: {category}/{name}")

        raw = self._read_yaml(file_path)
        versions = raw.get('versions', [])

        if version < 1 or version > len(versions):
            raise ValidationError(f"Version {version} not found")

        # Reconstruct state at target version
        target_state = self.reconstruct_recipe(versions, up_to=version)

        # Reconstruct current state
        current_state = self.reconstruct_recipe(versions)

        # Compute changes from current to target
        changes = self._compute_changes(current_state, target_state)

        if not changes:
            return file_path

        if not comment:
            comment = f"Restored to version {version}"

        new_version = {
            'version': len(versions) + 1,
            'comment': comment,
            'timestamp': datetime.now().isoformat(timespec='seconds'),
            'changes': changes
        }
        versions.append(new_version)

        self._write_yaml(file_path, {'versions': versions})
        return file_path

    def remove_latest_version(self, category: str, name: str) -> Path:
        """Remove the most recent version entry from a recipe

        Only allows removing if there are at least 2 versions (V1 cannot be removed).

        Args:
            category: Recipe category
            name: Recipe name

        Returns:
            Path to updated recipe file

        Raises:
            ValidationError: If recipe not found or only one version exists
        """
        file_path = self._find_recipe_file(category, name)
        if not file_path:
            raise ValidationError(f"Recipe not found: {category}/{name}")

        raw = self._read_yaml(file_path)
        versions = raw.get('versions', [])

        if len(versions) <= 1:
            raise ValidationError("Cannot remove the only version")

        versions.pop()
        self._write_yaml(file_path, {'versions': versions})
        return file_path

    def reconstruct_recipe(self, versions: list, up_to: int = None) -> dict:
        """Reconstruct full recipe state from version chain

        Args:
            versions: List of version entries
            up_to: Reconstruct up to this version number (inclusive). None = all.

        Returns:
            Reconstructed recipe data dict
        """
        if not versions:
            return {}

        # V1 must have 'original'
        v1 = versions[0]
        state = copy.deepcopy(v1.get('original', {}))

        # Apply subsequent versions
        limit = up_to if up_to is not None else len(versions)
        for i in range(1, min(limit, len(versions))):
            changes = versions[i].get('changes', {})
            state = self._deep_merge(state, changes)

        return state

    def get_version_count(self, file_path: Path) -> int:
        """Get the number of versions in a recipe file

        Args:
            file_path: Path to recipe file

        Returns:
            Number of versions, or 1 if not versioned
        """
        try:
            raw = self._read_yaml(file_path)
            if 'versions' in raw:
                return len(raw['versions'])
            return 1
        except Exception:
            return 1

    def load_versioned_recipe(self, file_path: Path) -> Tuple[dict, int]:
        """Load a recipe file, handling both versioned and legacy formats

        Args:
            file_path: Path to recipe file

        Returns:
            Tuple of (reconstructed recipe data, version count)
        """
        raw = self._read_yaml(file_path)

        if 'versions' in raw and isinstance(raw['versions'], list):
            # Versioned format
            versions = raw['versions']
            recipe_data = self.reconstruct_recipe(versions)
            return recipe_data, len(versions)
        else:
            # Legacy format (no versions wrapper)
            return raw, 1

    # --- Private helpers ---

    def _find_recipe_file(self, category: str, name: str) -> Optional[Path]:
        """Find a recipe file by category and name

        Searches the recipes directory for a YAML file whose reconstructed
        meta.category and meta.name match.

        Args:
            category: Recipe category
            name: Recipe name

        Returns:
            Path to recipe file or None
        """
        recipes_dir = self.config.recipes_dir
        if not recipes_dir.exists():
            return None

        yaml_files = list(recipes_dir.rglob('*.yaml')) + list(recipes_dir.rglob('*.yml'))

        for yaml_file in yaml_files:
            try:
                raw = self._read_yaml(yaml_file)

                # Handle versioned format
                if 'versions' in raw and isinstance(raw['versions'], list):
                    recipe_data = self.reconstruct_recipe(raw['versions'])
                else:
                    recipe_data = raw

                meta = recipe_data.get('meta', {})
                if meta.get('name') == name and meta.get('category', 'Misc') == category:
                    return yaml_file
            except Exception:
                continue

        return None

    def _generate_filename(self, name: str) -> str:
        """Generate a safe filename from recipe name

        Args:
            name: Recipe name

        Returns:
            Snake_case filename with .yaml extension
        """
        # Convert to snake_case
        safe = re.sub(r'[^\w\s-]', '', name.lower())
        safe = re.sub(r'[-\s]+', '_', safe).strip('_')
        return f"{safe}.yaml"

    def _sanitize_dirname(self, name: str) -> str:
        """Generate a safe directory name

        Args:
            name: Directory name

        Returns:
            Sanitized directory name
        """
        safe = re.sub(r'[^\w\s-]', '', name)
        safe = re.sub(r'[-\s]+', '_', safe).strip('_')
        return safe

    @staticmethod
    def _normalize_str(value: str) -> str:
        """Normalize a string for comparison by stripping trailing whitespace per line
        and trailing newlines. This prevents false diffs caused by YAML serialization
        normalizing multiline block scalars differently."""
        return '\n'.join(line.rstrip() for line in value.rstrip('\n').split('\n'))

    def _values_equal(self, old_val, new_val) -> bool:
        """Compare two values, normalizing strings to avoid YAML whitespace false diffs"""
        if isinstance(old_val, str) and isinstance(new_val, str):
            return self._normalize_str(old_val) == self._normalize_str(new_val)
        return old_val == new_val

    def _compute_changes(self, old_data: dict, new_data: dict) -> dict:
        """Compute the minimal changes dict between old and new recipe data

        For dicts: only include keys that changed (recursively).
        For lists: full replacement if any element differs.

        Args:
            old_data: Previous recipe state
            new_data: New recipe state

        Returns:
            Dict of changes (may be empty if identical)
        """
        changes = {}

        for key in new_data:
            if key not in old_data:
                # New key added
                changes[key] = copy.deepcopy(new_data[key])
            elif isinstance(new_data[key], dict) and isinstance(old_data[key], dict):
                # Recursively compute dict changes
                sub_changes = self._compute_changes(old_data[key], new_data[key])
                if sub_changes:
                    changes[key] = sub_changes
            elif isinstance(new_data[key], list):
                # Lists: compare element-by-element with string normalization
                if len(new_data[key]) != len(old_data[key]):
                    changes[key] = copy.deepcopy(new_data[key])
                else:
                    list_changed = False
                    for old_item, new_item in zip(old_data[key], new_data[key]):
                        if isinstance(old_item, dict) and isinstance(new_item, dict):
                            if self._compute_changes(old_item, new_item):
                                list_changed = True
                                break
                        elif not self._values_equal(old_item, new_item):
                            list_changed = True
                            break
                    if list_changed:
                        changes[key] = copy.deepcopy(new_data[key])
            elif not self._values_equal(new_data[key], old_data[key]):
                # Scalar value changed
                changes[key] = copy.deepcopy(new_data[key])

        # Handle removed keys by setting them to None
        for key in old_data:
            if key not in new_data:
                changes[key] = None

        return changes

    def _deep_merge(self, base: dict, changes: dict) -> dict:
        """Deep merge changes into base dict

        Rules:
        - Dict fields: recursively merge (only overwrite specified keys)
        - List fields: full replacement
        - None values: remove the key

        Args:
            base: Base dict to merge into (will be deep copied)
            changes: Changes to apply

        Returns:
            Merged dict
        """
        result = copy.deepcopy(base)

        for key, value in changes.items():
            if value is None:
                # Remove key
                result.pop(key, None)
            elif isinstance(value, dict) and isinstance(result.get(key), dict):
                # Recursively merge dicts
                result[key] = self._deep_merge(result[key], value)
            else:
                # Replace (scalar or list)
                result[key] = copy.deepcopy(value)

        return result

    def _read_yaml(self, file_path: Path) -> dict:
        """Read and parse a YAML file

        Args:
            file_path: Path to YAML file

        Returns:
            Parsed YAML data
        """
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}

    def _write_yaml(self, file_path: Path, data: dict) -> None:
        """Write data to a YAML file

        Uses a custom representer for multiline strings so they are stored as
        YAML block scalars (|) instead of escaped single-line strings.

        Args:
            file_path: Path to YAML file
            data: Data to write
        """
        class _BlockDumper(yaml.Dumper):
            pass

        def _str_representer(dumper, data):
            if '\n' in data:
                return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
            return dumper.represent_scalar('tag:yaml.org,2002:str', data)

        _BlockDumper.add_representer(str, _str_representer)

        with open(file_path, 'w') as f:
            yaml.dump(data, f, Dumper=_BlockDumper, default_flow_style=False,
                      sort_keys=False, allow_unicode=True, width=120)
