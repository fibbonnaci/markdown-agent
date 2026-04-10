"""
@tool decorator — registers Python functions as Claude-compatible tools.

Usage:
    from backend.decorator import tool

    @tool
    def search_docs(query: str, top_k: int = 3):
        \"\"\"Search uploaded documents for relevant passages.

        Args:
            query: The search query string.
            top_k: Number of top results to return.
        \"\"\"
        ...
"""

import inspect
import re
from typing import Dict, List, Optional, Tuple

TOOL_REGISTRY: Dict[str, dict] = {}

_TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _python_type_to_json(annotation) -> str:
    """Map a Python type annotation to a JSON Schema type string."""
    if annotation is inspect.Parameter.empty:
        return "string"
    return _TYPE_MAP.get(annotation, "string")


def _parse_docstring(docstring: Optional[str]) -> Tuple[str, Dict[str, str]]:
    """Parse a Google-style docstring into description + param docs.

    Returns:
        (description, {param_name: param_description})
    """
    if not docstring:
        return "", {}

    lines = docstring.strip().splitlines()
    description_lines = []
    param_docs = {}
    in_args = False

    for line in lines:
        stripped = line.strip()

        if stripped.lower().startswith("args:"):
            in_args = True
            continue

        if in_args:
            # Check if this is a new section header (e.g., Returns:, Raises:)
            if stripped and not stripped.startswith("-") and stripped.endswith(":") and ":" not in stripped[:-1]:
                in_args = False
                continue
            # Parse "param_name: description" or "param_name (type): description"
            match = re.match(r"^\s*(\w+)(?:\s*\([^)]*\))?\s*:\s*(.+)", line)
            if match:
                param_docs[match.group(1)] = match.group(2).strip()
        else:
            if stripped:
                description_lines.append(stripped)

    description = " ".join(description_lines)
    return description, param_docs


def tool(func):
    """Decorator that registers a function as a Claude-compatible tool.

    - Extracts parameter names, types, and defaults from the signature
    - Uses the docstring for tool and parameter descriptions
    - Generates a Claude API tool schema
    - Stores everything in TOOL_REGISTRY
    - Returns the function unchanged
    """
    name = func.__name__
    sig = inspect.signature(func)
    description, param_docs = _parse_docstring(func.__doc__)

    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        json_type = _python_type_to_json(param.annotation)
        prop: dict = {"type": json_type}

        if param_name in param_docs:
            prop["description"] = param_docs[param_name]

        properties[param_name] = prop

        if param.default is inspect.Parameter.empty:
            required.append(param_name)

    schema = {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }

    TOOL_REGISTRY[name] = {
        "function": func,
        "schema": schema,
    }

    return func


if __name__ == "__main__":
    import json

    @tool
    def search_docs(query: str, top_k: int = 3):
        """Search uploaded documents for relevant passages.

        Args:
            query: The search query string.
            top_k: Number of top results to return.
        """
        return f"Results for: {query}"

    @tool
    def list_docs():
        """List all uploaded documents and their chunk counts."""
        return "No documents."

    print("=== TOOL_REGISTRY ===")
    for name, entry in TOOL_REGISTRY.items():
        print(f"\n{name}:")
        print(json.dumps(entry["schema"], indent=2))
