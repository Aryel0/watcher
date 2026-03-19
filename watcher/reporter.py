import os
from datetime import datetime
from .schema import NodeType, KnowledgeGraph

class Reporter:
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def generate_report(self, root_path: str) -> str:
        """Generates a Markdown report of the project."""
        
        nodes = list(self.graph.nodes.values())
        files = [n for n in nodes if n.type == NodeType.FILE]
        functions = [n for n in nodes if n.type == NodeType.FUNCTION]
        classes = [n for n in nodes if n.type == NodeType.CLASS]
        
        # 1. Overview
        project_name = os.path.basename(os.path.abspath(root_path))
        report = f"# Project Report: {project_name}\n\n"
        report += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "##  Overview\n\n"
        report += f"- **Total Nodes:** {len(nodes)}\n"
        report += f"- **Files:** {len(files)}\n"
        report += f"- **Classes:** {len(classes)}\n"
        report += f"- **Functions:** {len(functions)}\n"
        report += f"- **Total Relationships:** {len(self.graph.edges)}\n\n"

        # 2. Complexity Analysis
        report += "## Complexity Analysis (Cyclomatic Complexity)\n\n"
        
        # Filter for items with complexity
        complex_items = []
        for n in functions + classes:
            cc = n.metadata.get('complexity', 0)
            if cc > 0:
                complex_items.append((n, cc))
        
        # Sort by complexity desc
        complex_items.sort(key=lambda x: x[1], reverse=True)
        
        report += "| Name | Type | Complexity | Status |\n"
        report += "| :--- | :--- | :--- | :--- |\n"
        
        for n, cc in complex_items[:10]:
            if cc < 5: status = "GOOD"
            elif cc < 10: status = "MID"
            else: status = "BAD"
            
            # Escape pipes just in case
            name = n.name.replace("|", "\|")
            report += f"| `{name}` | {n.type.name} | {cc} | {status} |\n"
            
        if not complex_items:
            report += "*No complexity data available.*\n"
            
        report += "\n"

        # 3. Dead Code Detection
        report += "## Potential Dead Code\n\n"
        report += "> **Note:** This is a heuristic based on zero incoming edges (excluding definitions and history). It may flag entry points (main, tests) as dead.\n\n"
        
        dead_items = []
        for n in functions + classes:
            # Check usage edges
            usage_edges = [
                edge for edge in self.graph.edges 
                if (edge.target_id == n.id or edge.target_id == f"sym::{n.name}") 
                and edge.type.name not in ['DEFINES', 'AFFECTS']
            ]
            
            if not usage_edges:
                # Naive filter for tests/main
                if n.name.startswith('test_') or n.name == 'main' or 'test' in n.id.lower():
                    continue
                dead_items.append(n)
                
        if dead_items:
            report += "| Name | Type | Location |\n"
            report += "| :--- | :--- | :--- |\n"
            for n in dead_items[:20]: # Limit to 20
                path = n.metadata.get('path', n.id)
                # Try to make path relative
                try:
                    rel_path = os.path.relpath(path, root_path)
                except:
                    rel_path = path
                report += f"| `{n.name}` | {n.type.name} | `{rel_path}` |\n"
            
            if len(dead_items) > 20:
                report += f"\n*...and {len(dead_items) - 20} more.*\n"
        else:
            report += "No dead code detected!\n"

        return report
