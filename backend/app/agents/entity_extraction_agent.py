"""
LexOrch-KG — Agent 2: Entity Extraction Agent
Extracts legal entities using spaCy NER + LLM-powered extraction.
"""

import json
import re
from typing import Any

import spacy
from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from app.agents.base_agent import BaseAgent, AgentResult


# Entity types we recognize in legal documents
LEGAL_ENTITY_TYPES = [
    "JUDGE", "COURT", "PLAINTIFF", "DEFENDANT", "LAWYER",
    "WITNESS", "SECTION", "ACT", "EVIDENCE", "DATE",
    "LOCATION", "ORGANIZATION", "CASE_NUMBER",
]

# Extraction prompt template
ENTITY_EXTRACTION_PROMPT = """You are a legal document analyst. Extract ALL named entities from the following legal text.

Return a JSON array where each object has:
- "type": one of {types}
- "value": the exact text of the entity
- "confidence": 0.0-1.0
- "context": a 1-sentence excerpt showing where it appears

Legal text:
{text}

Return ONLY valid JSON array, no other text."""


class EntityExtractionAgent(BaseAgent):
    """
    Agent 2 — Entity Extraction
    
    Uses a hybrid approach:
    1. spaCy NER for standard NLP entities (fast, high recall)
    2. LLM extraction for legal-specific entities (high precision)
    3. Deduplication and confidence scoring
    """

    def __init__(self) -> None:
        super().__init__("EntityExtractionAgent", step=2)
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            logger.warning("spaCy model not found, using LLM-only extraction")
            self.nlp = None

    async def execute(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], AgentResult]:
        raw_text = state.get("raw_text", "")
        chunks = state.get("chunks", [])

        if not raw_text:
            raise ValueError("No raw text available for entity extraction")

        # Use first 10K chars for entity extraction (LLM context window)
        sample_text = raw_text[:10000]

        # ── Method 1: spaCy NER ─────────────────────────────────────────────
        spacy_entities = self._extract_with_spacy(sample_text)

        # ── Method 2: LLM extraction ────────────────────────────────────────
        llm_entities = await self._extract_with_llm(sample_text)

        # ── Merge and deduplicate ───────────────────────────────────────────
        all_entities = self._merge_entities(spacy_entities, llm_entities)

        logger.info(
            f"[EntityExtractionAgent] Found {len(all_entities)} unique entities "
            f"(spaCy={len(spacy_entities)}, LLM={len(llm_entities)})"
        )

        state["entities"] = all_entities

        result = AgentResult(
            agent_name=self.name,
            status="completed",
            output={
                "total_entities": len(all_entities),
                "spacy_entities": len(spacy_entities),
                "llm_entities": len(llm_entities),
                "entity_types": self._count_by_type(all_entities),
            },
        )
        return state, result

    def _extract_with_spacy(self, text: str) -> list[dict[str, Any]]:
        """Standard NLP entity extraction via spaCy."""
        if not self.nlp:
            return []

        entities = []
        doc = self.nlp(text[:100000])  # spaCy limit

        # Map spaCy labels to our legal entity types
        spacy_to_legal = {
            "PERSON": "PLAINTIFF",  # Will be refined by LLM
            "ORG": "ORGANIZATION",
            "GPE": "LOCATION",
            "LOC": "LOCATION",
            "DATE": "DATE",
            "LAW": "ACT",
            "CARDINAL": None,  # Ignore
        }

        for ent in doc.ents:
            legal_type = spacy_to_legal.get(ent.label_)
            if legal_type:
                entities.append({
                    "type": legal_type,
                    "value": ent.text.strip(),
                    "confidence": 0.75,
                    "source": "spacy",
                    "context": text[max(0, ent.start_char - 50):ent.end_char + 50],
                })

        return entities

    async def _extract_with_llm(self, text: str) -> list[dict[str, Any]]:
        """Legal-domain-specific entity extraction using LLM."""
        prompt = ENTITY_EXTRACTION_PROMPT.format(
            types=", ".join(LEGAL_ENTITY_TYPES),
            text=text,
        )

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response.content, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
                for e in entities:
                    e["source"] = "llm"
                return entities
        except Exception as e:
            logger.error(f"LLM entity extraction failed: {e}")

        return []

    def _merge_entities(
        self,
        spacy_entities: list[dict],
        llm_entities: list[dict],
    ) -> list[dict[str, Any]]:
        """
        Deduplicate and merge entities from both sources.
        LLM entities take precedence when there's overlap.
        """
        seen = set()
        merged = []

        # Add LLM entities first (higher priority)
        for entity in llm_entities:
            key = (entity.get("type", ""), entity.get("value", "").lower().strip())
            if key not in seen and entity.get("value"):
                seen.add(key)
                merged.append(entity)

        # Add spaCy entities that aren't duplicates
        for entity in spacy_entities:
            key = (entity.get("type", ""), entity.get("value", "").lower().strip())
            if key not in seen and entity.get("value"):
                seen.add(key)
                merged.append(entity)

        return merged

    def _count_by_type(self, entities: list[dict]) -> dict[str, int]:
        """Count entities grouped by type."""
        counts: dict[str, int] = {}
        for e in entities:
            etype = e.get("type", "UNKNOWN")
            counts[etype] = counts.get(etype, 0) + 1
        return counts
