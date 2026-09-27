# Enterprise-Knowledge-Discovery
<img width="1521" height="780" alt="image" src="https://github.com/user-attachments/assets/d5e8c2f8-38d9-4c38-aca8-857723736434" />
<img width="1402" height="566" alt="image" src="https://github.com/user-attachments/assets/77ec9cef-3e59-448b-b878-e7f6b5df8d17" />
# 🔍 Enterprise Knowledge Discovery System

An enterprise-grade **Graph-RAG and Multi-Agent Knowledge Discovery System** built with **Neo4j**, **LangGraph**, **FastAPI**, and **Streamlit**. 

This application breaks down data silos by dynamically routing queries across structured relational knowledge graphs (Cypher) and unstructured document vector spaces, providing fully transparent, verifiable answers with exact execution trails.

---

## 📸 Overview

Standard Retrieval-Augmented Generation (RAG) struggles with complex, multi-hop relational questions (e.g., *"Which consultants with Kubernetes experience worked on projects for Financial Services clients?"*). 

This system solves that by integrating **Graph-RAG**:
1. **Knowledge Graph (Neo4j)** models nodes and relationships across Consultants, Skills, Projects, and Clients.
2. **Autonomous Agent Router (LangGraph)** classifies incoming queries and executes the optimal retrieval path (**Structured/Cypher**, **Unstructured/Vector**, or **Hybrid**).
3. **Execution Transparency UI (Streamlit)** exposes the exact Cypher queries executed, raw graph JSON, retrieved vector chunks, and health diagnostics in real time.

---

## ✨ Key Features

- **🔀 Tri-Mode Dynamic Query Routing:** Autonomous classification into `STRUCTURED`, `UNSTRUCTURED`, or `HYBRID` paths using LangGraph state graphs.
- **🕸️ Schema-Constrained Cypher Generation:** Pydantic-validated graph query construction to ensure syntax compliance with Neo4j.
- **⚡ FastAPI REST Backend:** Asynchronous microservice engine providing structured query endpoints and automated database health checks (`/health`).
- **🔍 Deep Inspection Dashboard:** Streamlit UI featuring expandable inspection panels for executed Cypher statements, raw Neo4j JSON responses, and vector similarity matches.
- **🟢 Real-Time Diagnostics:** Built-in connection testing and ping verification for both FastAPI and Neo4j instances prior to query execution.

---

## 🏗️ System Architecture
┌─────────────────────────┐
                   │  Streamlit Frontend UI  │
                   └────────────┬────────────┘
                                │ HTTP Requests
                                ▼
                   ┌─────────────────────────┐
                   │   FastAPI REST Engine   │
                   └────────────┬────────────┘
                                │ Invokes Graph
                                ▼
                   ┌─────────────────────────┐
                   │  LangGraph Router Agent │
                   └─────┬───────────┬───────┘
                         │           │
       ┌─────────────────┘           └─────────────────┐
       ▼                                               ▼
