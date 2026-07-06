"""
LexOrch-KG — Agent 3: Knowledge Graph Agent
Inserts entities and relationships into Neo4j, then queries for context.
"""

import uuid
from typing import Any

from langchain.schema import HumanMessage, SystemMessage
from loguru import logger

from app.agents.base_agent import BaseAgent, AgentResult
from app.infrastructure.neo4j.client import neo4j_client


# Mapping from entity type to Neo4j node label
ENTITY_TO_NODE_LABEL = {
    "JUDGE": "Judge",
    "COURT": "Court",
    "PLAINTIFF": "Person",
    "DEFENDANT": "Person",
    "LAWYER": "Person",
    "WITNESS": "Witness",
    "ACT": "Act",
    "SECTION": "Law",
    "EVIDENCE": "Evidence",
    "ORGANIZATION": "Organization",
    "LOCATION": "Location",
    "CASE_NUMBER": "Precedent",
}

# Relationship mappings (entity_type -> relationship_type to Case)
ENTITY_RELATIONSHIPS = {
    "DEFENDANT": "ACCUSED_IN",
    "PLAINTIFF": "FILED_IN",
    "JUDGE": "DECIDED",
    "COURT": "HEARD_IN",
    "ACT": "GOVERNED_BY",
    "SECTION": "APPLIES",
    "EVIDENCE": "SUPPORTS",
    "WITNESS": "TESTIFIED_IN",
    "ORGANIZATION": "INVOLVED_IN",
    "LAWYER": "REPRESENTED_IN",
}


class KnowledgeGraphAgent(BaseAgent):
    """
    Agent 3 — Knowledge Graph Builder
    
    Responsibilities:
    - Insert Case node into Neo4j
    - Insert all extracted entities as typed nodes
    - Create relationships between entities and the Case
    - Query graph for related/similar cases
    - Return enriched graph context
    """

    def __init__(self) -> None:
        super().__init__("KnowledgeGraphAgent", step=3)

    async def execute(
        self, state: dict[str, Any]
    ) -> tuple[dict[str, Any], AgentResult]:
        case_id = str(state["case_id"])
        entities = state.get("entities", [])
        summary = state.get("summary", "")

        nodes_created = 0
        relationships_created = 0

        # ── Step 1: Create Case node ────────────────────────────────────────
        case_props = {
            "id": case_id,
            "title": state.get("case_title", "Unknown"),
            "summary": summary[:500] if summary else "",
            "file_type": state.get("file_type", ""),
            "status": "processing",
        }
        await neo4j_client.create_node("Case", case_props, merge_key="id")
        nodes_created += 1
        logger.info(f"[KnowledgeGraphAgent] Created Case node: {case_id}")

        # ── Step 2: Insert entities and link to case ────────────────────────
        for entity in entities:
            entity_type = entity.get("type", "")
            entity_value = entity.get("value", "")
            node_label = ENTITY_TO_NODE_LABEL.get(entity_type, "Entity")

            if not entity_value:
                continue

            # Deterministic ID for deduplication across cases
            entity_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{node_label}:{entity_value}"))

            # Create entity node
            node_props = {
                "id": entity_id,
                "name": entity_value,
                "entity_type": entity_type,
                "confidence": entity.get("confidence", 0.5),
            }
            await neo4j_client.create_node(node_label, node_props, merge_key="id")
            nodes_created += 1

            # Create relationship to Case
            relationship = ENTITY_RELATIONSHIPS.get(entity_type, "RELATED_TO")
            if entity_type == "JUDGE":
                # Judge DECIDED Case (reversed direction)
                created = await neo4j_client.create_relationship(
                    from_label="Judge",
                    from_id=entity_id,
                    to_label="Case",
                    to_id=case_id,
                    relationship_type="DECIDED",
                )
            elif entity_type == "COURT":
                created = await neo4j_client.create_relationship(
                    from_label="Case",
                    from_id=case_id,
                    to_label="Court",
                    to_id=entity_id,
                    relationship_type="HEARD_IN",
                )
            else:
                created = await neo4j_client.create_relationship(
                    from_label=node_label,
                    from_id=entity_id,
                    to_label="Case",
                    to_id=case_id,
                    relationship_type=relationship,
                )

            if created:
                relationships_created += 1

        # ── Step 3: Query related cases ─────────────────────────────────────
        similar_cases = await neo4j_client.find_similar_cases(case_id, limit=5)
        graph_context = await neo4j_client.get_case_graph(case_id)

        logger.info(
            f"[KnowledgeGraphAgent] nodes={nodes_created} "
            f"relationships={relationships_created} "
            f"similar_cases={len(similar_cases)}"
        )

        state.update({
            "graph_nodes_created": nodes_created,
            "graph_relationships_created": relationships_created,
            "similar_cases": similar_cases,
            "graph_context": graph_context,
        })

        result = AgentResult(
            agent_name=self.name,
            status="completed",
            output={
                "nodes_created": nodes_created,
                "relationships_created": relationships_created,
                "similar_cases_found": len(similar_cases),
                "graph_summary": {
                    "node_count": len(graph_context.get("nodes", [])),
                    "edge_count": len(graph_context.get("edges", [])),
                },
            },
        )
        return state, result
