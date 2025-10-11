"""
Main MCP Server for macOS GUI Control

FastMCP-based server that exposes GUI control tools for LLMs.
"""

from mcp.server.fastmcp import FastMCP
import mcp_osx.ax as ax

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
    title="Perform element action",
    description="Executes the given action (e.g. Press, Open, ShowMenu, type, scroll, ...) on the specified element_id (as returned by list_elements. Note: The value argument is used for type, input, setValue"
)
def perform_element_action(bundle_id: str, element_id: str, action: str, value: str | None = None) -> bool:
    try:
        return ax.perform_element_action(bundle_id, element_id, action, value)
    except Exception as e:
        error_msg = f"Error performing action: {e}"
        print(f"✗ {error_msg}")
        return {"error": error_msg}

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

    # print(list_elements("com.apple.Music"))
    # print(perform_element_action("com.apple.Music", "0/0/0/0/0/0/0", "type", "RUFUS DU SOL"))
    # print(press_element("com.apple.finder", "AXStaticText[0]@0/0/0/0/4/0/0"))

    # Start the MCP server
    mcp.run()


if __name__ == "__main__":
    main()