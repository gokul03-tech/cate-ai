"""
LexOrch-KG — Base Agent
Abstract base class for all specialized agents in the pipeline.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from loguru import logger

from app.core.config import settings


def get_llm():
    """
    Factory function — returns the configured LLM based on settings.
    Supports Groq (default), OpenAI, and Ollama.
    """
    provider = settings.llm_provider.lower()

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            temperature=0.1,
            max_tokens=4096,
        )
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.1,
            max_tokens=4096,
        )
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.1,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


class AgentResult:
    """Standardized agent output container."""

    def __init__(
        self,
        agent_name: str,
        status: str,
        output: dict[str, Any],
        error: str | None = None,
        tokens_used: int = 0,
        execution_time: float = 0.0,
    ) -> None:
        self.agent_name = agent_name
        self.status = status  # "completed" | "failed"
        self.output = output
        self.error = error
        self.tokens_used = tokens_used
        self.execution_time = execution_time
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "status": self.status,
            "output": self.output,
            "error": self.error,
            "tokens_used": self.tokens_used,
            "execution_time_seconds": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgent(ABC):
    """
    Abstract base for all LexOrch-KG agents.
    
    Each agent:
    1. Receives the current pipeline state
    2. Performs its specialized task
    3. Returns updated state + AgentResult
    """

    def __init__(self, name: str, step: int) -> None:
        self.name = name
        self.step = step
        self.llm = get_llm()
        logger.info(f"Agent initialized: {name} (step {step})")

    @abstractmethod
    async def execute(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], AgentResult]:
        """
        Execute the agent's primary task.

        Args:
            state: Current pipeline state dict

        Returns:
            Tuple of (updated_state, agent_result)
        """
        ...

    async def run(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], AgentResult]:
        """
        Wrapper that adds timing, logging, and error handling around execute().
        """
        logger.info(f"[{self.name}] Starting execution for case {state.get('case_id')}")
        start_time = time.monotonic()

        try:
            updated_state, result = await self.execute(state)
            elapsed = time.monotonic() - start_time
            result.execution_time = elapsed
            logger.success(
                f"[{self.name}] Completed in {elapsed:.2f}s | "
                f"tokens={result.tokens_used}"
            )
            return updated_state, result

        except Exception as e:
            elapsed = time.monotonic() - start_time
            logger.error(f"[{self.name}] Failed after {elapsed:.2f}s: {e}")
            error_result = AgentResult(
                agent_name=self.name,
                status="failed",
                output={},
                error=str(e),
                execution_time=elapsed,
            )
            # Don't update state on failure — return original
            state[f"{self.name}_error"] = str(e)
            return state, error_result
