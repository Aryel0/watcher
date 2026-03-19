import os
import sys

# Ensure we can import 'watcher' package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from watcher.inspector import Inspector
from watcher.schema import NodeType

def test_inspector():
    print(f"Current Dir: {os.getcwd()}")
    try:
        inspector = Inspector()
        # Test on a known file, e.g., tui.py which we know exists
        test_file = os.path.abspath("tui.py")
        
        print(f"Testing inspector on: {test_file}")
        if not os.path.exists(test_file):
            print("File not found!")
            return

        nodes, edges = inspector.inspect_file(test_file)
        print(f"Nodes found: {len(nodes)}")
        print(f"Edges found: {len(edges)}")
        
        py_nodes = [n for n in nodes if n.type == NodeType.FILE]
        if py_nodes:
            print(f"File Node: {py_nodes[0].name}")
        else:
            print("No FILE node found!")
            
        func_nodes = [n for n in nodes if n.type == NodeType.FUNCTION]
        print(f"Function Nodes: {len(func_nodes)}")
        for f in func_nodes[:3]:
            print(f" - {f.name} (Complexity: {f.metadata.get('complexity')})")
            
    except Exception as e:
        print(f"Inspector failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_inspector()
