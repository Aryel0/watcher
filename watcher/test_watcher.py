import os
import sys

# Ensure we can import watcher as a package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from watcher.collector import Collector
except ImportError:
    # Fallback if package import fails (e.g. if parent is not in path correctly)
    sys.path.append(current_dir)
    from collector import Collector


def main():
    print("Starting Collector Test...")
    collector = Collector()
    
    # Run slightly above watcher to capture watcher itself
    root_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning {root_dir}...")
    
    collector.collect_all(root_dir)
    
    graph = collector.get_graph()
    
    with open("test_output.txt", "w") as f:
        f.write(f"Graph Nodes: {len(graph.nodes)}\n")
        f.write(f"Graph Edges: {len(graph.edges)}\n")

        # Group by type
        node_counts = {}
        for node in graph.nodes.values():
            node_counts[node.type.name] = node_counts.get(node.type.name, 0) + 1
        
        f.write("\n--- Node Counts by Type ---\n")
        for type_name, count in node_counts.items():
            f.write(f"{type_name}: {count}\n")

        f.write("\n--- Sample Edges (First 5) ---\n")
        for i, edge in enumerate(graph.edges[:5]):
            f.write(f"{edge.source_id} --[{edge.type.name}]--> {edge.target_id}\n")
    
    print("Test complete. Results written to test_output.txt")

if __name__ == "__main__":
    main()
