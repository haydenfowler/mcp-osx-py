# MCP macOS GUI Control

A Model Context Protocol (MCP) server that enables LLMs to control macOS GUI applications through a robust three-tier automation strategy: **AppleScript → Accessibility API → PyAutoGUI fallback**.

## Features

- 🤖 **LLM Integration**: Full MCP protocol support for AI assistants
- 🍎 **Three-Tier Automation**: AppleScript → Accessibility → PyAutoGUI fallback
- 🎯 **Universal Control**: Works with any macOS application
- 🔒 **Permission Management**: Automatic permission checking and guidance
- 📊 **Rich UI Discovery**: Complete UI element hierarchy inspection
- ⚡ **Fast & Reliable**: Intelligent fallback ensures maximum compatibility

## Installation

### Prerequisites

- macOS 10.14+ (Mojave or later)
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Required macOS permissions (see below)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-osx-py.git
cd mcp-osx-py

# Install in development mode with uv (recommended)
uv add -e .

# Or sync dependencies only
uv sync
```

### Install as Package

```bash
# Using uv (recommended)
uv add mcp-osx

# Or using pip
pip install mcp-osx
```

## Required Permissions

### 1. Accessibility Permissions (Required)

**Why**: Needed for UI element discovery and interaction via the Accessibility API.

**How to enable**:
1. Open **System Settings** (or **System Preferences** on older macOS)
2. Go to **Privacy & Security** → **Accessibility**
3. Click the **+** button
4. Add your terminal application (Terminal, iTerm2, etc.)
5. Add Python (usually `/usr/bin/python3` or your Python path)

**Verify**: Run the server and check the startup message.

### 2. Apple Events Permissions (Optional but Recommended)

**Why**: Allows AppleScript automation for better compatibility.

**How to enable**:
1. Open **System Settings** → **Privacy & Security** → **Automation**
2. Enable automation for your terminal/Python process
3. Grant access to target applications (Finder, Safari, etc.)

## Usage

### Start the MCP Server

```bash
# Using the command-line tool
uv run mcp-osx

# Or run directly
uv run python -m mcp_osx.main

# Or from the package directory
uv run python src/mcp_osx/main.py
```

### Connect with MCP Client

The server will start and display connection information. Connect your MCP client (e.g., Claude Desktop) to the server URL.

### Available MCP Tools

#### `list_elements(app_name: str, window: str = None) -> dict`
List all UI elements in the specified app window.

```python
# Example: List all elements in Finder's front window
list_elements("Finder")
```

#### `press_element(app_name: str, element_id: str) -> bool`
Press (click) a UI element using three-tier automation.

```python
# Example: Click a button in TextEdit
press_element("TextEdit", "Save")
```

#### `enter_text(app_name: str, element_id: str, text: str) -> bool`
Enter text into a UI element.

```python
# Example: Type in a text field
enter_text("TextEdit", "document", "Hello, World!")
```

#### `read_value(app_name: str, element_id: str) -> str`
Read the value from a UI element.

```python
# Example: Read text field content
read_value("TextEdit", "document")
```

#### `scroll(app_name: str, direction: str, amount: int = 3) -> bool`
Scroll within an application.

```python
# Example: Scroll down in Safari
scroll("Safari", "down", 5)
```

#### `get_app_info(app_name: str) -> dict`
Get information about a running application.

#### `list_running_apps() -> dict`
List all currently running applications that can be controlled. Returns app names, bundle IDs, and other metadata.

```python
# Example: Get list of all running applications
list_running_apps()
```

#### `check_permissions() -> dict`
Check the current status of required macOS permissions.

## Application Discovery

The MCP server includes intelligent application discovery to handle various app naming conventions:

- **Automatic Name Matching**: Tries multiple variations of app names (with/without ".app", different cases, etc.)
- **Running Apps List**: Use `list_running_apps()` to see all available applications and their exact names
- **Bundle ID Support**: Supports both app names and bundle identifiers
- **Frontmost App Detection**: Can identify the currently active application

This means you can use natural app names like "Spotify", "Chrome", or "Finder" without worrying about exact system identifiers.

## Three-Tier Automation Strategy

### Tier 1: AppleScript
- **Best for**: Apps with scripting support (Finder, Safari, TextEdit, etc.)
- **Advantages**: Native, fast, reliable
- **Limitations**: Not all apps support AppleScript

### Tier 2: Accessibility API (via atomacos)
- **Best for**: Any visible UI element
- **Advantages**: Universal, detailed element information
- **Limitations**: Requires Accessibility permissions

### Tier 3: PyAutoGUI Fallback
- **Best for**: When other methods fail
- **Advantages**: Always works, pixel-perfect
- **Limitations**: No semantic understanding, requires coordinates

## Example Workflows

### Basic Text Editing
```python
# Open TextEdit and create a new document
press_element("TextEdit", "New Document")
enter_text("TextEdit", "document", "This is automated text!")
press_element("TextEdit", "Save")
```

### Web Browsing
```python
# Navigate Safari
press_element("Safari", "Address Bar")
enter_text("Safari", "Address Bar", "https://example.com")
press_element("Safari", "Go")
scroll("Safari", "down", 3)
```

### File Management
```python
# Use Finder
list_elements("Finder")  # See current directory contents
press_element("Finder", "New Folder")
enter_text("Finder", "folder_name", "My New Folder")
press_element("Finder", "Create")
```

## Troubleshooting

### Common Issues

#### "Accessibility permissions not granted"
- **Solution**: Enable Accessibility permissions in System Settings
- **Check**: Run `check_permissions()` tool to verify

#### "Application not found"
- **Solution**: Ensure the app is running and spelled correctly
- **Tip**: Use exact app names (e.g., "Finder", not "finder")

#### "Element not found"
- **Solution**: Use `list_elements()` to discover available elements
- **Tip**: Element IDs can be titles, descriptions, or identifiers

#### AppleScript errors
- **Solution**: Check if the app supports AppleScript
- **Fallback**: The system will automatically try Accessibility API and PyAutoGUI

### Debug Mode

Run with verbose output to see which automation tier is being used:

```bash
python -m mcp_osx.main --verbose
```

### Permission Verification

```python
# Check all permissions
check_permissions()

# Test basic functionality
get_app_info("Finder")
list_elements("Finder")
```

## Development

This project uses [uv](https://github.com/astral-sh/uv) for fast dependency management and virtual environment handling.

### Project Structure
```
mcp-osx-py/
├── src/mcp_osx/
│   ├── __init__.py
│   ├── main.py          # FastMCP server and tool definitions
│   ├── applescript.py   # AppleScript automation layer
│   ├── ax.py           # Accessibility API layer
│   └── fallback.py     # PyAutoGUI fallback layer
├── pyproject.toml       # Package configuration (uv managed)
├── requirements.txt     # Dependencies (for reference)
└── README.md
```

### Adding New Tools

1. Define the tool function with `@mcp.tool()` decorator
2. Implement three-tier logic in the function
3. Add proper error handling and logging
4. Update documentation

### Testing

```bash
# Test individual components
uv run python -c "from mcp_osx import ax; print(ax.check_ax_permissions())"
uv run python -c "from mcp_osx import applescript; print(applescript.is_app_scriptable('Finder'))"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on macOS
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP framework
- [atomacos](https://github.com/daveenguyen/atomacos) for Accessibility API bindings
- [PyAutoGUI](https://github.com/asweigart/pyautogui) for cross-platform automation
- [PyObjC](https://github.com/ronaldoussoren/pyobjc) for Objective-C bindings

## Support

- 📖 **Documentation**: This README and inline code comments
- 🐛 **Issues**: GitHub Issues for bug reports
- 💬 **Discussions**: GitHub Discussions for questions and ideas
- 🔧 **Contributing**: Pull requests welcome!

---

**Note**: This tool requires macOS and appropriate system permissions. Always test automation scripts in a safe environment before using them with important data.
