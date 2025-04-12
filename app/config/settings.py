"""
Configuration settings for the Azure Image Description AI Matching application.
"""
import os
from typing import List, Dict, Any, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure OpenAI configuration
    azure_openai_endpoint: str = Field(
        default="", 
        env="AZURE_OPENAI_ENDPOINT"
    )
    azure_openai_api_key: str = Field(
        default="", 
        env="AZURE_OPENAI_API_KEY"
    )
    azure_openai_api_version: str = Field(
        default="2024-12-01-preview", 
        env="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_deployment: str = Field(
        default="o1", 
        env="AZURE_OPENAI_DEPLOYMENT"
    )
    
    # Azure AI Vision configuration
    azure_vision_endpoint: str = Field(
        default="", 
        env="AZURE_VISION_ENDPOINT"
    )
    azure_vision_key: str = Field(
        default="", 
        env="AZURE_VISION_KEY"
    )
    azure_vision_region: str = Field(
        default="westus", 
        env="AZURE_VISION_REGION"
    )
    
    # File paths
    food_descriptions_file: str = "food-descriptions.txt"
    images_dir: str = "images"
    results_base_dir: str = "results"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global instance of settings
settings = Settings()