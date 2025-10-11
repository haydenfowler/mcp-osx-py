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
