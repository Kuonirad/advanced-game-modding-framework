"""Directed Acyclic Graph (DAG) implementation for asset dependencies.

This module provides DAG-based tracking of game asset dependencies to prevent
circular references and maintain consistency during modifications.
"""

from typing import Dict, Optional, Set


class AssetGraph:
    """Manages game asset dependencies using a DAG structure."""

    def __init__(self) -> None:
        """Initialize an empty asset dependency graph."""
        self._nodes: Set[str] = set()  # Asset IDs
        self._edges: Dict[str, Set[str]] = {}  # Dependencies
        self._versions: Dict[str, int] = {}  # Asset versions

    def add_asset(self, asset_id: str, version: int = 1) -> bool:
        """Add a new asset to the dependency graph.

        Args:
            asset_id: Unique identifier for the asset
            version: Initial version number

        Returns:
            bool: True if asset was added successfully
        """
        if not asset_id or not isinstance(asset_id, str):
            return False

        if asset_id in self._nodes:
            return False

        self._nodes.add(asset_id)
        self._edges[asset_id] = set()
        self._versions[asset_id] = version
        return True

    def add_dependency(self, asset_id: str, depends_on: str) -> bool:
        """Add a dependency relationship between assets.

        Args:
            asset_id: Asset that depends on another
            depends_on: Asset being depended upon

        Returns:
            bool: True if dependency was added without creating cycles
        """
        # Validate inputs
        if not asset_id or not depends_on:
            return False

        if asset_id not in self._nodes or depends_on not in self._nodes:
            return False

        # Check if dependency already exists
        if depends_on in self._edges[asset_id]:
            return True

        # Check for cycles before adding edge
        if self._would_create_cycle(asset_id, depends_on):
            return False

        # Add the dependency
        self._edges[asset_id].add(depends_on)
        return True

    def _would_create_cycle(self, from_node: str, to_node: str) -> bool:
        """Check if adding an edge would create a cycle in the graph.

        Args:
            from_node: Source node of new edge
            to_node: Target node of new edge

        Returns:
            bool: True if adding edge would create cycle
        """
        visited = set()

        def dfs(current: str) -> bool:
            if current == from_node:
                return True

            visited.add(current)
            for neighbor in self._edges[current]:
                if neighbor not in visited and dfs(neighbor):
                    return True
            visited.remove(current)
            return False

        return dfs(to_node)

    def get_dependencies(self, asset_id: str) -> Optional[Set[str]]:
        """Get all direct dependencies of an asset.

        Args:
            asset_id: Asset to get dependencies for

        Returns:
            Optional[Set[str]]: Set of asset dependencies, or None if not found
        """
        return self._edges.get(asset_id)
