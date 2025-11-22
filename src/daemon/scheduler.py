import asyncio
import logging
import signal
from datetime import datetime, timedelta
from typing import Callable, Any, Awaitable

logger = logging.getLogger(__name__)

class Scheduler:
    """
    Handles scheduling of periodic tasks and graceful shutdown (Async).
    """
    def __init__(self, interval_seconds: int):
        self.interval = timedelta(seconds=interval_seconds)
        self.running = False
        self._shutdown_requested = False
        self._shutdown_event = asyncio.Event()
        
        # Register signal handlers (requires main thread)
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except ValueError:
            # Not in main thread, ignore signal handling
            logger.warning("Scheduler not running in main thread, signal handling disabled")

    def _handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}, scheduling shutdown...")
        self._shutdown_requested = True
        self.running = False
        # We can't set async event from signal handler directly reliably in all loops, 
        # but we can set the flag. The loop checks the flag.

    async def run_loop_async(self, task: Callable[[], Awaitable[Any]]):
        """
        Runs the given async task periodically until shutdown is requested.
        """
        self.running = True
        logger.info(f"Starting async scheduler with interval {self.interval}")

        while self.running and not self._shutdown_requested:
            start_time = datetime.now()
            try:
                logger.info("Executing scheduled task...")
                await task()
            except asyncio.CancelledError:
                logger.info("Task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduled task: {e}", exc_info=True)
            
            if self._shutdown_requested:
                break

            # Calculate sleep time
            elapsed = datetime.now() - start_time
            sleep_seconds = (self.interval - elapsed).total_seconds()
            
            # Sleep in 1-second chunks to remain responsive to shutdown signals
            while sleep_seconds > 0 and not self._shutdown_requested:
                chunk = min(1.0, sleep_seconds)
                try:
                    await asyncio.sleep(chunk)
                    sleep_seconds -= chunk
                except asyncio.CancelledError:
                    break
        
        logger.info("Scheduler stopped")

