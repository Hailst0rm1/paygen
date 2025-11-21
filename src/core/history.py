"""
History Management for Paygen

Tracks all generated payloads with parameters, output files, and build status.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class HistoryEntry:
    """Represents a single payload generation in history"""
    
    # Identification
    recipe_name: str
    timestamp: str  # ISO 8601 format
    
    # Build info
    success: bool
    output_file: str
    
    # Parameters and instructions
    parameters: Dict[str, Any]
    launch_instructions: str
    
    # Build logs (optional)
    build_steps: List[Dict[str, str]] = None  # List of step info
    
    def __post_init__(self):
        """Initialize optional fields"""
        if self.build_steps is None:
            self.build_steps = []
    
    @property
    def formatted_timestamp(self) -> str:
        """Get human-readable timestamp"""
        try:
            dt = datetime.fromisoformat(self.timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return self.timestamp
    
    @property
    def status_icon(self) -> str:
        """Get status icon"""
        return "✓" if self.success else "✗"
    
    @property
    def output_filename(self) -> str:
        """Get just the filename from output path"""
        try:
            return Path(self.output_file).name
        except:
            return self.output_file


class HistoryManager:
    """Manages payload generation history"""
    
    def __init__(self, history_file: Path):
        """
        Initialize history manager
        
        Args:
            history_file: Path to history.json file
        """
        self.history_file = history_file
        self.entries: List[HistoryEntry] = []
        self._load()
    
    def _load(self) -> None:
        """Load history from file"""
        if not self.history_file.exists():
            self.entries = []
            return
        
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                self.entries = [
                    HistoryEntry(**entry) for entry in data
                ]
        except Exception as e:
            print(f"Warning: Could not load history: {e}")
            self.entries = []
    
    def _save(self) -> None:
        """Save history to file"""
        try:
            # Ensure parent directory exists
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert entries to dictionaries
            data = [asdict(entry) for entry in self.entries]
            
            # Write to file
            with open(self.history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save history: {e}")
    
    def add_entry(
        self,
        recipe_name: str,
        success: bool,
        output_file: str,
        parameters: Dict[str, Any],
        launch_instructions: str,
        build_steps: List[Dict[str, str]] = None
    ) -> HistoryEntry:
        """
        Add a new history entry
        
        Args:
            recipe_name: Name of the recipe used
            success: Whether build succeeded
            output_file: Path to output file
            parameters: Parameters used
            launch_instructions: Launch instructions
            build_steps: List of build step info (optional)
            
        Returns:
            Created HistoryEntry
        """
        entry = HistoryEntry(
            recipe_name=recipe_name,
            timestamp=datetime.now().isoformat(),
            success=success,
            output_file=output_file,
            parameters=parameters,
            launch_instructions=launch_instructions,
            build_steps=build_steps or []
        )
        
        # Add to beginning (newest first)
        self.entries.insert(0, entry)
        
        # Save to file
        self._save()
        
        return entry
    
    def get_entries(
        self,
        recipe_name: Optional[str] = None,
        success_only: Optional[bool] = None
    ) -> List[HistoryEntry]:
        """
        Get history entries with optional filtering
        
        Args:
            recipe_name: Filter by recipe name
            success_only: If True, only successful builds; if False, only failed
            
        Returns:
            List of matching HistoryEntry objects
        """
        entries = self.entries
        
        if recipe_name:
            entries = [e for e in entries if e.recipe_name == recipe_name]
        
        if success_only is not None:
            entries = [e for e in entries if e.success == success_only]
        
        return entries
    
    def delete_entry(self, index: int) -> bool:
        """
        Delete entry at index
        
        Args:
            index: Index of entry to delete
            
        Returns:
            True if deleted, False if index out of range
        """
        if 0 <= index < len(self.entries):
            self.entries.pop(index)
            self._save()
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all history"""
        self.entries = []
        self._save()
    
    def get_entry_count(self) -> int:
        """Get total number of entries"""
        return len(self.entries)
    
    def get_success_count(self) -> int:
        """Get number of successful builds"""
        return sum(1 for e in self.entries if e.success)
    
    def get_failure_count(self) -> int:
        """Get number of failed builds"""
        return sum(1 for e in self.entries if not e.success)
