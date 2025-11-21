import pytest
import json
from pathlib import Path
from cryptography.fernet import Fernet
from src.email_receiver.token_manager import TokenManager

@pytest.fixture
def temp_token_file(tmp_path):
    return tmp_path / "token.json"

@pytest.fixture
def encryption_key():
    return Fernet.generate_key().decode()

def test_save_and_load_encrypted_token(temp_token_file, encryption_key):
    manager = TokenManager(temp_token_file, encryption_key)
    token_data = {"access_token": "foo", "refresh_token": "bar"}
    
    manager.save_token(token_data)
    
    assert temp_token_file.exists()
    # Verify it's not plain text
    content = temp_token_file.read_bytes()
    assert b"access_token" not in content
    
    loaded_data = manager.load_token()
    assert loaded_data == token_data

def test_save_and_load_unencrypted_token(temp_token_file):
    manager = TokenManager(temp_token_file, encryption_key=None)
    token_data = {"access_token": "foo", "refresh_token": "bar"}
    
    manager.save_token(token_data)
    
    assert temp_token_file.exists()
    # Verify it IS plain text
    content = temp_token_file.read_text()
    assert "access_token" in content
    
    loaded_data = manager.load_token()
    assert loaded_data == token_data

def test_load_fallback_migration(temp_token_file, encryption_key):
    # Save as plain text first
    token_data = {"access_token": "foo", "refresh_token": "bar"}
    temp_token_file.write_text(json.dumps(token_data))
    
    # Try to load with encryption enabled
    manager = TokenManager(temp_token_file, encryption_key)
    loaded_data = manager.load_token()
    
    # Should fallback to plain text read
    assert loaded_data == token_data
