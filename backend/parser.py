"""
Parser for agent.md files.

Reads a markdown file and extracts structured agent configuration:
  - H1 heading -> agent name
  - ## Purpose -> purpose text
  - ## Tools -> list of tool references
  - ## Behavior -> behavior text
  - ## Guardrails -> guardrails text
  - ## Model -> model identifier
"""

import re
from dataclasses import dataclass, field
from typing import List

DEFAULT_MODEL = "claude-sonnet-4-20250514"


@dataclass
class ToolRef:
    name: str
    description: str = ""


@dataclass
class AgentConfig:
    name: str = "Unnamed Agent"
    purpose: str = ""
    tools: List[ToolRef] = field(default_factory=list)
    behavior: str = ""
    guardrails: str = ""
    model: str = DEFAULT_MODEL


def parse_agent_md(path: str) -> AgentConfig:
    """Parse an agent.md file into an AgentConfig."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    config = AgentConfig()

    # Extract H1 heading as agent name
    h1_match = re.match(r"^#\s+(.+)", content, re.MULTILINE)
    if h1_match:
        config.name = h1_match.group(1).strip()

    # Split into ## sections
    sections = re.split(r"^## ", content, flags=re.MULTILINE)

    for section in sections[1:]:  # skip content before first ##
        lines = section.strip().splitlines()
        if not lines:
            continue

        heading = lines[0].strip().lower()
        body = "\n".join(lines[1:]).strip()

        if heading == "purpose":
            config.purpose = body
        elif heading == "tools":
            config.tools = _parse_tools(body)
        elif heading == "behavior":
            config.behavior = body
        elif heading == "guardrails":
            config.guardrails = body
        elif heading == "model":
            model_line = body.strip().splitlines()[0].strip() if body.strip() else ""
            if model_line:
                config.model = model_line

    return config


def _parse_tools(body: str) -> List[ToolRef]:
    """Parse bullet lines into ToolRef list.

    Accepts lines like:
      - search_docs: Search uploaded documents
      - list_docs
    """
    tools = []
    for line in body.splitlines():
        match = re.match(r"^\s*-\s+(\w+)(?:\s*:\s*(.*))?$", line)
        if match:
            name = match.group(1)
            desc = (match.group(2) or "").strip()
            tools.append(ToolRef(name=name, description=desc))
    return tools


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "agent.md"
    config = parse_agent_md(path)
    print(f"Name:       {config.name}")
    print(f"Model:      {config.model}")
    print(f"Purpose:    {config.purpose[:80]}...")
    print(f"Behavior:   {config.behavior[:80]}...")
    print(f"Guardrails: {config.guardrails[:80]}...")
    print(f"Tools:      {[(t.name, t.description) for t in config.tools]}")
