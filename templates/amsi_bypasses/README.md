# AMSI Bypasses

This directory contains PowerShell AMSI bypass methods that can be injected into:
- PowerShell template payloads (.ps1 files)
- Launch instruction PowerShell code blocks

## Built-in Bypasses

1. **AmsiInitialize.ps1** - Sets AmsiInitFailed to true
2. **amsiContext.ps1** - Patches AMSI context in memory

## Adding Custom Bypasses

To add your own AMSI bypass:

1. Create a `.ps1` file in this directory
2. The filename (without extension) becomes the bypass name in the dropdown
3. Underscores in filename are converted to spaces (e.g., `my_custom_bypass.ps1` → "my custom bypass")
4. File should contain only the bypass code (no comments or extra whitespace needed)

### Example

Create `memory_patch_v2.ps1`:
```powershell
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)
```

This will appear in the dropdown as "memory patch v2".

## Notes

- Keep bypasses concise (one-liners work best for inline injection)
- Test bypasses against current Windows Defender signatures
- Bypasses are injected BEFORE obfuscation for better evasion
- One-liner bypasses in launch instructions are automatically prepended to download cradles
