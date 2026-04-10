"""
AgentRuntime — loads an agent.md + tools.py and runs the Claude agentic loop.
"""

import asyncio
import importlib
import importlib.util
import json
import os
import sys
from typing import AsyncGenerator, Dict, List, Optional

from backend.parser import parse_agent_md, AgentConfig
from backend.decorator import TOOL_REGISTRY


class AgentRuntime:
    def __init__(self, agent_md_path: str, tools_py_path: str):
        self.agent_md_path = agent_md_path
        self.tools_py_path = tools_py_path

        # Parse agent definition
        self.config: AgentConfig = parse_agent_md(agent_md_path)

        # Clear and reload tools
        TOOL_REGISTRY.clear()
        self._load_tools(tools_py_path)

        # Filter registry to only tools listed in agent.md
        agent_tool_names = {t.name for t in self.config.tools}
        self.tools: Dict[str, dict] = {
            name: entry
            for name, entry in TOOL_REGISTRY.items()
            if name in agent_tool_names
        }

        # Compute warnings for missing tool implementations
        self.warnings: List[str] = []
        for tool_ref in self.config.tools:
            if tool_ref.name not in TOOL_REGISTRY:
                msg = f"Tool '{tool_ref.name}' listed in agent.md has no implementation. It will be skipped."
                self.warnings.append(msg)

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

        # Initialize Anthropic client
        import anthropic
        self.client = anthropic.AsyncAnthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        )

    def _load_tools(self, tools_py_path: str):
        """Dynamically import tools.py to trigger @tool decorators."""
        abs_path = os.path.abspath(tools_py_path)
        module_name = "backend.tools"

        # If already loaded, reload it
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            spec = importlib.util.spec_from_file_location(module_name, abs_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

    def _build_system_prompt(self) -> str:
        parts = []
        if self.config.purpose:
            parts.append(self.config.purpose)
        if self.config.behavior:
            parts.append(f"## Behavior\n{self.config.behavior}")
        if self.config.guardrails:
            parts.append(f"## Guardrails\n{self.config.guardrails}")
        return "\n\n".join(parts)

    def get_tools_schema(self) -> List[dict]:
        """Return Claude-compatible tool schemas for active tools."""
        return [entry["schema"] for entry in self.tools.values()]

    async def chat_stream(self, messages: List[dict]) -> AsyncGenerator[dict, None]:
        """Run the full agentic tool-use loop, yielding events."""
        tools_schema = self.get_tools_schema()

        while True:
            # Call Claude
            kwargs = {
                "model": self.config.model,
                "max_tokens": 4096,
                "system": self.system_prompt,
                "messages": messages,
            }
            if tools_schema:
                kwargs["tools"] = tools_schema

            response = await self.client.messages.create(**kwargs)

            # Check for tool use
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            if response.stop_reason == "tool_use" and tool_use_blocks:
                # Add assistant response to messages
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for tool_block in tool_use_blocks:
                    tool_name = tool_block.name
                    tool_input = tool_block.input

                    yield {
                        "type": "tool_start",
                        "tool": tool_name,
                        "input": tool_input,
                    }

                    # Execute the tool
                    if tool_name in self.tools:
                        func = self.tools[tool_name]["function"]
                        try:
                            result = await asyncio.to_thread(func, **tool_input)
                            result_str = str(result)
                        except Exception as e:
                            result_str = f"Error executing {tool_name}: {str(e)}"
                    else:
                        result_str = f"Tool '{tool_name}' is not available."

                    yield {
                        "type": "tool_end",
                        "tool": tool_name,
                        "result": result_str[:200],
                    }

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": result_str,
                    })

                # Add tool results to messages
                messages.append({"role": "user", "content": tool_results})

                # Loop back to call Claude again with the tool results
                continue

            else:
                # End turn — extract and stream text
                for block in response.content:
                    if hasattr(block, "text"):
                        # Yield text in small chunks to simulate streaming
                        text = block.text
                        chunk_size = 4
                        for i in range(0, len(text), chunk_size):
                            yield {
                                "type": "text",
                                "content": text[i:i + chunk_size],
                            }

                yield {"type": "done"}
                return

    def get_info(self) -> dict:
        """Return agent info for the /health and /agent endpoints."""
        return {
            "name": self.config.name,
            "purpose": self.config.purpose,
            "behavior": self.config.behavior,
            "guardrails": self.config.guardrails,
            "model": self.config.model,
            "tools": [{"name": t.name, "description": t.description} for t in self.config.tools],
            "active_tools": list(self.tools.keys()),
            "warnings": self.warnings,
        }
