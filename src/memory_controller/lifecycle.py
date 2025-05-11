#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Lifecycle Manager

This module handles the transitions between memory tiers, implementing
consolidation, forgetting, and retrieval mechanisms.
"""

import logging
import time
from typing import Dict, List, Optional, Any

from config.settings import AppSettings
from memory_controller.short_term import ShortTermMemoryManager
from memory_controller.long_term import LongTermMemoryManager

logger = logging.getLogger(__name__)

class MemoryLifecycleManager:
    """Manages memory lifecycle transitions between short-term and long-term storage."""
    
    def __init__(self, 
                 settings: AppSettings,
                 stm_manager: ShortTermMemoryManager,
                 ltm_manager: LongTermMemoryManager):
        """Initialize the Memory Lifecycle Manager.
        
        Args:
            settings: Application settings
            stm_manager: Short-Term Memory Manager
            ltm_manager: Long-Term Memory Manager
        """
        self.settings = settings
        self.stm_manager = stm_manager
        self.ltm_manager = ltm_manager
        self.consolidation_threshold = settings.memory.consolidation_threshold
    
    def run_consolidation(self):
        """Run the consolidation process for eligible memories."""
        logger.info("Running memory consolidation process")
        
        # Get memories eligible for consolidation
        eligible_memories = self.stm_manager.get_all_for_consolidation(
            min_access_count=self.consolidation_threshold
        )
        
        if not eligible_memories:
            logger.info("No memories eligible for consolidation")
            return
        
        logger.info(f"Found {len(eligible_memories)} memories eligible for consolidation")
        
        # Process each eligible memory
        for memory in eligible_memories:
            try:
                self.consolidate_memory(memory)
            except Exception as e:
                logger.error(f"Error consolidating memory {memory.get('_id')}: {e}")
    
    def consolidate_memory(self, memory: Dict[str, Any]):
        """Consolidate a single memory from short-term to long-term storage.
        
        Args:
            memory: The memory data to consolidate
        """
        memory_id = memory.get("_id")
        logger.debug(f"Consolidating memory: {memory_id}")
        
        # Prepare the memory for long-term storage
        ltm_memory = self._prepare_for_long_term(memory)
        
        # Store in long-term memory
        try:
            self.ltm_manager.create(ltm_memory)
            logger.debug(f"Memory {memory_id} stored in long-term memory")
            
            # Delete from short-term memory
            self.stm_manager.delete(memory_id)
            logger.debug(f"Memory {memory_id} removed from short-term memory")
        except Exception as e:
            logger.error(f"Failed to consolidate memory {memory_id}: {e}")
            raise
    
    def _prepare_for_long_term(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a short-term memory for long-term storage.
        
        Args:
            memory: The short-term memory data
            
        Returns:
            The prepared long-term memory data
        """
        # Create a copy of the memory
        ltm_memory = memory.copy()
        
        # Remove STM-specific metadata
        ltm_memory.pop("_access_count", None)
        ltm_memory.pop("_last_accessed_at", None)
        ltm_memory.pop("_locked", None)
        ltm_memory.pop("_locked_at", None)
        
        # Add LTM-specific metadata
        ltm_memory["stm_created_at"] = ltm_memory.pop("_created_at", time.time())
        ltm_memory["stm_updated_at"] = ltm_memory.pop("_updated_at", time.time())
        ltm_memory["consolidated_at"] = time.time()
        
        # TODO: Enrich with additional metadata
        
        return ltm_memory
    
    def retrieve_to_short_term(self, memory_id: str, ttl: Optional[int] = None) -> Optional[str]:
        """Retrieve a memory from long-term storage to short-term storage.
        
        Args:
            memory_id: The memory ID in long-term storage
            ttl: Optional time-to-live for the short-term memory
            
        Returns:
            The short-term memory ID if successful, None otherwise
        """
        # Get the memory from long-term storage
        ltm_memory = self.ltm_manager.get(memory_id)
        
        if not ltm_memory:
            logger.debug(f"Long-term memory not found for retrieval: {memory_id}")
            return None
        
        # Prepare for short-term storage
        stm_memory = self._prepare_for_short_term(ltm_memory)
        
        # Store in short-term memory
        stm_id = self.stm_manager.create(stm_memory, ttl=ttl)
        logger.debug(f"Retrieved memory {memory_id} to short-term memory as {stm_id}")
        
        return stm_id
    
    def _prepare_for_short_term(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a long-term memory for short-term storage.
        
        Args:
            memory: The long-term memory data
            
        Returns:
            The prepared short-term memory data
        """
        # Create a copy of the memory
        stm_memory = memory.copy()
        
        # Add STM-specific metadata
        stm_memory["_ltm_id"] = stm_memory["_id"]
        stm_memory["_id"] = None  # Will be assigned by STM manager
        stm_memory["_retrieved_at"] = time.time()
        stm_memory["_retrieved_from_ltm"] = True
        
        return stm_memory
    
    def forget_memory(self, memory_id: str) -> bool:
        """Permanently forget a memory from long-term storage.
        
        Args:
            memory_id: The memory ID in long-term storage
            
        Returns:
            True if the memory was forgotten, False otherwise
        """
        # Archive the memory before deletion (if needed)
        # TODO: Implement archival logic if required
        
        # Delete from long-term memory
        result = self.ltm_manager.delete(memory_id)
        
        if result:
            logger.debug(f"Permanently forgot memory: {memory_id}")
        
        return result
