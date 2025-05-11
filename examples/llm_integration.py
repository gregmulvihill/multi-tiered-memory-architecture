#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example integration of the Multi-Tiered Memory Architecture with an LLM context.

This example demonstrates how an LLM context can use the MTMA API to maintain
persistent memory across multiple interactions.
"""

import json
import time
import uuid
import requests
import argparse
from typing import Dict, List, Any, Optional

class MTMAClient:
    """Client for interacting with the MTMA API."""
    
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        """Initialize the MTMA client.
        
        Args:
            base_url: Base URL of the MTMA API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def create_short_term_memory(self, content, metadata=None, ttl=None):
        """Create a new short-term memory.
        
        Args:
            content: Memory content
            metadata: Optional metadata dictionary
            ttl: Optional time-to-live in seconds
            
        Returns:
            Created memory ID
        """
        url = f"{self.base_url}/memory/short-term"
        data = {"content": content}
        if metadata:
            data["metadata"] = metadata
        if ttl:
            data["ttl"] = ttl
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()["id"]
    
    def search_memories(self, query, limit=10):
        """Search for memories matching a query.
        
        Args:
            query: Search query dictionary
            limit: Maximum number of results
            
        Returns:
            List of matching memories
        """
        url = f"{self.base_url}/memory/short-term/search"
        params = {
            "query": json.dumps(query),
            "limit": limit
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()["results"]
    
    def get_world_state(self):
        """Get the current world state.
        
        Returns:
            World state data
        """
        url = f"{self.base_url}/world-state"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def update_world_state(self, updates):
        """Update the world state.
        
        Args:
            updates: Dictionary of updates to apply
            
        Returns:
            New version number
        """
        url = f"{self.base_url}/world-state/update"
        data = {"updates": updates}
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()["version"]

class LLMContext:
    """Simulated LLM context that uses MTMA for memory persistence."""
    
    def __init__(self, mtma_client):
        """Initialize the LLM context.
        
        Args:
            mtma_client: MTMA client instance
        """
        self.mtma_client = mtma_client
        self.context_id = str(uuid.uuid4())
        
        # Register this context in the world state
        self._register_context()
    
    def _register_context(self):
        """Register this context in the world state."""
        # Get current world state
        state = self.mtma_client.get_world_state()
        
        # Get active contexts or initialize if not present
        active_contexts = state.get("state", {}).get("active_contexts", [])
        
        # Add this context
        active_contexts.append({
            "context_id": self.context_id,
            "created_at": time.time(),
            "last_active": time.time()
        })
        
        # Update world state
        self.mtma_client.update_world_state({
            "active_contexts": active_contexts
        })
    
    def update_activity(self):
        """Update the last active timestamp for this context."""
        # Get current world state
        state = self.mtma_client.get_world_state()
        
        # Get active contexts
        active_contexts = state.get("state", {}).get("active_contexts", [])
        
        # Update this context's timestamp
        for context in active_contexts:
            if context.get("context_id") == self.context_id:
                context["last_active"] = time.time()
                break
        
        # Update world state
        self.mtma_client.update_world_state({
            "active_contexts": active_contexts
        })
    
    def remember_interaction(self, user_message, system_response, metadata=None):
        """Remember an interaction with the user.
        
        Args:
            user_message: User's message
            system_response: System's response
            metadata: Optional metadata
            
        Returns:
            Memory ID
        """
        # Create memory
        memory_data = {
            "user_message": user_message,
            "system_response": system_response,
            "context_id": self.context_id,
            "timestamp": time.time()
        }
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        metadata.update({
            "category": "interaction",
            "tags": ["user_message", "system_response"],
            "context_id": self.context_id
        })
        
        # Store in short-term memory
        memory_id = self.mtma_client.create_short_term_memory(
            content=memory_data,
            metadata=metadata,
            ttl=3600  # 1 hour
        )
        
        # Update activity
        self.update_activity()
        
        return memory_id
    
    def get_conversation_history(self, limit=10):
        """Get the conversation history for this context.
        
        Args:
            limit: Maximum number of interactions to retrieve
            
        Returns:
            List of interaction memories
        """
        # Search for memories with this context_id
        query = {"metadata.context_id": self.context_id}
        memories = self.mtma_client.search_memories(query, limit=limit)
        
        # Sort by timestamp (newest first)
        memories.sort(key=lambda m: m.get("content", {}).get("timestamp", 0), reverse=True)
        
        # Extract interaction data
        interactions = []
        for memory in memories:
            content = memory.get("content", {})
            interactions.append({
                "user_message": content.get("user_message"),
                "system_response": content.get("system_response"),
                "timestamp": content.get("timestamp")
            })
        
        return interactions
    
    def update_world_knowledge(self, key, value):
        """Update shared world knowledge.
        
        Args:
            key: Knowledge key
            value: Knowledge value
            
        Returns:
            New version number
        """
        # Get current world state
        state = self.mtma_client.get_world_state()
        
        # Get world knowledge or initialize if not present
        world_knowledge = state.get("state", {}).get("world_knowledge", {})
        
        # Update knowledge
        world_knowledge[key] = {
            "value": value,
            "updated_by": self.context_id,
            "updated_at": time.time()
        }
        
        # Update world state
        return self.mtma_client.update_world_state({
            "world_knowledge": world_knowledge
        })
    
    def get_world_knowledge(self, key=None):
        """Get shared world knowledge.
        
        Args:
            key: Optional specific knowledge key
            
        Returns:
            Knowledge value or dictionary of all knowledge
        """
        # Get current world state
        state = self.mtma_client.get_world_state()
        
        # Get world knowledge
        world_knowledge = state.get("state", {}).get("world_knowledge", {})
        
        if key is not None:
            # Return specific knowledge item
            knowledge_item = world_knowledge.get(key, {})
            return knowledge_item.get("value")
        else:
            # Return all knowledge values
            return {k: v.get("value") for k, v in world_knowledge.items()}

def simulate_conversation(client, num_turns=3):
    """Simulate a conversation with the LLM context.
    
    Args:
        client: MTMA client
        num_turns: Number of conversation turns to simulate
    """
    # Create LLM context
    context = LLMContext(client)
    print(f"Created LLM context with ID: {context.context_id}")
    print()
    
    # Simulate conversation turns
    for i in range(1, num_turns + 1):
        print(f"Turn {i}:")
        
        # Simulate user message
        user_message = f"Tell me about turn {i}"
        print(f"User: {user_message}")
        
        # Simulate system response
        system_response = f"This is turn {i} of our conversation."
        print(f"System: {system_response}")
        
        # Remember the interaction
        memory_id = context.remember_interaction(
            user_message=user_message,
            system_response=system_response,
            metadata={"turn": i}
        )
        print(f"Interaction stored with memory ID: {memory_id}")
        
        # Update world knowledge
        context.update_world_knowledge(f"turn_{i}_completed", True)
        print(f"World knowledge updated: turn_{i}_completed = True")
        print()
    
    # Get conversation history
    print("Conversation History:")
    history = context.get_conversation_history()
    for i, interaction in enumerate(history, 1):
        print(f"Interaction {i}:")
        print(f"User: {interaction['user_message']}")
        print(f"System: {interaction['system_response']}")
        print(f"Timestamp: {interaction['timestamp']}")
        print()
    
    # Get world knowledge
    print("World Knowledge:")
    knowledge = context.get_world_knowledge()
    for key, value in knowledge.items():
        print(f"{key}: {value}")

def main():
    """Main function for the example."""
    parser = argparse.ArgumentParser(description="MTMA LLM Integration Example")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--key", help="API key (optional)")
    parser.add_argument("--turns", type=int, default=3, help="Number of conversation turns")
    args = parser.parse_args()
    
    client = MTMAClient(base_url=args.url, api_key=args.key)
    simulate_conversation(client, num_turns=args.turns)

if __name__ == "__main__":
    main()