"""Unit tests for core framework functionality."""

import pytest
from src.core.base import ModFramework


def test_mod_framework_initialization():
    """Test ModFramework initialization."""
    framework = ModFramework()
    assert len(framework._memory_regions) == 0
    assert len(framework._hooks) == 0
    assert len(framework._assets) == 0


def test_validate_memory_region():
    """Test memory region validation."""
    framework = ModFramework()
    
    # Test non-overlapping regions
    is_valid, error = framework.validate_memory_region(0x1000, 16)
    assert is_valid and error is None
    
    is_valid, error = framework.validate_memory_region(0x2000, 16)
    assert is_valid and error is None
    
    # Test invalid inputs
    with pytest.raises(ValueError, match="Memory address cannot be negative"):
        framework.validate_memory_region(-1, 16)
    
    with pytest.raises(ValueError, match="Memory region size must be positive"):
        framework.validate_memory_region(0x1000, 0)
    
    # Add a region and test overlap
    framework._memory_regions.add(0x3000)
    
    # Test overlap with existing region (4096 byte pages)
    is_valid, error = framework.validate_memory_region(0x3100, 16)  # Inside page
    assert not is_valid
    assert error is not None and "overlaps with existing region" in error
    
    is_valid, error = framework.validate_memory_region(0x4000, 16)  # Next page
    assert is_valid and error is None
    
    # Test boundary conditions
    is_valid, error = framework.validate_memory_region(0x2F00, 16)  # Just before
    assert is_valid and error is None
    
    is_valid, error = framework.validate_memory_region(0x3FF0, 16)  # Just inside
    assert not is_valid
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
    assert framework.validate_memory_region(0x1000, 16)
    framework._memory_regions.add(0x1000)
    
    assert framework.validate_memory_region(0x2000, 16)
    framework._memory_regions.add(0x2000)
    
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
