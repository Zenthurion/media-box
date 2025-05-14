import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')

class RestartHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_app()

    def start_app(self):
        if self.process:
            logging.info("Stopping previous instance...")
            self.process.kill()
            self.process.wait()
        logging.info("Starting application...")
        self.process = subprocess.Popen([sys.executable, "src/main.py"],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      universal_newlines=True,
                                      bufsize=1)  # Line buffered
        
        # Start threads to read output in real-time
        def print_output(pipe, prefix=''):
            for line in pipe:
                print(f"{prefix}{line}", end='')
                
        import threading
        threading.Thread(target=print_output, args=(self.process.stdout,), daemon=True).start()
        threading.Thread(target=print_output, args=(self.process.stderr, 'ERROR: '), daemon=True).start()

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            logging.info(f"Detected change in {event.src_path}")
            self.start_app()

def main():
    logging.info("Starting development server...")
    handler = RestartHandler()
    observer = Observer()
    
    # Watch the src directory
    observer.schedule(handler, path='src', recursive=True)
    logging.info("Watching for changes in src directory...")
    
    observer.start()

    try:
        while True:
            time.sleep(1)
            # Check if the process is still running
            if handler.process and handler.process.poll() is not None:
                out, err = handler.process.communicate()
                if err:
                    logging.error(f"Application error: {err}")
                handler.start_app()
    except KeyboardInterrupt:
        logging.info("Shutting down development server...")
        observer.stop()
        if handler.process:
            handler.process.kill()
    observer.join()

if __name__ == "__main__":
    main() 