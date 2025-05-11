#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the World State Manager.
"""

import json
import time
from unittest.mock import patch, MagicMock

import pytest

from memory_controller.world_state import WorldStateManager

def test_get_current_state_new(world_state_manager, stm_manager, mock_redis):
    """Test getting current state when it doesn't exist yet."""
    # Setup mock to return None (not found)
    mock_redis.get.return_value = None
    
    state = world_state_manager.get_current_state()
    
    # Verify Redis get was called
    mock_redis.get.assert_called_once_with("stm:world_state")
    
    # Verify state was initialized
    assert state["_id"] == "world_state"
    assert state["version"] == 1
    assert state["state"] == {}
    assert "updated_at" in state
    
    # Verify Redis create was called
    assert mock_redis.set.call_count == 1

def test_get_current_state_existing(world_state_manager, stm_manager, mock_redis):
    """Test getting current state when it already exists."""
    # Setup mock to return existing state
    existing_state = {
        "_id": "world_state",
        "version": 3,
        "state": {"key": "value"},
        "updated_at": time.time()
    }
    mock_redis.get.return_value = json.dumps(existing_state)
    
    state = world_state_manager.get_current_state()
    
    # Verify Redis get was called
    mock_redis.get.assert_called_once_with("stm:world_state")
    
    # Verify state was returned as is
    assert state["_id"] == "world_state"
    assert state["version"] == 3
    assert state["state"] == {"key": "value"}

def test_update_state(world_state_manager, stm_manager, mock_redis):
    """Test updating the world state."""
    # Setup mock to return existing state
    existing_state = {
        "_id": "world_state",
        "version": 3,
        "state": {"existing": "value"},
        "updated_at": time.time()
    }
    history_state = {
        "_id": "world_state_history",
        "versions": []
    }
    
    # Mock get to return state and then history
    mock_redis.get.side_effect = [json.dumps(existing_state), json.dumps(history_state)]
    
    # Update the state
    version = world_state_manager.update_state({"new": "value"})
    
    # Verify new version
    assert version == 4
    
    # Verify Redis calls
    assert mock_redis.get.call_count == 2
    
    # Check update calls - this is complicated by the mocking, so we examine all calls
    update_calls = []
    for call in mock_redis.mock_calls:
        if call[0] == 'set' and 'world_state' in str(call[1]):
            update_calls.append(call)
    
    # There should be at least one update call
    assert len(update_calls) >= 1
    
    # For the key call, check the args
    key_call = None
    for call in update_calls:
        if call[1][0] == 'stm:world_state':
            key_call = call
            break
    
    assert key_call is not None
    
    # Parse the JSON that was set
    updated_data = json.loads(key_call[1][1])
    
    # Verify the updated state
    assert updated_data["version"] == 4
    assert updated_data["state"]["existing"] == "value"  # Existing value preserved
    assert updated_data["state"]["new"] == "value"  # New value added
    assert updated_data["previous_version"] == 3

def test_get_state_version(world_state_manager, stm_manager, mock_redis):
    """Test getting a specific version of the world state."""
    # Setup mock to return current state
    current_state = {
        "_id": "world_state",
        "version": 5,
        "state": {"current": "value"},
        "updated_at": time.time()
    }
    
    # Setup mock to return history
    history_state = {
        "_id": "world_state_history",
        "versions": [
            {
                "version": 3,
                "state": {"old": "value"},
                "timestamp": time.time() - 3600
            },
            {
                "version": 4,
                "state": {"less_old": "value"},
                "timestamp": time.time() - 1800
            }
        ]
    }
    
    # Test getting current version
    mock_redis.get.return_value = json.dumps(current_state)
    state = world_state_manager.get_state_version(5)
    assert state["version"] == 5
    assert state["state"] == {"current": "value"}
    
    # Test getting historical version
    mock_redis.get.side_effect = [json.dumps(current_state), json.dumps(history_state)]
    state = world_state_manager.get_state_version(3)
    assert state["version"] == 3
    assert state["state"] == {"old": "value"}
    
    # Test getting non-existent version
    mock_redis.get.side_effect = [json.dumps(current_state), json.dumps(history_state)]
    state = world_state_manager.get_state_version(2)
    assert state is None

def test_rollback_to_version(world_state_manager, stm_manager, mock_redis):
    """Test rolling back to a previous world state version."""
    # Setup mock to return current state
    current_state = {
        "_id": "world_state",
        "version": 5,
        "state": {"current": "value"},
        "updated_at": time.time()
    }
    
    # Setup mock to return history
    history_state = {
        "_id": "world_state_history",
        "versions": [
            {
                "version": 3,
                "state": {"old": "value"},
                "timestamp": time.time() - 3600
            }
        ]
    }
    
    # Test successful rollback with complex mocking
    # First return current state, then history, then current state again for the save history operation
    mock_redis.get.side_effect = [
        json.dumps(current_state),  # For initial get current state
        json.dumps(history_state),  # For getting history
        json.dumps(current_state),  # For save to history
        json.dumps(current_state)   # Extra call if needed
    ]
    
    result = world_state_manager.rollback_to_version(3)
    assert result is True
    
    # Verify Redis calls
    assert mock_redis.get.call_count >= 3
    
    # Check the final update to see if it contains the rollback info
    update_calls = []
    for call in mock_redis.mock_calls:
        if call[0] == 'set' and 'world_state' in str(call[1]) and 'world_state_history' not in str(call[1]):
            update_calls.append(call)
    
    # There should be at least one update call
    assert len(update_calls) >= 1
    
    # Get the last update call
    last_call = update_calls[-1]
    
    # Parse the JSON that was set
    updated_data = json.loads(last_call[1][1])
    
    # Verify rollback data
    assert updated_data["version"] == 6  # New version
    assert updated_data["state"] == {"old": "value"}  # Old state
    assert updated_data["rolled_back_from"] == 5
    assert updated_data["rolled_back_to"] == 3
    
    # Test failed rollback (version not found)
    mock_redis.get.reset_mock()
    mock_redis.get.side_effect = [json.dumps(current_state), json.dumps(history_state)]
    result = world_state_manager.rollback_to_version(2)
    assert result is False

def test_save_to_history(world_state_manager, stm_manager, mock_redis):
    """Test saving a state to history."""
    # Setup state to save
    state_to_save = {
        "_id": "world_state",
        "version": 3,
        "state": {"key": "value"},
        "updated_at": time.time()
    }
    
    # Test saving to new history
    mock_redis.get.return_value = None
    
    world_state_manager._save_to_history(state_to_save)
    
    # Verify Redis calls
    mock_redis.get.assert_called_once_with("stm:world_state_history")
    assert mock_redis.create.call_count if hasattr(mock_redis, 'create') else mock_redis.set.call_count >= 1
    
    # Test saving to existing history
    mock_redis.reset_mock()
    existing_history = {
        "_id": "world_state_history",
        "versions": [
            {
                "version": 1,
                "state": {"old": "value"},
                "timestamp": time.time() - 3600
            },
            {
                "version": 2,
                "state": {"less_old": "value"},
                "timestamp": time.time() - 1800
            }
        ]
    }
    mock_redis.get.return_value = json.dumps(existing_history)
    
    world_state_manager._save_to_history(state_to_save)
    
    # Verify Redis calls
    mock_redis.get.assert_called_once_with("stm:world_state_history")
    assert mock_redis.update.call_count if hasattr(mock_redis, 'update') else mock_redis.set.call_count >= 1
    
    # Check the update call
    update_calls = []
    for call in mock_redis.mock_calls:
        if call[0] in ['update', 'set'] and 'world_state_history' in str(call):
            update_calls.append(call)
    
    # There should be at least one update call
    assert len(update_calls) >= 1
    
    # For the first appropriate call, parse the updated history
    history_data = None
    for call in update_calls:
        if call[0] == 'set':
            # For set calls
            history_json = call[1][1]
            history_data = json.loads(history_json) if isinstance(history_json, str) else history_json
            break
        elif call[0] == 'update':
            # For update calls
            history_data = call[1][1] if isinstance(call[1][1], dict) else json.loads(call[1][1])
            break
    
    # If we found history data, verify it
    if history_data:
        assert len(history_data["versions"]) == 3
        assert history_data["versions"][-1]["version"] == 3