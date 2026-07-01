"""
Step 2 — runtime verification of the Cognee 1.2 API surface.

Purpose: confirm (or refute) the API assumptions recorded in ARCHITECTURE.md
§2.4/§4/§6 by introspecting the *installed* package. Requires NO LLM key —
pure introspection. Any discrepancy is printed so it can be documented before
the spike is written.

Run:  prototype/.venv/Scripts/python.exe prototype/memory_core_spike/_verify_api.py
"""
import inspect


def show(title):
    print("\n" + "=" * 70 + f"\n{title}\n" + "=" * 70)


def sig(fn):
    try:
        return str(inspect.signature(fn))
    except (TypeError, ValueError):
        return "<no signature>"


def main():
    import cognee

    show("VERSION & TOP-LEVEL SYMBOLS")
    print("cognee.__version__ =", getattr(cognee, "__version__", "<unknown>"))
    top = [n for n in dir(cognee) if not n.startswith("_")]
    print("public symbols:", ", ".join(sorted(top)))

    show("CORE CALLABLES — signatures")
    for name in ["add", "cognify", "search", "memify", "update", "prune"]:
        obj = getattr(cognee, name, None)
        if obj is None:
            print(f"  {name:10} -> MISSING")
        elif callable(obj):
            print(f"  {name:10} -> {sig(obj)}")
        else:
            # e.g. prune is a module/object with methods
            methods = [m for m in dir(obj) if not m.startswith("_")]
            print(f"  {name:10} -> (object) methods: {methods}")

    show("cognify PARAMETERS (checking ontology_file_path / custom_prompt)")
    try:
        params = inspect.signature(cognee.cognify).parameters
        print("  params:", list(params))
        for key in ["ontology_file_path", "custom_prompt", "graph_model", "datasets", "chunk_size"]:
            print(f"  has '{key}':", key in params)
    except Exception as e:
        print("  could not introspect cognify:", e)

    show("add PARAMETERS (checking node_set / dataset_name)")
    try:
        params = inspect.signature(cognee.add).parameters
        print("  params:", list(params))
        for key in ["node_set", "dataset_name", "datasets"]:
            print(f"  has '{key}':", key in params)
    except Exception as e:
        print("  could not introspect add:", e)

    show("search PARAMETERS (checking node_name / only_context / top_k)")
    try:
        params = inspect.signature(cognee.search).parameters
        print("  params:", list(params))
        for key in ["query_text", "query_type", "node_name", "only_context", "top_k", "datasets"]:
            print(f"  has '{key}':", key in params)
    except Exception as e:
        print("  could not introspect search:", e)

    show("SearchType MEMBERS (is INSIGHTS gone? is GRAPH_COMPLETION/CYPHER present?)")
    try:
        from cognee import SearchType
        members = [m for m in dir(SearchType) if not m.startswith("_")]
        print("  members:", members)
        for key in ["INSIGHTS", "GRAPH_COMPLETION", "CYPHER", "TRIPLET_COMPLETION", "RAG_COMPLETION"]:
            print(f"  has {key}:", hasattr(SearchType, key))
    except Exception as e:
        print("  could not import SearchType:", e)

    show("DELETE / DATASET LIFECYCLE (forget mechanism)")
    for path in ["delete", "datasets", "prune"]:
        obj = getattr(cognee, path, None)
        if obj is None:
            print(f"  cognee.{path} -> MISSING")
        elif callable(obj):
            print(f"  cognee.{path} -> callable {sig(obj)}")
        else:
            print(f"  cognee.{path} -> methods: {[m for m in dir(obj) if not m.startswith('_')]}")

    show("DataPoint IMPORT (fallback edge-writing mechanism)")
    try:
        from cognee.infrastructure.engine import DataPoint
        print("  DataPoint OK:", DataPoint)
    except Exception as e:
        print("  DataPoint import failed:", e)
    try:
        from cognee.tasks.storage import add_data_points
        print("  add_data_points OK:", sig(add_data_points))
    except Exception as e:
        print("  add_data_points import failed:", e)

    show("GRAPH RETRIEVAL / VISUALIZATION helpers")
    for name in ["visualize_graph", "start_visualization_server", "get_graph_data"]:
        obj = getattr(cognee, name, None)
        print(f"  cognee.{name}:", "present" if obj else "MISSING")
    # low-level graph engine (for deterministic traversal / evidence subgraph)
    try:
        from cognee.infrastructure.databases.graph import get_graph_engine
        print("  get_graph_engine OK:", get_graph_engine)
    except Exception as e:
        print("  get_graph_engine import failed:", e)

    print("\n[done] API verification complete.")


if __name__ == "__main__":
    main()
