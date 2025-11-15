"""
Interrupt handling for graceful CLI shutdown.

Handles SIGINT (Ctrl+C) and SIGTERM signals to save progress
and provide resume instructions for long-running operations.
"""

import signal
import json
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from ..formatters.colors import get_console


class InterruptHandler:
    """
    Context manager for handling interrupts gracefully.

    Catches SIGINT and SIGTERM, saves state to a file,
    and provides resume instructions.

    Example:
        handler = InterruptHandler(state_file=Path("data/state.json"))

        with handler:
            for item in items:
                # ... process item
                if handler.interrupted:
                    handler.save_state({"processed": processed_ids, "pending": pending_ids})
                    console = get_console()
                    console.print("[cyan]Resume with: collabiq test e2e --resume run_id[/cyan]")
                    raise typer.Exit(1)
    """

    def __init__(self, state_file: Optional[Path] = None):
        """
        Initialize interrupt handler.

        Args:
            state_file: Path to save state on interrupt (optional)
        """
        self.state_file = state_file
        self.interrupted = False
        self._original_sigint = None
        self._original_sigterm = None

    def _handle_interrupt(self, signum: int, frame: Any) -> None:
        """Handle interrupt signal."""
        self.interrupted = True
        console = get_console()
        console.print("\n[yellow]⚠ Operation interrupted - saving progress...[/yellow]")

    def __enter__(self) -> "InterruptHandler":
        """Set up signal handlers."""
        self._original_sigint = signal.signal(signal.SIGINT, self._handle_interrupt)
        self._original_sigterm = signal.signal(signal.SIGTERM, self._handle_interrupt)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Restore original signal handlers."""
        if self._original_sigint:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm:
            signal.signal(signal.SIGTERM, self._original_sigterm)

    def save_state(self, state: Dict[str, Any]) -> None:
        """
        Save state to file for resume capability.

        Args:
            state: Dictionary of state to save
        """
        if not self.state_file:
            return

        # Ensure parent directory exists
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # Write state as JSON
        self.state_file.write_text(json.dumps(state, indent=2))
        console = get_console()
        console.print(f"[dim]State saved to: {self.state_file}[/dim]")

    def load_state(self) -> Optional[Dict[str, Any]]:
        """
        Load state from file if it exists.

        Returns:
            State dictionary or None if file doesn't exist
        """
        if not self.state_file or not self.state_file.exists():
            return None

        return json.loads(self.state_file.read_text())


def handle_interrupt(callback: Optional[Callable[[], None]] = None) -> InterruptHandler:
    """
    Create an interrupt handler with optional callback.

    Args:
        callback: Function to call on interrupt (before saving state)

    Returns:
        Configured InterruptHandler

    Example:
        def cleanup():
            console.print("Cleaning up...")

        with handle_interrupt(cleanup):
            # ... long operation
            pass
    """
    handler = InterruptHandler()

    if callback:
        # Wrap the interrupt handler to call callback first
        original_handler = handler._handle_interrupt

        def wrapped_handler(signum: int, frame: Any) -> None:
            callback()
            original_handler(signum, frame)

        handler._handle_interrupt = wrapped_handler

    return handler
