#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Short-Term Memory Manager.
"""

import json
import time
import uuid
from unittest.mock import patch, MagicMock

import pytest

from memory_controller.short_term import ShortTermMemoryManager

def test_initialize(app_settings, mock_redis):
    """Test initialization of the Short-Term Memory Manager."""
    with patch("memory_controller.short_term.redis.Redis", return_value=mock_redis):
        manager = ShortTermMemoryManager(app_settings)
        manager.initialize()
        
        # Verify Redis connection was created
        mock_redis.ping.assert_called_once()

def test_create(stm_manager, mock_redis):
    """Test creation of a short-term memory."""
    memory_data = {"key": "value"}
    
    # Mock UUID generation
    test_uuid = "12345678-1234-5678-1234-567812345678"
    with patch("uuid.uuid4", return_value=uuid.UUID(test_uuid)):
        memory_id = stm_manager.create(memory_data)
        
        # Verify memory ID
        assert memory_id == test_uuid
        
        # Verify Redis set was called
        mock_redis.set.assert_called_once()
        
        # Verify saved data contains metadata
        args, kwargs = mock_redis.set.call_args
        saved_data = json.loads(args[1])
        assert saved_data["_id"] == test_uuid
        assert saved_data["key"] == "value"
        assert "_created_at" in saved_data
        assert saved_data["_access_count"] == 0

def test_get_not_found(stm_manager, mock_redis):
    """Test getting a non-existent memory."""
    # Setup mock to return None (not found)
    mock_redis.get.return_value = None
    
    result = stm_manager.get("not-found-id")
    assert result is None
    mock_redis.get.assert_called_once_with("stm:not-found-id")

def test_get_found(stm_manager, mock_redis):
    """Test getting an existing memory."""
    # Setup mock to return a memory
    test_memory = {
        "_id": "test-id",
        "key": "value",
        "_created_at": time.time(),
        "_access_count": 1
    }
    mock_redis.get.return_value = json.dumps(test_memory)
    
    result = stm_manager.get("test-id")
    assert result is not None
    assert result["_id"] == "test-id"
    assert result["key"] == "value"
    assert result["_access_count"] == 2  # Incremented
    assert "_last_accessed_at" in result
    
    # Verify Redis get and set were called
    mock_redis.get.assert_called_once_with("stm:test-id")
    mock_redis.set.assert_called_once()

def test_update(stm_manager, mock_redis):
    """Test updating a memory."""
    # Setup mock to return a memory
    test_memory = {
        "_id": "test-id",
        "key": "value",
        "_created_at": time.time()
    }
    mock_redis.get.return_value = json.dumps(test_memory)
    
    result = stm_manager.update("test-id", {"key": "new-value", "new_key": "value"})
    assert result is True
    
    # Verify Redis get and set were called
    mock_redis.get.assert_called_once_with("stm:test-id")
    mock_redis.set.assert_called_once()
    
    # Verify updated data
    args, kwargs = mock_redis.set.call_args
    updated_data = json.loads(args[1])
    assert updated_data["key"] == "new-value"
    assert updated_data["new_key"] == "value"
    assert "_updated_at" in updated_data

def test_delete(stm_manager, mock_redis):
    """Test deleting a memory."""
    # Test successful deletion
    mock_redis.delete.return_value = 1
    result = stm_manager.delete("test-id")
    assert result is True
    mock_redis.delete.assert_called_once_with("stm:test-id")
    
    # Test failed deletion (not found)
    mock_redis.delete.reset_mock()
    mock_redis.delete.return_value = 0
    result = stm_manager.delete("not-found-id")
    assert result is False
    mock_redis.delete.assert_called_once_with("stm:not-found-id")

def test_extend_ttl(stm_manager, mock_redis):
    """Test extending TTL of a memory."""
    # Test successful extension
    mock_redis.expire.return_value = 1
    result = stm_manager.extend_ttl("test-id", 3600)
    assert result is True
    mock_redis.expire.assert_called_once_with("stm:test-id", 3600)
    
    # Test failed extension (not found)
    mock_redis.expire.reset_mock()
    mock_redis.expire.return_value = 0
    result = stm_manager.extend_ttl("not-found-id", 3600)
    assert result is False
    mock_redis.expire.assert_called_once_with("stm:not-found-id", 3600)

def test_lock_memory(stm_manager, mock_redis):
    """Test locking a memory."""
    # Setup mock to return a memory
    test_memory = {
        "_id": "test-id",
        "key": "value",
        "_created_at": time.time()
    }
    mock_redis.get.return_value = json.dumps(test_memory)
    
    result = stm_manager.lock_memory("test-id")
    assert result is True
    
    # Verify Redis get and set were called
    mock_redis.get.assert_called_once_with("stm:test-id")
    mock_redis.set.assert_called_once()
    
    # Verify locked data
    args, kwargs = mock_redis.set.call_args
    locked_data = json.loads(args[1])
    assert locked_data["_locked"] is True
    assert "_locked_at" in locked_data
    
    # Verify TTL was removed
    assert kwargs.get("keepttl") is False

def test_unlock_memory(stm_manager, mock_redis):
    """Test unlocking a memory."""
    # Setup mock to return a memory
    test_memory = {
        "_id": "test-id",
        "key": "value",
        "_created_at": time.time(),
        "_locked": True,
        "_locked_at": time.time()
    }
    mock_redis.get.return_value = json.dumps(test_memory)
    
    result = stm_manager.unlock_memory("test-id", ttl=7200)
    assert result is True
    
    # Verify Redis get and set were called
    mock_redis.get.assert_called_once_with("stm:test-id")
    mock_redis.set.assert_called_once()
    
    # Verify unlocked data
    args, kwargs = mock_redis.set.call_args
    unlocked_data = json.loads(args[1])
    assert "_locked" not in unlocked_data
    assert "_locked_at" not in unlocked_data
    
    # Verify TTL was set
    assert kwargs.get("ex") == 7200

def test_search(stm_manager, mock_redis):
    """Test searching for memories."""
    # Setup mock to return some keys
    memory1 = {
        "_id": "id1",
        "category": "test",
        "value": 1
    }
    memory2 = {
        "_id": "id2",
        "category": "test",
        "value": 2
    }
    memory3 = {
        "_id": "id3",
        "category": "other",
        "value": 3
    }
    
    # Setup mock for scan and get
    mock_redis.scan.return_value = (0, ["stm:id1", "stm:id2", "stm:id3"])
    mock_redis.get.side_effect = [
        json.dumps(memory1),
        json.dumps(memory2),
        json.dumps(memory3)
    ]
    
    # Search for category=test
    results = stm_manager.search({"category": "test"})
    assert len(results) == 2
    assert results[0]["_id"] == "id1"
    assert results[1]["_id"] == "id2"
    
    # Verify Redis scan and get were called
    mock_redis.scan.assert_called_once()
    assert mock_redis.get.call_count == 3