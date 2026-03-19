from dataclasses import dataclass, field
from typing import List, Dict, Any
from enum import Enum, auto

class NodeType(Enum):
    FILE = auto()
    DIRECTORY = auto()
    CLASS = auto()
    FUNCTION = auto()
    VARIABLE = auto()
    IMPORT = auto()
    MODULE = auto()
    AUTHOR = auto()
    COMMIT = auto()
    SNAPSHOT = auto()  # Local history snapshot

class EdgeType(Enum):
    CONTAINS = auto()       # Directory -> File
    DEFINES = auto()        # File -> Class/Func
    IMPORTS = auto()        # File -> Module
    INHERITS = auto()       # Class -> Class
    CALLS = auto()          # Func -> Func (Runtime/Static analysis)
    INSTANTIATES = auto()   # Func -> Class
    REFERENCES = auto()     # Any -> Any
    MODIFIED_BY = auto()    # File -> Author
    COMMITTED = auto()      # Author -> Commit
    AFFECTS = auto()        # Commit -> File

@dataclass
class Node:
    id: str  # Unique identifier (e.g., file path, fully qualified symbol name)
    type: NodeType
    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)

@dataclass
class Edge:
    source_id: str
    target_id: str
    type: EdgeType
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class KnowledgeGraph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    def add_node(self, node: Node):
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge):
        self.edges.append(edge)
    
    def get_subgraph(self, node_id: str):
        # Placeholder for query logic
        pass

    def get_children(self, node_id: str) -> List[Any]:
        """Returns list of nodes that this node influences (outgoing edges)."""
        children = []
        for edge in self.edges:
            if edge.source_id == node_id:
                child = self.nodes.get(edge.target_id)
                if child:
                    children.append((child, edge.type))
        return children

    def get_parents(self, node_id: str) -> List[Any]:
        """Returns list of nodes that influence this node (incoming edges)."""
        parents = []
        for edge in self.edges:
            if edge.target_id == node_id:
                parent = self.nodes.get(edge.source_id)
                if parent:
                    parents.append((parent, edge.type))
        return parents
