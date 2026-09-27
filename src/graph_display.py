import html
import math
from typing import Any, Dict, List, Tuple


RELATIONSHIP_KEYS = {"relationship", "rel", "type", "edge", "label"}


def _add_node(nodes: Dict[str, Dict[str, str]], node_id: Any, label: str | None = None) -> None:
    clean_id = str(node_id).strip()
    if not clean_id:
        return
    if clean_id not in nodes:
        nodes[clean_id] = {"id": clean_id, "label": (label or clean_id)[:40]}


def build_graph_data_from_cypher_result(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Convert raw Cypher rows into node and edge structures for rendering."""
    nodes: Dict[str, Dict[str, str]] = {}
    edges: List[Dict[str, str]] = []

    if not rows:
        return [], []

    for row in rows:
        if not isinstance(row, dict):
            continue

        scalar_items: List[Tuple[str, str]] = []
        for key, value in row.items():
            lower_key = key.lower()
            if lower_key in RELATIONSHIP_KEYS:
                continue
            if isinstance(value, (str, int, float, bool)):
                scalar_items.append((key, str(value)))
                _add_node(nodes, value, str(value))

        rel_value = None
        for key in ["relationship", "rel", "type", "edge", "label"]:
            if key in row:
                rel_value = str(row[key])
                break

        if row.get("source") is not None and row.get("target") is not None:
            source = str(row["source"])
            target = str(row["target"])
            _add_node(nodes, source)
            _add_node(nodes, target)
            edges.append({"source": source, "target": target, "label": rel_value or "related_to"})
            continue

        pairings = [
            ("person", "project"),
            ("consultant", "project"),
            ("consultant", "client"),
            ("person", "client"),
            ("employee", "project"),
            ("name", "project"),
            ("project", "client"),
            ("project", "person"),
            ("source", "target"),
        ]

        matched = False
        for left_key, right_key in pairings:
            if left_key in row and right_key in row:
                left_value = str(row[left_key])
                right_value = str(row[right_key])
                _add_node(nodes, left_value)
                _add_node(nodes, right_value)
                edges.append({"source": left_value, "target": right_value, "label": rel_value or f"{left_key}_to_{right_key}"})
                matched = True
                break

        if matched:
            continue

        if len(scalar_items) >= 2:
            source, target = scalar_items[0][1], scalar_items[1][1]
            if source != target:
                edges.append({"source": source, "target": target, "label": rel_value or "related_to"})

    return list(nodes.values()), edges


def render_graph_html(nodes: List[Dict[str, str]], edges: List[Dict[str, str]]) -> str:
    """Render graph data as a simple SVG graph inside Streamlit."""
    if not nodes:
        return "<div style='padding:16px; color:#666;'>No graph data available for this query.</div>"

    width = 920
    height = 540
    center_x = width / 2
    center_y = height / 2
    radius_x = 260
    radius_y = 160

    positions: Dict[str, Tuple[float, float]] = {}
    for index, node in enumerate(nodes):
        angle = (2 * math.pi * index) / max(len(nodes), 1)
        x = center_x + math.cos(angle) * radius_x
        y = center_y + math.sin(angle) * radius_y
        positions[node["id"]] = (x, y)

    edge_svg: List[str] = []
    for edge in edges:
        source = positions.get(edge["source"])
        target = positions.get(edge["target"])
        if not source or not target:
            continue
        x1, y1 = source
        x2, y2 = target
        edge_svg.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            'stroke="#6ea8fe" stroke-width="2" stroke-linecap="round" opacity="0.8" />'
        )
        label_x = (x1 + x2) / 2
        label_y = (y1 + y2) / 2
        edge_svg.append(
            f'<text x="{label_x}" y="{label_y - 8}" font-size="11" text-anchor="middle" fill="#dbeafe">'
            f'{html.escape(str(edge.get("label", "related_to"))[:18])}</text>'
        )

    node_svg: List[str] = []
    for node in nodes:
        node_id = node["id"]
        x, y = positions.get(node_id, (center_x, center_y))
        node_svg.append(
            f'<g>'
            f'<circle cx="{x}" cy="{y}" r="34" fill="#1f2937" stroke="#93c5fd" stroke-width="2" />'
            f'<text x="{x}" y="{y + 4}" text-anchor="middle" font-size="12" fill="#f8fafc" font-weight="600">'
            f'{html.escape(str(node["label"]))}</text>'
            f'</g>'
        )

    graph_svg = " ".join(edge_svg + node_svg)
    return f"""
    <div style="width:100%; overflow:auto; background:#0f172a; border:1px solid #334155; border-radius:12px; padding:12px;">
      <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#0f172a" rx="12"/>
        {graph_svg}
      </svg>
    </div>
    """
