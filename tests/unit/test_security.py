"""Unit tests for security validation and rollback mechanisms."""
import pytest
from src.security.validation import SecurityValidator

def test_security_validator_initialization():
    """Test SecurityValidator initialization."""
    validator = SecurityValidator()
    assert len(validator._checksums) == 0
    assert len(validator._backups) == 0

def test_compute_checksum():
    """Test checksum computation."""
    validator = SecurityValidator()
    test_data = b"test data"
    checksum = validator.compute_checksum(test_data)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 produces 64 hex chars

def test_validate_modification():
    """Test modification validation."""
    validator = SecurityValidator()
    
    # Test basic modification
    success, error = validator.validate_modification(0x1000, b"test")
    assert success is True
    assert error is None
    
    # Test with expected checksum
    test_data = b"test data"
    checksum = validator.compute_checksum(test_data)
    success, error = validator.validate_modification(0x2000, test_data, checksum)
    assert success is True
    assert error is None
    
    # Test with incorrect checksum
    wrong_checksum = "0" * 64
    success, error = validator.validate_modification(0x3000, test_data, wrong_checksum)
    assert success is False
    assert error is not None and "Checksum mismatch" in error

def test_rollback_modification():
    """Test modification rollback functionality."""
    validator = SecurityValidator()
    
    # Setup test modification
    address = 0x1000
    test_data = b"test data"
    validator.validate_modification(address, test_data)
    
    # Test successful rollback
    assert validator.rollback_modification(address) is True
    assert address not in validator._backups
    assert address not in validator._checksums
    
    # Test rollback of non-existent modification
    assert validator.rollback_modification(0x2000) is False
