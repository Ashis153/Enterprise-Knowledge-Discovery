import os

import requests
import streamlit as st
from dotenv import load_dotenv

from graph_display import build_graph_data_from_cypher_result, render_graph_html

load_dotenv()

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")

st.set_page_config(page_title="Enterprise Knowledge Discovery", page_icon=":brain:", layout="wide")
st.title("Enterprise Knowledge Discovery")
st.caption("Search your enterprise knowledge base")

with st.sidebar:
    try:
        response = requests.get(f"{FASTAPI_URL}/health", timeout=3)
        if response.status_code == 200 and response.json().get("database_connected"):
            st.success("API and Neo4j connected")
        else:
            st.warning("API is running; database is unavailable")
    except requests.RequestException:
        st.error("API backend is offline")

examples = [
    "Who on our team has built a cloud platform for a healthcare client in Europe?",
    "Which consultants have skills in Cybersecurity and EU Data Regulations?",
    "What projects were created for Bank X and who worked on them?",
    "List all consultants located in London and their active skills.",
]

selected_question = st.selectbox("Sample questions", examples)
question = st.text_input("Question", value=selected_question)

if st.button("Search", type="primary"):
    if not question.strip():
        st.warning("Enter a question.")
    else:
        try:
            with st.spinner("Searching the knowledge base..."):
                response = requests.post(
                    f"{FASTAPI_URL}/api/v1/query",
                    json={"question": question},
                    timeout=30,
                )
            if response.status_code != 200:
                st.error(f"API error ({response.status_code}): {response.text}")
            else:
                data = response.json()
                st.subheader("Answer")
                st.markdown(data.get("answer", "No answer generated."))

                cypher_result = data.get("cypher_result") or []
                if cypher_result:
                    with st.container():
                        st.subheader("Knowledge Graph")
                        nodes, edges = build_graph_data_from_cypher_result(cypher_result)
                        st.components.v1.html(render_graph_html(nodes, edges), height=600, scrolling=False)

                sources = data.get("sources", [])
                if sources:
                    st.subheader("Sources")
                    for source in sources:
                        st.markdown(f"- `{source}`")
        except requests.RequestException as error:
            st.error(f"Failed to connect to the backend: {error}")
