#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Tiered Memory Architecture Orchestration Agent

This is the main entry point for the MTMA system. It initializes all components
and starts the Memory Controller Service.
"""

import os
import logging
import argparse
from dotenv import load_dotenv

from memory_controller.service import MemoryControllerService
from config.settings import AppSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("mtma.log"),
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Multi-Tiered Memory Architecture")
    parser.add_argument(
        "--config", 
        type=str, 
        default=".env", 
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(args.config)
    
    # Set debug mode if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Load application settings
    settings = AppSettings()
    logger.info(f"Starting MTMA Orchestration Agent v{settings.version}")
    
    try:
        # Initialize the Memory Controller Service
        service = MemoryControllerService(settings)
        
        # Start the service
        service.start()
        
        logger.info("MTMA Orchestration Agent started successfully")
        
        # Keep the main thread running
        service.join()
        
    except KeyboardInterrupt:
        logger.info("Shutting down MTMA Orchestration Agent")
        if 'service' in locals():
            service.stop()
    except Exception as e:
        logger.exception(f"Error starting MTMA Orchestration Agent: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
