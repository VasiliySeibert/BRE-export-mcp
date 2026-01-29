"""
MCP Tools for querying seismology repository data.

This module defines all the tools that are exposed to LLMs through the MCP server.
Each tool has a clear description to help the LLM understand when and how to use it.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from .data_loader import DataLoader, Repository
from .vector_store import VectorStore
from .config import config


class BRETools:
    """
    Collection of tools for querying the BRE seismology repository dataset.

    These tools provide both structured queries (filtering, sorting) and
    semantic search (natural language queries) capabilities.
    """

    def __init__(
        self,
        data_file_path: Optional[Path] = None,
    ):
        """
        Initialize tools with data loader and vector store.

        Args:
            data_file_path: Optional path to JSON data file. Can also load via upload_data().
        """
        self.data_file_path = data_file_path
        self._data_loader: Optional[DataLoader] = None
        self._vector_store: Optional[VectorStore] = None
        self._data_loaded = False

    def upload_data(self, json_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload JSON data to initialize the session.

        This must be called before using any other tools. The uploaded data
        is stored in memory for the duration of the session.

        Args:
            json_data: List of repository objects as dictionaries

        Returns:
            Dictionary with upload status and repository count
        """
        self._data_loader = DataLoader()
        self._data_loader.load_from_json(json_data)
        self._vector_store = None  # Reset vector store for new data
        self._data_loaded = True

        return {
            "status": "success",
            "message": "Data uploaded successfully",
            "repository_count": len(self._data_loader.repositories),
        }

    def _ensure_data_loaded(self):
        """Ensure data has been uploaded before using tools."""
        if not self._data_loaded:
            # Try loading from file path if provided
            if self.data_file_path:
                self._data_loader = DataLoader(self.data_file_path)
                self._data_loader.load()
                self._data_loaded = True
            else:
                raise ValueError(
                    "No data loaded. Call upload_data() first to upload the JSON data."
                )

    @property
    def data_loader(self) -> DataLoader:
        """Get data loader, ensuring data is loaded."""
        self._ensure_data_loaded()
        return self._data_loader

    @property
    def vector_store(self) -> VectorStore:
        """Lazy initialization of vector store."""
        self._ensure_data_loaded()
        if self._vector_store is None:
            self._vector_store = VectorStore(self._data_loader)
        return self._vector_store

    # =========================================================================
    # TOOL: list_repos
    # =========================================================================
    def list_repos(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List all repositories in the dataset with pagination.

        Use this tool to get an overview of available repositories. Returns
        summary information for each repository including name, description,
        stars, language, and whether it has an associated academic paper.

        Args:
            limit: Maximum number of repositories to return (default: 20, max: 100)
            offset: Number of repositories to skip for pagination (default: 0)

        Returns:
            Dictionary with total count and list of repository summaries
        """
        limit = min(limit, 100)  # Cap at 100
        repos = self.data_loader.repositories
        total = len(repos)

        paginated = repos[offset:offset + limit]

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "repositories": [repo.to_summary() for repo in paginated],
        }

    # =========================================================================
    # TOOL: get_repo_details
    # =========================================================================
    def get_repo_details(self, name: str) -> Dict[str, Any]:
        """
        Get complete details for a specific repository by its name.

        Use this tool when you need full information about a repository including
        its complete README content, associated paper details, citations, and
        all metadata. The name should match the GitHub repository name format
        (e.g., "owner/repo-name").

        Args:
            name: Repository name in "owner/repo-name" format (case-insensitive)

        Returns:
            Complete repository data or error if not found
        """
        repo = self.data_loader.get_by_name(name)
        if repo:
            return {
                "found": True,
                "repository": repo.to_full_dict(),
            }
        return {
            "found": False,
            "error": f"Repository '{name}' not found",
            "suggestion": "Use search_by_name to find repositories with similar names",
        }

    # =========================================================================
    # TOOL: search_by_name
    # =========================================================================
    def search_by_name(self, query: str) -> Dict[str, Any]:
        """
        Search for repositories by name using substring matching.

        Use this tool when you know part of a repository's name but not the
        exact full name. Performs case-insensitive substring matching.

        Args:
            query: Search string to match against repository names

        Returns:
            List of matching repositories with summary information
        """
        results = self.data_loader.search_by_name(query)
        return {
            "query": query,
            "count": len(results),
            "repositories": [repo.to_summary() for repo in results],
        }

    # =========================================================================
    # TOOL: filter_by_language
    # =========================================================================
    def filter_by_language(self, language: str) -> Dict[str, Any]:
        """
        Filter repositories by programming language.

        Use this tool to find repositories written in a specific programming
        language (e.g., Python, Jupyter Notebook, Fortran, MATLAB).

        Args:
            language: Programming language to filter by (case-insensitive)

        Returns:
            List of repositories using the specified language
        """
        results = self.data_loader.filter_by_language(language)
        available = self.data_loader.get_available_languages()

        return {
            "language": language,
            "count": len(results),
            "repositories": [repo.to_summary() for repo in results],
            "available_languages": available,
        }

    # =========================================================================
    # TOOL: sort_by_stars
    # =========================================================================
    def sort_by_stars(
        self,
        limit: int = 10,
        ascending: bool = False,
    ) -> Dict[str, Any]:
        """
        Get repositories sorted by GitHub star count.

        Use this tool to find the most popular (or least popular) repositories
        based on GitHub stars. By default returns the top-starred repositories.

        Args:
            limit: Number of repositories to return (default: 10)
            ascending: If True, sort from lowest to highest stars (default: False)

        Returns:
            List of repositories sorted by star count
        """
        sorted_repos = self.data_loader.sort_by_stars(ascending=ascending)
        limited = sorted_repos[:limit]

        return {
            "sort_order": "ascending" if ascending else "descending",
            "count": len(limited),
            "repositories": [repo.to_summary() for repo in limited],
        }

    # =========================================================================
    # TOOL: sort_by_forks
    # =========================================================================
    def sort_by_forks(
        self,
        limit: int = 10,
        ascending: bool = False,
    ) -> Dict[str, Any]:
        """
        Get repositories sorted by fork count.

        Use this tool to find repositories with the most (or fewest) forks,
        which can indicate community engagement and derivative work.

        Args:
            limit: Number of repositories to return (default: 10)
            ascending: If True, sort from lowest to highest forks (default: False)

        Returns:
            List of repositories sorted by fork count
        """
        sorted_repos = self.data_loader.sort_by_forks(ascending=ascending)
        limited = sorted_repos[:limit]

        return {
            "sort_order": "ascending" if ascending else "descending",
            "count": len(limited),
            "repositories": [repo.to_summary() for repo in limited],
        }

    # =========================================================================
    # TOOL: get_repos_with_paper
    # =========================================================================
    def get_repos_with_paper(self) -> Dict[str, Any]:
        """
        Get all repositories that have an associated academic paper.

        Use this tool to find repositories that have been formally published
        or have a DOI associated with them. These repositories typically have
        more rigorous documentation and are citable in academic work.

        Returns:
            List of repositories with associated papers, including paper details
        """
        repos = self.data_loader.get_repos_with_paper()

        results = []
        for repo in repos:
            summary = repo.to_summary()
            summary["paper"] = {
                "doi": repo.mainPaper.doi,
                "title": repo.mainPaper.title,
                "journal": repo.mainPaper.journal,
                "citation_count": repo.mainPaper.citation_count,
            }
            results.append(summary)

        return {
            "count": len(results),
            "repositories": results,
        }

    # =========================================================================
    # TOOL: get_repos_with_citations
    # =========================================================================
    def get_repos_with_citations(
        self,
        min_citations: int = 1,
    ) -> Dict[str, Any]:
        """
        Get repositories that have citations, optionally filtered by minimum count.

        Use this tool to find repositories whose associated papers have been
        cited by other works. This indicates academic impact and validation.

        Args:
            min_citations: Minimum number of citations required (default: 1)

        Returns:
            List of repositories with citations, sorted by citation count
        """
        repos = self.data_loader.get_repos_with_citations(min_citations)

        # Sort by citation count descending
        repos_sorted = sorted(
            repos,
            key=lambda r: r.mainPaper.citation_count,
            reverse=True
        )

        results = []
        for repo in repos_sorted:
            summary = repo.to_summary()
            summary["paper"] = {
                "doi": repo.mainPaper.doi,
                "title": repo.mainPaper.title,
                "citation_count": repo.mainPaper.citation_count,
                "citations": repo.mainPaper.citationsArray[:5],  # First 5 citing DOIs
            }
            results.append(summary)

        return {
            "min_citations": min_citations,
            "count": len(results),
            "repositories": results,
        }

    # =========================================================================
    # TOOL: get_repos_by_date_range
    # =========================================================================
    def get_repos_by_date_range(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_field: str = "createdAt",
    ) -> Dict[str, Any]:
        """
        Filter repositories by creation or update date.

        Use this tool to find repositories created or updated within a specific
        time period. Useful for finding recent tools or tools from a specific era.

        Args:
            start_date: Start date in ISO format (e.g., "2020-01-01")
            end_date: End date in ISO format (e.g., "2024-12-31")
            date_field: Which date to filter by - "createdAt" or "updatedAt"

        Returns:
            List of repositories within the date range
        """
        if date_field not in ["createdAt", "updatedAt"]:
            return {
                "error": f"Invalid date_field: {date_field}. Use 'createdAt' or 'updatedAt'",
            }

        repos = self.data_loader.filter_by_date_range(
            start_date=start_date,
            end_date=end_date,
            date_field=date_field,
        )

        return {
            "date_field": date_field,
            "start_date": start_date,
            "end_date": end_date,
            "count": len(repos),
            "repositories": [repo.to_summary() for repo in repos],
        }

    # =========================================================================
    # TOOL: semantic_search
    # =========================================================================
    def semantic_search(
        self,
        query: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Search repositories using natural language semantic search.

        Use this tool when you need to find repositories based on concepts,
        topics, or descriptions rather than exact keyword matches. This tool
        searches through README content and descriptions using AI embeddings
        to find semantically similar content.

        Examples of good queries:
        - "earthquake detection using machine learning"
        - "ambient noise tomography"
        - "tsunami simulation and modeling"
        - "seismic waveform analysis"

        Args:
            query: Natural language search query describing what you're looking for
            limit: Maximum number of results to return (default: 10)

        Returns:
            List of semantically matching repositories with similarity scores
        """
        results = self.vector_store.search(query=query, limit=limit)

        # Format for cleaner output (remove full_data to reduce size)
        formatted = []
        for r in results:
            formatted.append({
                "name": r["name"],
                "url": r["url"],
                "description": r["description"],
                "language": r["language"],
                "stars": r["stars"],
                "has_paper": r["has_paper"],
                "similarity_score": round(r["similarity_score"], 4) if r["similarity_score"] else None,
            })

        return {
            "query": query,
            "count": len(formatted),
            "results": formatted,
        }

    # =========================================================================
    # TOOL: get_statistics
    # =========================================================================
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the entire repository dataset.

        Use this tool to get an overview of the dataset including total counts,
        language distribution, and paper/citation coverage.

        Returns:
            Dataset statistics including counts and available languages
        """
        return self.data_loader.get_statistics()

    # =========================================================================
    # TOOL: get_available_languages
    # =========================================================================
    def get_available_languages(self) -> Dict[str, Any]:
        """
        Get list of all programming languages represented in the dataset.

        Use this tool to see what programming languages are available before
        filtering by language.

        Returns:
            List of programming languages
        """
        languages = self.data_loader.get_available_languages()
        return {
            "count": len(languages),
            "languages": languages,
        }
