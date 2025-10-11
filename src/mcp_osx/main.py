"""
Main MCP Server for macOS GUI Control

FastMCP-based server that exposes GUI control tools for LLMs.
"""

from mcp.server.fastmcp import FastMCP
# import mcp_osx.applescript as applescript
import mcp_osx.ax as ax
# import mcp_osx.fallback as fallback

# Initialize FastMCP server
mcp = FastMCP(
    name="macOS_GUI_Control",
    instructions="A tool for controlling the macOS GUI, including listing and interacting with UI elements in running applications."
)

def check_permissions_on_startup():
    """Check and report on required permissions."""
    print("Checking macOS permissions...")
    
    # Check Accessibility permissions
    if not ax.check_ax_permissions():
        try:
            import subprocess
            # Try to open Accessibility using URI (works on Ventura+)
            subprocess.run([
                "open",
                "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
            ], check=True)
        except Exception as err:
            print(f"Unable to open System Settings automatically: {err}")


        print("\n" + "="*60)
        print("⚠️  Accessibility Permission Required ⚠️")
        print(f"This application needs Accessibility permissions to function.")
        print(f"Enable Accessibility access for this app and restart this application after enabling permissions.")
        print("="*60 + "\n")
        raise RuntimeError("Accessibility permissions are not granted. Cannot interact with windows or list elements. Please enable Accessibility permissions for this app in System Settings → Privacy & Security → Accessibility.")
    else:
        print("✓ Accessibility permissions granted")
    
    print("Note: Some apps may require 'Allow Apple Events' in System Settings → Privacy & Security → Automation")

@mcp.tool(
    title="List UI Elements",
    description="Return the UI element hierarchy of the specified app window."
)
def list_elements(bundle_id: str = None) -> dict:
    try:
        result = ax.list_elements(bundle_id=bundle_id)
        return result
    except Exception as e:
        error_msg = f"Error listing elements: {e}"
        print(f"✗ {error_msg}")
        return {"error": error_msg}


@mcp.tool(
    title="Press UI Element",
    description="Press (click) the specified UI element in the given application."
)
def press_element(bundle_id: str = None, element_id: str = None) -> bool:
    """
    Press (click) the specified UI element in the given application.
    
    Args:
        bundle_id: Bundle ID of the application (e.g., com.apple.finder)
        element_id: Element identifier, title, or description to press
        
    Returns:
        True if successful, False otherwise
    """
    
    # Layer 1: AppleScript
    # try:
    #     if applescript.press_element(bundle_id=bundle_id, element_id=element_id):
    #         print(f"✓ AppleScript: pressed '{element_id}' in '{bundle_id}'")
    #         return True
    # except Exception as e:
    #     print(f"  AppleScript failed: {e}")
    
    # Layer 2: Accessibility API
    try:
        elem = ax.find_element(bundle_id=bundle_id, element_id=element_id)
        print(elem)
        if elem:
            if ax.press_element(elem):
                return True
            else:
                print(f"  Accessibility: found element but press failed")
        else:
            print(f"  Accessibility: element '{element_id}' not found")
    except Exception as e:
        print(f"  Accessibility failed: {e}")
    
    # Layer 3: PyAutoGUI Fallback
    # try:
    #     elem = ax.find_element(bundle_id=bundle_id, element_id=element_id)
    #     if elem:
    #         coords = ax.get_element_coords(elem)
    #         if coords:
    #             if fallback.click_at(*coords):
    #                 print(f"✓ PyAutoGUI: clicked at {coords}")
    #                 return True
    #             else:
    #                 print(f"  PyAutoGUI: click at {coords} failed")
    #         else:
    #             print(f"  PyAutoGUI: could not get coordinates for element")
    #     else:
    #         print(f"  PyAutoGUI: element not found for coordinate lookup")
    # except Exception as e:
    #     print(f"  PyAutoGUI failed: {e}")
    
    # print(f"✗ Failed to press '{element_id}' in '{bundle_id}' using all methods")
    return False


@mcp.tool(
    title="Enter Text",
    description="Enter text into the specified UI element in the given application."
)
def enter_text(bundle_id: str = None, element_id: str = None, text: str = None) -> bool:
    """
    Enter text into the specified UI element in the given application.
    
    Args:
        bundle_id: Bundle ID of the application (e.g., com.apple.finder)
        element_id: Element identifier, title, or description
        text: Text to enter into the element
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Attempting to enter text '{text}' into element '{element_id}' in '{bundle_id}'...")
    
    # Layer 1: AppleScript
    # try:
    #     if applescript.enter_text(bundle_id=bundle_id, element_id=element_id, text=text):
    #         print(f"✓ AppleScript: entered text into '{element_id}'")
    #         return True
    # except Exception as e:
    #     print(f"  AppleScript failed: {e}")
    
    # Layer 2: Accessibility API
    try:
        elem = ax.find_element(bundle_id=bundle_id, element_id=element_id)
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
    # try:
    #     elem = ax.find_element(bundle_id=bundle_id, element_id=element_id)
    #     if elem:
    #         coords = ax.get_element_coords(elem)
    #         if coords:
    #             # Click to focus, then type
    #             if fallback.click_at(*coords) and fallback.type_text(text):
    #                 print(f"✓ PyAutoGUI: clicked at {coords} and typed text")
    #                 return True
    #             else:
    #                 print(f"  PyAutoGUI: click or typing failed")
    #         else:
    #             print(f"  PyAutoGUI: could not get coordinates for element")
    #     else:
    #         print(f"  PyAutoGUI: element not found for coordinate lookup")
    # except Exception as e:
    #     print(f"  PyAutoGUI failed: {e}")
    
    # print(f"✗ Failed to enter text into '{element_id}' in '{bundle_id}' using all methods")
    return False


@mcp.tool(
    title="Read Value",
    description="Read the value from the specified UI element in the given application."
)
def read_value(bundle_id: str = None, element_id: str = None) -> str:
    """
    Read the value from the specified UI element in the given application.
        
    Args:
        bundle_id: Bundle ID of the application (e.g., com.apple.finder)
        element_id: Element identifier, title, or description
        
    Returns:
        Element value as string, or error message if failed
    """
    print(f"Attempting to read value from element '{element_id}' in '{bundle_id}'...")
    
    # Layer 1: AppleScript
    # try:
    #     success, value = applescript.read_value(bundle_id=bundle_id, element_id=element_id)
    #     if success:
    #         print(f"✓ AppleScript: read value '{value}' from '{element_id}'")
    #         return value
    #     else:
    #         print(f"  AppleScript: {value}")
    # except Exception as e:
    #     print(f"  AppleScript failed: {e}")
    
    # Layer 2: Accessibility API
    try:
        elem = ax.find_element(bundle_id=bundle_id, element_id=element_id)
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
    
    error_msg = f"Failed to read value from '{element_id}' in '{bundle_id}'"
    print(f"✗ {error_msg}")
    return error_msg


@mcp.tool(
    title="Scroll",
    description="Scroll in the specified direction within the given application."
)
def scroll(bundle_id: str = None, direction: str = None, amount: int = 3) -> bool:
    """
    Scroll in the specified direction within the given application.
    
    Args:
        bundle_id: Bundle ID of the application (e.g., com.apple.finder)
        direction: Direction to scroll ("up", "down", "left", "right")
        amount: Number of scroll units (default: 3)
        
    Returns:
        True if successful, False otherwise
    """
    print(f"Attempting to scroll {direction} by {amount} units in '{bundle_id}'...")
    
    # Layer 1: Accessibility API
    try:
        if ax.scroll_window(bundle_id=bundle_id, direction=direction, amount=amount):
            print(f"✓ Accessibility: scrolled {direction} by {amount} units")
            return True
        else:
            print(f"  Accessibility: scroll action not available")
    except Exception as e:
        print(f"  Accessibility failed: {e}")
    
    # Layer 2: PyAutoGUI Fallback
    # try:
    #     # Convert direction to scroll amount
    #     scroll_amount = amount if direction.lower() in ["up", "right"] else -amount
        
    #     if direction.lower() in ["up", "down"]:
    #         success = fallback.scroll(scroll_amount)
    #     else:  # left, right
    #         success = fallback.hscroll(scroll_amount)
        
    #     if success:
    #         print(f"✓ PyAutoGUI: scrolled {direction} by {amount} units")
    #         return True
    #     else:
    #         print(f"  PyAutoGUI: scroll failed")
    # except Exception as e:
    #     print(f"  PyAutoGUI failed: {e}")
    
    # print(f"✗ Failed to scroll {direction} in '{bundle_id}' using all methods")
    return False

@mcp.tool(
    title="List Running Apps",
    description="List all currently running applications that can be controlled."
)
def list_running_apps() -> dict:
    """
    List all currently running applications that can be controlled.
    
    Returns:
        Dictionary containing list of running applications with their names
        as the key and their bundle_id as the value
    """
    try:
        result = ax.list_running_apps()
        print("✓ Retrieved list of running applications")
        return result
    except Exception as e:
        return {"error": f"Error listing running apps: {e}"}

@mcp.tool(
    title="Start an app",
    description="Starts an app and optionally focusses the window"
)
def start_app(bundle_id: str, focusApp: bool = False) -> bool:
    try :
        result = ax.start_app(bundle_id)
        if result and focusApp:
            return ax.focus_app(bundle_id)
        return result
    except Exception as e:
        return {"error": f"Error starting app: {e}"}

@mcp.tool(
    title="Check Permissions",
    description="Check the current status of required macOS permissions."
)
def check_permissions() -> dict:
    """
    Check the current status of required macOS permissions.
    
    Returns:
        Dictionary containing permission status
    """
    ax_permissions = ax.check_ax_permissions()
    
    result = {
        "accessibility": ax_permissions,
    }
    
    print("Permission status:")
    print(f"  Accessibility: {'✓ Granted' if ax_permissions else '✗ Not granted'}")
    
    return result

def main():
    # Check permissions on startup
    check_permissions_on_startup()

    # print(list_elements("com.apple.finder"))
    # print(press_element("com.apple.finder", "AXStaticText[0]@0/0/0/0/4/0/0"))

    # Start the MCP server
    mcp.run()


if __name__ == "__main__":
    main()