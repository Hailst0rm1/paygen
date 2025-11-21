"""
History Popup Widget

Displays payload generation history with filtering and actions.
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.widgets import Static, Label, ListView, ListItem
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message
from typing import List, Optional
import os

from ..core.history import HistoryManager, HistoryEntry
from .colors import MOCHA


class HistoryPopup(Widget):
    """Widget overlay for viewing payload generation history"""
    
    can_focus = True
    
    BINDINGS = [
        Binding("q,escape", "dismiss", "Close", show=True),
        Binding("enter", "view_details", "View Details", show=True),
        Binding("r", "regenerate", "Regenerate", show=True),
        Binding("c", "copy_launch", "Copy Launch", show=True),
        Binding("d", "delete", "Delete", show=True),
        Binding("o", "open_output", "Open Output", show=True),
    ]
    
    DEFAULT_CSS = """
    HistoryPopup {
        width: 90;
        height: 80%;
        border: thick """ + MOCHA['blue'] + """;
        background: """ + MOCHA['base'] + """;
        layer: overlay;
    }
    
    HistoryPopup .panel-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: """ + MOCHA['base'] + """;
        padding: 0 1;
        text-align: center;
        dock: top;
        height: 1;
    }
    
    HistoryPopup .stats-bar {
        color: """ + MOCHA['subtext0'] + """;
        background: """ + MOCHA['surface0'] + """;
        padding: 0 1;
        text-align: center;
        dock: top;
        height: 1;
    }
    
    HistoryPopup #history-list {
        width: 100%;
        height: 1fr;
        background: """ + MOCHA['base'] + """;
        border: solid """ + MOCHA['surface1'] + """;
        margin: 0 1;
    }
    
    HistoryPopup .history-entry {
        width: 100%;
        height: auto;
        padding: 0 1;
        background: """ + MOCHA['surface0'] + """;
        color: """ + MOCHA['text'] + """;
    }
    
    HistoryPopup .history-entry:hover {
        background: """ + MOCHA['surface1'] + """;
    }
    
    HistoryPopup .entry-header {
        width: 100%;
        color: """ + MOCHA['text'] + """;
    }
    
    HistoryPopup .entry-details {
        width: 100%;
        color: """ + MOCHA['subtext0'] + """;
    }
    
    HistoryPopup .success-icon {
        color: """ + MOCHA['green'] + """;
        text-style: bold;
    }
    
    HistoryPopup .failure-icon {
        color: """ + MOCHA['red'] + """;
        text-style: bold;
    }
    
    HistoryPopup #detail-view {
        width: 100%;
        height: 1fr;
        background: """ + MOCHA['mantle'] + """;
        border: solid """ + MOCHA['surface1'] + """;
        margin: 0 1;
        padding: 1;
        display: none;
    }
    
    HistoryPopup .detail-section {
        color: """ + MOCHA['blue'] + """;
        text-style: bold;
        margin-top: 1;
    }
    
    HistoryPopup .detail-content {
        color: """ + MOCHA['text'] + """;
        margin-left: 2;
    }
    """
    
    class HistoryAction(Message):
        """Message for history actions"""
        def __init__(self, action: str, entry: Optional[HistoryEntry] = None, index: int = -1):
            super().__init__()
            self.action = action
            self.entry = entry
            self.index = index
    
    def __init__(self, history: HistoryManager):
        """
        Initialize history popup
        
        Args:
            history: HistoryManager instance
        """
        super().__init__()
        self.history = history
        self.entries = history.get_entries()
        self.selected_index = 0
        self.detail_mode = False
    
    def compose(self) -> ComposeResult:
        """Compose the history popup layout"""
        # Title
        yield Label("Payload Generation History", classes="panel-title")
        
        # Stats bar
        total = self.history.get_entry_count()
        success = self.history.get_success_count()
        failed = self.history.get_failure_count()
        yield Label(
            f"Total: {total} | Success: {success} | Failed: {failed}",
            classes="stats-bar"
        )
        
        # History list
        with VerticalScroll(id="history-list"):
            yield Static(id="history-content")
        
        # Detail view (hidden by default)
        with VerticalScroll(id="detail-view"):
            yield Static(id="detail-content")
    
    def on_mount(self) -> None:
        """Called when widget is mounted"""
        self._render_list()
        self.focus()
    
    def _render_list(self) -> None:
        """Render the history entry list"""
        content = self.query_one("#history-content", Static)
        
        if not self.entries:
            content.update(
                f"[{MOCHA['overlay1']}]No history entries yet.\n"
                f"Generate a payload to see it here![/{MOCHA['overlay1']}]"
            )
            return
        
        lines = []
        for i, entry in enumerate(self.entries):
            # Status icon
            if entry.success:
                status_icon = f"[{MOCHA['green']}]✓[/{MOCHA['green']}]"
            else:
                status_icon = f"[{MOCHA['red']}]✗[/{MOCHA['red']}]"
            
            # Highlight selected entry
            if i == self.selected_index:
                bg = MOCHA['surface2']
            else:
                bg = MOCHA['surface0']
            
            # Entry header: status, recipe name, timestamp
            header = (
                f"[on {bg}]{status_icon} "
                f"[{MOCHA['mauve']}]{entry.recipe_name}[/{MOCHA['mauve']}] "
                f"[{MOCHA['subtext0']}]{entry.formatted_timestamp}[/{MOCHA['subtext0']}][/on {bg}]"
            )
            
            # Entry details: output file
            details = (
                f"[on {bg}]  [{MOCHA['text']}]{entry.output_filename}[/{MOCHA['text']}][/on {bg}]"
            )
            
            lines.append(header)
            lines.append(details)
            lines.append("")  # Spacing
        
        content.update("\n".join(lines))
    
    def _render_detail(self, entry: HistoryEntry) -> None:
        """Render detailed view of an entry"""
        detail_widget = self.query_one("#detail-content", Static)
        list_widget = self.query_one("#history-list", VerticalScroll)
        detail_view = self.query_one("#detail-view", VerticalScroll)
        
        # Hide list, show detail
        list_widget.display = False
        detail_view.display = True
        
        # Build detail content
        lines = []
        
        # Header
        status = "SUCCESS" if entry.success else "FAILED"
        status_color = MOCHA['green'] if entry.success else MOCHA['red']
        lines.append(f"[{status_color}]{status}[/{status_color}] [{MOCHA['mauve']}]{entry.recipe_name}[/{MOCHA['mauve']}]")
        lines.append(f"[{MOCHA['subtext0']}]{entry.formatted_timestamp}[/{MOCHA['subtext0']}]")
        lines.append("")
        
        # Output file
        lines.append(f"[{MOCHA['blue']}]Output File:[/{MOCHA['blue']}]")
        lines.append(f"  [{MOCHA['text']}]{entry.output_file}[/{MOCHA['text']}]")
        lines.append("")
        
        # Parameters
        lines.append(f"[{MOCHA['blue']}]Parameters:[/{MOCHA['blue']}]")
        for key, value in entry.parameters.items():
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 60:
                value_str = value_str[:57] + "..."
            lines.append(f"  [{MOCHA['green']}]{key}[/{MOCHA['green']}]: [{MOCHA['text']}]{value_str}[/{MOCHA['text']}]")
        lines.append("")
        
        # Build steps
        if entry.build_steps:
            lines.append(f"[{MOCHA['blue']}]Build Steps:[/{MOCHA['blue']}]")
            for step in entry.build_steps:
                status_icon = {
                    'success': f"[{MOCHA['green']}]✓[/{MOCHA['green']}]",
                    'failed': f"[{MOCHA['red']}]✗[/{MOCHA['red']}]",
                    'running': f"[{MOCHA['yellow']}]⏳[/{MOCHA['yellow']}]",
                    'pending': f"[{MOCHA['overlay1']}]⏳[/{MOCHA['overlay1']}]",
                }.get(step.get('status', 'pending'), '?')
                
                lines.append(f"  {status_icon} [{MOCHA['text']}]{step.get('name', 'Unknown')}[/{MOCHA['text']}]")
                
                if step.get('error'):
                    error = str(step['error'])[:200]
                    lines.append(f"    [{MOCHA['red']}]Error: {error}[/{MOCHA['red']}]")
            lines.append("")
        
        # Launch instructions
        if entry.launch_instructions:
            lines.append(f"[{MOCHA['blue']}]Launch Instructions:[/{MOCHA['blue']}]")
            for line in entry.launch_instructions.split('\n'):
                lines.append(f"  [{MOCHA['text']}]{line}[/{MOCHA['text']}]")
        
        lines.append("")
        lines.append(f"[{MOCHA['overlay1']}]Press Esc to go back[/{MOCHA['overlay1']}]")
        
        detail_widget.update("\n".join(lines))
    
    def _exit_detail(self) -> None:
        """Exit detail view back to list"""
        list_widget = self.query_one("#history-list", VerticalScroll)
        detail_view = self.query_one("#detail-view", VerticalScroll)
        
        list_widget.display = True
        detail_view.display = False
        self.detail_mode = False
    
    def action_dismiss(self) -> None:
        """Dismiss the popup"""
        if self.detail_mode:
            self._exit_detail()
        else:
            self.remove()
    
    def action_view_details(self) -> None:
        """View details of selected entry"""
        if self.entries and 0 <= self.selected_index < len(self.entries):
            entry = self.entries[self.selected_index]
            self.detail_mode = True
            self._render_detail(entry)
    
    def action_regenerate(self) -> None:
        """Regenerate payload from selected entry"""
        if self.entries and 0 <= self.selected_index < len(self.entries):
            entry = self.entries[self.selected_index]
            self.post_message(self.HistoryAction("regenerate", entry, self.selected_index))
            self.remove()
    
    def action_copy_launch(self) -> None:
        """Copy launch instructions to clipboard"""
        if self.entries and 0 <= self.selected_index < len(self.entries):
            entry = self.entries[self.selected_index]
            # Post message to app to handle clipboard
            self.post_message(self.HistoryAction("copy_launch", entry, self.selected_index))
    
    def action_delete(self) -> None:
        """Delete selected entry"""
        if self.entries and 0 <= self.selected_index < len(self.entries):
            entry = self.entries[self.selected_index]
            # Delete from history
            self.history.delete_entry(self.selected_index)
            # Refresh entries
            self.entries = self.history.get_entries()
            # Adjust selected index
            if self.selected_index >= len(self.entries) and self.selected_index > 0:
                self.selected_index -= 1
            # Re-render
            self._render_list()
            # Update stats
            total = self.history.get_entry_count()
            success = self.history.get_success_count()
            failed = self.history.get_failure_count()
            stats_bar = self.query_one(".stats-bar", Label)
            stats_bar.update(f"Total: {total} | Success: {success} | Failed: {failed}")
    
    def action_open_output(self) -> None:
        """Open output directory in file manager"""
        if self.entries and 0 <= self.selected_index < len(self.entries):
            entry = self.entries[self.selected_index]
            self.post_message(self.HistoryAction("open_output", entry, self.selected_index))
    
    def on_key(self, event) -> None:
        """Handle key events for navigation"""
        if self.detail_mode:
            return  # Let bindings handle it in detail mode
        
        if event.key == "j" or event.key == "down":
            if self.selected_index < len(self.entries) - 1:
                self.selected_index += 1
                self._render_list()
            event.prevent_default()
        elif event.key == "k" or event.key == "up":
            if self.selected_index > 0:
                self.selected_index -= 1
                self._render_list()
            event.prevent_default()
        elif event.key == "g":
            self.selected_index = 0
            self._render_list()
            event.prevent_default()
        elif event.key == "G":
            if self.entries:
                self.selected_index = len(self.entries) - 1
                self._render_list()
            event.prevent_default()
