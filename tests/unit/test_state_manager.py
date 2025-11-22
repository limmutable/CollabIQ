import pytest
import json
from pathlib import Path
from models.daemon_state import DaemonProcessState
from daemon.state_manager import StateManager

@pytest.fixture
def state_file(tmp_path):
    return tmp_path / "daemon_state.json"

@pytest.fixture
def state_manager(state_file):
    return StateManager(state_file)

def test_load_default_state(state_manager, state_file):
    """Test loading state when file doesn't exist returns default"""
    assert not state_file.exists()
    state = state_manager.load_state()
    assert isinstance(state, DaemonProcessState)
    assert state.current_status == "stopped"
    assert state.total_processing_cycles == 0

def test_save_and_load_state(state_manager, state_file):
    """Test saving state creates file and load reads it back"""
    state = DaemonProcessState(
        current_status="running",
        total_processing_cycles=5,
        emails_processed_count=10
    )
    state_manager.save_state(state)
    
    assert state_file.exists()
    
    loaded_state = state_manager.load_state()
    assert loaded_state.current_status == "running"
    assert loaded_state.total_processing_cycles == 5
    assert loaded_state.emails_processed_count == 10

def test_atomic_write(state_manager, state_file):
    """Test that writes are atomic (temp file moves)"""
    state = DaemonProcessState()
    
    # We can't easily interrupt the write, but we can check that the temp file is gone
    state_manager.save_state(state)
    
    temp_file = state_file.with_suffix(".tmp")
    assert not temp_file.exists()
    assert state_file.exists()

def test_load_corrupt_state(state_manager, state_file):
    """Test loading corrupt JSON returns default state"""
    state_file.write_text("{invalid_json")
    
    state = state_manager.load_state()
    # Should return default state and log error (implied)
    assert state.total_processing_cycles == 0
    assert isinstance(state, DaemonProcessState)
