"""
Catppuccin Mocha Color Palette for Paygen TUI

Color scheme and utility functions for the Textual TUI.
"""

# Catppuccin Mocha Palette
MOCHA = {
    'rosewater': '#f5e0dc',
    'flamingo': '#f2cdcd',
    'pink': '#f5c2e7',
    'mauve': '#cba6f7',      # Accents, headers
    'red': '#f38ba8',        # Errors, high effectiveness
    'maroon': '#eba0ac',
    'peach': '#fab387',      # Warnings, medium effectiveness
    'yellow': '#f9e2af',     
    'green': '#a6e3a1',      # Success, high effectiveness
    'teal': '#94e2d5',       # Info
    'sky': '#89dceb',
    'sapphire': '#74c7ec',
    'blue': '#89b4fa',       # Links, selections
    'lavender': '#b4befe',   
    'text': '#cdd6f4',       # Primary text
    'subtext1': '#bac2de',   # Secondary text
    'subtext0': '#a6adc8',   
    'overlay2': '#9399b2',   
    'overlay1': '#7f849c',   
    'overlay0': '#6c7086',   
    'surface2': '#585b70',   
    'surface1': '#45475a',   
    'surface0': '#313244',   
    'base': '#1e1e2e',       # Background (or transparent)
    'mantle': '#181825',     
    'crust': '#11111b',      
}


def get_effectiveness_color(effectiveness: str) -> str:
    """
    Get the color for an effectiveness rating.
    
    Args:
        effectiveness: 'high', 'medium', or 'low'
    
    Returns:
        Hex color code
    """
    effectiveness = effectiveness.lower()
    
    if effectiveness == 'high':
        return MOCHA['green']
    elif effectiveness == 'medium':
        return MOCHA['peach']
    elif effectiveness == 'low':
        return MOCHA['red']
    else:
        return MOCHA['text']


def get_effectiveness_badge(effectiveness: str) -> str:
    """
    Get a formatted effectiveness badge with color.
    
    Args:
        effectiveness: 'high', 'medium', or 'low'
    
    Returns:
        Formatted badge string with Rich markup
    """
    effectiveness = effectiveness.lower()
    color = get_effectiveness_color(effectiveness)
    text = effectiveness.upper()
    
    return f"[{color}]{text}[/{color}]"


# Textual CSS color mappings
CSS_COLORS = {
    'primary': MOCHA['blue'],
    'secondary': MOCHA['mauve'],
    'accent': MOCHA['lavender'],
    'background': 'transparent',  # Use terminal background
    'surface': MOCHA['surface0'],
    'error': MOCHA['red'],
    'warning': MOCHA['peach'],
    'success': MOCHA['green'],
    'info': MOCHA['teal'],
    'text': MOCHA['text'],
    'text-muted': MOCHA['subtext0'],
    'border': MOCHA['blue'],
    'border-muted': MOCHA['surface1'],
}


def get_css_variables() -> str:
    """
    Generate CSS variables for Textual app.
    
    Returns:
        CSS variable definitions as a string
    """
    css = ""
    for name, color in CSS_COLORS.items():
        css += f"${name}: {color};\n"
    return css
