import typer
import asyncio
from daemon.controller import DaemonController

def run(
    daemon: bool = typer.Option(False, "--daemon", "-d", help="Run in daemon mode"),
    interval: int = typer.Option(15, "--interval", "-i", help="Check interval in minutes (daemon mode only)"),
):
    """
    Run the CollabIQ pipeline.
    
    By default, runs a single processing cycle.
    Use --daemon to run continuously in the background.
    """
    controller = DaemonController(interval_minutes=interval)
    if daemon:
        controller.run()
    else:
        # Process cycle is async, needs event loop
        asyncio.run(controller.process_cycle())
