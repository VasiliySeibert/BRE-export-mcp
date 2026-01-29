"""
Configuration module for BRE Export MCP Server.

Handles environment variables and configuration for:
- LLM provider switching (OpenAI vs LM Studio)
- API keys
- Data file paths
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal, Optional

# Load environment variables from .env file
load_dotenv()


class Config(BaseModel):
    """Configuration settings for the MCP server."""

    # LLM Provider Settings
    llm_provider: Literal["openai", "lmstudio"] = Field(
        default="openai",
        description="LLM provider to use: 'openai' for OpenAI API, 'lmstudio' for local LM Studio"
    )

    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for embeddings and LLM calls"
    )

    lmstudio_base_url: str = Field(
        default="http://192.168.2.57:1234/v1",
        description="Base URL for LM Studio API"
    )

    # Data Settings
    data_file_path: Path = Field(
        default=Path("BettysResult_seismology_tools_doi_in_readme.json"),
        description="Path to the JSON data file"
    )

    # Embedding Settings
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model to use"
    )

    # ChromaDB Settings
    chroma_persist_directory: Path = Field(
        default=Path("chroma_data"),
        description="Directory for ChromaDB persistence"
    )

    chroma_collection_name: str = Field(
        default="bre_repos",
        description="Name of the ChromaDB collection"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "openai"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            lmstudio_base_url=os.getenv("LMSTUDIO_BASE_URL", "http://192.168.2.57:1234/v1"),
            data_file_path=Path(os.getenv("DATA_FILE_PATH", "BettysResult_seismology_tools_doi_in_readme.json")),
            embedding_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            chroma_persist_directory=Path(os.getenv("CHROMA_PERSIST_DIR", "chroma_data")),
            chroma_collection_name=os.getenv("CHROMA_COLLECTION", "bre_repos"),
        )

    def get_llm_base_url(self) -> Optional[str]:
        """Get the base URL for the LLM API based on provider."""
        if self.llm_provider == "lmstudio":
            return self.lmstudio_base_url
        return None  # OpenAI uses default URL


# Global config instance
config = Config.from_env()
