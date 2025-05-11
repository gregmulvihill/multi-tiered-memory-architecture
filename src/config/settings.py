#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application settings module for the MTMA Orchestration Agent.

This module handles loading and validating configuration settings from
environment variables and configuration files.
"""

import os
from typing import Dict, List, Optional, Union
from pydantic import BaseSettings, Field, validator
import logging

logger = logging.getLogger(__name__)

class RedisSettings(BaseSettings):
    """Settings for Redis connection."""
    host: str = Field("localhost", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")
    db: int = Field(0, env="REDIS_DB")
    password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    ssl: bool = Field(False, env="REDIS_SSL")
    
    class Config:
        env_prefix = "REDIS_"

class MongoDBSettings(BaseSettings):
    """Settings for MongoDB connection."""
    uri: str = Field("mongodb://localhost:27017", env="MONGODB_URI")
    database: str = Field("mtma", env="MONGODB_DATABASE")
    
    class Config:
        env_prefix = "MONGODB_"

class Neo4jSettings(BaseSettings):
    """Settings for Neo4j connection."""
    uri: str = Field("bolt://localhost:7687", env="NEO4J_URI")
    user: str = Field("neo4j", env="NEO4J_USER")
    password: str = Field("password", env="NEO4J_PASSWORD")
    
    class Config:
        env_prefix = "NEO4J_"

class QdrantSettings(BaseSettings):
    """Settings for Qdrant connection."""
    host: str = Field("localhost", env="QDRANT_HOST")
    port: int = Field(6333, env="QDRANT_PORT")
    grpc_port: int = Field(6334, env="QDRANT_GRPC_PORT")
    api_key: Optional[str] = Field(None, env="QDRANT_API_KEY")
    https: bool = Field(False, env="QDRANT_HTTPS")
    
    class Config:
        env_prefix = "QDRANT_"

class KafkaSettings(BaseSettings):
    """Settings for Kafka connection."""
    bootstrap_servers: str = Field("localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    topic_prefix: str = Field("mtma", env="KAFKA_TOPIC_PREFIX")
    
    class Config:
        env_prefix = "KAFKA_"

class APISettings(BaseSettings):
    """Settings for the API server."""
    host: str = Field("0.0.0.0", env="API_HOST")
    port: int = Field(8000, env="API_PORT")
    debug: bool = Field(False, env="API_DEBUG")
    workers: int = Field(4, env="API_WORKERS")
    cors_origins: List[str] = Field(["*"], env="API_CORS_ORIGINS")
    
    class Config:
        env_prefix = "API_"

class MemorySettings(BaseSettings):
    """Settings for memory management."""
    # Short-term memory settings
    stm_default_ttl: int = Field(3600, env="STM_DEFAULT_TTL")  # 1 hour in seconds
    stm_max_size: int = Field(10000, env="STM_MAX_SIZE")  # Maximum number of items
    
    # Long-term memory settings
    ltm_batch_size: int = Field(100, env="LTM_BATCH_SIZE")  # Batch size for operations
    ltm_vector_dim: int = Field(384, env="LTM_VECTOR_DIM")  # Dimension for vector embeddings
    
    # Memory lifecycle settings
    consolidation_threshold: int = Field(5, env="CONSOLIDATION_THRESHOLD")  # Min access count for consolidation
    consolidation_interval: int = Field(300, env="CONSOLIDATION_INTERVAL")  # Time between consolidation runs (seconds)
    
    class Config:
        env_prefix = "MEMORY_"

class AppSettings(BaseSettings):
    """Main application settings."""
    # Application metadata
    app_name: str = Field("mtma-orchestration-agent", env="APP_NAME")
    version: str = Field("0.1.0", env="APP_VERSION")
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # Component settings
    redis: RedisSettings = RedisSettings()
    mongodb: MongoDBSettings = MongoDBSettings()
    neo4j: Neo4jSettings = Neo4jSettings()
    qdrant: QdrantSettings = QdrantSettings()
    kafka: KafkaSettings = KafkaSettings()
    api: APISettings = APISettings()
    memory: MemorySettings = MemorySettings()
    
    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v
    
    def get_log_level(self) -> int:
        """Convert string log level to logging module constant."""
        return getattr(logging, self.log_level)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
