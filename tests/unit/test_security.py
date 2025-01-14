"""Unit tests for security validation and rollback mechanisms."""

import os
from base64 import b64decode, b64encode

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from src.security.validation import SecurityValidator


def generate_test_keypair():
    """Generate a test key pair for signatures."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    
    # Get PEM encoding of public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_key, public_key, public_pem


def test_security_validator_initialization():
    """Test SecurityValidator initialization."""
    validator = SecurityValidator()
    assert len(validator._checksums) == 0
    assert len(validator._backups) == 0
    assert len(validator._approved_keys) == 0


def test_compute_checksum():
    """Test checksum computation."""
    validator = SecurityValidator()
    test_data = b"test data"
    checksum = validator.compute_checksum(test_data)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 produces 64 hex chars


def test_key_management():
    """Test approved key management."""
    validator = SecurityValidator()
    
    # Generate test keys
    private_key, public_key, public_pem = generate_test_keypair()
    
    # Test adding valid key
    assert validator.add_approved_key(public_pem) is True
    assert len(validator._approved_keys) == 1
    
    # Test adding invalid key data
    with pytest.raises(ValueError):
        validator.add_approved_key(b"invalid key data")
        
    # Test adding duplicate key
    assert validator.add_approved_key(public_pem) is True
    assert len(validator._approved_keys) == 1  # Should not add duplicate


def test_validate_modification():
    """Test modification validation with signatures."""
    validator = SecurityValidator()
    
    # Generate test keys
    private_key, public_key, public_pem = generate_test_keypair()
    validator.add_approved_key(public_pem)
    
    # Test data
    test_data = b"test data"
    address = 0x1000
    
    # Create signature
    signature = private_key.sign(
        test_data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    # Test with valid signature
    success, error = validator.validate_modification(
        address, test_data, signature=signature
    )
    assert success is True
    assert error is None
    
    # Test with invalid signature
    bad_signature = os.urandom(256)  # Random invalid signature
    success, error = validator.validate_modification(
        address, test_data, signature=bad_signature
    )
    assert success is False
    assert error is not None and "Invalid signature" in error
    
    # Test with no signature (should pass if signatures not required)
    success, error = validator.validate_modification(address, test_data)
    assert success is True
    assert error is None
    
    # Test with checksum
    checksum = validator.compute_checksum(test_data)
    success, error = validator.validate_modification(
        0x2000, test_data, expected_checksum=checksum
    )
    assert success is True
    assert error is None
    
    # Test with incorrect checksum
    wrong_checksum = "0" * 64
    success, error = validator.validate_modification(
        0x3000, test_data, expected_checksum=wrong_checksum
    )
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
