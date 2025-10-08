"""
Accessibility (AX) Layer for macOS GUI Control

Provides functions to interact with macOS UI elements via the Accessibility API using atomacos.
This is the second tier in our three-layer automation strategy.
"""

import atomacos
from typing import Dict, Any, List, Optional, Tuple
try:
    from Quartz import AXIsProcessTrusted
except ImportError:
    try:
        from ApplicationServices import AXIsProcessTrusted
    except ImportError:
        # Fallback function if AXIsProcessTrusted is not available
        def AXIsProcessTrusted():
            return False
import json


def check_ax_permissions() -> bool:
    """
    Check if the current process has Accessibility permissions.
    
    Returns:
        True if permissions are granted, False otherwise
    """
    return AXIsProcessTrusted()


def get_app_by_name(app_name: str) -> Optional[atomacos.NativeUIElement]:
    """
    Get an atomacos Atom instance for the specified application.
    
    Args:
        app_name: Name of the application (e.g., "Finder", "TextEdit", "Spotify")
        
    Returns:
        Atom instance or None if not found
    """
    try:
        # Try different variations of the app name for better matching
        name_variations = [
            app_name,
            app_name + ".app",
            app_name.lower(),
            app_name.upper(),
            app_name.title(),
            app_name.replace(" ", ""),  # Remove spaces
            app_name.replace(" ", "").lower()
        ]
        
        for variation in name_variations:
            # Try to find the app by bundle ID first
            app = atomacos.getAppRefByBundleId(variation)
            if app:
                return app
            
            # Try to find by localized name
            app = atomacos.getAppRefByLocalizedName(variation)
            if app:
                return app
        
        # Try to get frontmost app if it matches
        try:
            frontmost = atomacos.getFrontmostApp()
            if frontmost and hasattr(frontmost, 'AXTitle'):
                frontmost_title = frontmost.AXTitle.lower()
                if any(var.lower() in frontmost_title for var in name_variations):
                    return frontmost
        except:
            pass
                
        return None
    except Exception as e:
        print(f"Error getting app {app_name}: {e}")
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
        windows = app.findFirstR(AXRole="AXWindow")
        if windows:
            return windows
        
        # Try to get the first window if no front window found
        windows = app.findFirst(AXRole="AXWindow")
        return windows
    except Exception as e:
        print(f"Error getting front window: {e}")
        return None


def list_elements(app_name: str, window_name: str = None) -> Dict[str, Any]:
    """
    List all UI elements in the specified app window.
    
    Args:
        app_name: Name of the application
        window_name: Name of the window (optional, uses front window if not specified)
        
    Returns:
        Dictionary containing the UI element hierarchy
    """
    try:
        app = get_app_by_name(app_name)
        if not app:
            return {"error": f"Application '{app_name}' not found"}
        
        window = get_front_window(app)
        if not window:
            return {"error": f"No window found in application '{app_name}'"}
        
        def element_to_dict(element: atomacos.NativeUIElement, depth: int = 0) -> Dict[str, Any]:
            """Recursively convert element to dictionary."""
            if depth > 10:  # Prevent infinite recursion
                return {"error": "Max depth reached"}
            
            try:
                element_dict = {
                    "role": getattr(element, 'AXRole', 'Unknown'),
                    "title": getattr(element, 'AXTitle', ''),
                    "description": getattr(element, 'AXDescription', ''),
                    "identifier": getattr(element, 'AXIdentifier', ''),
                    "value": getattr(element, 'AXValue', ''),
                    "enabled": getattr(element, 'AXEnabled', True),
                    "focused": getattr(element, 'AXFocused', False),
                }
                
                # Get position and size
                try:
                    position = element.AXPosition
                    size = element.AXSize
                    element_dict["position"] = {"x": position.x, "y": position.y}
                    element_dict["size"] = {"width": size.width, "height": size.height}
                except:
                    pass
                
                # Get actions
                try:
                    actions = element.getActions()
                    element_dict["actions"] = actions
                except:
                    element_dict["actions"] = []
                
                # Get children
                try:
                    children = element.findAll()
                    if children:
                        element_dict["children"] = [element_to_dict(child, depth + 1) for child in children]
                except:
                    element_dict["children"] = []
                
                return element_dict
                
            except Exception as e:
                return {"error": f"Error processing element: {e}"}
        
        result = element_to_dict(window)
        result["app_name"] = app_name
        result["window_title"] = getattr(window, 'AXTitle', 'Unknown')
        
        return result
        
    except Exception as e:
        return {"error": f"Error listing elements: {e}"}


def find_element(app_name: str, element_id: str) -> Optional[atomacos.NativeUIElement]:
    """
    Find a UI element by identifier, title, or description.
    
    Args:
        app_name: Name of the application
        element_id: Element identifier, title, or description
        
    Returns:
        Atom instance of the element or None if not found
    """
    try:
        app = get_app_by_name(app_name)
        if not app:
            return None
        
        window = get_front_window(app)
        if not window:
            return None
        
        # Try different search strategies
        search_strategies = [
            lambda: window.findFirstR(AXIdentifier=element_id),
            lambda: window.findFirstR(AXTitle=element_id),
            lambda: window.findFirstR(AXDescription=element_id),
            lambda: window.findFirstR(AXRole="AXButton", AXTitle=element_id),
            lambda: window.findFirstR(AXRole="AXTextField", AXTitle=element_id),
            lambda: window.findFirstR(AXRole="AXStaticText", AXTitle=element_id),
        ]
        
        for strategy in search_strategies:
            try:
                element = strategy()
                if element:
                    return element
            except:
                continue
        
        # Try searching in all windows if not found in front window
        try:
            all_windows = app.findAllR(AXRole="AXWindow")
            for win in all_windows:
                for strategy in search_strategies:
                    try:
                        element = strategy()
                        if element:
                            return element
                    except:
                        continue
        except:
            pass
        
        return None
        
    except Exception as e:
        print(f"Error finding element {element_id}: {e}")
        return None


def press_element(element: atomacos.NativeUIElement) -> bool:
    """
    Press (click) a UI element.
    
    Args:
        element: Atom instance of the element to press
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if element has Press action
        actions = element.getActions()
        if 'Press' in actions:
            element.Press()
            return True
        
        # Try clicking if Press is not available
        element.click()
        return True
        
    except Exception as e:
        print(f"Error pressing element: {e}")
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


def read_value(element: atomacos.NativeUIElement) -> str:
    """
    Read the value from a UI element.
    
    Args:
        element: Atom instance of the element
        
    Returns:
        Element value as string
    """
    try:
        # Try different value attributes
        value_attrs = ['AXValue', 'AXTitle', 'AXDescription']
        
        for attr in value_attrs:
            try:
                value = getattr(element, attr, None)
                if value:
                    return str(value)
            except:
                continue
        
        return ""
        
    except Exception as e:
        print(f"Error reading value: {e}")
        return ""


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


def scroll_window(app_name: str, direction: str, amount: int) -> bool:
    """
    Scroll the front window of an application.
    
    Args:
        app_name: Name of the application
        direction: "up", "down", "left", or "right"
        amount: Number of units to scroll
        
    Returns:
        True if successful, False otherwise
    """
    try:
        app = get_app_by_name(app_name)
        if not app:
            return False
        
        window = get_front_window(app)
        if not window:
            return False
        
        return scroll_element(window, direction, amount)
        
    except Exception as e:
        print(f"Error scrolling window: {e}")
        return False


def list_running_apps() -> Dict[str, Any]:
    """
    List all currently running applications that can be controlled.
    
    Returns:
        Dictionary containing list of running applications with their exact names
    """
    try:
        apps = []
        
        # Import applescript here to avoid circular imports
        from . import applescript
        
        # Use AppleScript to get running applications
        script = '''
        tell application "System Events"
            set appList to {}
            repeat with appProcess in (every process whose background only is false)
                try
                    set appName to name of appProcess
                    set end of appList to appName & return
                end try
            end repeat
            return appList as string
        end tell
        '''
        
        success, output = applescript.run_applescript(script)
        if success and output.strip():
            # Parse the output (newline-separated list)
            app_names = [name.strip() for name in output.split('\n') if name.strip()]
            
            # For each app, try to get more info via atomacos
            for app_name in app_names:
                try:
                    app = atomacos.getAppRefByLocalizedName(app_name)
                    if app:
                        # Try multiple methods to get bundle ID
                        bundle_id = ""
                        try:
                            bundle_id = getattr(app, 'bundleIdentifier', '')
                            if not bundle_id:
                                # Try alternative method
                                bundle_id = app.bundleIdentifier()
                        except:
                            try:
                                # Try direct attribute access
                                bundle_id = app.bundleIdentifier
                            except:
                                bundle_id = ""
                        
                        app_info = {
                            "name": app_name,
                            "bundle_id": bundle_id,
                            "localized_name": getattr(app, 'AXTitle', app_name),
                            "frontmost": getattr(app, 'AXFrontmost', False)
                        }
                        apps.append(app_info)
                    else:
                        # Fallback: just add the name if we can't get more info
                        apps.append({
                            "name": app_name,
                            "bundle_id": "",
                            "localized_name": app_name,
                            "frontmost": False
                        })
                except:
                    # Fallback: just add the name if we can't get more info
                    apps.append({
                        "name": app_name,
                        "bundle_id": "",
                        "localized_name": app_name,
                        "frontmost": False
                    })
        
        return {
            "success": True,
            "apps": apps,
            "count": len(apps)
        }
        
    except Exception as e:
        return {"error": f"Error listing running apps: {e}"}
