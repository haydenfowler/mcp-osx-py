"""
AppleScript Layer for macOS GUI Control

Provides functions to execute AppleScript commands via osascript subprocess calls.
This is the first tier in our three-layer automation strategy.
"""

import subprocess
import json
from typing import Tuple, Dict, Any


def run_applescript(script: str) -> Tuple[bool, str]:
    """
    Execute an AppleScript via osascript subprocess.
    
    Args:
        script: The AppleScript code to execute
        
    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown AppleScript error"
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, "AppleScript execution timed out"
    except Exception as e:
        return False, f"AppleScript execution failed: {str(e)}"


def is_app_scriptable(app: str) -> bool:
    """
    Test if an application responds to basic AppleScript commands.
    
    Args:
        app: Application name to test
        
    Returns:
        True if the app is scriptable, False otherwise
    """
    test_script = f'''
    tell application "{app}"
        return name
    end tell
    '''
    
    success, _ = run_applescript(test_script)
    return success


def get_app_info(app: str) -> Dict[str, Any]:
    """
    Get basic information about an application via AppleScript.
    
    Args:
        app: Application name
        
    Returns:
        Dictionary with app information or error details
    """
    script = f'''
    tell application "{app}"
        try
            return {{name:name, frontmost:frontmost, version:version}}
        on error
            return {{error:"Cannot get app info"}}
        end try
    end tell
    '''
    
    success, output = run_applescript(script)
    if success:
        try:
            # Try to parse as JSON-like structure
            return {"success": True, "info": output}
        except:
            return {"success": True, "info": output}
    else:
        return {"success": False, "error": output}


def click_button(app: str, button_name: str) -> bool:
    """
    Try to click a button in an application via AppleScript.
    
    Args:
        app: Application name
        button_name: Name or identifier of the button
        
    Returns:
        True if successful, False otherwise
    """
    script = f'''
    tell application "{app}"
        try
            click button "{button_name}" of front window
            return "success"
        on error
            try
                click button "{button_name}"
                return "success"
            on error
                return "error"
            end try
        end try
    end tell
    '''
    
    success, output = run_applescript(script)
    return success and "success" in output


def set_text_field(app: str, field_name: str, text: str) -> bool:
    """
    Try to set text in a text field via AppleScript.
    
    Args:
        app: Application name
        field_name: Name or identifier of the text field
        text: Text to enter
        
    Returns:
        True if successful, False otherwise
    """
    script = f'''
    tell application "{app}"
        try
            set value of text field "{field_name}" of front window to "{text}"
            return "success"
        on error
            try
                set value of text field "{field_name}" to "{text}"
                return "success"
            on error
                return "error"
            end try
        end try
    end tell
    '''
    
    success, output = run_applescript(script)
    return success and "success" in output


def get_text_field_value(app: str, field_name: str) -> Tuple[bool, str]:
    """
    Try to get text from a text field via AppleScript.
    
    Args:
        app: Application name
        field_name: Name or identifier of the text field
        
    Returns:
        Tuple of (success: bool, value: str)
    """
    script = f'''
    tell application "{app}"
        try
            return value of text field "{field_name}" of front window
        on error
            try
                return value of text field "{field_name}"
            on error
                return "error"
            end try
        end try
    end tell
    '''
    
    success, output = run_applescript(script)
    if success and output != "error":
        return True, output
    else:
        return False, output if not success else "Field not found"


def press_element(app: str, element_id: str) -> bool:
    """
    Generic function to try pressing an element via AppleScript.
    Attempts different AppleScript patterns based on element type.
    
    Args:
        app: Application name
        element_id: Element identifier or name
        
    Returns:
        True if successful, False otherwise
    """
    # Try button first (most common)
    if click_button(app, element_id):
        return True
    
    # Try menu item
    script = f'''
    tell application "{app}"
        try
            click menu item "{element_id}"
            return "success"
        on error
            return "error"
        end try
    end tell
    '''
    
    success, output = run_applescript(script)
    if success and "success" in output:
        return True
    
    # Try generic click
    script = f'''
    tell application "System Events"
        try
            click UI element "{element_id}" of application process "{app}"
            return "success"
        on error
            return "error"
        end try
    end tell
    '''
    
    success, output = run_applescript(script)
    return success and "success" in output


def enter_text(app: str, element_id: str, text: str) -> bool:
    """
    Generic function to enter text via AppleScript.
    
    Args:
        app: Application name
        element_id: Element identifier or name
        text: Text to enter
        
    Returns:
        True if successful, False otherwise
    """
    # Try text field first
    if set_text_field(app, element_id, text):
        return True
    
    # Try generic text entry via System Events
    script = f'''
    tell application "System Events"
        try
            set focused of text field "{element_id}" of application process "{app}" to true
            set value of text field "{element_id}" of application process "{app}" to "{text}"
            return "success"
        on error
            return "error"
        end try
    end tell
    '''
    
    success, output = run_applescript(script)
    return success and "success" in output


def read_value(app: str, element_id: str) -> Tuple[bool, str]:
    """
    Generic function to read a value via AppleScript.
    
    Args:
        app: Application name
        element_id: Element identifier or name
        
    Returns:
        Tuple of (success: bool, value: str)
    """
    # Try text field first
    success, value = get_text_field_value(app, element_id)
    if success:
        return True, value
    
    # Try generic value reading via System Events
    script = f'''
    tell application "System Events"
        try
            return value of UI element "{element_id}" of application process "{app}"
        on error
            return "error"
        end try
    end tell
    '''
    
    success, output = run_applescript(script)
    if success and output != "error":
        return True, output
    else:
        return False, output if not success else "Element not found"
