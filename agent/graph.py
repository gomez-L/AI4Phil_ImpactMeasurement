"""
LangGraph ReAct agent graph for impact measurement.

Architecture:
  START → agent_node ⟷ tools_node → END
              ↑ (standard ReAct loop via conditional edge)

Additional features:
  • MemorySaver checkpointer for multi-turn conversation memory
  • LangFuse callbacks injected via build_run_config()
  • Streaming support
  • Helper run() function for simple single-turn invocations
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

import config
from agent.prompts import SYSTEM_PROMPT
from observability import build_run_config
from tools import ALL_TOOLS

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# LLM
# ──────────────────────────────────────────────────────────────────────────────

def _build_llm() -> ChatGoogleGenerativeAI:
    if not config.GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Copy .env.example → .env and add your key."
        )
    return ChatGoogleGenerativeAI(
        model=config.MODEL_NAME,
        temperature=config.TEMPERATURE,
        google_api_key=config.GEMINI_API_KEY,
        streaming=True,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Agent graph (singleton)
# ──────────────────────────────────────────────────────────────────────────────

_agent = None


def get_agent():
    """
    Build (or return cached) the LangGraph ReAct agent.

    The agent uses:
            - ChatGoogleGenerativeAI as the LLM backbone
      - ALL_TOOLS (7 domain tools)
      - MemorySaver for cross-turn memory (keyed by thread_id)
            - SYSTEM_PROMPT as the agent prompt
    """
    global _agent
    if _agent is not None:
        return _agent

    llm = _build_llm()
    memory = MemorySaver()

    _agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,
    )

    logger.info(
        "Impact Measurement Agent ready. Model: %s | Tools: %d | LangFuse: %s",
        config.MODEL_NAME,
        len(ALL_TOOLS),
        "enabled" if config.LANGFUSE_ENABLED else "disabled",
    )
    return _agent


# ──────────────────────────────────────────────────────────────────────────────
# Public helpers
# ──────────────────────────────────────────────────────────────────────────────

def run(
    query: str,
    thread_id: str = "default",
    session_name: str | None = None,
    verbose: bool = False,
) -> str:
    """
    Run a single-turn query and return the final text response.

    Args:
        query:        Natural-language question or instruction.
        thread_id:    Conversation thread ID (for MemorySaver continuity).
        session_name: Optional label shown in LangFuse traces.
        verbose:      If True, print intermediate tool calls to stdout.

    Returns:
        The agent's final text response as a string.
    """
    agent = get_agent()
    cfg = build_run_config(thread_id=thread_id, session_name=session_name)

    result = agent.invoke(
        {"messages": [("human", query)]},
        config=cfg,
    )

    # Extract final AI message
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.__class__.__name__ == "AIMessage":
            content = msg.content
            if isinstance(content, list):
                # Handle structured content (tool call + text)
                for block in content:
                    if isinstance(block, str):
                        return block
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block["text"]
            elif isinstance(content, str) and content.strip():
                return content

    return "No response generated."


def stream(
    query: str,
    thread_id: str = "default",
    session_name: str | None = None,
):
    """
    Stream the agent's response token by token.

    Yields strings (tokens or intermediate tool outputs if verbose).
    Usage:
        for chunk in stream("Analyse workshop ws_2026_001"):
            print(chunk, end="", flush=True)
    """
    agent = get_agent()
    cfg = build_run_config(thread_id=thread_id, session_name=session_name)

    for chunk in agent.stream(
        {"messages": [("human", query)]},
        config=cfg,
        stream_mode="values",
    ):
        messages = chunk.get("messages", [])
        if messages:
            last = messages[-1]
            if hasattr(last, "content") and last.__class__.__name__ == "AIMessage":
                content = last.content
                if isinstance(content, str):
                    yield content
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, str):
                            yield block
                        elif isinstance(block, dict) and block.get("type") == "text":
                            yield block["text"]


def get_graph_diagram() -> str:
    """Return a Mermaid diagram of the agent graph (for documentation)."""
    try:
        return get_agent().get_graph().draw_mermaid()
    except Exception:
        return (
            "graph TD\n"
            "  START --> agent\n"
            "  agent -->|tool call| tools\n"
            "  tools --> agent\n"
            "  agent -->|done| END\n"
        )
