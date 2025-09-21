"""Unit tests for concurrency control and atomic operations."""
import pytest
from src.concurrency.atomic import AtomicModifier


def test_atomic_modifier_initialization():
    """Test AtomicModifier initialization."""
    modifier = AtomicModifier()
    assert modifier._global_lock is not None
    assert len(modifier._region_locks) == 0


def test_atomic_patch():
    """Test atomic patching functionality."""
    modifier = AtomicModifier()

    # Test basic patch
    assert modifier.atomic_patch(0x1000, b"test") is True

    # Test patch with verification
    def verify_callback(data: bytes) -> bool:
        return len(data) == 4

    assert modifier.atomic_patch(0x2000, b"test", verify_callback) is True
    assert modifier.atomic_patch(0x3000, b"toolong", verify_callback) is False

    # Test concurrent patches to same region
    import threading

    results = []

    def concurrent_patch():
        result = modifier.atomic_patch(0x4000, b"test")
        results.append(result)

    threads = [threading.Thread(target=concurrent_patch) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # All patches should succeed due to proper locking
    assert all(results)


def test_ensure_thread_safety():
    """Test thread safety verification."""
    modifier = AtomicModifier()

    # Test non-overlapping regions
    assert modifier.ensure_thread_safety(0x1000, 4096) is True
    assert modifier.ensure_thread_safety(0x2000, 4096) is True

    # Test overlapping regions
    assert modifier.ensure_thread_safety(0x1500, 4096) is False

    # Test region release
    modifier.release_region(0x1000)
    # Try to lock a region that doesn't overlap with 0x2000-0x3000
    assert modifier.ensure_thread_safety(0x1000, 4096) is True


def test_release_non_existent_region():
    """Test that releasing a non-existent region raises an error."""
    modifier = AtomicModifier()
    modifier.ensure_thread_safety(0x1000, 100)
    with pytest.raises(KeyError, match="Address 0x2000 is not an active region."):
        modifier.release_region(0x2000)
