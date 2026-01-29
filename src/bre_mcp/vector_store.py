"""
Vector store module for semantic search using ChromaDB and OpenAI embeddings.

Provides RAG (Retrieval Augmented Generation) capabilities for natural language
queries against repository README content and descriptions.
"""

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Any, Optional
from pathlib import Path

from .config import config
from .data_loader import DataLoader, Repository


class VectorStore:
    """
    Manages vector embeddings for semantic search over repository content.

    Uses ChromaDB for local vector storage and OpenAI's text-embedding-3-small
    model for generating embeddings from repository descriptions and README content.
    """

    def __init__(
        self,
        data_loader: DataLoader,
        persist_directory: Optional[Path] = None,
        collection_name: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize the vector store.

        Args:
            data_loader: DataLoader instance with repository data
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the ChromaDB collection
            openai_api_key: OpenAI API key for embeddings
        """
        self.data_loader = data_loader
        self.persist_directory = persist_directory or config.chroma_persist_directory
        self.collection_name = collection_name or config.chroma_collection_name
        self.openai_api_key = openai_api_key or config.openai_api_key

        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[chromadb.Collection] = None
        self._initialized = False

    def _get_embedding_function(self):
        """Get the OpenAI embedding function."""
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=self.openai_api_key,
            model_name=config.embedding_model,
        )

    def _initialize(self):
        """Initialize ChromaDB client and collection."""
        if self._initialized:
            return

        # Create persistent client
        self._client = chromadb.PersistentClient(
            path=str(self.persist_directory)
        )

        # Get or create collection with OpenAI embeddings
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._get_embedding_function(),
            metadata={"description": "BRE seismology repositories"}
        )

        self._initialized = True

    def _build_document(self, repo: Repository) -> str:
        """
        Build a searchable document from repository content.

        Combines description and README for comprehensive semantic matching.
        """
        parts = []

        # Add repository name
        parts.append(f"Repository: {repo.name}")

        # Add description if available
        if repo.description:
            parts.append(f"Description: {repo.description}")

        # Add main paper info if available
        if repo.mainPaper:
            if repo.mainPaper.title:
                parts.append(f"Paper Title: {repo.mainPaper.title}")
            if repo.mainPaper.abstract:
                parts.append(f"Abstract: {repo.mainPaper.abstract}")

        # Add README content (truncated to avoid token limits)
        if repo.readme:
            # Truncate README to ~4000 characters to stay within embedding limits
            readme_truncated = repo.readme[:4000]
            parts.append(f"README: {readme_truncated}")

        return "\n\n".join(parts)

    def index_repositories(self, force_reindex: bool = False):
        """
        Index all repositories into the vector store.

        Args:
            force_reindex: If True, delete existing collection and reindex
        """
        self._initialize()

        # Check if already indexed
        existing_count = self._collection.count()
        repo_count = len(self.data_loader.repositories)

        if existing_count == repo_count and not force_reindex:
            print(f"Collection already contains {existing_count} documents. Skipping indexing.")
            return

        if force_reindex and existing_count > 0:
            # Delete and recreate collection
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                embedding_function=self._get_embedding_function(),
                metadata={"description": "BRE seismology repositories"}
            )

        # Prepare documents for indexing
        documents = []
        metadatas = []
        ids = []

        for i, repo in enumerate(self.data_loader.repositories):
            doc = self._build_document(repo)
            documents.append(doc)

            # Store metadata for filtering and retrieval
            metadatas.append({
                "name": repo.name,
                "url": repo.url,
                "language": repo.language or "",
                "stars": repo.stars,
                "forks": repo.forks,
                "has_paper": str(repo.has_paper),
                "description": repo.description or "",
            })

            ids.append(f"repo_{i}")

        # Add to collection in batches
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            self._collection.add(
                documents=documents[i:end_idx],
                metadatas=metadatas[i:end_idx],
                ids=ids[i:end_idx],
            )
            print(f"Indexed {end_idx}/{len(documents)} repositories...")

        print(f"Indexing complete. Total documents: {self._collection.count()}")

    def search(
        self,
        query: str,
        limit: int = 10,
        filter_language: Optional[str] = None,
        filter_has_paper: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search for repositories.

        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            filter_language: Optional filter by programming language
            filter_has_paper: Optional filter by whether repo has associated paper

        Returns:
            List of matching repositories with similarity scores
        """
        self._initialize()

        # Check if collection is empty
        if self._collection.count() == 0:
            print("Collection is empty. Indexing repositories...")
            self.index_repositories()

        # Build where filter
        where_filter = None
        where_conditions = []

        if filter_language:
            where_conditions.append({"language": filter_language})

        if filter_has_paper is not None:
            where_conditions.append({"has_paper": str(filter_has_paper)})

        if len(where_conditions) == 1:
            where_filter = where_conditions[0]
        elif len(where_conditions) > 1:
            where_filter = {"$and": where_conditions}

        # Perform query
        results = self._collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted_results = []
        if results["metadatas"] and results["metadatas"][0]:
            for i, metadata in enumerate(results["metadatas"][0]):
                distance = results["distances"][0][i] if results["distances"] else None

                # Get full repository data
                repo = self.data_loader.get_by_name(metadata["name"])

                formatted_results.append({
                    "name": metadata["name"],
                    "url": metadata["url"],
                    "description": metadata.get("description", ""),
                    "language": metadata.get("language", ""),
                    "stars": metadata.get("stars", 0),
                    "has_paper": metadata.get("has_paper", "False") == "True",
                    "similarity_score": 1 - distance if distance else None,
                    "full_data": repo.to_full_dict() if repo else None,
                })

        return formatted_results

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector store collection."""
        self._initialize()
        return {
            "collection_name": self.collection_name,
            "document_count": self._collection.count(),
            "persist_directory": str(self.persist_directory),
        }
