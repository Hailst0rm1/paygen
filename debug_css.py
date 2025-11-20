#!/usr/bin/env python3
"""Debug CSS classes applied to widgets"""

from textual.widgets import Input, Select, Tree
from textual.app import App

# Check what internal classes/attributes Textual uses for focus
print("Input widget attributes:")
print([attr for attr in dir(Input) if 'focus' in attr.lower() or 'class' in attr.lower()])

print("\nSelect widget attributes:")
print([attr for attr in dir(Select) if 'focus' in attr.lower() or 'class' in attr.lower()])

print("\nTree widget attributes:")
print([attr for attr in dir(Tree) if 'focus' in attr.lower() or 'select' in attr.lower() or 'cursor' in attr.lower()])

# Check Textual's default theme
from textual import _theme_builder
from textual.design import ColorSystem

print("\nTextual default design system colors:")
design = ColorSystem.default()
print(f"Primary background: {design.primary_background}")
print(f"Surface: {design.surface}")
print(f"Panel: {design.panel}")

# Check if there's a way to see default CSS
from textual.css.stylesheet import Stylesheet
print("\nChecking default stylesheet...")
