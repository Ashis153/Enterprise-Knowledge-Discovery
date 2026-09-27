from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import agent_graph
from database import verify_connection

app = FastAPI(
    title="Enterprise Knowledge Discovery API",
    description="Multi-Agent Knowledge Graph & Vector Search System using Neo4j and LangGraph.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    question: str
    route_taken: str
    cypher_query: Optional[str] = None
    cypher_result: Optional[List[dict]] = None
    vector_result: Optional[List[dict]] = None
    answer: str
    sources: List[str]


@app.get("/health")
def health_check():
    db_ok = verify_connection()
    return {"status": "healthy", "database_connected": db_ok}


@app.post("/api/v1/query", response_model=QueryResponse)
def execute_query(payload: QueryRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    
    try:
        initial_state = {
            "question": payload.question,
            "route": "",
            "cypher_query": None,
            "cypher_result": None,
            "vector_result": None,
            "final_answer": None,
            "sources": []
        }
        
        final_state = agent_graph.invoke(initial_state)
        
        return QueryResponse(
            question=payload.question,
            route_taken=final_state.get("route", "unknown"),
            cypher_query=final_state.get("cypher_query"),
            cypher_result=final_state.get("cypher_result"),
            vector_result=final_state.get("vector_result"),
            answer=final_state.get("final_answer", "No answer generated."),
            sources=final_state.get("sources", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Execution Failure: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)