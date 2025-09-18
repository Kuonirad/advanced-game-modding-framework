"""Integration tests for memory management and concurrency control.

This module tests the interaction between memory management and concurrency
control systems to ensure thread-safe memory modifications.
"""

from src.core.base import ModFramework
from src.security.validation import SecurityValidator
import threading
import pytest


def test_concurrent_memory_validation():
    """Test concurrent memory region validation."""
    framework = ModFramework()
    validator = SecurityValidator()
    
    # Test addresses and data
    addresses = [0x1000, 0x1010, 0x1020, 0x1030]  # These addresses are within the same 4k page
    test_data = b"test data"
    results = []
    
    def validate_region(address):
        """Validate memory region in a thread."""
        # Validate memory region
        is_valid, _ = framework.validate_memory_region(address, len(test_data))
        # Validate modification if region is valid
        if is_valid:
            success, _ = validator.validate_modification(address, test_data)
            results.append(success)
        else:
            results.append(False)
    
    # Create threads for concurrent validation
    threads = [
        threading.Thread(target=validate_region, args=(addr,))
        for addr in addresses
    ]
    
    # Start all threads
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify results
    assert len(results) == len(addresses)
    assert any(results), "At least one modification should succeed"
    # Not all should succeed due to overlap prevention
    assert not all(results), "Not all modifications should succeed"


def test_memory_integrity_after_concurrent_access():
    """Test memory integrity after concurrent modifications."""
    framework = ModFramework()
    validator = SecurityValidator()
    
    # Test data
    address = 0x5000
    original_data = b"original"
    new_data = b"modified"
    
    # First modification
    assert framework.validate_memory_region(address, len(original_data))
    success, _ = validator.validate_modification(address, original_data)
    assert success
    
    # Attempt concurrent modifications
    def modify_memory():
        """Attempt to modify memory in a thread."""
        if framework.validate_memory_region(address, len(new_data)):
            validator.validate_modification(address, new_data)
    
    threads = [
        threading.Thread(target=modify_memory)
        for _ in range(5)
    ]
    
    # Start concurrent modification attempts
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Verify final state
    assert address in validator._checksums, "Address should be tracked"
    final_checksum = validator.compute_checksum(new_data)
    assert validator._checksums[address] == final_checksum


def test_rollback_during_concurrent_access():
    """Test rollback functionality during concurrent access."""
    framework = ModFramework()
    validator = SecurityValidator()
    
    # Test data
    address = 0x6000
    test_data = b"test data"
    
    # Initial modification
    assert framework.validate_memory_region(address, len(test_data))
    success, _ = validator.validate_modification(address, test_data)
    assert success
    
    # Track rollback success
    rollback_results = []
    
    def concurrent_operation(op_type):
        """Perform either modification or rollback."""
        if op_type == "modify":
            if framework.validate_memory_region(address, len(test_data)):
                validator.validate_modification(address, b"new data")
        else:  # rollback
            success = validator.rollback_modification(address)
            rollback_results.append(success)
    
    # Create mixed threads for modification and rollback
    threads = (
        [threading.Thread(target=concurrent_operation, args=("modify",))
         for _ in range(3)] +
        [threading.Thread(target=concurrent_operation, args=("rollback",))
         for _ in range(2)]
    )
    
    # Run concurrent operations
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # Verify rollback results
    assert len(rollback_results) > 0, "Some rollback attempts should complete"
    # At least one rollback should succeed
    assert any(rollback_results), "At least one rollback should succeed"
