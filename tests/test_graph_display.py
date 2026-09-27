from graph_display import build_graph_data_from_cypher_result


def test_build_graph_data_from_cypher_result():
    rows = [
        {"person": "Alice", "project": "Project A", "relationship": "WORKED_ON"},
        {"person": "Bob", "project": "Project A", "relationship": "LED_PROJECT"},
        {"person": "Alice", "project": "Project B", "relationship": "WORKED_ON"},
    ]

    nodes, edges = build_graph_data_from_cypher_result(rows)

    node_ids = {node["id"] for node in nodes}
    assert {"Alice", "Bob", "Project A", "Project B"}.issubset(node_ids)
    assert any(edge["source"] == "Alice" and edge["target"] == "Project A" for edge in edges)
    assert any(edge["source"] == "Bob" and edge["target"] == "Project A" for edge in edges)
