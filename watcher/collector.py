import os
from .schema import KnowledgeGraph
from .inspector import Inspector
from .local_tracker import LocalTracker

class Collector:
    def __init__(self):
        self.graph = KnowledgeGraph()
        self.inspector = Inspector()
        self.local_tracker = LocalTracker(os.getcwd())
        self.ignore_dirs = {'.git', '__pycache__', 'venv', '.venv', 'env', 'Lib', 'Scripts', 'Include', 'node_modules', '.idea', '.vscode', '.agent803', 'site-packages', 'dist', 'build'}

    def collect_all(self, root_path: str):
        """Scans the entire directory and populates the graph."""
        # Update inspectors path if root changes
        self.local_tracker.root_path = root_path
        self.local_tracker._ensure_history_dir()
        
        for root, dirs, files in os.walk(root_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file == 'pyvenv.cfg': continue # Skip venv config
                
                file_path = os.path.join(root, file)
                self.process_file(file_path)

    def process_file(self, file_path: str):
        """Inspects a single file and adds it to the graph."""
        # 1. Static Analysis
        nodes, edges = self.inspector.inspect_file(file_path)
        
        # 3. Local History Analysis
        local_nodes, local_edges = self.local_tracker.inspect_file(file_path)
        
        all_nodes = nodes + local_nodes
        all_edges = edges + local_edges
        
        for node in all_nodes:
            self.graph.add_node(node)
        
        for edge in all_edges:
            self.graph.add_edge(edge)
            
    def get_graph(self):
        return self.graph
        
    def get_node_content(self, node) -> str:
        """Retrieves text content for a file or snapshot node."""
        if not node: return ""
        
        from .schema import NodeType
        
        if node.type == NodeType.FILE:
            try:
                with open(node.id, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
                
        elif node.type == NodeType.SNAPSHOT:
            return self.local_tracker.get_snapshot_content(node.metadata)
            
        return f"Content view not supported for {node.type.name} nodes."
    