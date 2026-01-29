"""
Data loader module for BRE Export MCP Server.

Handles loading and validating the JSON dataset of seismology repositories.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AgentQueryTerm(BaseModel):
    """Query terms for various academic platforms."""
    zenodo: str = ""
    openAlex: str = ""
    openCitations: str = ""
    dataCite: str = ""


class MainPaper(BaseModel):
    """Main publication associated with a repository."""
    doi: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    dateReleased: Optional[str] = None
    abstract: Optional[str] = None
    citationsArray: List[str] = Field(default_factory=list)

    @property
    def citation_count(self) -> int:
        """Get the number of citations."""
        return len(self.citationsArray)


class Repository(BaseModel):
    """A seismology tool repository from GitHub."""
    name: str
    url: str
    description: Optional[str] = None
    stars: int = 0
    forks: int = 0
    readme: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    language: Optional[str] = None
    homepage: Optional[str] = None
    amountPublications: Dict[str, Any] = Field(default_factory=dict)
    agentQueryTerm: AgentQueryTerm = Field(default_factory=AgentQueryTerm)
    readmeUrl: Optional[str] = None
    mainPaper: Optional[MainPaper] = None
    publications: List[Dict[str, Any]] = Field(default_factory=list)

    @property
    def has_paper(self) -> bool:
        """Check if repository has an associated main paper."""
        return self.mainPaper is not None and self.mainPaper.doi is not None

    @property
    def has_citations(self) -> bool:
        """Check if repository's paper has citations."""
        return self.has_paper and self.mainPaper.citation_count > 0

    def to_summary(self) -> Dict[str, Any]:
        """Return a summary dict for list views."""
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "stars": self.stars,
            "forks": self.forks,
            "language": self.language,
            "has_paper": self.has_paper,
            "citation_count": self.mainPaper.citation_count if self.mainPaper else 0,
        }

    def to_full_dict(self) -> Dict[str, Any]:
        """Return full repository data as dict."""
        return self.model_dump()


class DataLoader:
    """Loads and manages the repository dataset."""

    def __init__(self, data_file_path: Optional[Path] = None):
        self.data_file_path = data_file_path
        self._repositories: Optional[List[Repository]] = None

    def load(self) -> List[Repository]:
        """Load repositories from JSON file."""
        if self._repositories is not None:
            return self._repositories

        if self.data_file_path is None:
            raise ValueError("No data file path set. Use load_from_json() or set data_file_path first.")

        with open(self.data_file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        self._repositories = [Repository(**item) for item in raw_data]
        return self._repositories

    def load_from_json(self, json_data: List[Dict[str, Any]]) -> List[Repository]:
        """Load repositories from JSON data (list of dicts).

        Args:
            json_data: List of repository dictionaries

        Returns:
            List of Repository objects
        """
        self._repositories = [Repository(**item) for item in json_data]
        return self._repositories

    def is_loaded(self) -> bool:
        """Check if data has been loaded."""
        return self._repositories is not None

    @property
    def repositories(self) -> List[Repository]:
        """Get all repositories, loading if necessary."""
        if self._repositories is None:
            self.load()
        return self._repositories

    def get_by_name(self, name: str) -> Optional[Repository]:
        """Get a repository by exact name match."""
        for repo in self.repositories:
            if repo.name.lower() == name.lower():
                return repo
        return None

    def search_by_name(self, query: str) -> List[Repository]:
        """Search repositories by name (case-insensitive substring match)."""
        query_lower = query.lower()
        return [repo for repo in self.repositories if query_lower in repo.name.lower()]

    def filter_by_language(self, language: str) -> List[Repository]:
        """Filter repositories by programming language."""
        language_lower = language.lower()
        return [
            repo for repo in self.repositories
            if repo.language and repo.language.lower() == language_lower
        ]

    def get_repos_with_paper(self) -> List[Repository]:
        """Get all repositories that have an associated main paper."""
        return [repo for repo in self.repositories if repo.has_paper]

    def get_repos_with_citations(self, min_citations: int = 1) -> List[Repository]:
        """Get repositories with citations, optionally filtered by minimum count."""
        return [
            repo for repo in self.repositories
            if repo.has_citations and repo.mainPaper.citation_count >= min_citations
        ]

    def sort_by_stars(self, ascending: bool = False) -> List[Repository]:
        """Sort repositories by GitHub stars."""
        return sorted(self.repositories, key=lambda r: r.stars, reverse=not ascending)

    def sort_by_forks(self, ascending: bool = False) -> List[Repository]:
        """Sort repositories by fork count."""
        return sorted(self.repositories, key=lambda r: r.forks, reverse=not ascending)

    def sort_by_citations(self, ascending: bool = False) -> List[Repository]:
        """Sort repositories by citation count (only repos with papers)."""
        repos_with_papers = self.get_repos_with_paper()
        return sorted(
            repos_with_papers,
            key=lambda r: r.mainPaper.citation_count,
            reverse=not ascending
        )

    def filter_by_date_range(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_field: str = "createdAt"
    ) -> List[Repository]:
        """Filter repositories by date range.

        Args:
            start_date: ISO format date string (e.g., "2020-01-01")
            end_date: ISO format date string (e.g., "2024-12-31")
            date_field: Which date field to use ("createdAt" or "updatedAt")
        """
        results = []
        for repo in self.repositories:
            date_str = getattr(repo, date_field, None)
            if not date_str:
                continue

            # Parse the ISO date string
            try:
                repo_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                continue

            # Check date range
            if start_date:
                start = datetime.fromisoformat(start_date)
                if repo_date.replace(tzinfo=None) < start:
                    continue

            if end_date:
                end = datetime.fromisoformat(end_date)
                if repo_date.replace(tzinfo=None) > end:
                    continue

            results.append(repo)

        return results

    def get_available_languages(self) -> List[str]:
        """Get list of all programming languages in the dataset."""
        languages = set()
        for repo in self.repositories:
            if repo.language:
                languages.add(repo.language)
        return sorted(languages)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the dataset."""
        repos = self.repositories
        return {
            "total_repositories": len(repos),
            "repos_with_description": len([r for r in repos if r.description]),
            "repos_with_readme": len([r for r in repos if r.readme]),
            "repos_with_paper": len([r for r in repos if r.has_paper]),
            "repos_with_citations": len([r for r in repos if r.has_citations]),
            "total_stars": sum(r.stars for r in repos),
            "total_forks": sum(r.forks for r in repos),
            "languages": self.get_available_languages(),
        }
