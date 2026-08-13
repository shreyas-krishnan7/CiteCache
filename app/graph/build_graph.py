
from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.graph.state import GraphState
from app.graph.nodes import (
    cache_lookup_node,
    route_after_cache_lookup,
    serve_cached_node,
    hybrid_retrieve_node,
    generate_node,
    verify_citations_node,
    score_confidence_node,
    cache_write_node,
    log_metrics_node,
)


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("cache_lookup", cache_lookup_node)
    graph.add_node("serve_cached", serve_cached_node)
    graph.add_node("hybrid_retrieve", hybrid_retrieve_node)
    graph.add_node("generate", generate_node)
    graph.add_node("verify_citations", verify_citations_node)
    graph.add_node("score_confidence", score_confidence_node)
    graph.add_node("cache_write", cache_write_node)
    graph.add_node("log_metrics", log_metrics_node)

    graph.set_entry_point("cache_lookup")

    graph.add_conditional_edges(
        "cache_lookup",
        route_after_cache_lookup,
        {
            "serve_cached": "serve_cached",
            "hybrid_retrieve": "hybrid_retrieve",
        },
    )

    graph.add_edge("hybrid_retrieve", "generate")
    graph.add_edge("generate", "verify_citations")
    graph.add_edge("verify_citations", "score_confidence")
    graph.add_edge("score_confidence", "cache_write")

    graph.add_edge("serve_cached", "log_metrics")
    graph.add_edge("cache_write", "log_metrics")
    graph.add_edge("log_metrics", END)

    return graph.compile()
