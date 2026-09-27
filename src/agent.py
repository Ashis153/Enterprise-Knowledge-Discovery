import json
import re
from typing import Any, Dict, List, Literal, Optional
from typing_extensions import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from database import get_graph_schema, run_cypher_query, run_vector_search

load_dotenv()


llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

class GraphState(TypedDict):
    question: str
    route: str  
    cypher_query: Optional[str]
    cypher_result: Optional[List[Dict[str, Any]]]
    vector_result: Optional[List[Dict[str, Any]]]
    final_answer: Optional[str]
    sources: Optional[List[str]]

class RouteDecision(BaseModel):
    route: Literal["structured", "unstructured", "hybrid"] = Field(
        description="Select 'structured' for direct relational/graph questions (who, skills, clients), 'unstructured' for doc/deck summaries, or 'hybrid' when both exact relationships and contextual descriptions are needed."
    )
    reasoning: str = Field(description="Explanation of routing choice.")

class CypherOutput(BaseModel):
    query: str = Field(description="Executable Cypher query without markdown formatting.")


def router_node(state: GraphState) -> Dict[str, Any]:
    """Analyzes user query and routes to structured, unstructured, or hybrid node."""
    structured_router = llm.with_structured_output(RouteDecision)
    
    system_prompt = """You are an Enterprise Knowledge Discovery Router.
    Determine the optimal search strategy:
    - 'structured': Questions asking for specific relational linkages (e.g. "Who has skill X?", "Which clients are located in Europe?", "Who led project Y?").
    - 'unstructured': Questions asking for semantic content, deck summaries, or qualitative descriptions (e.g. "What was discussed in project reports?", "Find deck details on cloud architecture").
    - 'hybrid': Complex multi-intent questions requiring BOTH structured graph traversals AND qualitative document searching (e.g. "Who built cloud platforms for healthcare clients in Europe?").
    """
    
    decision: RouteDecision = structured_router.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=state["question"])]
    )
    
    return {"route": decision.route}


def cypher_generator_node(state: GraphState) -> Dict[str, Any]:
    """Generates schema-compliant Cypher query and executes it against Neo4j."""
    schema = get_graph_schema()
    
    system_prompt = f"""You are a Cypher Expert for Neo4j.
    Generate ONLY a valid Cypher read query based on this Graph Schema:
    {schema}

    Rules:
    - DO NOT write data modification queries (CREATE, MERGE, DELETE).
    - Return clean entity names, properties, and relationships.
    - Perform case-insensitive matches using toLower() where appropriate.
    - Output ONLY the Cypher query text, with no markdown fences (` ```cypher `).
    """

    structured_cypher = llm.with_structured_output(CypherOutput)
    res = structured_cypher.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=f"Question: {state['question']}")]
    )
    
    clean_query = res.query.replace("```cypher", "").replace("```", "").strip()
    execution_result = run_cypher_query(clean_query)
    
    return {
        "cypher_query": clean_query,
        "cypher_result": execution_result
    }


def vector_search_node(state: GraphState) -> Dict[str, Any]:
    """Executes vector / unstructured text search on document and project descriptions."""
    results = run_vector_search(state["question"], top_k=3)
    return {"vector_result": results}


def hybrid_search_node(state: GraphState) -> Dict[str, Any]:
    """Executes both Cypher structured query generation and vector similarity search."""
    cypher_data = cypher_generator_node(state)
    vector_data = vector_search_node(state)
    
    return {
        "cypher_query": cypher_data.get("cypher_query"),
        "cypher_result": cypher_data.get("cypher_result"),
        "vector_result": vector_data.get("vector_result")
    }


def synthesizer_node(state: GraphState) -> Dict[str, Any]:
    """Synthesizes structured graph results and unstructured vector matches into a clear answer with citations."""
    question = state["question"]
    cypher_query = state.get("cypher_query", "N/A")
    cypher_res = json.dumps(state.get("cypher_result", []), indent=2)
    vector_res = json.dumps(state.get("vector_result", []), indent=2)

    def has_error(results: Optional[List[Dict[str, Any]]]) -> bool:
        return bool(results) and all("error" in row for row in results)

    cypher_failed = has_error(state.get("cypher_result"))
    vector_failed = has_error(state.get("vector_result"))
    if cypher_failed and (state.get("vector_result") is None or vector_failed):
        return {
            "final_answer": (
                "I can't determine a match because the knowledge graph is currently "
                "unavailable. Start Neo4j and verify the connection settings, then try again."
            ),
            "sources": ["Neo4j connection unavailable"]
        }

    system_prompt = """You are an Enterprise AI Brain & Matchmaker.
    Synthesize facts from the Knowledge Graph query and Document/Vector search into a clear, direct, professional answer.

    Guidelines:
    - Directly answer the question in sentence 1.
    - Highlight specific people, projects, skills, and clients discovered.
    - Include a clear 'Sources & Citations' section explicitly naming matched projects, clients, or nodes.
    - If no relevant match is found, state that clearly without guessing.
    """

    user_content = f"""User Question: {question}
    Route Taken: {state.get('route')}
    Executed Cypher: {cypher_query}
    
    Structured Graph Result:
    {cypher_res}

    Unstructured Vector Match Result:
    {vector_res}
    """

    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_content)])
    
    sources = []
    if state.get("cypher_result"):
        for row in state["cypher_result"]:
            for v in row.values():
                if isinstance(v, str) and v not in sources and len(v) < 60:
                    sources.append(v)
    if state.get("vector_result"):
        for row in state["vector_result"]:
            pname = row.get("project_name")
            cname = row.get("client_name")
            if pname and pname not in sources:
                sources.append(f"Project: {pname}")
            if cname and cname not in sources:
                sources.append(f"Client: {cname}")

    return {
        "final_answer": response.content,
        "sources": sources
    }


def route_decision_edge(state: GraphState) -> str:
    route = state.get("route", "hybrid")
    if route == "structured":
        return "cypher_node"
    elif route == "unstructured":
        return "vector_node"
    else:
        return "hybrid_node"


builder = StateGraph(GraphState)

builder.add_node("router_node", router_node)
builder.add_node("cypher_node", cypher_generator_node)
builder.add_node("vector_node", vector_search_node)
builder.add_node("hybrid_node", hybrid_search_node)
builder.add_node("synthesizer_node", synthesizer_node)


builder.add_edge(START, "router_node")
builder.add_conditional_edges(
    "router_node",
    route_decision_edge,
    {
        "cypher_node": "cypher_node",
        "vector_node": "vector_node",
        "hybrid_node": "hybrid_node"
    }
)
builder.add_edge("cypher_node", "synthesizer_node")
builder.add_edge("vector_node", "synthesizer_node")
builder.add_edge("hybrid_node", "synthesizer_node")
builder.add_edge("synthesizer_node", END)

agent_graph = builder.compile()
