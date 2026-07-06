"""
LexOrch-KG — Agent 5: Reasoning Agent
Applies legal logic, compares precedents, and generates structured reasoning.
"""

import json
import re
from typing import Any

from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from app.agents.base_agent import BaseAgent, AgentResult


REASONING_SYSTEM_PROMPT = """You are an expert legal reasoning AI assistant specialized in judicial decision support.

IMPORTANT DISCLAIMER: You are a decision SUPPORT tool only. Your analysis must NEVER replace or override the judgment of qualified legal professionals. Every recommendation must be clearly labeled as AI-generated support material.

Your task is to:
1. Analyze the case facts
2. Apply relevant legal principles and provisions
3. Compare with retrieved legal precedents
4. Generate structured legal reasoning
5. Identify applicable laws and their interpretation

Always maintain objectivity, cite evidence, and acknowledge uncertainty.
"""

REASONING_PROMPT = """Analyze this legal case and provide detailed legal reasoning.

CASE SUMMARY:
{summary}

KEY FACTS:
{facts}

APPLICABLE LAWS/ACTS:
{acts}

RETRIEVED PRECEDENTS:
{precedents}

ENTITY CONTEXT:
{entities}

Please provide:
1. LEGAL ANALYSIS: Analyze the case under applicable laws
2. PRECEDENT APPLICATION: How do retrieved precedents apply?
3. LEGAL PRINCIPLES: What legal principles govern this case?
4. POINTS IN FAVOR OF CONVICTION/RULING: List key supporting points
5. POINTS AGAINST CONVICTION/RULING: List key opposing points
6. PRELIMINARY ASSESSMENT: Your legal assessment (with confidence 0.0-1.0)
7. LIMITATIONS: What information is missing or uncertain?

Format your response as structured JSON."""


class ReasoningAgent(BaseAgent):
    """
    Agent 5 — Legal Reasoning
    
    Synthesizes information from previous agents to generate
    structured legal reasoning with confidence scores and limitations.
    """

    def __init__(self) -> None:
        super().__init__("ReasoningAgent", step=5)

    async def execute(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], AgentResult]:
        summary = state.get("summary", "")
        key_facts = state.get("key_facts", [])
        entities = state.get("entities", [])
        precedents = state.get("retrieved_precedents", [])

        # ── Extract relevant context ─────────────────────────────────────────
        acts = [
            e["value"] for e in entities
            if e.get("type") in ("ACT", "SECTION")
        ]

        precedent_texts = [
            f"- {p.get('title', 'Unknown')}: {p.get('text', '')[:300]}"
            for p in precedents[:5]
        ]

        entity_summary = self._summarize_entities(entities)

        # ── Build and invoke reasoning prompt ────────────────────────────────
        prompt = REASONING_PROMPT.format(
            summary=summary[:2000],
            facts="\n".join(f"- {f}" for f in key_facts[:10]),
            acts="\n".join(f"- {a}" for a in acts[:10]) or "No specific acts identified",
            precedents="\n".join(precedent_texts) or "No precedents retrieved",
            entities=entity_summary,
        )

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=REASONING_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            reasoning_text = response.content
            tokens_used = getattr(response, "usage_metadata", {}).get("total_tokens", 0)
        except Exception as e:
            logger.error(f"Reasoning LLM call failed: {e}")
            reasoning_text = "{}"
            tokens_used = 0

        # ── Parse structured output ──────────────────────────────────────────
        reasoning = self._parse_reasoning(reasoning_text)

        logger.info(
            f"[ReasoningAgent] Generated reasoning | "
            f"confidence={reasoning.get('preliminary_confidence', 0):.2f}"
        )

        state.update({
            "legal_reasoning": reasoning,
            "reasoning_text": reasoning_text,
        })

        result = AgentResult(
            agent_name=self.name,
            status="completed",
            output={
                "reasoning_sections": list(reasoning.keys()),
                "preliminary_confidence": reasoning.get("preliminary_confidence", 0),
                "points_for": len(reasoning.get("points_in_favor", [])),
                "points_against": len(reasoning.get("points_against", [])),
            },
            tokens_used=tokens_used,
        )
        return state, result

    def _summarize_entities(self, entities: list[dict]) -> str:
        """Format entities for the reasoning prompt."""
        by_type: dict[str, list[str]] = {}
        for e in entities:
            etype = e.get("type", "UNKNOWN")
            by_type.setdefault(etype, []).append(e.get("value", ""))

        lines = []
        for etype, values in by_type.items():
            unique_vals = list(set(values))[:5]
            lines.append(f"  {etype}: {', '.join(unique_vals)}")
        return "\n".join(lines)

    def _parse_reasoning(self, text: str) -> dict[str, Any]:
        """Parse LLM output into structured reasoning dict."""
        # Try JSON extraction first
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

        # Fallback: structure the text manually
        return {
            "legal_analysis": self._extract_section(text, "LEGAL ANALYSIS"),
            "precedent_application": self._extract_section(text, "PRECEDENT APPLICATION"),
            "legal_principles": self._extract_section(text, "LEGAL PRINCIPLES"),
            "points_in_favor": self._extract_list(text, "POINTS IN FAVOR"),
            "points_against": self._extract_list(text, "POINTS AGAINST"),
            "preliminary_assessment": self._extract_section(text, "PRELIMINARY ASSESSMENT"),
            "preliminary_confidence": 0.5,
            "limitations": self._extract_list(text, "LIMITATIONS"),
            "raw_output": text[:2000],
        }

    def _extract_section(self, text: str, header: str) -> str:
        """Extract a named section from the LLM output."""
        pattern = rf"{header}[:\s]*(.*?)(?=\n\d+\.|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_list(self, text: str, header: str) -> list[str]:
        """Extract a bulleted/numbered list from the LLM output."""
        pattern = rf"{header}.*?\n((?:[-•*\d\.]\s+.+\n?)+)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            return []
        items = re.findall(r'[-•*\d\.]\s+(.+)', match.group(1))
        return [item.strip() for item in items if item.strip()]
