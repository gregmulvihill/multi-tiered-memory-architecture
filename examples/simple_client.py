#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple client for the Multi-Tiered Memory Architecture API.

This example demonstrates basic usage of the MTMA API for memory operations.
"""

import json
import time
import requests
import argparse

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
    
    def health_check(self):
        """Check the health of the API.
        
        Returns:
            API health status
        """
        url = f"{self.base_url}/health"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
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
    
    def get_short_term_memory(self, memory_id):
        """Get a short-term memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            Memory data or None if not found
        """
        url = f"{self.base_url}/memory/short-term/{memory_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    
    def update_short_term_memory(self, memory_id, content=None, metadata=None):
        """Update a short-term memory.
        
        Args:
            memory_id: Memory ID
            content: Optional new content
            metadata: Optional new metadata
            
        Returns:
            True if updated, False if not found
        """
        url = f"{self.base_url}/memory/short-term/{memory_id}"
        data = {}
        if content is not None:
            data["content"] = content
        if metadata is not None:
            data["metadata"] = metadata
        
        response = requests.put(url, headers=self.headers, json=data)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True
    
    def delete_short_term_memory(self, memory_id):
        """Delete a short-term memory.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            True if deleted, False if not found
        """
        url = f"{self.base_url}/memory/short-term/{memory_id}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return response.status_code == 204
    
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

def main():
    """Main function for the example client."""
    parser = argparse.ArgumentParser(description="MTMA API Client Example")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--key", help="API key (optional)")
    args = parser.parse_args()
    
    client = MTMAClient(base_url=args.url, api_key=args.key)
    
    # Check API health
    print("Checking API health...")
    health = client.health_check()
    print(f"API Status: {health['status']}")
    print(f"API Version: {health['version']}")
    print()
    
    # Create a short-term memory
    print("Creating short-term memory...")
    memory_id = client.create_short_term_memory(
        content="User asked about project timeline",
        metadata={
            "category": "user_interaction",
            "tags": ["timeline", "project"],
            "importance": 3
        },
        ttl=3600  # 1 hour
    )
    print(f"Created memory with ID: {memory_id}")
    print()
    
    # Get the memory
    print("Retrieving memory...")
    memory = client.get_short_term_memory(memory_id)
    print(f"Memory content: {memory['content']}")
    print(f"Access count: {memory['_access_count']}")
    print(f"Created at: {memory['_created_at']}")
    print()
    
    # Update the memory
    print("Updating memory...")
    client.update_short_term_memory(
        memory_id,
        content="User requested detailed project timeline",
        metadata={
            "category": "user_interaction",
            "tags": ["timeline", "project", "detailed"],
            "importance": 4
        }
    )
    print("Memory updated")
    print()
    
    # Get the updated memory
    print("Retrieving updated memory...")
    memory = client.get_short_term_memory(memory_id)
    print(f"Updated content: {memory['content']}")
    print(f"Updated tags: {memory['metadata']['tags']}")
    print(f"Updated importance: {memory['metadata']['importance']}")
    print(f"Access count: {memory['_access_count']}")
    print()
    
    # Get world state
    print("Getting world state...")
    state = client.get_world_state()
    print(f"Current state version: {state['version']}")
    print(f"State: {json.dumps(state['state'], indent=2)}")
    print()
    
    # Update world state
    print("Updating world state...")
    version = client.update_world_state({
        "user_status": "active",
        "current_task": "project_planning",
        "task_progress": 0.3
    })
    print(f"New state version: {version}")
    print()
    
    # Get updated world state
    print("Getting updated world state...")
    state = client.get_world_state()
    print(f"Current state version: {state['version']}")
    print(f"State: {json.dumps(state['state'], indent=2)}")
    print()
    
    # Delete the memory
    print("Deleting memory...")
    client.delete_short_term_memory(memory_id)
    print("Memory deleted")
    print()
    
    # Try to get the deleted memory
    print("Trying to retrieve deleted memory...")
    memory = client.get_short_term_memory(memory_id)
    print(f"Memory found: {memory is not None}")

if __name__ == "__main__":
    main()