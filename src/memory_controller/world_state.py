#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
World State Manager

This module maintains a shared representation of the current state across
all LLM contexts, enabling coordinated multi-agent behavior.
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any

from config.settings import AppSettings
from memory_controller.short_term import ShortTermMemoryManager

logger = logging.getLogger(__name__)

class WorldStateManager:
    """Manages the shared world state across LLM contexts."""
    
    def __init__(self, settings: AppSettings, stm_manager: ShortTermMemoryManager):
        """Initialize the World State Manager.
        
        Args:
            settings: Application settings
            stm_manager: Short-Term Memory Manager
        """
        self.settings = settings
        self.stm_manager = stm_manager
        self.world_state_key = "world_state"
        self.state_history_key = "world_state_history"
        self.max_history_length = 100  # Maximum number of versions to keep
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get the current world state.
        
        Returns:
            The current world state
        """
        # Get the world state from short-term memory
        state = self.stm_manager.get(self.world_state_key)
        
        if not state:
            # Initialize world state if it doesn't exist
            state = {
                "_id": self.world_state_key,
                "version": 1,
                "state": {},
                "updated_at": time.time()
            }
            self.stm_manager.create(state, ttl=None)  # No expiration for world state
        
        return state
    
    def update_state(self, updates: Dict[str, Any]) -> int:
        """Update the world state.
        
        Args:
            updates: The updates to apply to the state
            
        Returns:
            The new version number
        """
        # Get the current state
        current_state = self.get_current_state()
        
        # Create a new version
        new_version = current_state.get("version", 0) + 1
        state_data = current_state.get("state", {})
        
        # Apply updates
        state_data.update(updates)
        
        # Create the updated state
        updated_state = {
            "_id": self.world_state_key,
            "version": new_version,
            "state": state_data,
            "previous_version": current_state.get("version"),
            "updated_at": time.time()
        }
        
        # Save to history before updating
        self._save_to_history(current_state)
        
        # Update the world state
        self.stm_manager.update(self.world_state_key, updated_state)
        
        logger.debug(f"Updated world state to version {new_version}")
        return new_version
    
    def _save_to_history(self, state: Dict[str, Any]):
        """Save a version of the world state to history.
        
        Args:
            state: The state to save
        """
        # Get the current history
        history = self.stm_manager.get(self.state_history_key)
        
        if not history:
            # Initialize history if it doesn't exist
            history = {
                "_id": self.state_history_key,
                "versions": []
            }
            self.stm_manager.create(history, ttl=None)  # No expiration for history
        
        # Add the current state to history
        versions = history.get("versions", [])
        versions.append({
            "version": state.get("version"),
            "state": state.get("state", {}),
            "timestamp": state.get("updated_at", time.time())
        })
        
        # Limit the history length
        if len(versions) > self.max_history_length:
            versions = versions[-self.max_history_length:]
        
        # Update the history
        self.stm_manager.update(self.state_history_key, {"versions": versions})
    
    def get_state_version(self, version: int) -> Optional[Dict[str, Any]]:
        """Get a specific version of the world state.
        
        Args:
            version: The version number to retrieve
            
        Returns:
            The requested state version or None if not found
        """
        # Check if it's the current version
        current_state = self.get_current_state()
        if current_state.get("version") == version:
            return current_state
        
        # Get from history
        history = self.stm_manager.get(self.state_history_key)
        if not history:
            return None
        
        # Find the requested version
        for v in history.get("versions", []):
            if v.get("version") == version:
                return {
                    "version": v.get("version"),
                    "state": v.get("state", {}),
                    "updated_at": v.get("timestamp")
                }
        
        return None
    
    def rollback_to_version(self, version: int) -> bool:
        """Rollback the world state to a specific version.
        
        Args:
            version: The version number to rollback to
            
        Returns:
            True if the rollback was successful, False otherwise
        """
        # Get the requested version
        target_state = self.get_state_version(version)
        
        if not target_state:
            logger.warning(f"Cannot rollback: Version {version} not found")
            return False
        
        # Create a new version based on the target state
        current_state = self.get_current_state()
        new_version = current_state.get("version", 0) + 1
        
        updated_state = {
            "_id": self.world_state_key,
            "version": new_version,
            "state": target_state.get("state", {}),
            "previous_version": current_state.get("version"),
            "rolled_back_from": current_state.get("version"),
            "rolled_back_to": version,
            "updated_at": time.time()
        }
        
        # Save current state to history before updating
        self._save_to_history(current_state)
        
        # Update the world state
        self.stm_manager.update(self.world_state_key, updated_state)
        
        logger.info(f"Rolled back world state from version {current_state.get('version')} to {version} (new version: {new_version})")
        return True
