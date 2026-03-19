import os
import shutil
import time
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from .schema import Node, Edge, NodeType, EdgeType

class LocalTracker:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.history_dir = os.path.join(root_path, '.agent803', 'history')
        self._ensure_history_dir()

    def _ensure_history_dir(self):
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

    def _get_file_hash(self, file_path: str) -> str:
        """Returns SHA256 hash of file content."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except FileNotFoundError:
            return ""

    def snapshot_file(self, file_path: str) -> Optional[Dict]:
        """Creates a snapshot of the file if it has changed from the last snapshot."""
        if not os.path.exists(file_path):
            return None

        rel_path = os.path.relpath(file_path, self.root_path)
        file_hash = self._get_file_hash(file_path)
        timestamp = datetime.now().isoformat()
        
        # Structure: history/<path_hash>/timestamp_hash.content
        # We use hash of the path to avoid long filenames and special characters
        path_hash = hashlib.sha256(rel_path.encode('utf-8')).hexdigest()
        file_history_dir = os.path.join(self.history_dir, path_hash)
        
        if not os.path.exists(file_history_dir):
            os.makedirs(file_history_dir)
            
        # Check if content matches latest snapshot to avoid dups
        # Simple implementation: check if hash exists in folder names (not robust if reverted, but good enough)
        # Better: checking manifest. Let's just check existing files in dir.
        # Actually, let's just save every "save" event for now, or check generic "latest" pointer.
        
        # Optimization: Check if the last saved snapshot has the same hash
        snapshots = sorted([f for f in os.listdir(file_history_dir) if f.endswith('.json')])
        if snapshots:
            last_snapshot_file = os.path.join(file_history_dir, snapshots[-1])
            try:
                with open(last_snapshot_file, 'r') as f:
                    meta = json.load(f)
                    if meta.get('hash') == file_hash:
                        return None # No change
            except:
                pass

        # Create new snapshot
        snapshot_id = f"{int(time.time())}_{file_hash[:8]}"
        snapshot_content_path = os.path.join(file_history_dir, f"{snapshot_id}.content")
        snapshot_meta_path = os.path.join(file_history_dir, f"{snapshot_id}.json")
        
        # Copy content
        shutil.copy2(file_path, snapshot_content_path)
        
        # Save metadata
        metadata = {
            'id': snapshot_id,
            'file': rel_path,
            'timestamp': timestamp,
            'hash': file_hash,
            'author': os.getlogin() # Simple local author
        }
        with open(snapshot_meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return metadata

    def get_history(self, file_path: str) -> List[Dict]:
        """Returns list of snapshots for a file."""
        rel_path = os.path.relpath(file_path, self.root_path)
        path_hash = hashlib.sha256(rel_path.encode('utf-8')).hexdigest()
        file_history_dir = os.path.join(self.history_dir, path_hash)
        
        history = []
        if os.path.exists(file_history_dir):
            for f_name in sorted(os.listdir(file_history_dir)):
                if f_name.endswith('.json'):
                    meta_path = os.path.join(file_history_dir, f_name)
                    try:
                        with open(meta_path, 'r') as f:
                            history.append(json.load(f))
                    except:
                        pass
        return history

    def inspect_file(self, file_path: str) -> Tuple[List[Node], List[Edge]]:
        """Returns graph nodes/edges for local history."""
        # 1. Take a snapshot
        snap_meta = self.snapshot_file(file_path)
        
        nodes: List[Node] = []
        edges: List[Edge] = []
        
        file_id = file_path
        
        # 2. Add History Nodes
        history = self.get_history(file_path)
        for meta in history:
            snapshot_id = f"snapshot::{meta['id']}"
            
            # Snapshot Node
            snap_node = Node(
                id=snapshot_id,
                type=NodeType.SNAPSHOT,
                name=f"v{meta['id']}",
                metadata=meta
            )
            nodes.append(snap_node)
            
            # File -> Modified By -> Snapshot (Using AFFECTS for consistency with Git Commit)
            # Actually, Snapshot -> Affects -> File makes more sense like Commit -> Affects -> File
            edges.append(Edge(source_id=snapshot_id, target_id=file_id, type=EdgeType.AFFECTS))
            
            # Author -> Created -> Snapshot (Optional, using current user)
            # author_id = f"author::{meta['author']}@local"
            # edges.append(Edge(source_id=author_id, target_id=snapshot_id, type=EdgeType.COMMITTED))

        return nodes, edges

    def get_snapshot_content(self, metadata: Dict) -> str:
        """Retrieves content for a specific snapshot."""
        # Reconstruct path from metadata
        rel_path = metadata.get('file')
        snapshot_id = metadata.get('id')
        
        if not rel_path or not snapshot_id:
            return ""
            
        path_hash = hashlib.sha256(rel_path.encode('utf-8')).hexdigest()
        file_history_dir = os.path.join(self.history_dir, path_hash)
        content_path = os.path.join(file_history_dir, f"{snapshot_id}.content")
        
        if os.path.exists(content_path):
            try:
                with open(content_path, 'r', encoding='utf-8', errors='replace') as f:
                    return f.read()
            except:
                return "Error reading snapshot content."
        return "Snapshot content not found."
