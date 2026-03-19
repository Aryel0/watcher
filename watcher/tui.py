from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Label, Static, Input
from textual.containers import Horizontal, Vertical, Container
from textual.widgets.tree import TreeNode
from textual import on
from rich.markup import escape
import os
import sys

# Ensure watcher can be imported
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from watcher.collector import Collector
from watcher.schema import Node


class NodeDetails(Static):
    """Widget to display details of a selected node."""
    def update_node(self, node: Node, graph, reference_node: Node = None, collector: Collector = None):
        if not node:
            self.update("Select a node to view details.")
            return
            
        # COMPARE MODE
        if reference_node and reference_node != node:
             self.show_compare(node, reference_node, graph, collector)
             return

        # STANDARD MODE
        # Get relationships
        parents = graph.get_parents(node.id)
        children = graph.get_children(node.id)
        
        parent_text = "\n".join([f"- {n.name} [{t.name}]" for n, t in parents]) if parents else "None"
        
        # SPECIALIZED HEADER (Signatures)
        header_info = ""
        docstring = node.metadata.get('docstring')
        doc_display = f"\n[i dim]{docstring.strip().splitlines()[0]}[/i dim]\n" if docstring else ""

        # Complexity Badge
        complexity = node.metadata.get('complexity')
        comp_display = ""
        if complexity:
            if complexity < 5:
                label, color = "GOOD", "green"
            elif complexity < 10:
                label, color = "MID", "yellow"
            else:
                label, color = "BAD", "red"
            
            comp_display = f" [bold {color}][{label}][/]"

        # Dead Code Detection (Heuristic)
        usage_edges = [edge for edge in graph.edges if (edge.target_id == node.id or edge.target_id == f"sym::{node.name}") and edge.type.name not in ['DEFINES', 'AFFECTS']]
        is_dead = len(usage_edges) == 0 and node.type.name in ['FUNCTION', 'CLASS']
        if is_dead and (node.name.startswith('test_') or node.name == 'main' or 'test' in node.id.lower()):
            is_dead = False
            
        dead_display = " [bold red]UNUSED[/bold red]" if is_dead else ""

        if node.type.name == "FUNCTION":
            args = node.metadata.get('args', [])
            ret = node.metadata.get('returns')
            
            arg_str = ", ".join([f"{escape(a['name'])}: {escape(a['type'] or 'Any')}" for a in args])
            ret_str = f" -> {escape(ret)}" if ret else ""
            header_info = f"[bold yellow]def {escape(node.name)}({arg_str}){ret_str}[/bold yellow]{comp_display}{dead_display}{doc_display}\n"
            
        elif node.type.name == "CLASS":
            bases = node.metadata.get('bases', [])
            base_str = f"({', '.join([escape(b) for b in bases])})" if bases else ""
            header_info = f"[bold yellow]class {escape(node.name)}{base_str}:[/bold yellow]{comp_display}{dead_display}{doc_display}\n"

        # Specialized display for Classes (Methods)
        if node.type.name == "CLASS":
            methods = []
            influences = []
            for n, t in children:
                if t.name == "DEFINES":
                    m_args = n.metadata.get('args', [])
                    m_ret = n.metadata.get('returns')
                    m_comp = n.metadata.get('complexity', 0)
                    m_comp_str = ""
                    if m_comp > 10:
                         m_comp_str = " [bold red][BAD][/]"
                    elif m_comp > 5:
                         m_comp_str = " [bold yellow][MID][/]"
                    else:
                         m_comp_str = " [bold green][GOOD][/]"
                    
                    if m_args is not None:
                         m_arg_str = ", ".join([f"{escape(a['name'])}: {escape(a['type'] or 'Any')}" for a in m_args])
                         m_ret_str = f" -> {escape(m_ret)}" if m_ret else ""
                         methods.append(f"- [yellow]def[/yellow] {escape(n.name)}({m_arg_str}){m_ret_str}{m_comp_str}")
                    else:
                         methods.append(f"- {escape(n.name)} ({escape(n.type.name)})")
                else:
                    influences.append(f"- {escape(n.name)} [{escape(t.name)}]")
            
            child_section = ""
            if methods:
                child_section += "[bold]Methods Defined:[/bold]\n" + "\n".join(methods) + "\n\n"
            child_section += "[bold]Other Influences:[/bold]\n" + ("\n".join(influences) if influences else "None")
        if node.type.name == "FILE":
            # Show file content preview
            content = "Unable to read content."
            if collector:
                 content = collector.get_node_content(node)
            
            # Simple line preview (first 50 lines to avoid UI lag)
            lines = content.splitlines()
            preview = "\n".join(lines[:50])
            if len(lines) > 50:
                preview += f"\n\n... ({len(lines)-50} more lines. Use Compare to view full file) ..."
            
            # Escape content to prevent Textual interpreting brackets as tags
            preview = escape(preview)
            
            child_section = f"""[bold]File Content Preview:[/bold]
```python
{preview}
```
"""
            # Still show structure analysis if any
            if children:
                 # Escape node names and relation types
                 child_list = [f"- {escape(n.name)} [{escape(t.name)}]" for n, t in children]
                 child_section += "\n[bold]Definitions:[/bold]\n" + "\n".join(child_list)

        elif node.type.name == "CLASS":
            pass # Handled above, but if we drop here (logic slightly dupe in original code)
            # The original code had if FILE ... elif CLASS ... else (FUNCTION etc).
            # But above block also checked if CLASS.
            # We must preserve logic flow. The above block checked CLASS to build 'methods' list but didn't assign child_section exclusively
            # Wait, line 76 in original 'if node.type.name == "CLASS":' sets methods/influences
            # Line 100 'if node.type.name == "FILE":'
            # Line 122 'elif node.type.name == "CLASS":' -> sets child_section.
            # Safe to assume we can just use the vars computed.
            pass

        else:
             # Default fallback (FUNCTION etc)
             if node.type.name != "FILE" and node.type.name != "CLASS":
                 child_section = "[bold]Influences (Outgoing):[/bold]\n" + ("\n".join([f"- {escape(n.name)} [{escape(t.name)}]" for n, t in children]) if children else "None")
            
        # Re-construct parent text with escaping, filtering out SNAPSHOTs (too noisy)
        parents = [p for p in parents if p[0].type.name != 'SNAPSHOT']
        parent_text = "\n".join([f"- {escape(n.name)} [{escape(t.name)}]" for n, t in parents]) if parents else "None"

        details = f"""
[bold]Name:[/bold] {escape(node.name)}
[bold]Type:[/bold] {escape(node.type.name)}
[bold]ID:[/bold] {escape(node.id)}
{header_info}
[bold]Influenced By (Incoming):[/bold]
{parent_text}

{child_section}

[bold]Metadata:[/bold]
{escape(str(node.metadata))}
"""
        self.update(details)

    def show_compare(self, node, ref_node, graph, collector):
        from difflib import unified_diff
        
        header = f"[bold green]COMPARING:[/bold green]\nTarget: {node.name} ({node.type.name})\nReference: {ref_node.name} ({ref_node.type.name})\n\n"
        
        # 1. Content Diff (for Files/Snapshots)
        if collector and (node.type.name in ['FILE', 'SNAPSHOT'] and ref_node.type.name in ['FILE', 'SNAPSHOT']):
             try:
                 content_a = collector.get_node_content(ref_node).splitlines(keepends=True)
                 content_b = collector.get_node_content(node).splitlines(keepends=True)
                 
                 diff = list(unified_diff(content_a, content_b, fromfile=ref_node.name, tofile=node.name))
                 
                 if not diff:
                     body = "[i]Contents are identical.[/i]"
                 else:
                     # Simple syntax highlighting for diff (naive)
                     colored_diff = []
                     for line in diff:
                         if line.startswith('+'): colored_diff.append(f"[green]{line.rstrip()}[/green]")
                         elif line.startswith('-'): colored_diff.append(f"[red]{line.rstrip()}[/red]")
                         elif line.startswith('@@'): colored_diff.append(f"[blue]{line.rstrip()}[/blue]")
                         else: colored_diff.append(line.rstrip())
                     body = "\n".join(colored_diff)
             except Exception as e:
                 body = f"Error generating diff: {e}"
        else:
             # 2. Metadata Diff (Side-by-side)
             body = f"""
             [bold]{ref_node.name}[/bold] vs [bold]{node.name}[/bold]
             
             Type: {ref_node.type.name} | {node.type.name}
             Parents: {len(graph.get_parents(ref_node.id))} | {len(graph.get_parents(node.id))}
             Children: {len(graph.get_children(ref_node.id))} | {len(graph.get_children(node.id))}
             """
             
        self.update(header + body)

class GraphStats(Static):
    """Widget to display graph statistics."""
    def update_stats(self, graph, root_path=""):
        count = len(graph.nodes)
        cwd_name = os.path.basename(os.path.abspath(root_path))
        self.update(f"Nodes: {count} | Edges: {len(graph.edges)} | Root: {cwd_name} | {len([n for n in graph.nodes.values() if n.type.name=='FILE'])} files")

class GraphTui(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    
    #left-pane {
        width: 30%;
        height: 100%;
        border: solid green;
    }
    
    #search-box {
        dock: top;
        height: 3;
        margin: 0 1;
    }
    
    #tree-view {
        height: 1fr;
    }

    #details-view {
        width: 70%;
        height: 100%;
        border: solid blue;
    }
    
    #stats-bar {
        dock: bottom;
        height: 1;
        background: $primary;
        color: white;
    }
    """

    BINDINGS = [
        ("c", "toggle_compare", "Compare"),
        ("q", "quit", "Quit")
    ]

    def __init__(self, root_path: str):
        super().__init__()
        self.root_path = root_path
        self.collector = Collector()
        # Initialize graph
        self.collector.collect_all(root_path)
        self.graph = self.collector.get_graph()
        self.original_tree_nodes = {} # Store original structure for filtering (simplified)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Input(placeholder="Search nodes...", id="search-box"),
            Tree("Knowledge Graph", id="tree-view"),
            id="left-pane"
        )
        yield Vertical(
            Label("Node Details", classes="header"),
            NodeDetails(id="details-view"),
        )
        yield GraphStats(id="stats-bar")
        yield Footer()


    def on_mount(self) -> None:
        self.refresh_tree()
        self.query_one(GraphStats).update_stats(self.graph, self.root_path)
        self.reference_node = None # Node selected for comparison
        
        # Notification to confirm scan worked
        file_count = len([n for n in self.graph.nodes.values() if n.type.name == 'FILE'])
        self.notify(f"Scanned {len(self.graph.nodes)} nodes ({file_count} files).")

    def action_toggle_compare(self) -> None:
        """Toggle compare mode with the currently selected node."""
        tree = self.query_one(Tree)
        if not tree.cursor_line and not tree.cursor_node: 
             return
             
        # Textual simplified selection access
        if tree.cursor_node and tree.cursor_node.data:
            node_id = tree.cursor_node.data
            node = self.graph.nodes.get(node_id)
            
            if self.reference_node == node:
                 # Unset
                 self.reference_node = None
                 self.notify("Compare mode cancelled.")
            else:
                 self.reference_node = node
                 self.notify(f"Comparing against: {node.name}")
            
            # Refresh view
            if node:
                self.query_one(NodeDetails).update_node(node, self.graph, self.reference_node, self.collector)

    def refresh_tree(self, filter_text: str = ""):
        tree = self.query_one(Tree)
        tree.clear()
        
        # Set Root Label to the folder name
        root_name = os.path.basename(os.path.abspath(self.root_path))
        tree.root.label = f"[b]{root_name}/[/b]"
        tree.root.expand()
        
        from .schema import NodeType
        
        # 1. Gather all File nodes
        files = [n for n in self.graph.nodes.values() if n.type == NodeType.FILE]
        files.sort(key=lambda x: x.name)
        
        if not files:
             tree.root.add(f"[i]No files found in graph ({len(self.graph.nodes)} nodes total).[/i]")
             return
        
        # Helper to get or create directory branch
        dir_branches = {}
        
        # Robust root path usage
        abs_root = os.path.abspath(self.root_path)
        norm_root = os.path.normcase(abs_root)
        
        # Debugging: Track how many files are actually added
        added_count = 0
        
        def get_dir_branch(path):
            # Normalize inputs
            abs_path = os.path.abspath(path)
            norm_path = os.path.normcase(abs_path)
            
            # Base Case: We reached the root
            if norm_path == norm_root:
                return tree.root
            
            # Safety: If outside root
            if not norm_path.startswith(norm_root):
                return tree.root
                
            if norm_path in dir_branches:
                return dir_branches[norm_path]
            
            parent_path = os.path.dirname(abs_path)
            # Prevent infinite recursion at drive root
            if os.path.normcase(parent_path) == norm_path:
                return tree.root

            parent_branch = get_dir_branch(parent_path)
            
            dir_name = os.path.basename(abs_path)
            branch = parent_branch.add(f"[+] {dir_name}", expand=True)
            dir_branches[norm_path] = branch
            return branch

        # 2. Add Files and their content
        for file_node in files:
            # Simple filter
            if filter_text and filter_text.lower() not in file_node.name.lower():
                continue

            # Resolve path relative to root, but robustly
            f_path = file_node.metadata.get('path', file_node.id)
            f_dir = os.path.dirname(f_path)
            
            # Get branch for directory
            parent_branch = get_dir_branch(f_dir)
            
            # File Node
            file_branch = parent_branch.add(f"[F] {file_node.name}", data=file_node.id, expand=False)
            added_count += 1
            
            # 3. Add Classes and Top-level Functions
            children = self.graph.get_children(file_node.id)
            # Sort: Classes first, then functions
            children.sort(key=lambda x: (0 if x[0].type == NodeType.CLASS else 1, x[0].name))
            
            for child_node, edge_type in children:
                if edge_type.name != "DEFINES": continue
                
                if child_node.type == NodeType.CLASS:
                    class_branch = file_branch.add(f"[C] {child_node.name}", data=child_node.id)
                    
                    # 4. Add Methods
                    methods = self.graph.get_children(child_node.id)
                    methods.sort(key=lambda x: x[0].name)
                    for method_node, m_edge_type in methods:
                        if m_edge_type.name == "DEFINES":
                             class_branch.add_leaf(f"[m] {method_node.name}", data=method_node.id)
                             
                elif child_node.type == NodeType.FUNCTION:
                     file_branch.add_leaf(f"[f] {child_node.name}", data=child_node.id)

        if added_count == 0:
             if not files:
                 msg = f"[i]No files found in graph ({len(self.graph.nodes)} nodes total).[/i]"
             else:
                 sample_path = files[0].metadata.get('path', '???')
                 msg = f"[i]Graph has {len(files)} files, but none matched root.\nRoot: {self.root_path}\nSample: {sample_path}[/i]"
             
             tree.root.add(msg)

    @on(Input.Changed, "#search-box")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.refresh_tree(event.value)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        pass # Handled by highlighted for smoother experience, or keep both

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Update details when a node is highlighted (navigated to)."""
        if event.node.data:
            node_id = event.node.data
            node = self.graph.nodes.get(node_id)
            if node:
                self.query_one(NodeDetails).update_node(node, self.graph, getattr(self, 'reference_node', None), self.collector)

if __name__ == "__main__":
    app = GraphTui(os.getcwd())
    app.run()

