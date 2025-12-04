"""
History Popup Widget

Displays payload generation history with filtering and actions.
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.widgets import Static, Label, ListView, ListItem, Button
from textual.widget import Widget
from textual.binding import Binding
from textual.message import Message
from typing import List, Optional
import os
import subprocess

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
        Binding("j", "scroll_down", "Scroll Down", show=False),
        Binding("k", "scroll_up", "Scroll Up", show=False),
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
    
    HistoryPopup .launch-copy-btn-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin: 0 0 1 0;
    }
    
    HistoryPopup .launch-copy-btn {
        width: 12;
        height: 1;
        margin: 0 1;
        background: """ + MOCHA['blue'] + """ !important;
        color: """ + MOCHA['base'] + """ !important;
        text-style: bold;
        border: none !important;
    }
    
    HistoryPopup .launch-copy-btn:hover {
        background: """ + MOCHA['sapphire'] + """ !important;
        color: """ + MOCHA['text'] + """ !important;
    }
    
    HistoryPopup #detail-help-text {
        width: 100%;
        height: auto;
        text-align: center;
        color: """ + MOCHA['overlay1'] + """;
        padding: 0 1;
        dock: bottom;
        background: """ + MOCHA['base'] + """;
        display: none;
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
        
        # Help text at bottom
        yield Static("Press Esc to go back", id="detail-help-text")
    
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
        help_text = self.query_one("#detail-help-text", Static)
        
        # Hide list, show detail and help text
        list_widget.display = False
        detail_view.display = True
        help_text.display = True
        
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
        
        detail_widget.update("\n".join(lines))
        
        # Now add launch instruction commands with copy buttons
        if entry.launch_instructions:
            for line in entry.launch_instructions.split('\n'):
                stripped = line.strip()
                if stripped.startswith('$ '):
                    # Command line - extract command without "$ "
                    command = stripped[2:]  # Remove "$ " prefix
                    
                    # Handle word wrapping with proper indentation
                    # Split command into words and wrap at ~60 chars
                    words = command.split()
                    wrapped_lines = []
                    current = ""
                    
                    for word in words:
                        test = current + (" " if current else "") + word
                        if len(test) <= 60:
                            current = test
                        else:
                            if current:
                                wrapped_lines.append(current)
                            current = word
                    if current:
                        wrapped_lines.append(current)
                    
                    # Render first line with $
                    if wrapped_lines:
                        escaped_first = wrapped_lines[0].replace('[', r'\[').replace(']', r'\]')
                        cmd_text = Static(
                            f"[bold {MOCHA['blue']}]$[/bold {MOCHA['blue']}] [italic {MOCHA['text']}]{escaped_first}[/italic {MOCHA['text']}]"
                        )
                        detail_view.mount(cmd_text)
                        
                        # Render continuation lines with indentation (2 spaces to align after "$ ")
                        for continuation in wrapped_lines[1:]:
                            escaped_cont = continuation.replace('[', r'\[').replace(']', r'\]')
                            cont_text = Static(
                                f"  [italic {MOCHA['text']}]{escaped_cont}[/italic {MOCHA['text']}]"
                            )
                            detail_view.mount(cont_text)
                    
                    # Add copy button in centered container
                    btn_container = Horizontal(classes="launch-copy-btn-container")
                    detail_view.mount(btn_container)
                    copy_btn = Button("Copy", classes="launch-copy-btn")
                    copy_btn.command_to_copy = command
                    btn_container.mount(copy_btn)
                else:
                    # Regular text line (including empty lines to preserve spacing)
                    if line:  # Non-empty line
                        escaped_line = line.replace('[', r'\[').replace(']', r'\]')
                        text_widget = Static(f"  [{MOCHA['text']}]{escaped_line}[/{MOCHA['text']}]")
                    else:  # Empty line - preserve spacing
                        text_widget = Static("")
                    detail_view.mount(text_widget)
    
    def _exit_detail(self) -> None:
        """Exit detail view back to list"""
        list_widget = self.query_one("#history-list", VerticalScroll)
        detail_view = self.query_one("#detail-view", VerticalScroll)
        help_text = self.query_one("#detail-help-text", Static)
        
        list_widget.display = True
        detail_view.display = False
        help_text.display = False
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
    
    def action_scroll_down(self) -> None:
        """Scroll down in active view"""
        if self.detail_mode:
            container = self.query_one("#detail-view", VerticalScroll)
        else:
            container = self.query_one("#history-list", VerticalScroll)
        container.scroll_down()
    
    def action_scroll_up(self) -> None:
        """Scroll up in active view"""
        if self.detail_mode:
            container = self.query_one("#detail-view", VerticalScroll)
        else:
            container = self.query_one("#history-list", VerticalScroll)
        container.scroll_up()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle copy button presses"""
        button = event.button
        
        # Check if it's a launch copy button
        if hasattr(button, 'command_to_copy'):
            command = button.command_to_copy
            try:
                # Copy to clipboard using wl-copy
                subprocess.run(
                    ['wl-copy'],
                    input=command,
                    text=True,
                    check=True
                )
                # Visual feedback
                original_label = button.label
                button.label = "✓ Copied!"
                self.set_timer(1.5, lambda: setattr(button, 'label', original_label))
            except FileNotFoundError:
                button.label = "wl-copy not found"
                self.set_timer(2.0, lambda: setattr(button, 'label', 'Copy'))
            except Exception as e:
                button.label = "Error"
                self.set_timer(2.0, lambda: setattr(button, 'label', 'Copy'))
    
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
