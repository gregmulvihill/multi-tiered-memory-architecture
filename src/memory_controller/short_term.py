#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Short-Term Memory Manager

This module handles the storage and retrieval of short-term memories using Redis.
"""

import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union

import redis

from config.settings import AppSettings

logger = logging.getLogger(__name__)

class ShortTermMemoryManager:
    """Manages short-term memory storage and retrieval."""
    
    def __init__(self, settings: AppSettings):
        """Initialize the Short-Term Memory Manager.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.redis = None
        self.namespace = "stm:"
        self.default_ttl = settings.memory.stm_default_ttl
    
    def initialize(self):
        """Initialize the connection to Redis."""
        logger.info("Initializing Short-Term Memory Manager")
        try:
            self.redis = redis.Redis(
                host=self.settings.redis.host,
                port=self.settings.redis.port,
                db=self.settings.redis.db,
                password=self.settings.redis.password,
                ssl=self.settings.redis.ssl,
                decode_responses=True
            )
            self.redis.ping()  # Test connection
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def shutdown(self):
        """Close the connection to Redis."""
        if self.redis:
            logger.info("Shutting down Short-Term Memory Manager")
            self.redis.close()
    
    def _get_key(self, memory_id: str) -> str:
        """Generate a Redis key for a memory ID.
        
        Args:
            memory_id: The memory ID
            
        Returns:
            The Redis key
        """
        return f"{self.namespace}{memory_id}"
    
    def create(self, memory_data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """Create a new short-term memory.
        
        Args:
            memory_data: The memory data to store
            ttl: Optional time-to-live in seconds (default: use system default)
            
        Returns:
            The memory ID
        """
        # Generate a unique ID
        memory_id = str(uuid.uuid4())
        
        # Add metadata
        memory_data["_id"] = memory_id
        memory_data["_created_at"] = time.time()
        memory_data["_access_count"] = 0
        
        # Serialize the data
        data_json = json.dumps(memory_data)
        
        # Determine TTL
        if ttl is None:
            ttl = self.default_ttl
        
        # Store in Redis
        key = self._get_key(memory_id)
        self.redis.set(key, data_json, ex=ttl)
        
        logger.debug(f"Created short-term memory: {memory_id} (TTL: {ttl}s)")
        return memory_id
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a short-term memory by ID.
        
        Args:
            memory_id: The memory ID
            
        Returns:
            The memory data or None if not found
        """
        key = self._get_key(memory_id)
        data_json = self.redis.get(key)
        
        if not data_json:
            logger.debug(f"Short-term memory not found: {memory_id}")
            return None
        
        # Parse the data
        memory_data = json.loads(data_json)
        
        # Update access count
        memory_data["_access_count"] = memory_data.get("_access_count", 0) + 1
        memory_data["_last_accessed_at"] = time.time()
        
        # Update the stored data
        self.redis.set(key, json.dumps(memory_data), xx=True)
        
        logger.debug(f"Retrieved short-term memory: {memory_id} (Access count: {memory_data['_access_count']})")
        return memory_data
    
    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing short-term memory.
        
        Args:
            memory_id: The memory ID
            updates: The updates to apply
            
        Returns:
            True if the memory was updated, False if not found
        """
        key = self._get_key(memory_id)
        data_json = self.redis.get(key)
        
        if not data_json:
            logger.debug(f"Short-term memory not found for update: {memory_id}")
            return False
        
        # Parse the data
        memory_data = json.loads(data_json)
        
        # Apply updates
        memory_data.update(updates)
        memory_data["_updated_at"] = time.time()
        
        # Store the updated data
        self.redis.set(key, json.dumps(memory_data), xx=True)
        
        logger.debug(f"Updated short-term memory: {memory_id}")
        return True
    
    def delete(self, memory_id: str) -> bool:
        """Delete a short-term memory.
        
        Args:
            memory_id: The memory ID
            
        Returns:
            True if the memory was deleted, False if not found
        """
        key = self._get_key(memory_id)
        result = self.redis.delete(key)
        
        if result > 0:
            logger.debug(f"Deleted short-term memory: {memory_id}")
            return True
        else:
            logger.debug(f"Short-term memory not found for deletion: {memory_id}")
            return False
    
    def extend_ttl(self, memory_id: str, ttl: int) -> bool:
        """Extend the TTL of a short-term memory.
        
        Args:
            memory_id: The memory ID
            ttl: The new TTL in seconds
            
        Returns:
            True if the TTL was extended, False if not found
        """
        key = self._get_key(memory_id)
        result = self.redis.expire(key, ttl)
        
        if result > 0:
            logger.debug(f"Extended TTL for short-term memory: {memory_id} (TTL: {ttl}s)")
            return True
        else:
            logger.debug(f"Short-term memory not found for TTL extension: {memory_id}")
            return False
    
    def lock_memory(self, memory_id: str) -> bool:
        """Lock a memory to prevent automatic decay.
        
        Args:
            memory_id: The memory ID
            
        Returns:
            True if the memory was locked, False if not found
        """
        key = self._get_key(memory_id)
        data_json = self.redis.get(key)
        
        if not data_json:
            return False
        
        # Parse the data
        memory_data = json.loads(data_json)
        
        # Set the locked flag
        memory_data["_locked"] = True
        memory_data["_locked_at"] = time.time()
        
        # Make the memory persistent (remove TTL)
        self.redis.set(key, json.dumps(memory_data), keepttl=False)
        
        logger.debug(f"Locked short-term memory: {memory_id}")
        return True
    
    def unlock_memory(self, memory_id: str, ttl: Optional[int] = None) -> bool:
        """Unlock a memory and restore its TTL.
        
        Args:
            memory_id: The memory ID
            ttl: Optional new TTL in seconds (default: use system default)
            
        Returns:
            True if the memory was unlocked, False if not found
        """
        key = self._get_key(memory_id)
        data_json = self.redis.get(key)
        
        if not data_json:
            return False
        
        # Parse the data
        memory_data = json.loads(data_json)
        
        # Remove the locked flag
        memory_data.pop("_locked", None)
        memory_data.pop("_locked_at", None)
        
        # Determine TTL
        if ttl is None:
            ttl = self.default_ttl
        
        # Update the memory with TTL
        self.redis.set(key, json.dumps(memory_data), ex=ttl)
        
        logger.debug(f"Unlocked short-term memory: {memory_id} (TTL: {ttl}s)")
        return True
    
    def search(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Search for short-term memories matching a query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching memories
        """
        # This is a simple implementation that scans all keys
        # For production, consider using Redis search capabilities
        results = []
        cursor = 0
        pattern = f"{self.namespace}*"
        
        while True:
            cursor, keys = self.redis.scan(cursor, pattern, count=1000)
            
            for key in keys:
                data_json = self.redis.get(key)
                if data_json:
                    memory_data = json.loads(data_json)
                    
                    # Simple matching logic
                    match = True
                    for k, v in query.items():
                        if k not in memory_data or memory_data[k] != v:
                            match = False
                            break
                    
                    if match:
                        results.append(memory_data)
                        if len(results) >= limit:
                            return results
            
            if cursor == 0:
                break
        
        return results
    
    def get_all_for_consolidation(self, min_access_count: int = 0) -> List[Dict[str, Any]]:
        """Get all memories eligible for consolidation.
        
        Args:
            min_access_count: Minimum access count for eligibility
            
        Returns:
            List of eligible memories
        """
        eligible = []
        cursor = 0
        pattern = f"{self.namespace}*"
        
        while True:
            cursor, keys = self.redis.scan(cursor, pattern, count=1000)
            
            for key in keys:
                data_json = self.redis.get(key)
                if data_json:
                    memory_data = json.loads(data_json)
                    
                    # Check if eligible for consolidation
                    if not memory_data.get("_locked", False) and \
                       memory_data.get("_access_count", 0) >= min_access_count:
                        eligible.append(memory_data)
            
            if cursor == 0:
                break
        
        return eligible
