# Paygen Development Environment
# Nix shell configuration for reproducible development
{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  packages = with pkgs; [
    # Python 3.11 with development tools
    python311
    python311Packages.pip
    python311Packages.virtualenv

    # Python dependencies for Paygen
    python311Packages.pyyaml
    python311Packages.jinja2
    python311Packages.textual
    python311Packages.rich
    python311Packages.pycryptodome
    python311Packages.pytest
    python311Packages.flask
    python311Packages.flask-cors

    # Development tools
    git

    # C# compilation
    mono

    # Payload generation tools
    metasploit

    # Additional compilation tools
    gcc
    gnumake

    # Mingw for Windows PE compilation (optional)
    # mingw-w64
  ];

  shellHook = ''
    echo "🚀 Paygen Development Environment"
    echo "=================================="
    echo "Python version: $(python --version)"
    echo "Mono version: $(mono --version | head -n1)"
    echo ""
    echo "Installed packages:"
    echo "  - PyYAML, Jinja2, Textual, Rich, PyCryptodome"
    echo "  - Flask, Flask-CORS (web GUI)"
    echo "  - pytest (testing framework)"
    echo ""
    echo "Payload tools:"
    echo "  - Metasploit Framework (msfvenom)"
    echo "  - Mono C# compiler (mcs)"
    echo "  - GCC & Make"
    echo ""
    echo "Ready to develop! Run 'pytest' to run tests."
  '';
}
