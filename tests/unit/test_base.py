"""Unit tests for core framework functionality."""

import pytest
from src.core.base import ModFramework


def test_mod_framework_initialization():
    """Test ModFramework initialization."""
    framework = ModFramework()
    assert len(framework._memory_regions) == 0
    assert len(framework._hooks) == 0
    assert len(framework._assets) == 0
    assert framework._lock is not None


def test_validate_memory_region_success():
    """Test successful memory region validation for non-overlapping regions."""
    framework = ModFramework()
    is_valid, error = framework.validate_memory_region(0x1000, 16)
    assert is_valid is True
    assert error is None
    assert 0x1000 in framework._memory_regions


def test_validate_memory_region_invalid_inputs():
    """Test memory region validation with invalid inputs."""
    framework = ModFramework()
    with pytest.raises(ValueError, match="Memory address cannot be negative"):
        framework.validate_memory_region(-1, 16)
    with pytest.raises(ValueError, match="Memory region size must be positive"):
        framework.validate_memory_region(0x1000, 0)


def test_validate_memory_region_overlap():
    """Test that overlapping memory regions are correctly detected."""
    framework = ModFramework()
    # Add a region
    is_valid, error = framework.validate_memory_region(0x3000, 16)
    assert is_valid is True
    
    # Test overlap with the existing region
    is_valid, error = framework.validate_memory_region(0x3100, 16)  # Inside page
    assert is_valid is False
    assert error is not None and "overlaps with existing region" in error


def test_validate_memory_region_no_overlap_adjacent():
    """Test that adjacent but non-overlapping regions are considered valid."""
    framework = ModFramework()
    # Add a region
    is_valid, error = framework.validate_memory_region(0x3000, 4096) # Assume page size
    assert is_valid is True

    # Test next page, which should not overlap
    is_valid, error = framework.validate_memory_region(0x4000, 16)
    assert is_valid is True
    assert error is None


def test_validate_memory_region_boundary_conditions():
    """Test boundary conditions for memory region validation."""
    framework = ModFramework()
    # Add a region at 0x3000
    framework.validate_memory_region(0x3000, 16)

    # Test just before the page boundary
    is_valid, error = framework.validate_memory_region(0x2000, 16)
    assert is_valid is True
    assert error is None

    # Test just inside the page boundary of the existing region
    # Existing region starts at 0x3000, page ends at 0x3000 + 4096 = 0x3FFF
    is_valid, error = framework.validate_memory_region(0x3FF0, 16)
    assert is_valid is False
    assert error is not None and "overlaps with existing region" in error


def test_register_hook():
    """Test hook registration functionality."""
    framework = ModFramework()
    
    # Test basic hook registration
    assert framework.register_hook(0x1000, b"\x90\x90")  # NOP instructions
    assert 0x1000 in framework._hooks
    assert framework._hooks[0x1000] == b"\x90\x90"
    
    # Test duplicate hook registration
    assert not framework.register_hook(0x1000, b"\x90\x90")
    
    # Test hook with empty bytes
    with pytest.raises(ValueError):
        framework.register_hook(0x2000, b"")
    
    # Test invalid address
    with pytest.raises(ValueError):
        framework.register_hook(0, b"")


def test_memory_region_tracking():
    """Test memory region tracking functionality."""
    framework = ModFramework()
    
    # Validate and track regions
    framework.validate_memory_region(0x1000, 16)
    framework.validate_memory_region(0x2000, 16)
    
    # Verify tracking
    assert 0x1000 in framework._memory_regions
    assert 0x2000 in framework._memory_regions
    assert 0x3000 not in framework._memory_regions


def test_asset_dependency_tracking():
    """Test asset dependency tracking."""
    framework = ModFramework()
    
    # Add dependencies
    framework._assets["texture.png"] = ["base_texture.png"]
    framework._assets["model.obj"] = ["texture.png", "material.mtl"]
    
    # Verify dependencies
    assert "texture.png" in framework._assets
    assert "model.obj" in framework._assets
    assert framework._assets["model.obj"] == ["texture.png", "material.mtl"]
    assert framework._assets["texture.png"] == ["base_texture.png"]
