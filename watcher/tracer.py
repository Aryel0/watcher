import sys
import threading
from typing import Callable
from .schema import KnowledgeGraph, Edge

class Tracer:
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.active = False
        self._trace_lock = threading.Lock()

    def start(self):
        """Starts tracing execution."""
        self.active = True
        sys.settrace(self._trace_func)

    def stop(self):
        """Stops tracing."""
        self.active = False
        sys.settrace(None)

    def _trace_func(self, frame, event, arg):
        if not self.active:
            return None
        
        if event == 'call':
            code = frame.f_code
            func_name = code.co_name
            filename = code.co_filename
            
            # Simple filter to avoid tracing internal python or library calls too deeply
            if 'agent803' not in filename: 
                return None

            # Create/Get Function Node
            func_id = f"{filename}::{func_name}"
            # In a real system, we'd check if node exists, or just add specific runtime metadata
            # For this MVP, we just record the call.
            
            # Identify caller
            back_frame = frame.f_back
            if back_frame:
                caller_code = back_frame.f_code
                caller_id = f"{caller_code.co_filename}::{caller_code.co_name}"
                
                # Add Call Edge: Caller -> Called
                edge = Edge(
                    source_id=caller_id,
                    target_id=func_id,
                    type=EdgeType.CALLS,
                    metadata={'dynamic': True}
                )
                with self._trace_lock:
                    self.graph.add_edge(edge)

        return self._trace_func

    def run_with_trace(self, func: Callable, *args, **kwargs):
        """Executes a function with tracing enabled."""
        self.start()
        try:
            return func(*args, **kwargs)
        finally:
            self.stop()
