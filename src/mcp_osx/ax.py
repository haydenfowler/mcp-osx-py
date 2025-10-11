"""
Accessibility (AX) Layer for macOS GUI Control

Provides functions to interact with macOS UI elements via the Accessibility API using atomacos.
This is the second tier in our three-layer automation strategy.
"""

import atomacos
from typing import Dict, Any, Optional, Tuple
try:
    from Quartz import AXIsProcessTrusted
except ImportError:
    try:
        from ApplicationServices import AXIsProcessTrusted
    except ImportError:
        # Fallback function if AXIsProcessTrusted is not available
        def AXIsProcessTrusted():
            return False
from objc import nil
import psutil
import plistlib
import os
import mcp_osx.serializewindowstructure  as windowmethods
import mcp_osx.elementfinder as elementfinder

def check_ax_permissions() -> bool:
    """
    Check if the current process has Accessibility permissions.
    
    Returns:
        True if permissions are granted, False otherwise
    """
    return AXIsProcessTrusted()


def get_app_reference(bundle_id: str = None) -> Optional[atomacos.NativeUIElement]:
    try:
        return atomacos.getAppRefByBundleId(bundle_id)
    except Exception as e:
        print(f"Error getting app reference for bundle_id='{bundle_id}': {e}")
        return None


def get_front_window(app: atomacos.NativeUIElement) -> Optional[atomacos.NativeUIElement]:
    """
    Get the front window of an application.
    
    Args:
        app: Atom instance of the application
        
    Returns:
        Atom instance of the front window or None
    """
    try:
        # Try to get the frontmost window, fallback to any window if needed
        windows = app.windows()
        if not windows:
            # Try to access alternate frontmostWindow property if present
            try:
                front_window = getattr(app, "AXFrontmostWindow", None)
                if front_window:
                    return front_window
            except Exception:
                pass
            return None
        # If any windows, return the one that is focused/frontmost if possible
        for win in windows:
            try:
                if getattr(win, "AXMain", False) or getattr(win, "AXFocused", False):
                    return win
            except Exception:
                continue
        # Otherwise just return the first window
        return windows[0]
    except Exception as e:
        print(f"Error getting front window: {e}")
        return None

def list_elements(bundle_id: str = None) -> Dict[str, Any]:
    try:
        app = get_app_reference(bundle_id)
        if not app:
            return {"error": f"Application with bundle_id='{bundle_id}' not found"}

        window = get_front_window(app)
        if not window:
            return {"error": f"No window found in application"}
        
        # return windowmethods.get_window_structure(window)
        return windowmethods.get_window_structure_abstract(window)
        
    except Exception as e:
        return {"error": f"Error listing elements: {e}"}


def find_element(bundle_id: str, element_id: str) -> Optional[atomacos.NativeUIElement]:
    try:
        app = get_app_reference(bundle_id)
        if not app:
            return None
        
        window = get_front_window(app)
        if not window:
            return None
        
        return elementfinder.find_element_by_id(window, element_id=element_id)
        
    except Exception as e:
        print(f"Error finding element {element_id}: {e}")
        return None  

def perform_element_action(bundle_id: str, element_id: str, action: str, value: str | None = None) -> bool:
    try:
        app = get_app_reference(bundle_id)
        if not app:
            return None
        
        window = get_front_window(app)
        if not window:
            return None
        
        return elementfinder.perform_element_action(app, window, element_id, action, value)
        
    except Exception as e:
        print(f"Error finding element {element_id}: {e}")
        return None  

def press_element(element: atomacos.NativeUIElement) -> bool:
    try:
        current = element
        visited = set()

        while current:
            if id(current) in visited:
                break
            visited.add(id(current))

            try:
                actions = current.getActions()
            except Exception:
                actions = []

            for action in ("Press", "Open", "ShowMenu", "Raise", "PerformClick"):
                if action in actions:
                    try:
                        getattr(current, action)()
                        return True
                    except Exception as e:
                        if "-25205" in str(e):
                            return True

            try:
                current = getattr(current, "AXParent", None)
            except Exception:
                current = None

        return False

    except Exception:
        return False


def enter_text(element: atomacos.NativeUIElement, text: str) -> bool:
    """
    Enter text into a text field element.
    
    Args:
        element: Atom instance of the text field
        text: Text to enter
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Focus the element first
        element.setAttribute("AXFocused", True)
        
        # Set the value
        element.setAttribute("AXValue", text)
        return True
        
    except Exception as e:
        print(f"Error entering text: {e}")
        return False

def get_element_coords(element: atomacos.NativeUIElement) -> Optional[Tuple[int, int]]:
    """
    Get the screen coordinates of a UI element.
    
    Args:
        element: Atom instance of the element
        
    Returns:
        Tuple of (x, y) coordinates or None if not available
    """
    try:
        position = element.AXPosition
        size = element.AXSize
        
        # Calculate center coordinates
        center_x = int(position.x + size.width / 2)
        center_y = int(position.y + size.height / 2)
        
        return (center_x, center_y)
        
    except Exception as e:
        print(f"Error getting element coordinates: {e}")
        return None


def scroll_element(element: atomacos.NativeUIElement, direction: str, amount: int) -> bool:
    """
    Scroll an element in the specified direction.
    
    Args:
        element: Atom instance of the element to scroll
        direction: "up", "down", "left", or "right"
        amount: Number of units to scroll
        
    Returns:
        True if successful, False otherwise
    """
    try:
        actions = element.getActions()
        
        # Map direction to action names
        action_map = {
            "up": "AXScrollUp",
            "down": "AXScrollDown", 
            "left": "AXScrollLeft",
            "right": "AXScrollRight"
        }
        
        action_name = action_map.get(direction.lower())
        if action_name and action_name in actions:
            # Try to scroll multiple times for the amount
            for _ in range(abs(amount)):
                getattr(element, action_name)()
            return True
        
        # Try generic scroll actions
        if direction.lower() in ["up", "down"]:
            for _ in range(abs(amount)):
                if direction.lower() == "up":
                    element.AXScrollUp()
                else:
                    element.AXScrollDown()
            return True
        
        return False
        
    except Exception as e:
        print(f"Error scrolling element: {e}")
        return False


def scroll_window(bundle_id: str = None, direction: str = None, amount: int = 3) -> bool:
    """
    Scroll the front window of an application.
    
    Args:
        bundle_id: Bundle ID of the application
        direction: "up", "down", "left", or "right"
        amount: Number of units to scroll
        
    Returns:
        True if successful, False otherwise
    """
    try:
        app = get_app_reference(bundle_id)
        if not app:
            return False
        
        window = get_front_window(app)
        if not window:
            return False
        
        return scroll_element(window, direction, amount)
        
    except Exception as e:
        print(f"Error scrolling window: {e}")
        return False

def start_app(bundle_id: str) -> bool:
    try:
        atomacos.launchAppByBundleId(bundle_id)
        app = get_app_reference(bundle_id)
        
        return app is not None
        
    except Exception as e:
        print(f"Failed to start app: {e}")
        return False

def focus_app(bundle_id: str) -> bool:
    try:
        app = get_app_reference(bundle_id)
        if not app:
            return False
        
        window = get_front_window(app)
        if not window:
            return False

        window.activate()
        return True
        
    except Exception as e:
        print(f"Failed to focus app: {e}")
        return False


def list_running_apps() -> Dict[str, Any]:
    """
    List all currently running applications that can be controlled.
    
    Returns:
        Dictionary containing list of running applications with their exact names
    """
    try:
        name_to_bundle = {}
        for p in psutil.process_iter(['name', 'exe']):
            if p.info['exe'] and ".app/Contents/MacOS" in p.info['exe']:
                try:
                    info_plist_path = os.path.join(p.info['exe'].split(".app/")[0] + ".app", "Contents", "Info.plist")
                    with open(info_plist_path, 'rb') as f:
                        plist = plistlib.load(f)
                        bundle_id = plist.get('CFBundleIdentifier')
                        name = plist.get('CFBundleName') or p.info['name']
                except (FileNotFoundError, ValueError, KeyError):
                    name = p.info['name']
                    bundle_id = None

                # Only add unique names
                if name not in name_to_bundle:
                    name_to_bundle[name] = bundle_id

        return name_to_bundle
    except Exception as e:
        return {"error": f"Error listing running apps: {e}"}
