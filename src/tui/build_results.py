"""
Build Results Panel - Display payload generation results

Shows build status, output file info, and launch instructions.
"""

from textual.widgets import Static, Label
from textual.containers import ScrollableContainer
from rich.markdown import Markdown
from rich.text import Text
from rich.console import Group


class BuildResultsPanel(ScrollableContainer):
    """Panel for displaying build results and launch instructions."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def compose(self):
        """Compose the results panel."""
        yield Label("📦 Build Results", id="results-panel-title")
        yield Static("Generate a payload to see results", id="results-content")
    
    def show_success(self, result: dict):
        """
        Display successful build results.
        
        Args:
            result: Build result dictionary from PayloadBuilder
        """
        renderables = []
        
        # Success header
        header = Text()
        header.append("✅ Payload Generated Successfully!\n\n", style="bold green")
        renderables.append(header)
        
        # Output file info
        info_md = f"""## 📁 Output File
**Path:** `{result['output_path']}`
**Size:** {self._format_size(result['output_size'])}
"""
        
        if 'sha256' in result:
            info_md += f"**SHA256:** `{result['sha256'][:16]}...`\n"
        
        renderables.append(Markdown(info_md))
        
        # Selected sub-recipes
        if result.get('selected_sub_recipes'):
            subs_text = Text()
            subs_text.append("\n🧩 Sub-Recipes Used:\n", style="bold")
            for sub in result['selected_sub_recipes']:
                subs_text.append(f"  ✓ {sub}\n", style="cyan")
            renderables.append(subs_text)
        
        # Build type specific info
        if result['type'] == 'template':
            compile_info = result.get('compilation', {})
            if compile_info:
                compile_md = f"""
## 🔨 Compilation
**Command:** `{compile_info.get('command', 'N/A')}`
**Status:** Success
"""
                renderables.append(Markdown(compile_md))
        
        elif result['type'] == 'command':
            exec_info = result.get('execution', {})
            if exec_info:
                exec_md = f"""
## ⚙️  Command Execution
**Command:** `{exec_info.get('command', 'N/A')[:100]}...`
**Status:** Success
"""
                renderables.append(Markdown(exec_md))
        
        # Launch instructions
        if result.get('launch_instructions'):
            launch_md = f"""
## 🚀 Launch Instructions

```bash
{result['launch_instructions']}
```
"""
            renderables.append(Markdown(launch_md))
        
        # Update content
        content_group = Group(*renderables)
        self.query("#results-content").first().update(content_group)
    
    def show_error(self, error: str):
        """
        Display build error.
        
        Args:
            error: Error message
        """
        renderables = []
        
        # Error header
        header = Text()
        header.append("❌ Payload Generation Failed\n\n", style="bold red")
        renderables.append(header)
        
        # Error details
        error_md = f"""## Error Details

```
{error}
```
"""
        renderables.append(Markdown(error_md))
        
        # Update content
        content_group = Group(*renderables)
        self.query("#results-content").first().update(content_group)
    
    def show_progress(self, message: str):
        """
        Display progress message.
        
        Args:
            message: Progress message
        """
        progress = Text()
        progress.append("⏳ ", style="yellow")
        progress.append(message, style="bold")
        
        self.query("#results-content").first().update(progress)
    
    def clear(self):
        """Clear the results panel."""
        self.query("#results-content").first().update("Generate a payload to see results")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
