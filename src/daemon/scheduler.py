import time
import logging
import signal
from datetime import datetime, timedelta
from typing import Callable, Any

logger = logging.getLogger(__name__)

class Scheduler:
    """
    Handles scheduling of periodic tasks and graceful shutdown.
    """
    def __init__(self, interval_seconds: int):
        self.interval = timedelta(seconds=interval_seconds)
        self.running = False
        self._shutdown_requested = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}, scheduling shutdown...")
        self._shutdown_requested = True
        self.running = False

    def run_loop(self, task: Callable[[], Any]):
        """
        Runs the given task periodically until shutdown is requested.
        """
        self.running = True
        logger.info(f"Starting scheduler with interval {self.interval}")

        while self.running and not self._shutdown_requested:
            start_time = datetime.now()
            try:
                task()
            except Exception as e:
                logger.error(f"Error in scheduled task: {e}", exc_info=True)
            
            if self._shutdown_requested:
                break

            elapsed = datetime.now() - start_time
            sleep_time = self.interval - elapsed
            
            if sleep_time.total_seconds() > 0:
                logger.debug(f"Sleeping for {sleep_time.total_seconds():.1f}s")
                time.sleep(sleep_time.total_seconds())
        
        logger.info("Scheduler stopped")
