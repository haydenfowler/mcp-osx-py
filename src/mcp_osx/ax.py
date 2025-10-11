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
import json
import psutil
import plistlib
import os


def check_ax_permissions() -> bool:
    """
    Check if the current process has Accessibility permissions.
    
    Returns:
        True if permissions are granted, False otherwise
    """
    return AXIsProcessTrusted()


def get_app_reference(bundle_id: str = None, app_name: str = None) -> Optional[atomacos.NativeUIElement]:
    """
    Get an atomacos Atom instance for the specified application.
    
    Args:
        bundle_id: Bundle ID of the application (e.g., "com.apple.finder")
        app_name: Name of the application (e.g., "Finder", "TextEdit")
        
    Returns:
        Atom instance or None if not found
    """
    try:
        # Prioritize bundle_id if provided
        if bundle_id:
            app = atomacos.getAppRefByBundleId(bundle_id)
            if app:
                return app
        
        # Fallback to app_name if bundle_id fails or is not provided
        if app_name:
            name_variations = [
                app_name,
                app_name + ".app",
                app_name.lower(),
                app_name.upper(),
                app_name.title(),
                app_name.replace(" ", ""),
                app_name.replace(" ", "").lower()
            ]
            
            for variation in name_variations:
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
        print(f"Error getting app reference for bundle_id='{bundle_id}' or app_name='{app_name}': {e}")
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


def list_elements(bundle_id: str = None, app_name: str = None) -> Dict[str, Any]:
    """
    List all UI elements in the specified app window.
    
    Args:
        bundle_id: Bundle ID of the application
        app_name: Name of the application
        
    Returns:
        Dictionary containing the UI element hierarchy
    """
    try:
        app = get_app_reference(bundle_id, app_name)
        if not app:
            return {"error": f"Application with bundle_id='{bundle_id}' or app_name='{app_name}' not found"}
        
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


def find_element(bundle_id: str = None, app_name: str = None, element_id: str = None) -> Optional[atomacos.NativeUIElement]:
    """
    Find a UI element by identifier, title, or description.
    
    Args:
        bundle_id: Bundle ID of the application
        app_name: Name of the application
        element_id: Element identifier, title, or description
        
    Returns:
        Atom instance of the element or None if not found
    """
    try:
        app = get_app_reference(bundle_id, app_name)
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


def scroll_window(bundle_id: str = None, app_name: str = None, direction: str = None, amount: int = 3) -> bool:
    """
    Scroll the front window of an application.
    
    Args:
        bundle_id: Bundle ID of the application
        app_name: Name of the application
        direction: "up", "down", "left", or "right"
        amount: Number of units to scroll
        
    Returns:
        True if successful, False otherwise
    """
    try:
        app = get_app_reference(bundle_id, app_name)
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
        for p in psutil.process_iter(['pid', 'name', 'exe']):
            if p.info['exe'] and ".app/Contents/MacOS" in p.info['exe']:
                try:
                    info_plist_path = os.path.join(p.info['exe'].split(".app/")[0] + ".app", "Contents", "Info.plist")
                    with open(info_plist_path, 'rb') as f:
                        plist = plistlib.load(f)
                        bundle_id = plist.get('CFBundleIdentifier')
                        name = plist.get('CFBundleName') or p.info['name']

                    apps.append({
                        "name": name,
                        "bundle_id": bundle_id,
                        "pid": p.info['pid'],
                    })
                except (FileNotFoundError, ValueError, KeyError):
                    # Fallback for apps with missing or malformed plists
                    apps.append({
                        "name": p.info['name'],
                        "bundle_id": None,
                        "pid": p.info['pid'],
                    })

        return {
            "success": True,
            "apps": apps,
            "count": len(apps)
        }
        
    except Exception as e:
        return {"error": f"Error listing running apps: {e}"}
