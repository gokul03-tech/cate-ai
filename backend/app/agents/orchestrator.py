"""
LexOrch-KG — LangGraph Orchestrator
Wires all 8 agents into a directed graph pipeline with state management.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph
from loguru import logger

from app.agents.case_understanding_agent import CaseUnderstandingAgent
from app.agents.debate_agent import DebateAgent
from app.agents.entity_extraction_agent import EntityExtractionAgent
from app.agents.explainability_agent import ExplainabilityAgent
from app.agents.knowledge_graph_agent import KnowledgeGraphAgent
from app.agents.report_agent import ReportAgent
from app.agents.reasoning_agent import ReasoningAgent
from app.agents.retrieval_agent import RetrievalAgent


# =============================================================================
# Pipeline State — TypedDict defines all fields that flow between agents
# =============================================================================

class PipelineState(TypedDict, total=False):
    # Input fields
    case_id: str
    case_title: str
    file_path: str
    file_type: str

    # Agent 1: Case Understanding
    raw_text: str
    chunks: list[dict[str, Any]]
    page_count: int
    word_count: int
    ocr_applied: bool
    summary: str
    key_facts: list[str]

    # Agent 2: Entity Extraction
    entities: list[dict[str, Any]]

    # Agent 3: Knowledge Graph
    graph_nodes_created: int
    graph_relationships_created: int
    similar_cases: list[dict[str, Any]]
    graph_context: dict[str, Any]

    # Agent 4: Retrieval
    retrieved_precedents: list[dict[str, Any]]
    embedding_count: int

    # Agent 5: Reasoning
    legal_reasoning: dict[str, Any]
    reasoning_text: str

    # Agent 6: Debate
    debate_result: dict[str, Any]

    # Agent 7: Explainability
    explainability: dict[str, Any]

    # Agent 8: Reports
    generated_reports: dict[str, Any]

    # Pipeline metadata
    pipeline_errors: list[str]
    completed_agents: list[str]


# =============================================================================
# LangGraph Pipeline
# =============================================================================

class LegalPipeline:
    """
    LangGraph-based multi-agent orchestrator.
    
    Each node in the graph corresponds to one specialized agent.
    Nodes execute sequentially with shared state flowing between them.
    """

    def __init__(self) -> None:
        # Instantiate all agents
        self.case_agent = CaseUnderstandingAgent()
        self.entity_agent = EntityExtractionAgent()
        self.kg_agent = KnowledgeGraphAgent()
        self.retrieval_agent = RetrievalAgent()
        self.reasoning_agent = ReasoningAgent()
        self.debate_agent = DebateAgent()
        self.explain_agent = ExplainabilityAgent()
        self.report_agent = ReportAgent()

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Construct the LangGraph directed pipeline."""
        graph = StateGraph(PipelineState)

        # Register all agent nodes
        graph.add_node("case_understanding", self._run_case_understanding)
        graph.add_node("entity_extraction", self._run_entity_extraction)
        graph.add_node("knowledge_graph", self._run_knowledge_graph)
        graph.add_node("retrieval", self._run_retrieval)
        graph.add_node("reasoning", self._run_reasoning)
        graph.add_node("debate", self._run_debate)
        graph.add_node("explainability", self._run_explainability)
        graph.add_node("report_generation", self._run_report)

        # Define edges (linear pipeline)
        graph.set_entry_point("case_understanding")
        graph.add_edge("case_understanding", "entity_extraction")
        graph.add_edge("entity_extraction", "knowledge_graph")
        graph.add_edge("knowledge_graph", "retrieval")
        graph.add_edge("retrieval", "reasoning")
        graph.add_edge("reasoning", "debate")
        graph.add_edge("debate", "explainability")
        graph.add_edge("explainability", "report_generation")
        graph.add_edge("report_generation", END)

        return graph.compile()

    # ── Node wrapper methods ──────────────────────────────────────────────────

    async def _run_case_understanding(self, state: PipelineState) -> PipelineState:
        state, result = await self.case_agent.run(state)
        return self._update_pipeline_meta(state, result)

    async def _run_entity_extraction(self, state: PipelineState) -> PipelineState:
        state, result = await self.entity_agent.run(state)
        return self._update_pipeline_meta(state, result)

    async def _run_knowledge_graph(self, state: PipelineState) -> PipelineState:
        state, result = await self.kg_agent.run(state)
        return self._update_pipeline_meta(state, result)

    async def _run_retrieval(self, state: PipelineState) -> PipelineState:
        state, result = await self.retrieval_agent.run(state)
        return self._update_pipeline_meta(state, result)

    async def _run_reasoning(self, state: PipelineState) -> PipelineState:
        state, result = await self.reasoning_agent.run(state)
        return self._update_pipeline_meta(state, result)

    async def _run_debate(self, state: PipelineState) -> PipelineState:
        state, result = await self.debate_agent.run(state)
        return self._update_pipeline_meta(state, result)

    async def _run_explainability(self, state: PipelineState) -> PipelineState:
        state, result = await self.explain_agent.run(state)
        return self._update_pipeline_meta(state, result)

    async def _run_report(self, state: PipelineState) -> PipelineState:
        state, result = await self.report_agent.run(state)
        return self._update_pipeline_meta(state, result)

    def _update_pipeline_meta(
        self, state: PipelineState, result: Any
    ) -> PipelineState:
        """Track completed agents and errors in the shared state."""
        completed = list(state.get("completed_agents", []))
        errors = list(state.get("pipeline_errors", []))

        completed.append(result.agent_name)
        if result.error:
            errors.append(f"{result.agent_name}: {result.error}")

        state["completed_agents"] = completed
        state["pipeline_errors"] = errors
        return state

    # ── Public interface ──────────────────────────────────────────────────────

    async def run(
        self,
        case_id: str,
        case_title: str,
        file_path: str,
        file_type: str,
    ) -> PipelineState:
        """
        Execute the full 8-agent pipeline for a legal case.
        
        Args:
            case_id: UUID of the case
            case_title: Human-readable case title
            file_path: Absolute path to the uploaded document
            file_type: File extension (pdf, docx, txt)
        
        Returns:
            Final pipeline state with all agent outputs
        """
        initial_state: PipelineState = {
            "case_id": case_id,
            "case_title": case_title,
            "file_path": file_path,
            "file_type": file_type,
            "pipeline_errors": [],
            "completed_agents": [],
        }

        logger.info(
            f"[Orchestrator] Starting pipeline for case {case_id} | "
            f"file={file_path} | type={file_type}"
        )

        start = asyncio.get_event_loop().time()
        final_state = await self._graph.ainvoke(initial_state)
        elapsed = asyncio.get_event_loop().time() - start

        completed = final_state.get("completed_agents", [])
        errors = final_state.get("pipeline_errors", [])

        logger.success(
            f"[Orchestrator] Pipeline complete in {elapsed:.1f}s | "
            f"agents={len(completed)}/8 | errors={len(errors)}"
        )

        if errors:
            logger.warning(f"[Orchestrator] Pipeline errors: {errors}")

        return final_state


# Singleton pipeline instance (lazy-loaded)
_pipeline: LegalPipeline | None = None


def get_pipeline() -> LegalPipeline:
    """Return the global pipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = LegalPipeline()
    return _pipeline
