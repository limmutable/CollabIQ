import asyncio
import logging
import signal
from datetime import datetime, timedelta, time, UTC
from typing import Callable, Any, Awaitable, Optional

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo  # type: ignore

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

    def should_run_daily_task(
        self,
        target_time: str,
        timezone_str: str,
        last_run: Optional[datetime] = None,
    ) -> bool:
        """
        Check if a daily task should run based on target time and last run.

        Args:
            target_time: Target time in HH:MM format (24-hour)
            timezone_str: IANA timezone string (e.g., 'Asia/Seoul')
            last_run: Last time the task was run (UTC)

        Returns:
            True if the task should run, False otherwise
        """
        try:
            tz = zoneinfo.ZoneInfo(timezone_str)
        except Exception as e:
            logger.warning(f"Invalid timezone {timezone_str}, defaulting to UTC: {e}")
            tz = UTC

        # Parse target time
        try:
            hour, minute = map(int, target_time.split(":"))
            target = time(hour=hour, minute=minute)
        except (ValueError, AttributeError):
            logger.error(f"Invalid target time format: {target_time}")
            return False

        # Get current time in target timezone
        now_utc = datetime.now(UTC)
        now_local = now_utc.astimezone(tz)
        current_time = now_local.time()

        # Check if we're within the target window (within 15 minutes after target)
        target_dt = datetime.combine(now_local.date(), target)
        target_dt = target_dt.replace(tzinfo=tz)

        # Task should run if:
        # 1. Current time is after target time
        # 2. Current time is within 15 minutes of target time
        # 3. Task hasn't run today (or last_run is None)

        if current_time < target:
            return False

        # Check if within 15-minute window
        window_end = target_dt + timedelta(minutes=15)
        if now_local > window_end:
            return False

        # Check if already run today
        if last_run:
            last_run_local = last_run.astimezone(tz) if last_run.tzinfo else last_run.replace(tzinfo=UTC).astimezone(tz)
            if last_run_local.date() == now_local.date():
                return False

        logger.info(
            f"Daily task should run: target={target_time}, "
            f"current={current_time.strftime('%H:%M')}, tz={timezone_str}"
        )
        return True

    def get_next_daily_run(
        self,
        target_time: str,
        timezone_str: str,
    ) -> datetime:
        """
        Calculate the next scheduled run time.

        Args:
            target_time: Target time in HH:MM format (24-hour)
            timezone_str: IANA timezone string (e.g., 'Asia/Seoul')

        Returns:
            Next scheduled run time in UTC
        """
        try:
            tz = zoneinfo.ZoneInfo(timezone_str)
        except Exception:
            tz = UTC

        # Parse target time
        hour, minute = map(int, target_time.split(":"))
        target = time(hour=hour, minute=minute)

        # Get current time in target timezone
        now_utc = datetime.now(UTC)
        now_local = now_utc.astimezone(tz)

        # Calculate next run
        next_run_local = datetime.combine(now_local.date(), target)
        next_run_local = next_run_local.replace(tzinfo=tz)

        # If target time has passed today, schedule for tomorrow
        if now_local.time() >= target:
            next_run_local += timedelta(days=1)

        # Convert to UTC
        return next_run_local.astimezone(UTC)

