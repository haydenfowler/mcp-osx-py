"""
Main MCP Server for macOS GUI Control

FastMCP-based server that exposes GUI control tools for LLMs.
Each tool uses a three-tier automation strategy: AppleScript → Accessibility API → PyAutoGUI.
"""

from mcp.server.fastmcp import FastMCP
from . import applescript
from . import ax
from . import fallback


# Initialize FastMCP server
mcp = FastMCP(name="macOS_GUI_Control")


def check_permissions_on_startup():
    """Check and report on required permissions."""
    print("Checking macOS permissions...")
    
    # Check Accessibility permissions
    if not ax.check_ax_permissions():
        print("⚠️  WARNING: Accessibility permissions not granted!")
        print("   Enable in: System Settings → Privacy & Security → Accessibility")
        print("   This will limit functionality to AppleScript and PyAutoGUI fallback.")
    else:
        print("✓ Accessibility permissions granted")
    
    print("Note: Some apps may require 'Allow Apple Events' in System Settings → Privacy & Security → Automation")


@mcp.tool()
def list_elements(app_name: str, window: str = None) -> dict:
    """
    Return the UI element hierarchy of the specified app window.
    
    Args:
        app_name: Name of the application (use exact name from list_running_apps())
        window: Name of the window (optional, uses front window if not specified)
        
    Returns:
        Dictionary containing the UI element hierarchy with roles, titles, identifiers, and positions
    """
    try:
        result = ax.list_elements(app_name, window)
        print(f"✓ Listed elements for {app_name} window: {window or 'front'}")
        return result
    except Exception as e:
        error_msg = f"Error listing elements: {e}"
        print(f"✗ {error_msg}")
        return {"error": error_msg}


@mcp.tool()
def press_element(app_name: str, element_id: str) -> bool:
    """
    Press (click) the specified UI element in the given application.
    
    Uses three-tier automation: AppleScript → Accessibility API → PyAutoGUI fallback.
    
    Args:
        app_name: Name of the application (use exact name from list_running_apps())
        element_id: Element identifier, title, or description to press
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Attempting to press element '{element_id}' in '{app_name}'...")
    
    # Layer 1: AppleScript
    try:
        if applescript.press_element(app_name, element_id):
            print(f"✓ AppleScript: pressed '{element_id}' in '{app_name}'")
            return True
    except Exception as e:
        print(f"  AppleScript failed: {e}")
    
    # Layer 2: Accessibility API
    try:
        elem = ax.find_element(app_name, element_id)
        if elem:
            if ax.press_element(elem):
                print(f"✓ Accessibility: pressed '{element_id}'")
                return True
            else:
                print(f"  Accessibility: found element but press failed")
        else:
            print(f"  Accessibility: element '{element_id}' not found")
    except Exception as e:
        print(f"  Accessibility failed: {e}")
    
    # Layer 3: PyAutoGUI Fallback
    try:
        elem = ax.find_element(app_name, element_id)
        if elem:
            coords = ax.get_element_coords(elem)
            if coords:
                if fallback.click_at(*coords):
                    print(f"✓ PyAutoGUI: clicked at {coords}")
                    return True
                else:
                    print(f"  PyAutoGUI: click at {coords} failed")
            else:
                print(f"  PyAutoGUI: could not get coordinates for element")
        else:
            print(f"  PyAutoGUI: element not found for coordinate lookup")
    except Exception as e:
        print(f"  PyAutoGUI failed: {e}")
    
    print(f"✗ Failed to press '{element_id}' in '{app}' using all methods")
    return False


@mcp.tool()
def enter_text(app_name: str, element_id: str, text: str) -> bool:
    """
    Enter text into the specified UI element in the given application.
    
    Uses three-tier automation: AppleScript → Accessibility API → PyAutoGUI fallback.
    
    Args:
        app_name: Name of the application (use exact name from list_running_apps())
        element_id: Element identifier, title, or description
        text: Text to enter into the element
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Attempting to enter text '{text}' into element '{element_id}' in '{app_name}'...")
    
    # Layer 1: AppleScript
    try:
        if applescript.enter_text(app_name, element_id, text):
            print(f"✓ AppleScript: entered text into '{element_id}'")
            return True
    except Exception as e:
        print(f"  AppleScript failed: {e}")
    
    # Layer 2: Accessibility API
    try:
        elem = ax.find_element(app_name, element_id)
        if elem:
            if ax.enter_text(elem, text):
                print(f"✓ Accessibility: entered text into '{element_id}'")
                return True
            else:
                print(f"  Accessibility: found element but text entry failed")
        else:
            print(f"  Accessibility: element '{element_id}' not found")
    except Exception as e:
        print(f"  Accessibility failed: {e}")
    
    # Layer 3: PyAutoGUI Fallback
    try:
        elem = ax.find_element(app_name, element_id)
        if elem:
            coords = ax.get_element_coords(elem)
            if coords:
                # Click to focus, then type
                if fallback.click_at(*coords) and fallback.type_text(text):
                    print(f"✓ PyAutoGUI: clicked at {coords} and typed text")
                    return True
                else:
                    print(f"  PyAutoGUI: click or typing failed")
            else:
                print(f"  PyAutoGUI: could not get coordinates for element")
        else:
            print(f"  PyAutoGUI: element not found for coordinate lookup")
    except Exception as e:
        print(f"  PyAutoGUI failed: {e}")
    
    print(f"✗ Failed to enter text into '{element_id}' in '{app_name}' using all methods")
    return False


@mcp.tool()
def read_value(app_name: str, element_id: str) -> str:
    """
    Read the value from the specified UI element in the given application.
    
    Uses two-tier approach: AppleScript → Accessibility API (PyAutoGUI cannot read values).
    
    Args:
        app_name: Name of the application (use exact name from list_running_apps())
        element_id: Element identifier, title, or description
        
    Returns:
        Element value as string, or error message if failed
    """
    print(f"Attempting to read value from element '{element_id}' in '{app_name}'...")
    
    # Layer 1: AppleScript
    try:
        success, value = applescript.read_value(app_name, element_id)
        if success:
            print(f"✓ AppleScript: read value '{value}' from '{element_id}'")
            return value
        else:
            print(f"  AppleScript: {value}")
    except Exception as e:
        print(f"  AppleScript failed: {e}")
    
    # Layer 2: Accessibility API
    try:
        elem = ax.find_element(app_name, element_id)
        if elem:
            value = ax.read_value(elem)
            if value:
                print(f"✓ Accessibility: read value '{value}' from '{element_id}'")
                return value
            else:
                print(f"  Accessibility: element found but no value available")
        else:
            print(f"  Accessibility: element '{element_id}' not found")
    except Exception as e:
        print(f"  Accessibility failed: {e}")
    
    error_msg = f"Failed to read value from '{element_id}' in '{app_name}'"
    print(f"✗ {error_msg}")
    return error_msg


@mcp.tool()
def scroll(app_name: str, direction: str, amount: int = 3) -> bool:
    """
    Scroll in the specified direction within the given application.
    
    Uses two-tier approach: Accessibility API → PyAutoGUI fallback.
    
    Args:
        app_name: Name of the application (use exact name from list_running_apps())
        direction: Direction to scroll ("up", "down", "left", "right")
        amount: Number of scroll units (default: 3)
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Attempting to scroll {direction} by {amount} units in '{app_name}'...")
    
    # Layer 1: Accessibility API
    try:
        if ax.scroll_window(app_name, direction, amount):
            print(f"✓ Accessibility: scrolled {direction} by {amount} units")
            return True
        else:
            print(f"  Accessibility: scroll action not available")
    except Exception as e:
        print(f"  Accessibility failed: {e}")
    
    # Layer 2: PyAutoGUI Fallback
    try:
        # Convert direction to scroll amount
        scroll_amount = amount if direction.lower() in ["up", "right"] else -amount
        
        if direction.lower() in ["up", "down"]:
            success = fallback.scroll(scroll_amount)
        else:  # left, right
            success = fallback.hscroll(scroll_amount)
        
        if success:
            print(f"✓ PyAutoGUI: scrolled {direction} by {amount} units")
            return True
        else:
            print(f"  PyAutoGUI: scroll failed")
    except Exception as e:
        print(f"  PyAutoGUI failed: {e}")
    
    print(f"✗ Failed to scroll {direction} in '{app_name}' using all methods")
    return False


@mcp.tool()
def get_app_info(app_name: str) -> dict:
    """
    Get information about a running application.
    
    Args:
        app_name: Name of the application (use exact name from list_running_apps())
        
    Returns:
        Dictionary containing app information
    """
    try:
        result = applescript.get_app_info(app_name)
        print(f"✓ Retrieved info for app '{app_name}'")
        return result
    except Exception as e:
        error_msg = f"Error getting app info: {e}"
        print(f"✗ {error_msg}")
        return {"error": error_msg}


@mcp.tool()
def list_running_apps() -> dict:
    """
    List all currently running applications that can be controlled.
    
    Returns:
        Dictionary containing list of running applications with their exact names
    """
    try:
        result = ax.list_running_apps()
        print("✓ Retrieved list of running applications")
        return result
    except Exception as e:
        error_msg = f"Error listing running apps: {e}"
        print(f"✗ {error_msg}")
        return {"error": error_msg}


@mcp.tool()
def check_permissions() -> dict:
    """
    Check the current status of required macOS permissions.
    
    Returns:
        Dictionary containing permission status
    """
    ax_permissions = ax.check_ax_permissions()
    
    result = {
        "accessibility": ax_permissions,
        "applescript": True,  # AppleScript doesn't require special permissions
        "pyautogui": True,    # PyAutoGUI doesn't require special permissions
    }
    
    print("Permission status:")
    print(f"  Accessibility: {'✓ Granted' if ax_permissions else '✗ Not granted'}")
    print(f"  AppleScript: ✓ Available")
    print(f"  PyAutoGUI: ✓ Available")
    
    return result


def main():
    """Main entry point for the MCP server."""
    print("🚀 Starting MCP macOS GUI Control Server")
    print("=" * 50)
    
    # Check permissions on startup
    check_permissions_on_startup()
    
    print("\n📋 Available MCP Tools:")
    print("  • list_elements(app_name, window) - List UI elements")
    print("  • press_element(app_name, element_id) - Click/press element")
    print("  • enter_text(app_name, element_id, text) - Enter text")
    print("  • read_value(app_name, element_id) - Read element value")
    print("  • scroll(app_name, direction, amount) - Scroll in app")
    print("  • get_app_info(app_name) - Get app information")
    print("  • list_running_apps() - List all running applications")
    print("  • check_permissions() - Check macOS permissions")
    
    print("\n🔗 MCP Server starting...")
    print("Connect your MCP client to this server to control macOS GUI applications!")
    print("=" * 50)
    
    # Start the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
