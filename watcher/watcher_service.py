import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .collector import Collector

class GraphUpdateHandler(FileSystemEventHandler):
    def __init__(self, collector: Collector):
        self.collector = collector

    def _should_ignore(self, path):
        # Normalize path
        path = os.path.normpath(path)
        # Check against collector's ignore list
        for ignore_dir in self.collector.ignore_dirs:
            if ignore_dir in path.split(os.sep):
                return True
        return False

    def on_modified(self, event):
        if event.is_directory:
            return
        
        if self._should_ignore(event.src_path):
            return

        print(f"File modified: {event.src_path}")
        try:
            self.collector.process_file(event.src_path)
        except Exception as e:
            print(f"Error processing {event.src_path}: {e}")

    def on_created(self, event):
        if event.is_directory:
            return
            
        if self._should_ignore(event.src_path):
            return
            
        print(f"File created: {event.src_path}")
        try:
            self.collector.process_file(event.src_path)
        except Exception as e:
            print(f"Error processing {event.src_path}: {e}")

class WatcherService:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.collector = Collector()
        # Initialize full graph on start
        print(f"Initializing graph for {root_path}...")
        self.collector.collect_all(root_path)
        print(f"Graph initialized with {len(self.collector.get_graph().nodes)} nodes.")
        
        self.event_handler = GraphUpdateHandler(self.collector)
        self.observer = Observer()

    def start(self):
        self.observer.schedule(self.event_handler, self.root_path, recursive=True)
        self.observer.start()
        print(f"Watcher started on {self.root_path}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.observer.stop()
        self.observer.join()
        print("Watcher stopped.")

if __name__ == "__main__":
    # Test run
    service = WatcherService(os.getcwd())
    service.start()
