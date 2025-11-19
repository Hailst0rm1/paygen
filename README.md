# Paygen - Payload Generation Framework

A menu-driven TUI tool for generating and customizing malicious payloads with MITRE ATT&CK context and effectiveness ratings.

## ⚠️ Disclaimer

This tool is for **authorized security testing and educational purposes only**. Unauthorized use of this tool against systems you do not own or have explicit permission to test is illegal. The authors assume no liability for misuse.

## Features

- 🎯 **MITRE ATT&CK Integration**: All payloads mapped to tactics and techniques
- 📊 **Effectiveness Ratings**: Know which payloads work best in different scenarios
- 🔍 **Artifact Documentation**: Understand what defenders will see
- 🧩 **Modular Sub-Recipes**: Combine multiple techniques in a single payload
- 📝 **Template-Based & Command-Based**: Generate from source templates or external tools
- 🎨 **TUI Interface**: Easy-to-use terminal interface (coming soon)
- 🔐 **Built-in Encryption**: XOR and AES shellcode encryption
- 📦 **Nix Package**: Reproducible builds and easy deployment

## Project Status

**Phase 1: Core Infrastructure** ✅ (Completed)
- [x] Project structure and dependencies
- [x] Recipe loader and YAML parser
- [x] Parameter validation system
- [x] Example recipes (process injection, msfvenom)

**Phase 2-5**: TUI, payload generation, recipe library, and distribution (In Progress)

## Installation

### With Nix (Recommended)

```bash
# Clone the repository
git clone https://github.com/Hailst0rm1/paygen.git
cd paygen

# Install with Nix
nix profile install .

# Or run directly
nix run .

# Or enter development environment
nix develop
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/Hailst0rm1/paygen.git
cd paygen

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run paygen
python src/main.py
```

## Usage

```bash
# From project root
python3 paygen.py

# Or use the convenience script
./run.sh

# Or run the module directly
python3 -m src.main
```

## Recipe Structure

Paygen supports two types of recipes:

### 1. Template-Based Recipes

Generate payloads from source code templates (C, C#, PowerShell, etc.)

```yaml
recipe_type: "template"
name: "Process Injection - PowerShell"
effectiveness: "medium"
mitre:
  tactic: "TA0005 - Defense Evasion"
  technique: "T1055.001 - Process Injection"
parameters:
  - name: "target_process"
    type: "string"
    required: true
sub_recipes:
  - name: "XOR Encrypted Shellcode"
    source_template: "payloads/process_injection/xor.ps1"
```

### 2. Command-Based Recipes

Execute external tools (sliver, msfvenom, etc.)

```yaml
recipe_type: "command"
name: "Msfvenom Reverse Shell"
dependencies:
  - tool: "msfvenom"
    check_command: "which msfvenom"
generation_command: |
  msfvenom -p {{ payload_type }} \
    LHOST={{ lhost }} LPORT={{ lport }} \
    -f {{ format }} -o {{ output_filename }}
```

## Recipe Organization

Recipes are organized by MITRE ATT&CK tactics:

```
recipes/
├── initial_access/
├── execution/
├── persistence/
├── privilege_escalation/
├── defense_evasion/
│   ├── process_injection_powershell.yaml
│   └── process_injection_csharp.yaml
├── credential_access/
├── discovery/
├── lateral_movement/
├── collection/
├── command_and_control/
└── exfiltration/
```

## Parameter Types

| Type      | Description                  | Example             |
| --------- | ---------------------------- | ------------------- |
| `ip`      | IPv4/IPv6 address            | `192.168.1.100`     |
| `port`    | Port number (1-65535)        | `4444`              |
| `string`  | Any text                     | `admin_user`        |
| `file`    | File path (must exist)       | `/tmp/shellcode.bin`|
| `path`    | Directory path               | `./output`          |
| `hex`     | Hexadecimal string           | `deadbeef`          |
| `bool`    | Boolean value                | `true`              |
| `choice`  | One of predefined options    | `https`             |
| `integer` | Whole number with range      | `5`                 |

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting
black src/ tests/

# Type checking
mypy src/

# Linting
flake8 src/
```

## Contributing

This is a private repository for personal use. See `project.md` for detailed development roadmap.

## Adding Custom Recipes

1. Create a YAML file in the appropriate MITRE tactic directory
2. Define metadata, parameters, and generation method
3. Add source templates (for template-based recipes)
4. Test with the validator

See `project.md` for detailed recipe development guidelines.

## License

MIT License - See LICENSE file for details.

## Acknowledgments

- Process injection examples inspired by common offensive security techniques
- MITRE ATT&CK framework for tactic/technique mappings
- Metasploit Framework, Sliver, and other open-source security tools

---

**Remember**: Only use on systems you own or have explicit written permission to test.
