#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Controller Service

This module implements the central coordination service for memory operations,
enforcing policies, managing transactions, and providing a unified API.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config.settings import AppSettings
from memory_controller.short_term import ShortTermMemoryManager
from memory_controller.long_term import LongTermMemoryManager
from memory_controller.lifecycle import MemoryLifecycleManager
from memory_controller.world_state import WorldStateManager

logger = logging.getLogger(__name__)

class MemoryControllerService:
    """Central service for coordinating memory operations across subsystems."""
    
    def __init__(self, settings: AppSettings):
        """Initialize the Memory Controller Service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.app = FastAPI(
            title="MTMA Memory Controller API",
            description="API for the Multi-Tiered Memory Architecture",
            version=settings.version
        )
        
        # Set up CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.api.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize memory managers
        self.stm_manager = ShortTermMemoryManager(settings)
        self.ltm_manager = LongTermMemoryManager(settings)
        self.lifecycle_manager = MemoryLifecycleManager(
            settings, self.stm_manager, self.ltm_manager
        )
        self.world_state_manager = WorldStateManager(settings, self.stm_manager)
        
        # Set up API routes
        self.setup_routes()
        
        # Service control
        self.running = False
        self.server = None
        self.lifecycle_thread = None
    
    def setup_routes(self):
        """Configure API routes for the service."""
        # Health check endpoints
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "version": self.settings.version}
        
        # Short-term memory endpoints
        @self.app.post("/memory/short-term")
        async def create_stm_memory(memory: Dict[str, Any]):
            try:
                memory_id = self.stm_manager.create(memory)
                return {"id": memory_id}
            except Exception as e:
                logger.error(f"Error creating short-term memory: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/short-term/{memory_id}")
        async def get_stm_memory(memory_id: str):
            memory = self.stm_manager.get(memory_id)
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            return memory
        
        # Long-term memory endpoints
        @self.app.post("/memory/long-term")
        async def create_ltm_memory(memory: Dict[str, Any]):
            try:
                memory_id = self.ltm_manager.create(memory)
                return {"id": memory_id}
            except Exception as e:
                logger.error(f"Error creating long-term memory: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/memory/long-term/{memory_id}")
        async def get_ltm_memory(memory_id: str):
            memory = self.ltm_manager.get(memory_id)
            if not memory:
                raise HTTPException(status_code=404, detail="Memory not found")
            return memory
        
        # World state endpoints
        @self.app.get("/world-state")
        async def get_world_state():
            return self.world_state_manager.get_current_state()
        
        @self.app.post("/world-state/update")
        async def update_world_state(update: Dict[str, Any]):
            try:
                version = self.world_state_manager.update_state(update)
                return {"version": version}
            except Exception as e:
                logger.error(f"Error updating world state: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def start_lifecycle_thread(self):
        """Start the memory lifecycle management thread."""
        def lifecycle_worker():
            logger.info("Memory lifecycle management thread started")
            while self.running:
                try:
                    self.lifecycle_manager.run_consolidation()
                except Exception as e:
                    logger.error(f"Error in lifecycle management: {e}")
                
                # Sleep for the configured interval
                time.sleep(self.settings.memory.consolidation_interval)
            
            logger.info("Memory lifecycle management thread stopped")
        
        self.lifecycle_thread = threading.Thread(target=lifecycle_worker)
        self.lifecycle_thread.daemon = True
        self.lifecycle_thread.start()
    
    def start(self):
        """Start the Memory Controller Service."""
        logger.info("Starting Memory Controller Service")
        
        # Initialize connections to backing services
        self.stm_manager.initialize()
        self.ltm_manager.initialize()
        
        # Start the lifecycle management thread
        self.running = True
        self.start_lifecycle_thread()
        
        # Start the API server
        host = self.settings.api.host
        port = self.settings.api.port
        logger.info(f"Starting API server on {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            workers=self.settings.api.workers,
            log_level=self.settings.get_log_level().lower(),
        )
        self.server = uvicorn.Server(config)
        self.server.run()
    
    def stop(self):
        """Stop the Memory Controller Service."""
        logger.info("Stopping Memory Controller Service")
        self.running = False
        
        # Close connections to backing services
        self.stm_manager.shutdown()
        self.ltm_manager.shutdown()
    
    def join(self):
        """Wait for the service to complete."""
        if self.server:
            # This is a blocking call until the server shuts down
            pass
        
        if self.lifecycle_thread and self.lifecycle_thread.is_alive():
            self.lifecycle_thread.join(timeout=5.0)
