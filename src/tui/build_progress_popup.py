"""
Build Progress Popup Widget

Displays real-time build progress with step tracking, spinner animations,
and detailed output.
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll, Container
from textual.widgets import Static, Label
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding
from typing import List, Optional

from ..core.payload_builder import BuildStep
from .colors import MOCHA


class BuildProgressPopup(Widget):
    """Widget overlay for build progress tracking"""
    
    # Make the popup focusable so it can capture keyboard input
    can_focus = True
    
    BINDINGS = [
        Binding("enter", "close", "Close", show=False),
    ]
    
    DEFAULT_CSS = """
    BuildProgressPopup {
        width: 70;
        height: 30;
        border: thick """ + MOCHA['blue'] + """;
        background: """ + MOCHA['base'] + """;
        layer: overlay;
    }
    
    BuildProgressPopup .panel-title {
        color: """ + MOCHA['mauve'] + """;
        text-style: bold;
        background: #1e1e2e;
        padding: 0 1;
        text-align: center;
        dock: top;
    }
    
    BuildProgressPopup #output-container {
        width: 100%;
        height: 1fr;
        background: #181825;
        border: solid """ + MOCHA['surface1'] + """;
        padding: 0 1;
        margin: 0 1;
    }
    
    BuildProgressPopup #output-content {
        width: 100%;
        color: """ + MOCHA['text'] + """;
    }
    
    BuildProgressPopup #result-message {
        width: 100%;
        height: auto;
        padding: 1;
        text-align: center;
        dock: bottom;
        background: """ + MOCHA['base'] + """;
    }
    
    BuildProgressPopup .success-message {
        color: """ + MOCHA['green'] + """;
        text-style: bold;
    }
    
    BuildProgressPopup .error-message {
        color: """ + MOCHA['red'] + """;
        text-style: bold;
    }
    
    BuildProgressPopup #help-text {
        width: 100%;
        height: auto;
        text-align: center;
        color: """ + MOCHA['overlay1'] + """;
        padding: 0 1;
        dock: bottom;
        background: """ + MOCHA['base'] + """;
    }
    """
    
    class BuildComplete(Message):
        """Message sent when build is complete and popup is closed"""
        def __init__(self, success: bool, output_file: str):
            super().__init__()
            self.success = success
            self.output_file = output_file
    
    spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    spinner_index = reactive(0)
    
    def __init__(self, recipe_name: str, show_debug: bool = False, **kwargs):
        """
        Initialize build progress popup
        
        Args:
            recipe_name: Name of the recipe being built
            show_debug: Whether to display debug output
        """
        super().__init__(**kwargs)
        self.recipe_name = recipe_name
        self.show_debug = show_debug
        self.steps: List[BuildStep] = []
        self.is_complete = False
        self.build_success = False
        self.output_file = ""
        self.launch_instructions = ""
        self.spinner_timer = None
    
    def compose(self) -> ComposeResult:
        """Compose the popup UI"""
        yield Static(f"Building: {self.recipe_name}", classes="panel-title")
        
        # Single scrolling output area for all build output
        with VerticalScroll(id="output-container"):
            yield Static("", id="output-content")
        
        # Result message at bottom
        yield Static("", id="result-message")
        
        # Help text at very bottom
        yield Static("Press Enter to close when complete", id="help-text")
    
    def on_mount(self) -> None:
        """Start spinner animation on mount"""
        self.spinner_timer = self.set_interval(0.1, self._update_spinner)
        # Use call_after_refresh to ensure popup is fully rendered before focusing
        self.call_after_refresh(self.focus)
    
    def _update_spinner(self) -> None:
        """Update spinner animation"""
        if not self.is_complete:
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
            self._refresh_output()
    
    def update_step(self, step: BuildStep) -> None:
        """
        Update a build step
        
        Args:
            step: BuildStep to update
        """
        # Update or add step to list
        existing = next((s for s in self.steps if s.name == step.name), None)
        if existing:
            existing.status = step.status
            existing.output = step.output
            existing.error = step.error
        else:
            self.steps.append(step)
        
        self._refresh_output()
    
    def _refresh_output(self) -> None:
        """Refresh the complete output display"""
        output_widget = self.query_one("#output-content", Static)
        
        lines = []
        
        # Add all step statuses and outputs
        for step in self.steps:
            status_icon = self._get_status_icon(step.status)
            
            # Color based on status
            if step.status == "pending":
                color = MOCHA['overlay1']
            elif step.status == "running":
                color = MOCHA['yellow']
            elif step.status == "success":
                color = MOCHA['green']
            elif step.status == "failed":
                color = MOCHA['red']
            else:
                color = MOCHA['text']
            
            # Add step status line
            lines.append(f"[{color}]{status_icon} {step.name}[/{color}]")
            
            # Add output if debug mode is enabled
            if self.show_debug:
                if step.output:
                    # Safely convert output to string, handling binary data
                    output_str = str(step.output)
                    # Truncate very long outputs and escape for markup
                    if len(output_str) > 500:
                        output_str = output_str[:500] + "... (truncated)"
                    # Escape markup characters
                    output_str = output_str.replace('[', '\\[').replace(']', '\\]')
                    for line in output_str.strip().split('\n')[:10]:  # Limit output lines
                        lines.append(f"[{MOCHA['subtext0']}]  {line}[/{MOCHA['subtext0']}]")
                if step.error:
                    error_str = str(step.error).replace('[', '\\[').replace(']', '\\]')
                    for line in error_str.strip().split('\n')[:10]:
                        lines.append(f"[{MOCHA['red']}]  Error: {line}[/{MOCHA['red']}]")
        
        if not lines:
            lines.append(f"[{MOCHA['overlay1']}]Preparing build...[/{MOCHA['overlay1']}]")
        
        output_widget.update("\n".join(lines))
        
        # Auto-scroll to bottom
        scroll_view = self.query_one("#output-container", VerticalScroll)
        scroll_view.scroll_end(animate=False)
    
    def _get_status_icon(self, status: str) -> str:
        """Get status icon for a step"""
        if status == "pending":
            return "⏳"
        elif status == "running":
            return self.spinner_frames[self.spinner_index]
        elif status == "success":
            return "✅"
        elif status == "failed":
            return "❌"
        return "?"
    
    def set_complete(
        self,
        success: bool,
        output_file: str = "",
        launch_instructions: str = ""
    ) -> None:
        """
        Mark build as complete
        
        Args:
            success: Whether build succeeded
            output_file: Path to output file
            launch_instructions: Instructions for launching payload
        """
        self.is_complete = True
        self.build_success = success
        self.output_file = output_file
        self.launch_instructions = launch_instructions
        
        if self.spinner_timer:
            self.spinner_timer.stop()
        
        # Update result message at bottom
        result_widget = self.query_one("#result-message", Static)
        result_widget.display = True
        if success and output_file:
            # Get file size
            import os
            try:
                file_size = os.path.getsize(output_file)
                # Format size nicely
                if file_size < 1024:
                    size_str = f"{file_size}B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                result_widget.update(
                    f"[{MOCHA['green']}]✅ Build completed successfully![/{MOCHA['green']}]\n"
                    f"[{MOCHA['text']}]Output: {output_file} ({size_str})[/{MOCHA['text']}]"
                )
            except Exception as e:
                # Fallback if file size can't be determined
                result_widget.update(
                    f"[{MOCHA['green']}]✅ Build completed successfully![/{MOCHA['green']}]\n"
                    f"[{MOCHA['text']}]Output: {output_file}[/{MOCHA['text']}]\n"
                    f"[{MOCHA['red']}](Error getting file size: {e})[/{MOCHA['red']}]"
                )
        elif success:
            # Success but no output file
            result_widget.update(
                f"[{MOCHA['green']}]✅ Build completed successfully![/{MOCHA['green']}]"
            )
        else:
            result_widget.update(
                f"[{MOCHA['red']}]❌ Build failed. See errors above.[/{MOCHA['red']}]"
            )
        
        # Show launch instructions if successful
        if success and launch_instructions:
            # Append launch instructions to the output area
            output_widget = self.query_one("#output-content", Static)
            current_content = output_widget.renderable
            new_content = (
                f"{current_content}\n\n"
                f"[{MOCHA['blue']}]Launch Instructions:[/{MOCHA['blue']}]\n"
                f"[{MOCHA['text']}]{launch_instructions}[/{MOCHA['text']}]"
            )
            output_widget.update(new_content)
    
    def action_close(self) -> None:
        """Handle close action"""
        if self.is_complete:
            self.remove()
            self.post_message(
                self.BuildComplete(self.build_success, self.output_file)
            )
