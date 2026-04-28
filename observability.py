"""
LangFuse observability setup.

Provides:
  - get_langfuse_handler()  → LangChain CallbackHandler (or None if not configured)
  - get_langfuse_client()   → Raw Langfuse client for custom spans/scores
  - observe decorator       → re-exported for use in tools / agent nodes
  - build_run_config()      → Helper that merges LangFuse callback into a LangChain config dict
"""
from __future__ import annotations

import logging
from typing import Any

import config

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# LangChain callback handler
# ──────────────────────────────────────────────────────────────────────────────

def get_langfuse_handler():
    """
    Returns a LangFuse CallbackHandler if credentials are configured,
    otherwise returns None (observability silently disabled).
    """
    if not config.LANGFUSE_ENABLED:
        logger.info("LangFuse not configured — observability disabled.")
        return None
    try:
        from langfuse.callback import CallbackHandler
        handler = CallbackHandler(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            host=config.LANGFUSE_HOST,
        )
        logger.info("LangFuse callback handler initialised (host: %s).", config.LANGFUSE_HOST)
        return handler
    except Exception as exc:
        logger.warning("Failed to initialise LangFuse handler: %s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Raw Langfuse client (for custom traces, spans, scores)
# ──────────────────────────────────────────────────────────────────────────────

def get_langfuse_client():
    """
    Returns the raw Langfuse client for posting custom scores,
    creating named traces, or flushing at shutdown.
    Returns None if LangFuse is not configured.
    """
    if not config.LANGFUSE_ENABLED:
        return None
    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=config.LANGFUSE_PUBLIC_KEY,
            secret_key=config.LANGFUSE_SECRET_KEY,
            host=config.LANGFUSE_HOST,
        )
    except Exception as exc:
        logger.warning("Failed to create Langfuse client: %s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# observe decorator — wraps any function with a LangFuse span
# ──────────────────────────────────────────────────────────────────────────────

def observe(name: str | None = None):
    """
    Decorator that wraps a function in a LangFuse observation span.
    Falls back to a no-op if LangFuse is not configured.

    Usage:
        @observe(name="analyze_knowledge_impact")
        def my_tool_function(...): ...
    """
    def decorator(fn):
        if not config.LANGFUSE_ENABLED:
            return fn
        try:
            from langfuse.decorators import observe as lf_observe
            return lf_observe(name=name or fn.__name__)(fn)
        except Exception:
            return fn
    return decorator


# ──────────────────────────────────────────────────────────────────────────────
# LangChain run config builder
# ──────────────────────────────────────────────────────────────────────────────

def build_run_config(
    thread_id: str = "default",
    session_name: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Builds a LangChain/LangGraph config dict that includes:
      - the LangFuse callback handler
      - a thread id for MemorySaver
      - optional extra metadata

    Usage:
        result = agent.invoke({"messages": [...]}, config=build_run_config("session_123"))
    """
    cfg: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    if session_name:
        cfg["configurable"]["session_name"] = session_name

    handler = get_langfuse_handler()
    if handler:
        cfg["callbacks"] = [handler]

    if extra:
        cfg.update(extra)

    return cfg


# ──────────────────────────────────────────────────────────────────────────────
# Score helper (post-session quality score)
# ──────────────────────────────────────────────────────────────────────────────

def post_score(trace_id: str, name: str, value: float, comment: str = "") -> None:
    """
    Post a numeric quality score to a LangFuse trace.
    Silently skips if LangFuse is not configured.
    """
    client = get_langfuse_client()
    if client and trace_id:
        try:
            client.score(trace_id=trace_id, name=name, value=value, comment=comment)
        except Exception as exc:
            logger.debug("LangFuse score failed: %s", exc)
