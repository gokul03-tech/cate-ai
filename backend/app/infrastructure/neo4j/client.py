"""
LexOrch-KG — Neo4j Knowledge Graph Client
Manages connection and CRUD operations for the legal knowledge graph.
"""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
from loguru import logger
from neo4j import AsyncGraphDatabase, AsyncDriver

from app.core.config import settings


class Neo4jClient:
    """
    Async Neo4j client wrapper.
    
    Provides methods to insert nodes, create relationships,
    and query the legal knowledge graph.
    """

    def __init__(self) -> None:
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        """Initialize the Neo4j async driver."""
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
            max_connection_pool_size=50,
        )
        logger.info(f"Neo4j connected → {settings.neo4j_uri}")

    async def close(self) -> None:
        """Close the Neo4j driver and all connections."""
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j connection closed")

    async def verify_connectivity(self) -> bool:
        """Test Neo4j connectivity."""
        try:
            await self._driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed: {e}")
            return False

    @asynccontextmanager
    async def session(self) -> AsyncGenerator:
        """Provide an async Neo4j session context."""
        if not self._driver:
            await self.connect()
        async with self._driver.session() as session:
            yield session

    # ── Node Operations ───────────────────────────────────────────────────────

    async def create_node(
        self,
        label: str,
        properties: dict[str, Any],
        merge_key: str = "id",
    ) -> dict[str, Any]:
        """
        MERGE a node (create if not exists, return if exists).
        
        Args:
            label: Neo4j node label (e.g., 'Case', 'Judge')
            properties: Node properties dict
            merge_key: Property to use for MERGE uniqueness
        """
        query = f"""
        MERGE (n:{label} {{{merge_key}: $merge_value}})
        ON CREATE SET n += $properties
        ON MATCH SET n += $properties
        RETURN n
        """
        async with self.session() as session:
            result = await session.run(
                query,
                merge_value=properties.get(merge_key),
                properties=properties,
            )
            record = await result.single()
            return dict(record["n"]) if record else {}

    async def create_relationship(
        self,
        from_label: str,
        from_id: str,
        to_label: str,
        to_id: str,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
    ) -> bool:
        """
        Create a directed relationship between two nodes.
        
        Example: (Person)-[:ACCUSED_IN]->(Case)
        """
        query = f"""
        MATCH (a:{from_label} {{id: $from_id}})
        MATCH (b:{to_label} {{id: $to_id}})
        MERGE (a)-[r:{relationship_type}]->(b)
        ON CREATE SET r += $properties
        RETURN r
        """
        async with self.session() as session:
            result = await session.run(
                query,
                from_id=from_id,
                to_id=to_id,
                properties=properties or {},
            )
            record = await result.single()
            return record is not None

    async def get_case_graph(self, case_id: str) -> dict[str, Any]:
        """
        Retrieve all nodes and relationships connected to a case.
        Returns data suitable for React Flow visualization.
        """
        query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (c)-[r]-(related)
        RETURN c, collect(r) as relationships, collect(related) as related_nodes
        """
        async with self.session() as session:
            result = await session.run(query, case_id=case_id)
            record = await result.single()
            if not record:
                return {"nodes": [], "edges": []}

            nodes = []
            edges = []

            # Add the case node
            case_node = dict(record["c"])
            nodes.append({"id": case_id, "label": "Case", "data": case_node})

            # Add related nodes and edges
            for i, (rel, node) in enumerate(
                zip(record["relationships"], record["related_nodes"])
            ):
                node_data = dict(node)
                node_id = node_data.get("id", f"node_{i}")
                nodes.append({
                    "id": str(node_id),
                    "label": list(node.labels)[0] if node.labels else "Unknown",
                    "data": node_data,
                })
                edges.append({
                    "source": case_id,
                    "target": str(node_id),
                    "type": rel.type,
                })

            return {"nodes": nodes, "edges": edges}

    async def find_similar_cases(
        self, case_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find cases similar to the given case via SIMILAR_TO relationships."""
        query = """
        MATCH (c:Case {id: $case_id})-[:SIMILAR_TO]-(similar:Case)
        RETURN similar
        LIMIT $limit
        """
        async with self.session() as session:
            result = await session.run(query, case_id=case_id, limit=limit)
            records = await result.data()
            return [dict(r["similar"]) for r in records]

    async def run_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a raw Cypher query and return results."""
        async with self.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

    async def create_schema_constraints(self) -> None:
        """Create uniqueness constraints and indexes for performance."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (j:Judge) REQUIRE j.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (ct:Court) REQUIRE ct.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Law) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Act) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (pr:Precedent) REQUIRE pr.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
        ]
        async with self.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint creation warning: {e}")
        logger.info("Neo4j schema constraints created")


# Global singleton client
neo4j_client = Neo4jClient()
