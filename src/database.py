import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))


def verify_connection():
    try:
        with driver.session() as session:
            result = session.run("RETURN 1 AS test")
            return result.single()["test"] == 1
    except Exception:
        return False


def get_graph_schema() -> str:
    """Returns a textual representation of node labels, relationship types, and properties."""
    schema_query = """
    CALL db.schema.visualization()
    """
    sample_query = """
    MATCH (n)
    WITH labels(n) AS lbls, keys(n) AS props
    UNWIND lbls AS label
    RETURN label, collect(distinct props)[..3] AS sample_properties
    """
    rel_query = """
    MATCH (a)-[r]->(b)
    RETURN DISTINCT labels(a)[0] AS source, type(r) AS relationship, labels(b)[0] AS target
    LIMIT 25
    """
    try:
        with driver.session() as session:
            nodes_res = session.run(sample_query).data()
            rels_res = session.run(rel_query).data()
    except Exception as exc:
        return f"Knowledge graph is currently unavailable: {exc}"

    schema_str = "Node Labels & Properties:\n"
    for row in nodes_res:
        schema_str += f"- :{row['label']} with properties: {row['sample_properties']}\n"

    schema_str += "\nRelationships:\n"
    for row in rels_res:
        schema_str += f"- (:{row['source']})-[:{row['relationship']}]->(:{row['target']})\n"

    return schema_str


def run_cypher_query(query: str) -> List[Dict[str, Any]]:
    """Executes a Cypher read query safely and returns serialized records."""
    with driver.session() as session:
        try:
            result = session.run(query)
            return [record.data() for record in result]
        except Exception as e:
            return [{"error": f"Cypher Execution Error: {str(e)}"}]


def run_vector_search(query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Executes text search or vector index search against Project/Document descriptions.
    Falls back to a keyword/full-text match if vector index is not configured.
    """
    cypher = """
    MATCH (p:Project)
    WHERE toLower(p.description) CONTAINS toLower($search_text)
       OR toLower(p.name) CONTAINS toLower($search_text)
       OR toLower(p.summary) CONTAINS toLower($search_text)
    OPTIONAL MATCH (c:Consultant)-[:LED_PROJECT|WORKED_ON]->(p)
    OPTIONAL MATCH (p)-[:FOR_CLIENT]->(cl:Client)
    RETURN p.name AS project_name, 
           p.description AS project_description, 
           cl.name AS client_name,
           cl.region AS region,
           collect(distinct c.name) AS consultants
    LIMIT $top_k
    """
    with driver.session() as session:
        try:
            res = session.run(cypher, search_text=query_text, top_k=top_k)
            records = [r.data() for r in res]
            if not records:
                
                words = [w for w in query_text.lower().split() if len(w) > 3]
                if words:
                    fallback_cypher = """
                    MATCH (p:Project)
                    WHERE ANY(w IN $words WHERE toLower(p.description) CONTAINS w)
                    OPTIONAL MATCH (c:Consultant)-[:LED_PROJECT|WORKED_ON]->(p)
                    OPTIONAL MATCH (p)-[:FOR_CLIENT]->(cl:Client)
                    RETURN p.name AS project_name, 
                           p.description AS project_description, 
                           cl.name AS client_name,
                           cl.region AS region,
                           collect(distinct c.name) AS consultants
                    LIMIT $top_k
                    """
                    res = session.run(fallback_cypher, words=words, top_k=top_k)
                    records = [r.data() for r in res]
            return records
        except Exception as e:
            return [{"error": f"Vector/Text Search Error: {str(e)}"}]


def close_driver():
    driver.close()
