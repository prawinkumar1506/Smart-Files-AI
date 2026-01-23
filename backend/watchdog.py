import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class BackendChangeHandler(FileSystemEventHandler):
    def __init__(self, backend_dir, restart_command):
        self.backend_dir = backend_dir
        self.restart_command = restart_command
        self.process = None
        self.last_restart = 0
        self.restart_delay = 2  # seconds

    def start_backend(self):
        """Start the backend process"""
        if self.process and self.process.poll() is None:
            logger.info("Backend is already running")
            return

        logger.info(f"Starting backend with command: {self.restart_command}")
        self.process = subprocess.Popen(
            self.restart_command,
            shell=True,
            cwd=self.backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Backend started with PID: {self.process.pid}")

    def restart_backend(self):
        """Restart the backend process"""
        current_time = time.time()
        if current_time - self.last_restart < self.restart_delay:
            logger.info(f"Skipping restart - too soon since last restart ({current_time - self.last_restart} seconds)")
            return

        self.last_restart = current_time
        logger.info("Restarting backend...")

        if self.process:
            logger.info(f"Terminating existing backend process (PID: {self.process.pid})")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Backend process did not terminate in time, killing it")
                self.process.kill()
                self.process.wait()

        self.start_backend()

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            logger.info(f"Detected change in: {event.src_path}")
            self.restart_backend()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            logger.info(f"Detected new file: {event.src_path}")
            self.restart_backend()

    def on_deleted(self, event):
        if not event.is_directory and event.src_path.endswith('.py'):
            logger.info(f"Detected deleted file: {event.src_path}")
            self.restart_backend()

def start_watchdog(backend_dir, restart_command):
    """Start the watchdog service to monitor backend files"""
    event_handler = BackendChangeHandler(backend_dir, restart_command)
    observer = Observer()
    observer.schedule(event_handler, backend_dir, recursive=True)

    # Start the backend initially
    event_handler.start_backend()

    try:
        logger.info(f"Starting watchdog to monitor {backend_dir}")
        observer.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watchdog...")
        observer.stop()
    except Exception as e:
        logger.error(f"Error in watchdog: {str(e)}")
    finally:
        observer.join()
        if event_handler.process:
            event_handler.process.terminate()

if __name__ == "__main__":
    # Get the backend directory from command line or use current directory
    backend_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))

    # Command to restart the backend
    restart_command = "python main.py"

    # Start the watchdog
    start_watchdog(backend_dir, restart_command)
