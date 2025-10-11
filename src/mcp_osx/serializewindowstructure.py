from typing import Any, Dict, List, Optional, Union

# If you use a type checker, you can import these:
# from atomacos.nativeui import NativeUIElement
# But we keep it untyped at runtime to avoid requiring stubs.

try:
    import atomacos
    from atomacos import errors as ax_errors
except Exception:  # pragma: no cover
    atomacos = None
    ax_errors = None


Number = Union[int, float]
PointLike = Union[Dict[str, Number], Any]  # NSPoint, dict, or tuple
SizeLike = Union[Dict[str, Number], Any]   # NSSize, dict, or tuple


def _coerce_point(obj: Optional[PointLike]) -> Optional[Dict[str, Number]]:
    if obj is None:
        return None
    # PyObjC NSPoint has attributes x, y
    if hasattr(obj, "x") and hasattr(obj, "y"):
        return {"x": float(getattr(obj, "x")), "y": float(getattr(obj, "y"))}
    # Some wrappers expose X, Y or dictionary-like
    if isinstance(obj, dict):
        if "x" in obj and "y" in obj:
            return {"x": float(obj["x"]), "y": float(obj["y"])}
        if "X" in obj and "Y" in obj:
            return {"x": float(obj["X"]), "y": float(obj["Y"])}
    # Tuple or list
    if isinstance(obj, (tuple, list)) and len(obj) >= 2:
        return {"x": float(obj[0]), "y": float(obj[1])}
    return None


def _coerce_size(obj: Optional[SizeLike]) -> Optional[Dict[str, Number]]:
    if obj is None:
        return None
    # PyObjC NSSize has attributes width, height
    if hasattr(obj, "width") and hasattr(obj, "height"):
        return {"width": float(getattr(obj, "width")), "height": float(getattr(obj, "height"))}
    # Some wrappers expose W, H or dictionary-like
    if isinstance(obj, dict):
        if "width" in obj and "height" in obj:
            return {"width": float(obj["width"]), "height": float(obj["height"])}
        if "W" in obj and "H" in obj:
            return {"width": float(obj["W"]), "height": float(obj["H"])}
    # Tuple or list
    if isinstance(obj, (tuple, list)) and len(obj) >= 2:
        return {"width": float(obj[0]), "height": float(obj[1])}
    return None


def _safe_getattr(elem: Any, attr: str) -> Any:
    try:
        return getattr(elem, attr)
    except Exception:
        return None


def _safe_actions(elem: Any) -> List[str]:
    try:
        acts = elem.getActions()
        if isinstance(acts, list):
            return [str(a) for a in acts]
        # Some bindings return an NSArray proxy
        return [str(a) for a in list(acts)]
    except Exception:
        return []


def _visible_hint(elem: Any) -> Optional[bool]:
    # AXHidden is more widely present; AXVisible exists on some roles
    v = _safe_getattr(elem, "AXVisible")
    if isinstance(v, bool):
        return v
    hidden = _safe_getattr(elem, "AXHidden")
    if isinstance(hidden, bool):
        return not hidden
    # As a last resort infer from size
    size = _coerce_size(_safe_getattr(elem, "AXSize"))
    if size and (size["width"] <= 0 or size["height"] <= 0):
        return False
    return None


def _name_for(elem: Any, role: Optional[str]) -> Optional[str]:
    # Prefer explicit accessibility name fields, then role-specific fallbacks
    for ax_attr in ("AXTitle", "AXLabel", "AXPlaceholderValue"):
        v = _safe_getattr(elem, ax_attr)
        if isinstance(v, str) and v.strip():
            return v
    # Text values for text-like roles
    if role in {"AXStaticText", "AXTextField", "AXTextArea", "AXMenuItem", "AXPopUpButton"}:
        v = _safe_getattr(elem, "AXValue")
        if isinstance(v, str) and v.strip():
            return v
    # Buttons often keep title in AXValue when AXTitle is empty
    if role in {"AXButton", "AXRadioButton", "AXCheckBox"}:
        v = _safe_getattr(elem, "AXValue")
        if isinstance(v, str) and v.strip():
            return v
    return None


def _value_for(elem: Any, role: Optional[str]) -> Optional[Union[str, Number, bool]]:
    # Expose useful state values without duplicating the "name"
    v = _safe_getattr(elem, "AXValue")
    if v is None:
        return None
    # Avoid echoing name for static text
    if role in {"AXStaticText"} and isinstance(v, str):
        return None
    # Sliders, progress indicators, checkboxes
    if isinstance(v, (int, float, bool, str)):
        return v
    # Catch-all representation
    try:
        return str(v)
    except Exception:
        return None


def _bool(attr_val: Any) -> Optional[bool]:
    return bool(attr_val) if isinstance(attr_val, bool) else None


def get_window_structure(window_element: Any) -> Dict[str, Any]:
    """
    Return a JSON-serializable dict describing the full accessibility tree of a macOS window.

    The output includes, for each node:
      id                Stable identifier. Uses AXIdentifier when present, else a path-based id.
      path              Canonical path of child indexes from the root, like "0/2/5".
      role              AXRole (e.g. AXButton).
      role_description  AXRoleDescription if available.
      name              Human readable label or text.
      description       AXDescription when available.
      help              AXHelp tooltip when available.
      enabled           AXEnabled if available.
      focused           AXFocused if available.
      selected          AXSelected if available.
      visible           Derived from AXVisible or AXHidden or size.
      position          {"x": float, "y": float} from AXPosition.
      size              {"width": float, "height": float} from AXSize.
      actions           List of supported action names.
      children          List of child nodes, recursively.
    """
    if atomacos is None:
        raise RuntimeError("atomacos is not available. Install and run on macOS with accessibility permissions.")

    ax_err = ax_errors or object()

    def serialize(elem: Any, path: List[int]) -> Dict[str, Any]:
        role = _safe_getattr(elem, "AXRole")
        node: Dict[str, Any] = {}
        # Path and id
        path_str = "/".join(str(i) for i in path)
        ax_identifier = _safe_getattr(elem, "AXIdentifier")
        # Primary id prefers AXIdentifier when present and non-empty
        if isinstance(ax_identifier, str) and ax_identifier.strip():
            node_id = ax_identifier.strip()
        else:
            # Construct a readable id including role and index, e.g. "AXButton[5]@0/2/5"
            leaf = f"{role or 'AXUnknown'}[{path[-1] if path else 0}]"
            node_id = f"{leaf}@{path_str}"

        # Core properties
        node["id"] = node_id
        node["path"] = path_str
        node["role"] = role
        node["role_description"] = _safe_getattr(elem, "AXRoleDescription")
        node["name"] = _name_for(elem, role)
        node["description"] = _safe_getattr(elem, "AXDescription")
        node["help"] = _safe_getattr(elem, "AXHelp")
        node["enabled"] = _bool(_safe_getattr(elem, "AXEnabled"))
        node["focused"] = _bool(_safe_getattr(elem, "AXFocused"))
        node["selected"] = _bool(_safe_getattr(elem, "AXSelected"))
        node["visible"] = _visible_hint(elem)
        node["position"] = _coerce_point(_safe_getattr(elem, "AXPosition"))
        node["size"] = _coerce_size(_safe_getattr(elem, "AXSize"))
        node["actions"] = _safe_actions(elem)

        # Children
        children: List[Any] = []
        try:
            kids = _safe_getattr(elem, "AXChildren") or []
            # Some wrappers return ObjC arrays
            kids = list(kids)
            children = kids
        except Exception:
            children = []

        node_children: List[Dict[str, Any]] = []
        for idx, child in enumerate(children):
            try:
                node_children.append(serialize(child, path + [idx]))
            except Exception as e:
                # Include a stub so the consumer can see there was a node we could not serialize
                node_children.append({
                    "id": f"AXUnknown[{idx}]@{path_str}/{idx}",
                    "path": f"{path_str}/{idx}",
                    "role": None,
                    "error": f"child_serialization_failed: {type(e).__name__}"
                })

        node["children"] = node_children
        return node

    # Root path starts at 0 to make selectors predictable
    return serialize(window_element, [0])
