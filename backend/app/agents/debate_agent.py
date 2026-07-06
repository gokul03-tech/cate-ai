"""
LexOrch-KG — Agent 6: Debate Agent
Multi-agent adversarial debate with Prosecution, Defense, Judge, and Consensus agents.
"""

import json
import re
from typing import Any

from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from app.agents.base_agent import BaseAgent, AgentResult


# ── System Prompts for each sub-agent ─────────────────────────────────────────

PROSECUTION_SYSTEM = """You are the Prosecution Agent in a legal debate.
Your role is to argue in FAVOR of conviction/ruling based on the evidence.
Be thorough, cite specific evidence, and apply relevant laws.
Acknowledge strengths of your position and weaknesses of the defense.
Your goal is NOT to be biased but to represent the prosecution's strongest case."""

DEFENSE_SYSTEM = """You are the Defense Agent in a legal debate.
Your role is to argue AGAINST conviction/ruling and in defense of the accused.
Challenge the evidence, highlight procedural issues, and apply constitutional protections.
Your goal is NOT to be biased but to represent the defense's strongest case."""

JUDGE_SYSTEM = """You are the Neutral Judge Agent evaluating a legal debate.
Your role is to:
1. Assess the strengths and weaknesses of both prosecution and defense arguments
2. Identify the most compelling points on each side
3. Apply legal principles impartially
4. Provide a balanced assessment without reaching a final verdict
You must remain strictly neutral and objective."""

CONSENSUS_SYSTEM = """You are the Consensus Agent in a legal AI system.
After reviewing arguments from prosecution, defense, and the judge's assessment,
synthesize a final recommendation.

CRITICAL: This is a DECISION SUPPORT recommendation only.
ALWAYS include the disclaimer: "This is an AI-generated analysis for decision support purposes only. 
The final legal decision must be made by qualified human legal professionals."

Provide: final_recommendation, confidence_score (0.0-1.0), key_factors, caveats."""


class DebateAgent(BaseAgent):
    """
    Agent 6 — Multi-Agent Adversarial Debate
    
    Sub-agents:
    1. ProsecutionAgent — argues for conviction/ruling
    2. DefenseAgent — argues against conviction/ruling
    3. JudgeAgent — provides neutral assessment
    4. ConsensusAgent — synthesizes final recommendation
    """

    def __init__(self) -> None:
        super().__init__("DebateAgent", step=6)

    async def execute(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], AgentResult]:
        summary = state.get("summary", "")
        reasoning = state.get("legal_reasoning", {})
        key_facts = state.get("key_facts", [])
        precedents = state.get("retrieved_precedents", [])

        # Build shared context for all agents
        context = self._build_context(summary, reasoning, key_facts, precedents)
        total_tokens = 0

        # ── Round 1: Prosecution ─────────────────────────────────────────────
        prosecution_arg, tokens = await self._run_sub_agent(
            "ProsecutionAgent",
            PROSECUTION_SYSTEM,
            f"Present your prosecution argument for this case:\n\n{context}",
        )
        total_tokens += tokens

        # ── Round 2: Defense ─────────────────────────────────────────────────
        defense_arg, tokens = await self._run_sub_agent(
            "DefenseAgent",
            DEFENSE_SYSTEM,
            f"Present your defense argument for this case:\n\n{context}\n\nProsecution has argued:\n{prosecution_arg[:1000]}",
        )
        total_tokens += tokens

        # ── Round 3: Judge Assessment ────────────────────────────────────────
        judge_assessment, tokens = await self._run_sub_agent(
            "JudgeAgent",
            JUDGE_SYSTEM,
            f"""Assess the following debate:

CASE CONTEXT:
{context}

PROSECUTION ARGUMENT:
{prosecution_arg[:1500]}

DEFENSE ARGUMENT:
{defense_arg[:1500]}

Provide your neutral judicial assessment.""",
        )
        total_tokens += tokens

        # ── Round 4: Consensus ───────────────────────────────────────────────
        consensus_input = f"""
PROSECUTION: {prosecution_arg[:1000]}
DEFENSE: {defense_arg[:1000]}
JUDGE ASSESSMENT: {judge_assessment[:1000]}
"""
        consensus, tokens = await self._run_sub_agent(
            "ConsensusAgent",
            CONSENSUS_SYSTEM,
            f"Synthesize a final recommendation from this debate:\n{consensus_input}",
        )
        total_tokens += tokens

        # ── Parse confidence scores ──────────────────────────────────────────
        prosecution_confidence = self._extract_confidence(prosecution_arg)
        defense_confidence = self._extract_confidence(defense_arg)
        consensus_confidence = self._extract_confidence(consensus)

        debate_result = {
            "prosecution_argument": prosecution_arg,
            "defense_argument": defense_arg,
            "judge_assessment": judge_assessment,
            "consensus": consensus,
            "prosecution_confidence": prosecution_confidence,
            "defense_confidence": defense_confidence,
            "final_recommendation": self._extract_recommendation(consensus),
            "recommendation_confidence": consensus_confidence,
            "debate_rounds": 1,
        }

        logger.info(
            f"[DebateAgent] Debate complete | "
            f"prosecution_conf={prosecution_confidence:.2f} "
            f"defense_conf={defense_confidence:.2f} "
            f"consensus_conf={consensus_confidence:.2f}"
        )

        state["debate_result"] = debate_result

        result = AgentResult(
            agent_name=self.name,
            status="completed",
            output={
                "prosecution_confidence": prosecution_confidence,
                "defense_confidence": defense_confidence,
                "consensus_confidence": consensus_confidence,
                "debate_rounds": 1,
                "has_recommendation": bool(debate_result["final_recommendation"]),
            },
            tokens_used=total_tokens,
        )
        return state, result

    def _build_context(
        self,
        summary: str,
        reasoning: dict,
        key_facts: list,
        precedents: list,
    ) -> str:
        """Build shared context string for all sub-agents."""
        facts_str = "\n".join(f"- {f}" for f in key_facts[:8])
        precedents_str = "\n".join(
            f"- {p.get('title', 'Unknown')}: {p.get('text', '')[:200]}"
            for p in precedents[:3]
        )
        return f"""CASE SUMMARY:
{summary[:1500]}

KEY FACTS:
{facts_str}

LEGAL REASONING:
{str(reasoning.get('legal_analysis', ''))[:800]}

PRECEDENTS:
{precedents_str}"""

    async def _run_sub_agent(
        self,
        agent_name: str,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[str, int]:
        """Run a single sub-agent and return (response, tokens_used)."""
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])
            tokens = getattr(response, "usage_metadata", {}).get("total_tokens", 0)
            logger.info(f"[{agent_name}] Completed | tokens={tokens}")
            return response.content, tokens
        except Exception as e:
            logger.error(f"[{agent_name}] Failed: {e}")
            return f"[{agent_name}] failed to generate response: {e}", 0

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence score from LLM output."""
        patterns = [
            r'confidence[:\s]+([0-9]*\.?[0-9]+)',
            r'([0-9]*\.?[0-9]+)\s*(?:/\s*1\.0|out of 1)',
            r'([0-9]+)%',
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                value = float(match.group(1))
                if value > 1.0:
                    value /= 100.0  # Convert percentage
                return min(max(value, 0.0), 1.0)
        return 0.5  # Default

    def _extract_recommendation(self, consensus: str) -> str:
        """Extract the final recommendation from consensus output."""
        # Look for recommendation keyword
        match = re.search(
            r'(?:final_recommendation|recommendation)[:\s]+"?([^"\n]+)"?',
            consensus, re.IGNORECASE
        )
        if match:
            return match.group(1).strip()
        # Return first substantial sentence
        sentences = [s.strip() for s in consensus.split(".") if len(s.strip()) > 50]
        return sentences[0] + "." if sentences else consensus[:300]
