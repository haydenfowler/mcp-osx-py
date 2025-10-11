from time import sleep
import atomacos

def find_element_by_id(root_window, element_id):
    import re

    if not element_id:
        return None

    # Case 1: direct AXIdentifier search
    if "@" not in element_id and "/" not in element_id and element_id.isidentifier():
        try:
            el = root_window.findFirstR(AXIdentifier=element_id)
            if el:
                return el
        except Exception:
            pass

    # Case 2: path-based ID (e.g. AXButton[2]@0/1/3 or 0/1/3)
    match = re.search(r"@([\d/]+)$", element_id)
    if match:
        path_str = match.group(1)
    else:
        path_str = element_id  # might already just be a path

    try:
        indices = [int(x) for x in path_str.strip("/").split("/") if x.strip() != ""]
    except Exception:
        raise ValueError(f"Invalid element_id path format: {element_id!r}")

    elem = root_window
    for i in indices[1:]:  # skip the first (root) index
        try:
            children = getattr(elem, "AXChildren", None)
            if not children or i >= len(children):
                return None
            elem = children[i]
        except Exception:
            return None

    return elem

def perform_element_action(app: atomacos.NativeUIElement,window: atomacos.NativeUIElement, element_id: str, action: str, value: str | None = None) -> bool:
    """
    Generic interaction helper.
    Executes the given action on the specified element_id (as returned by get_window_structure_abstract()).
    """
    try:
        # Parse path id like "0/1/3"
        indices = [int(x) for x in element_id.strip("/").split("/") if x.strip() != ""]
        elem = window

        for i in indices[1:]:
            children = getattr(elem, "AXChildren", None) or []
            if i >= len(children):
                return False
            elem = children[i]

        # Normalize action
        action = action.lower()

        # Text entry
        if action in ("type", "input", "setvalue"):
            if value is None:
                return False
            elem.setString("AXValue", value)
            elemActions = elem.getActions()
            if "Confirm" in elemActions:
                getattr(elem, "Confirm")()
                sleep(0.1)
                elem.sendGlobalKey("return")
                elem.sendGlobalKey("return")
            return True

        # Scroll actions
        if action in ("scrollup", "scrolldown", "scrollleft", "scrollright"):
            ax_action = {
                "scrollup": "ScrollUpByPage",
                "scrolldown": "ScrollDownByPage",
                "scrollleft": "ScrollLeftByPage",
                "scrollright": "ScrollRightByPage",
            }[action]
            try:
                getattr(elem, ax_action)()
                return True
            except Exception:
                return False

        # Press / click / open / menu actions
        for candidate in ("Press", "Open", "ShowMenu", "Raise", "PerformClick"):
            try:
                actions = elem.getActions()
                if candidate in actions:
                    getattr(elem, candidate)()
                    return True
            except Exception as e:
                # Ignore benign macOS accessibility errors like -25205
                if "-25205" in str(e):
                    return True

        # As a fallback, climb parents if the target itself isn't actionable
        parent = getattr(elem, "AXParent", None)
        while parent:
            try:
                actions = parent.getActions()
            except Exception:
                actions = []
            for candidate in ("Press", "Open", "ShowMenu", "Raise", "PerformClick"):
                if candidate in actions:
                    try:
                        getattr(parent, candidate)()
                        return True
                    except Exception as e:
                        if "-25205" in str(e):
                            return True
            parent = getattr(parent, "AXParent", None)

        return False

    except Exception:
        return False
