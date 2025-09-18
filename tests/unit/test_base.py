"""Unit tests for core framework functionality."""

import pytest
from src.core.base import ModFramework


@pytest.fixture
def framework():
    """Pytest fixture to provide a clean ModFramework instance for each test."""
    fw = ModFramework()
    yield fw
    # Teardown: ensure regions are cleared after test
    fw.reset_regions()


def test_mod_framework_initialization(framework):
    """Test ModFramework initialization."""
    assert len(framework._regions) == 0
    assert len(framework._hooks) == 0
    assert len(framework._assets) == 0
    assert framework._lock is not None


def test_validate_memory_region_success(framework):
    """Test successful validation of a single, valid memory region."""
    is_valid, error = framework.validate_memory_region(0x1000, 16)
    assert is_valid is True
    assert error is None
    assert framework._regions == [(0x1000, 0x1000 + 16)]


def test_validate_memory_region_invalid_inputs(framework):
    """Test validation with invalid arguments."""
    with pytest.raises(ValueError, match="Memory address cannot be negative"):
        framework.validate_memory_region(-1, 16)
    with pytest.raises(ValueError, match="Memory region size must be positive"):
        framework.validate_memory_region(0x1000, 0)


def test_validate_memory_region_overlap(framework):
    """Test that an overlapping region is correctly identified."""
    framework.validate_memory_region(0x1000, 100)  # Reserve 0x1000 - 0x1064
    is_valid, error = framework.validate_memory_region(0x1020, 16)  # Attempt to reserve overlapping region
    assert is_valid is False
    assert "overlaps with existing region" in error


def test_validate_memory_region_no_overlap(framework):
    """Test that non-overlapping regions are validated successfully."""
    framework.validate_memory_region(0x1000, 100)
    is_valid, error = framework.validate_memory_region(0x2000, 16)
    assert is_valid is True
    assert error is None
    assert len(framework._regions) == 2


def test_register_hook(framework):
    """Test hook registration functionality."""
    assert framework.register_hook(0x1000, b"\x90\x90")
    assert 0x1000 in framework._hooks
    assert framework._hooks[0x1000] == b"\x90\x90"
    
    assert not framework.register_hook(0x1000, b"\x90\x90")
    
    with pytest.raises(ValueError, match="Original bytes cannot be empty"):
        framework.register_hook(0x2000, b"")
    
    with pytest.raises(ValueError, match="Hook address cannot be None"):
        framework.register_hook(None, b"test")


def test_memory_region_tracking(framework):
    """Test memory region tracking functionality."""
    framework.validate_memory_region(0x1000, 16)
    framework.validate_memory_region(0x2000, 16)
    
    assert (0x1000, 0x1010) in framework._regions
    assert (0x2000, 0x2010) in framework._regions
    assert not any(r[0] == 0x3000 for r in framework._regions)


def test_asset_dependency_tracking(framework):
    """Test asset dependency tracking."""
    framework._assets["texture.png"] = ["base_texture.png"]
    framework._assets["model.obj"] = ["texture.png", "material.mtl"]
    
    assert "texture.png" in framework._assets
    assert framework._assets["model.obj"] == ["texture.png", "material.mtl"]
