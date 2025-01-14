"""Unit tests for asset dependency management."""

from src.assets.dag import AssetGraph


def test_asset_graph_initialization():
    """Test AssetGraph initialization."""
    graph = AssetGraph()
    assert len(graph._nodes) == 0
    assert len(graph._edges) == 0
    assert len(graph._versions) == 0


def test_add_asset():
    """Test adding assets to the graph."""
    graph = AssetGraph()

    # Test adding valid asset
    assert graph.add_asset("asset1") is True
    assert "asset1" in graph._nodes
    assert graph._versions["asset1"] == 1

    # Test adding duplicate asset
    assert graph.add_asset("asset1") is False

    # Test adding invalid asset
    assert graph.add_asset("") is False
    # Note: None test removed as it's not valid for str parameter


def test_add_dependency():
    """Test adding dependencies between assets."""
    graph = AssetGraph()

    # Add test assets
    graph.add_asset("asset1")
    graph.add_asset("asset2")
    graph.add_asset("asset3")

    # Test valid dependency
    assert graph.add_dependency("asset1", "asset2") is True
    assert "asset2" in graph._edges["asset1"]

    # Test cyclic dependency
    assert graph.add_dependency("asset2", "asset1") is False

    # Test chain dependency
    assert graph.add_dependency("asset2", "asset3") is True
    assert (
        graph.add_dependency("asset3", "asset1") is False
    )  # Would create cycle

    # Test invalid assets
    assert graph.add_dependency("nonexistent", "asset1") is False
    assert graph.add_dependency("asset1", "nonexistent") is False
