import argparse
import os
import sys
from typing import List

# Ensure watcher can be imported if run directly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from watcher.collector import Collector
from watcher.schema import Node, Edge, NodeType, EdgeType

def find_node(graph, name: str) -> List[Node]:
    """Finds nodes by name (partial match support could be added)."""
    matches = []
    for node in graph.nodes.values():
        if node.name == name:
            matches.append(node)
        elif node.name.endswith(f".{name}"): # Match short name if fully qualified
             matches.append(node)
    return matches

def trace_usage(graph, node: Node):
    """Traces where a node is defined, used, or calls."""
    node_id = node.id
    
    # 1. Defined In (Incoming DEFINES edge)
    defined_in = []
    for edge in graph.edges:
        if edge.target_id == node_id and edge.type == EdgeType.DEFINES:
            source = graph.nodes.get(edge.source_id)
            if source: defined_in.append(source)

    # 2. Used By (Incoming CALLS/IMPORTS/REFERENCES edges)
    # Note: 'source' calls 'target' (node_id)
    used_by = []
    for edge in graph.edges:
        if edge.target_id == node_id and edge.type in {EdgeType.CALLS, EdgeType.IMPORTS, EdgeType.REFERENCES, EdgeType.INSTANTIATES}:
            source = graph.nodes.get(edge.source_id)
            if source: used_by.append(source)
            
    # 3. Uses (Outgoing CALLS/IMPORTS edges)
    # Note: 'source' (node_id) calls 'target'
    uses = []
    for edge in graph.edges:
        if edge.source_id == node_id and edge.type in {EdgeType.CALLS, EdgeType.IMPORTS, EdgeType.REFERENCES, EdgeType.INSTANTIATES}:
            target = graph.nodes.get(edge.target_id)
            if target: uses.append(target)

    return defined_in, used_by, uses

def command_where(name: str, root_path: str):
    print(f"Scanning {root_path}...")
    collector = Collector()
    collector.collect_all(root_path)
    graph = collector.get_graph()
    
    print(f"Searching for '{name}' in {len(graph.nodes)} nodes...")
    matches = find_node(graph, name)
    
    if not matches:
        print(f"No symbol found matching '{name}'.")
        return

    for i, node in enumerate(matches):
        print(f"\n--- Result {i+1}: {node.name} ({node.type.name}) ---")
        defined_in, used_by, uses = trace_usage(graph, node)
        
        if defined_in:
            print("  Defined in:")
            for p in defined_in:
                print(f"    - {p.name} ({p.type.name})")
        else:
             pass
        
        if used_by:
            print("  Used by:")
            for u in used_by:
                print(f"    - {u.name} ({u.type.name})")
                
        if uses:
            print("  Uses / Calls:")
            for u in uses:
                print(f"    - {u.name} ({u.type.name})")

def command_stats(root_path: str):
    print(f"Scanning {root_path}...")
    collector = Collector()
    collector.collect_all(root_path)
    graph = collector.get_graph()
    
    print(f"\n--- Graph Statistics ---")
    print(f"Total Nodes: {len(graph.nodes)}")
    print(f"Total Edges: {len(graph.edges)}")
    
    # Breakdown by type
    counts = {}
    for node in graph.nodes.values():
        counts[node.type.name] = counts.get(node.type.name, 0) + 1
    
    print("\n--- Node Counts by Type ---")
    for type_name, count in sorted(counts.items()):
        print(f"{type_name}: {count}")

def command_export(root_path: str, output_file: str):
    import json
    print(f"Scanning {root_path}...")
    collector = Collector()
    collector.collect_all(root_path)
    graph = collector.get_graph()
    
    data = {
        "nodes": [],
        "edges": []
    }
    
    for node in graph.nodes.values():
        data["nodes"].append({
            "id": node.id,
            "type": node.type.name,
            "name": node.name,
            "metadata": node.metadata
        })
        
    for edge in graph.edges:
        data["edges"].append({
            "source": edge.source_id,
            "target": edge.target_id,
            "type": edge.type.name
        })
        
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Graph exported to {output_file} ({len(data['nodes'])} nodes, {len(data['edges'])} edges)")

def command_inspect(target_path: str):
    from .inspector import Inspector
    file_path = os.path.abspath(target_path)
    if not os.path.exists(file_path):
        print(f"Error: File '{target_path}' not found.")
        return

    print(f"Inspecting {target_path}...")
    inspector = Inspector()
    nodes, edges = inspector.inspect_file(file_path)
    
    print(f"\n--- Found {len(nodes)} Nodes ---")
    for node in nodes:
        print(f"[{node.type.name}] {node.name} (Line {node.metadata.get('line', '?')})")
        
    print(f"\n--- Found {len(edges)} Edges ---")
    for edge in edges:
        print(f"{edge.source_id} --[{edge.type.name}]--> {edge.target_id}")

def command_scan(root_path: str):
    print(f"Scanning {root_path}...")
    collector = Collector()
    collector.collect_all(root_path)
    graph = collector.get_graph()
    
    print("Scan complete.")
    print(f"Total Nodes: {len(graph.nodes)}")
    print(f"Total Edges: {len(graph.edges)}")

def command_ui(root_path: str):
    """Starts the Textual UI."""
    from .tui import GraphTui
    app = GraphTui(os.path.abspath(root_path))
    app.run()

def command_report(root_path: str, output_file: str = "report.md"):
    """Generates a project report."""
    from .reporter import Reporter
    
    print(f"Generating report for: {root_path}...")
    collector = Collector()
    collector.collect_all(root_path)
    
    reporter = Reporter(collector.get_graph())
    report_content = reporter.generate_report(root_path)
    
    out_path = os.path.join(root_path, output_file)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Report saved to: {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Agent803 Watcher CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # 'where' command
    where_parser = subparsers.add_parser("where", help="Find where a symbol is defined and used")
    where_parser.add_argument("name", help="Name of the file, function, or class")
    
    # 'stats' command
    subparsers.add_parser("stats", help="Show graph statistics")
    
    # 'export' command
    export_parser = subparsers.add_parser("export", help="Export graph to JSON")
    export_parser.add_argument("output", help="Output JSON file path")

    # 'inspect' command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a specific file")
    inspect_parser.add_argument("path", help="Path to the file")

    # 'scan' command
    scan_parser = subparsers.add_parser("scan", help="Scan a directory")
    scan_parser.add_argument("path", nargs="?", default=".", help="Path to scan (default: current dir)")

    # 'ui' command
    ui_parser = subparsers.add_parser("ui", help="Start the UI")
    ui_parser.add_argument("path", nargs="?", default=".", help="Path to scan (default: current dir)")

    # 'clean' command
    clean_parser = subparsers.add_parser("clean", help="Clean cache and history")
    clean_parser.add_argument("--all", action="store_true", help="Also remove local history")

    # 'report' command
    report_parser = subparsers.add_parser("report", help="Generate project report")
    report_parser.add_argument("path", nargs="?", default=".", help="Path to project (default: current dir)")
    report_parser.add_argument("--output", default="report.md", help="Output filename (default: report.md)")

    args = parser.parse_args()
    
    # Clean command
    if args.command == "clean":
        collector = Collector()
        # Default: clean cache
        if os.path.exists("knowledge_graph.json"):
            os.remove("knowledge_graph.json")
            print("Removed knowledge_graph.json")
        else:
            print("No cache found.")
            
        # Optional: clean history
        if args.all:
            import shutil
            history_dir = os.path.join(os.getcwd(), '.agent803', 'history')
            if os.path.exists(history_dir):
                shutil.rmtree(history_dir)
                print("Removed local history.")
            else:
                print("No local history found.")
        return

    # Dispatcher
    if args.command == "where":
        command_where(args.name, os.getcwd())
    elif args.command == "stats":
        command_stats(os.getcwd())
    elif args.command == "export":
        command_export(os.getcwd(), args.output)
    elif args.command == "inspect":
        command_inspect(args.path)
    elif args.command == "scan":
        command_scan(os.path.abspath(args.path))
    elif args.command == "ui":
        # Lazy import to avoid heavy dependencies if not needed
        from .tui import GraphTui
        app = GraphTui(os.path.abspath(args.path))
        app.run()
    elif args.command == "report":
        command_report(os.path.abspath(args.path), args.output)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
