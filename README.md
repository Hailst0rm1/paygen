# Paygen - Payload Generation Framework v2.0# paygen

Menu-driven TUI tool for generating and customizing malicious payloads with MITRE ATT&amp;CK context

A menu-driven TUI tool for generating and customizing malicious payloads with MITRE ATT&CK context and effectiveness ratings.

## Features

- 🎨 **Beautiful TUI** with Catppuccin Mocha theme and vim-style navigation
- 📦 **Template-based** payload generation using Jinja2
- 🔧 **Command-based** recipes for external tools (msfvenom, sliver, etc.)
- 🔐 **Preprocessing system** with built-in encryption and custom scripts
- 🎯 **Freeform categories** for flexible organization
- 📊 **Effectiveness ratings** and MITRE ATT&CK mappings
- ⚙️ **Configuration system** at `~/.config/paygen/config.yaml`

## Installation

```bash
# Clone the repository
git clone https://github.com/Hailst0rm1/paygen.git
cd paygen

# Install dependencies
pip install -r requirements.txt

# Run paygen
python -m src.main
```

## Project Structure

```
paygen/
├── src/               # Source code
│   ├── core/         # Core functionality
│   ├── tui/          # TUI components
│   └── utils/        # Utilities
├── recipes/          # Recipe YAML files
├── payloads/         # Source code templates
├── preprocessors/    # Custom preprocessing scripts
└── output/           # Generated payloads (gitignored)
```

## Configuration

Configuration is stored at `~/.config/paygen/config.yaml`:

```yaml
recipes_dir: "~/Documents/Tools/paygen/recipes"
payloads_dir: "~/Documents/Tools/paygen/payloads"
preprocessors_dir: "~/Documents/Tools/paygen/preprocessors"
output_dir: "~/Documents/Tools/paygen/output"
theme: "catppuccin_mocha"
transparent_background: true
```

## Recipe Format

See `plan.md` for complete recipe schema and examples.

## Development Status

- [x] Phase 1: Core Infrastructure
- [ ] Phase 2: Preprocessing System
- [ ] Phase 3: TUI Development
- [ ] Phase 4: Payload Generation
- [ ] Phase 5: Recipe Development
- [ ] Phase 6: Polish & Distribution

## License

Private repository - not for public distribution.
