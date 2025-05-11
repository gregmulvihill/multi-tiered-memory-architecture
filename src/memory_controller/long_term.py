#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Long-Term Memory Manager

This module handles the storage and retrieval of long-term memories using
MongoDB, Neo4j, and Qdrant.
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Union

import pymongo
from pymongo import MongoClient
from neo4j import GraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from config.settings import AppSettings

logger = logging.getLogger(__name__)

class LongTermMemoryManager:
    """Manages long-term memory storage and retrieval across multiple databases."""
    
    def __init__(self, settings: AppSettings):
        """Initialize the Long-Term Memory Manager.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.mongo_client = None
        self.mongo_db = None
        self.neo4j_driver = None
        self.qdrant_client = None
        self.collection_name = "memories"
        self.vector_dim = settings.memory.ltm_vector_dim
    
    def initialize(self):
        """Initialize connections to the databases."""
        logger.info("Initializing Long-Term Memory Manager")
        
        # Initialize MongoDB connection
        try:
            self.mongo_client = MongoClient(self.settings.mongodb.uri)
            self.mongo_db = self.mongo_client[self.settings.mongodb.database]
            # Ensure indexes
            self.mongo_db[self.collection_name].create_index("_id")
            self.mongo_db[self.collection_name].create_index("category")
            self.mongo_db[self.collection_name].create_index("created_at")
            logger.info("Connected to MongoDB successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        
        # Initialize Neo4j connection
        try:
            self.neo4j_driver = GraphDatabase.driver(
                self.settings.neo4j.uri,
                auth=(self.settings.neo4j.user, self.settings.neo4j.password)
            )
            # Test connection
            with self.neo4j_driver.session() as session:
                session.run("RETURN 1")
            logger.info("Connected to Neo4j successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        
        # Initialize Qdrant connection
        try:
            self.qdrant_client = QdrantClient(
                host=self.settings.qdrant.host,
                port=self.settings.qdrant.port,
                api_key=self.settings.qdrant.api_key,
                https=self.settings.qdrant.https
            )
            
            # Check if collection exists, create if not
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
            
            logger.info("Connected to Qdrant successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def shutdown(self):
        """Close connections to the databases."""
        logger.info("Shutting down Long-Term Memory Manager")
        
        if self.mongo_client:
            self.mongo_client.close()
        
        if self.neo4j_driver:
            self.neo4j_driver.close()
        
        # Qdrant client doesn't require explicit closing
    
    def create(self, memory_data: Dict[str, Any]) -> str:
        """Create a new long-term memory.
        
        Args:
            memory_data: The memory data to store
            
        Returns:
            The memory ID
        """
        # Generate a unique ID if not provided
        memory_id = memory_data.get("_id", str(uuid.uuid4()))
        
        # Add metadata
        memory_data["_id"] = memory_id
        memory_data["created_at"] = time.time()
        memory_data["updated_at"] = time.time()
        memory_data["version"] = 1
        
        # Store in MongoDB
        self.mongo_db[self.collection_name].insert_one(memory_data)
        
        # TODO: Add relationship handling for Neo4j
        
        # TODO: Add vector embedding and storage for Qdrant
        
        logger.debug(f"Created long-term memory: {memory_id}")
        return memory_id
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a long-term memory by ID.
        
        Args:
            memory_id: The memory ID
            
        Returns:
            The memory data or None if not found
        """
        result = self.mongo_db[self.collection_name].find_one({"_id": memory_id})
        
        if not result:
            logger.debug(f"Long-term memory not found: {memory_id}")
            return None
        
        logger.debug(f"Retrieved long-term memory: {memory_id}")
        return result
    
    def update(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing long-term memory.
        
        Args:
            memory_id: The memory ID
            updates: The updates to apply
            
        Returns:
            True if the memory was updated, False if not found
        """
        # Get the current version
        current = self.mongo_db[self.collection_name].find_one(
            {"_id": memory_id},
            {"version": 1}
        )
        
        if not current:
            logger.debug(f"Long-term memory not found for update: {memory_id}")
            return False
        
        # Update the memory
        updates["updated_at"] = time.time()
        updates["version"] = current.get("version", 0) + 1
        
        result = self.mongo_db[self.collection_name].update_one(
            {"_id": memory_id},
            {"$set": updates}
        )
        
        if result.modified_count > 0:
            logger.debug(f"Updated long-term memory: {memory_id}")
            return True
        else:
            logger.debug(f"Long-term memory not modified: {memory_id}")
            return False
    
    def delete(self, memory_id: str) -> bool:
        """Delete a long-term memory.
        
        Args:
            memory_id: The memory ID
            
        Returns:
            True if the memory was deleted, False if not found
        """
        result = self.mongo_db[self.collection_name].delete_one({"_id": memory_id})
        
        # TODO: Remove relationships from Neo4j
        
        # TODO: Remove vectors from Qdrant
        
        if result.deleted_count > 0:
            logger.debug(f"Deleted long-term memory: {memory_id}")
            return True
        else:
            logger.debug(f"Long-term memory not found for deletion: {memory_id}")
            return False
    
    def search(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Search for long-term memories matching a query.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of matching memories
        """
        cursor = self.mongo_db[self.collection_name].find(query).limit(limit)
        return list(cursor)
    
    # TODO: Implement vector similarity search using Qdrant
    
    # TODO: Implement relationship queries using Neo4j
