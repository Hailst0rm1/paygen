# Phase 4 - Parameter Configuration Usage Guide

## Quick Start

### Running the TUI

```bash
python -m src.main
```

### Testing Parameter Configuration

1. **Select a Recipe**

   - Use `j/k` to navigate up/down in the recipe tree
   - Press Enter to expand categories
   - Select either:
     - "C# AES-Encrypted Shellcode Injector" (5 parameters)
     - "C# XOR-Encrypted Shellcode Injector" (5 parameters)

2. **Open Parameter Configuration**

   - Press `g` to generate
   - Modal parameter screen appears

3. **Configure Parameters**

   - **Pre-filled defaults**: All parameters have defaults (some from config)
   - **Navigation**:
     - Tab / Shift+Tab to move between fields
     - Arrow keys within text inputs
   - **Parameter Types**:
     - Text inputs: string, ip, port, path, hex
     - Select dropdowns: choice type
     - Checkboxes: boolean type
     - Number inputs: integer type

4. **Validation**

   - **Real-time**: Errors appear as you type
   - **IP validation**: Must be valid IPv4 or IPv6
     - ✓ Valid: `192.168.1.1`, `10.0.0.1`, `::1`
     - ✗ Invalid: `999.999.999.999`, `not-an-ip`
   - **Port validation**: Must be 1-65535
     - ✓ Valid: `80`, `443`, `4444`, `65535`
     - ✗ Invalid: `0`, `99999`, `abc`
   - **Hex validation**: Only hex characters (0-9, a-f, A-F)
     - ✓ Valid: `deadbeef`, `CAFEBABE`, `0123456789abcdef`
     - ✗ Invalid: `xyz`, `12 34`, `0x1234`
   - **Required fields**: Marked with red \*
     - Cannot generate until all required fields filled

5. **Generate or Cancel**
   - **Generate**: Press `Ctrl+G` or click "Generate" button
   - **Cancel**: Press `Esc` or click "Cancel" button
   - On success: Shows parameter summary notification

## Example Session

### Testing with AES Recipe

```
1. Start TUI:
   $ python -m src.main

2. Navigate to recipe:
   - Press 'j' to move down
   - Press Enter on "Process Injection"
   - Press 'j' to select AES recipe
   - Press 'g' to generate

3. Parameter screen shows 5 parameters:
   * target_process (string) = "explorer.exe"
   * lhost (ip) = ""                         <-- REQUIRED, empty
   * lport (port) = 4444
   * output_file (string) = "injector.exe"
   * output_path (path) = "/home/user/Documents/Tools/paygen/output"

4. Fill in LHOST:
   - Tab to lhost field
   - Type: 192.168.1.100
   - Error disappears (was showing "This field is required")

5. Optional: Modify other parameters
   - Change lport to 8080
   - Change output_file to "custom_injector.exe"

6. Generate:
   - Press Ctrl+G
   - Notification shows:
     ✓ Configuration Complete
     Parameters configured for C# AES-Encrypted Shellcode Injector:
       • target_process: explorer.exe
       • lhost: 192.168.1.100
       • lport: 8080
       • output_file: custom_injector.exe
       • output_path: /home/user/Documents/Tools/paygen/output

     Build system will be implemented in Phase 5
```

## Testing Validation

### Test Invalid IP

```
1. Open parameter screen (press 'g')
2. Tab to lhost field
3. Type: 999.999.999.999
4. Error appears: ⚠ Invalid IP address: 999.999.999.999
5. Cannot generate until fixed
```

### Test Invalid Port

```
1. Tab to lport field
2. Type: 99999
3. Error appears: ⚠ Port must be between 1 and 65535, got 99999
4. Change to: 4444
5. Error disappears
```

### Test Required Fields

```
1. Clear lhost field (it's required)
2. Try to generate (Ctrl+G)
3. Error appears: ⚠ This field is required
4. Notification: "Please fill in all required fields"
5. Fill in lhost
6. Generate succeeds
```

## Keyboard Shortcuts

### In Parameter Screen

- `Tab` - Next field
- `Shift+Tab` - Previous field
- `Ctrl+G` - Generate with current parameters
- `Esc` - Cancel and return to recipe view
- `Enter` on button - Activate button
- Arrow keys - Navigate within text inputs

### In Main TUI (still available)

- `j/k` - Navigate recipes
- `h/l` - Switch between panels
- `g` - Open parameter configuration
- `?` - Help screen
- `q` - Quit

## Parameter Types Reference

| Type    | Widget   | Validation             | Example Valid Values    |
| ------- | -------- | ---------------------- | ----------------------- |
| string  | Input    | None                   | Any text                |
| ip      | Input    | IPv4/IPv6              | 192.168.1.1, ::1        |
| port    | Input    | 1-65535                | 80, 443, 4444           |
| path    | Input    | Path format            | /home/user, ~/Documents |
| hex     | Input    | Hex characters only    | deadbeef, CAFEBABE      |
| integer | Input    | Number, optional range | 1, 100, 9999            |
| choice  | Select   | One of allowed choices | Dropdown selection      |
| bool    | Checkbox | true/false             | Checked/Unchecked       |

## Config Placeholders

Parameters can reference config values:

```yaml
parameters:
  - name: "output_path"
    type: "path"
    default: "{config.output_dir}" # Automatically filled from config
```

Supported placeholders:

- `{config.output_dir}` → `/home/user/Documents/Tools/paygen/output`
- `{config.recipes_dir}` → `/home/user/Documents/Tools/paygen/recipes`
- `{config.payloads_dir}` → `/home/user/Documents/Tools/paygen/payloads`
- `{config.preprocessors_dir}` → `/home/user/Documents/Tools/paygen/preprocessors`

## Troubleshooting

### "No recipe selected" notification

- You must select a recipe first before pressing 'g'
- Navigate to a recipe in the left panel
- Then press 'g'

### Validation errors won't clear

- Make sure value is truly valid
- For IP: Must be valid IPv4 (192.168.1.1) or IPv6 (::1)
- For port: Must be numeric and 1-65535
- For hex: Only 0-9, a-f, A-F (no spaces, no 0x prefix)

### Cannot click Generate button

- Make sure there are no validation errors
- Make sure all required fields (\*) are filled
- Red error messages prevent generation

### Parameter screen doesn't appear

- Make sure you pressed 'g' while a recipe is selected
- Check that src/tui/param_config_screen.py exists
- Try restarting the TUI

## What's Next?

Phase 4 is complete! The parameter configuration system:

- ✅ Collects user input
- ✅ Validates parameters
- ✅ Returns configured parameters

**Phase 5** will:

- Execute preprocessing steps (msfvenom, encryption)
- Render templates with parameters
- Compile code
- Generate actual payloads
- Show build logs and output

---

Enjoy testing the parameter configuration! 🎉
