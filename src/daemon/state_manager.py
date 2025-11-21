import json
import logging
from pathlib import Path
from typing import Optional
from models.daemon_state import DaemonProcessState

logger = logging.getLogger(__name__)

class StateManager:
    """
    Manages the state of the daemon process using a JSON file.
    """
    def __init__(self, state_file_path: Path):
        self.state_file_path = state_file_path
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> DaemonProcessState:
        """
        Loads the daemon state from file. If not found, returns default state.
        """
        if not self.state_file_path.exists():
            return DaemonProcessState()

        try:
            with open(self.state_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DaemonProcessState(**data)
        except Exception as e:
            logger.error(f"Failed to load daemon state: {e}")
            return DaemonProcessState()

    def save_state(self, state: DaemonProcessState):
        """
        Saves the daemon state to file atomically.
        """
        try:
            temp_path = self.state_file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))
            temp_path.replace(self.state_file_path)
        except Exception as e:
            logger.error(f"Failed to save daemon state: {e}")
