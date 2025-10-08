"""
PyAutoGUI Fallback Layer for macOS GUI Control

Provides functions to simulate mouse clicks, keyboard input, and scrolling using PyAutoGUI.
This is the third and final tier in our three-layer automation strategy, used when
AppleScript and Accessibility API methods fail.
"""

import pyautogui
import time
from typing import Tuple


# Configure PyAutoGUI
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions


def click_at(x: int, y: int) -> bool:
    """
    Move mouse to coordinates and click.
    
    Args:
        x: X coordinate
        y: Y coordinate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)  # Brief pause for movement
        pyautogui.click()
        return True
    except Exception as e:
        print(f"Error clicking at ({x}, {y}): {e}")
        return False


def double_click_at(x: int, y: int) -> bool:
    """
    Move mouse to coordinates and double-click.
    
    Args:
        x: X coordinate
        y: Y coordinate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
        pyautogui.doubleClick()
        return True
    except Exception as e:
        print(f"Error double-clicking at ({x}, {y}): {e}")
        return False


def right_click_at(x: int, y: int) -> bool:
    """
    Move mouse to coordinates and right-click.
    
    Args:
        x: X coordinate
        y: Y coordinate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
        pyautogui.rightClick()
        return True
    except Exception as e:
        print(f"Error right-clicking at ({x}, {y}): {e}")
        return False


def type_text(text: str, interval: float = 0.05) -> bool:
    """
    Type text using PyAutoGUI.
    
    Args:
        text: Text to type
        interval: Delay between keystrokes
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.write(text, interval=interval)
        return True
    except Exception as e:
        print(f"Error typing text: {e}")
        return False


def press_key(key: str) -> bool:
    """
    Press a single key.
    
    Args:
        key: Key name (e.g., 'enter', 'space', 'tab', 'cmd', etc.)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.press(key)
        return True
    except Exception as e:
        print(f"Error pressing key '{key}': {e}")
        return False


def key_combination(*keys) -> bool:
    """
    Press a key combination (e.g., hotkey).
    
    Args:
        *keys: Keys to press simultaneously
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.hotkey(*keys)
        return True
    except Exception as e:
        print(f"Error pressing key combination {keys}: {e}")
        return False


def scroll(amount: int) -> bool:
    """
    Scroll the mouse wheel.
    
    Args:
        amount: Positive for up, negative for down
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.scroll(amount)
        return True
    except Exception as e:
        print(f"Error scrolling {amount}: {e}")
        return False


def scroll_at(x: int, y: int, amount: int) -> bool:
    """
    Move mouse to coordinates and scroll.
    
    Args:
        x: X coordinate
        y: Y coordinate
        amount: Positive for up, negative for down
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
        pyautogui.scroll(amount)
        return True
    except Exception as e:
        print(f"Error scrolling at ({x}, {y}) with amount {amount}: {e}")
        return False


def hscroll(amount: int) -> bool:
    """
    Horizontal scroll.
    
    Args:
        amount: Positive for right, negative for left
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.hscroll(amount)
        return True
    except Exception as e:
        print(f"Error horizontal scrolling {amount}: {e}")
        return False


def hscroll_at(x: int, y: int, amount: int) -> bool:
    """
    Move mouse to coordinates and horizontal scroll.
    
    Args:
        x: X coordinate
        y: Y coordinate
        amount: Positive for right, negative for left
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.moveTo(x, y, duration=0.2)
        time.sleep(0.1)
        pyautogui.hscroll(amount)
        return True
    except Exception as e:
        print(f"Error horizontal scrolling at ({x}, {y}) with amount {amount}: {e}")
        return False


def drag_to(x1: int, y1: int, x2: int, y2: int, duration: float = 0.5) -> bool:
    """
    Drag from one point to another.
    
    Args:
        x1: Starting X coordinate
        y1: Starting Y coordinate
        x2: Ending X coordinate
        y2: Ending Y coordinate
        duration: Duration of the drag in seconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.drag(x2 - x1, y2 - y1, duration=duration, button='left')
        return True
    except Exception as e:
        print(f"Error dragging from ({x1}, {y1}) to ({x2}, {y2}): {e}")
        return False


def get_screen_size() -> Tuple[int, int]:
    """
    Get the screen size.
    
    Returns:
        Tuple of (width, height)
    """
    try:
        return pyautogui.size()
    except Exception as e:
        print(f"Error getting screen size: {e}")
        return (1920, 1080)  # Default fallback


def get_mouse_position() -> Tuple[int, int]:
    """
    Get current mouse position.
    
    Returns:
        Tuple of (x, y)
    """
    try:
        return pyautogui.position()
    except Exception as e:
        print(f"Error getting mouse position: {e}")
        return (0, 0)


def move_mouse_to(x: int, y: int, duration: float = 0.2) -> bool:
    """
    Move mouse to coordinates.
    
    Args:
        x: X coordinate
        y: Y coordinate
        duration: Duration of movement in seconds
        
    Returns:
        True if successful, False otherwise
    """
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return True
    except Exception as e:
        print(f"Error moving mouse to ({x}, {y}): {e}")
        return False


def take_screenshot(filename: str = None) -> str:
    """
    Take a screenshot.
    
    Args:
        filename: Optional filename to save screenshot
        
    Returns:
        Path to screenshot file or error message
    """
    try:
        if filename:
            screenshot = pyautogui.screenshot(filename)
            return filename
        else:
            screenshot = pyautogui.screenshot()
            return str(screenshot)
    except Exception as e:
        return f"Error taking screenshot: {e}"


def locate_on_screen(image_path: str) -> Tuple[int, int, int, int]:
    """
    Locate an image on the screen.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Tuple of (left, top, width, height) or None if not found
    """
    try:
        location = pyautogui.locateOnScreen(image_path)
        if location:
            return (location.left, location.top, location.width, location.height)
        return None
    except Exception as e:
        print(f"Error locating image {image_path}: {e}")
        return None


def click_image(image_path: str) -> bool:
    """
    Find and click an image on the screen.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        location = pyautogui.locateOnScreen(image_path)
        if location:
            center = pyautogui.center(location)
            pyautogui.click(center)
            return True
        return False
    except Exception as e:
        print(f"Error clicking image {image_path}: {e}")
        return False


def wait_for_image(image_path: str, timeout: int = 10) -> bool:
    """
    Wait for an image to appear on screen.
    
    Args:
        image_path: Path to the image file
        timeout: Timeout in seconds
        
    Returns:
        True if image found, False if timeout
    """
    try:
        location = pyautogui.locateOnScreen(image_path, timeout=timeout)
        return location is not None
    except Exception as e:
        print(f"Error waiting for image {image_path}: {e}")
        return False
