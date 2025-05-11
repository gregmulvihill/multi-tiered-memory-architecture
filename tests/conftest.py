#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pytest configuration file for Multi-Tiered Memory Architecture tests.

This module sets up fixtures and configurations for testing the MTMA system.
"""

import os
import pytest
from dotenv import load_dotenv
from unittest.mock import MagicMock, patch

from config.settings import AppSettings
from memory_controller.short_term import ShortTermMemoryManager
from memory_controller.long_term import LongTermMemoryManager
from memory_controller.lifecycle import MemoryLifecycleManager
from memory_controller.world_state import WorldStateManager
from memory_controller.service import MemoryControllerService

# Load test environment variables
load_dotenv(".env.test")

@pytest.fixture
def app_settings():
    """Fixture for application settings."""
    return AppSettings(
        app_name="mtma-test",
        version="0.1.0-test",
        environment="test"
    )

@pytest.fixture
def mock_redis():
    """Fixture for a mocked Redis client."""
    mock = MagicMock()
    # Setup common Redis methods
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 0
    mock.expire.return_value = 0
    mock.scan.return_value = (0, [])
    mock.ping.return_value = True
    return mock

@pytest.fixture
def mock_mongo_collection():
    """Fixture for a mocked MongoDB collection."""
    mock = MagicMock()
    # Setup common MongoDB collection methods
    mock.find_one.return_value = None
    mock.insert_one.return_value = MagicMock(inserted_id="test_id")
    mock.update_one.return_value = MagicMock(modified_count=0)
    mock.delete_one.return_value = MagicMock(deleted_count=0)
    mock.find.return_value = MagicMock()
    mock.find.return_value.limit.return_value = []
    mock.create_index.return_value = "index_name"
    return mock

@pytest.fixture
def mock_mongo_db(mock_mongo_collection):
    """Fixture for a mocked MongoDB database."""
    mock = MagicMock()
    mock.__getitem__.return_value = mock_mongo_collection
    return mock

@pytest.fixture
def mock_neo4j_session():
    """Fixture for a mocked Neo4j session."""
    mock = MagicMock()
    mock.run.return_value = MagicMock()
    mock.__enter__.return_value = mock
    mock.__exit__.return_value = None
    return mock

@pytest.fixture
def mock_neo4j_driver(mock_neo4j_session):
    """Fixture for a mocked Neo4j driver."""
    mock = MagicMock()
    mock.session.return_value = mock_neo4j_session
    return mock

@pytest.fixture
def mock_qdrant_client():
    """Fixture for a mocked Qdrant client."""
    mock = MagicMock()
    mock.get_collections.return_value = MagicMock(collections=[])
    mock.create_collection.return_value = None
    return mock

@pytest.fixture
def stm_manager(app_settings, mock_redis):
    """Fixture for a Short-Term Memory Manager with mocked Redis."""
    with patch("memory_controller.short_term.redis.Redis", return_value=mock_redis):
        manager = ShortTermMemoryManager(app_settings)
        manager.initialize()
        yield manager

@pytest.fixture
def ltm_manager(app_settings, mock_mongo_db, mock_neo4j_driver, mock_qdrant_client):
    """Fixture for a Long-Term Memory Manager with mocked databases."""
    with patch("memory_controller.long_term.MongoClient", return_value=MagicMock(return_value=mock_mongo_db)), \
         patch("memory_controller.long_term.GraphDatabase.driver", return_value=mock_neo4j_driver), \
         patch("memory_controller.long_term.QdrantClient", return_value=mock_qdrant_client):
        manager = LongTermMemoryManager(app_settings)
        manager.mongo_db = mock_mongo_db
        manager.neo4j_driver = mock_neo4j_driver
        manager.qdrant_client = mock_qdrant_client
        yield manager

@pytest.fixture
def lifecycle_manager(app_settings, stm_manager, ltm_manager):
    """Fixture for a Memory Lifecycle Manager."""
    return MemoryLifecycleManager(app_settings, stm_manager, ltm_manager)

@pytest.fixture
def world_state_manager(app_settings, stm_manager):
    """Fixture for a World State Manager."""
    return WorldStateManager(app_settings, stm_manager)

@pytest.fixture
def memory_controller_service(app_settings, stm_manager, ltm_manager, lifecycle_manager, world_state_manager):
    """Fixture for a Memory Controller Service with mocked components."""
    with patch("memory_controller.service.ShortTermMemoryManager", return_value=stm_manager), \
         patch("memory_controller.service.LongTermMemoryManager", return_value=ltm_manager), \
         patch("memory_controller.service.MemoryLifecycleManager", return_value=lifecycle_manager), \
         patch("memory_controller.service.WorldStateManager", return_value=world_state_manager):
        service = MemoryControllerService(app_settings)
        yield service