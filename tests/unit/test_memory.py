"""Unit tests for memory integrity and validation functionality."""

from src.memory.integrity import MemoryValidator


def test_memory_validator_initialization():
    """Test MemoryValidator initialization."""
    validator = MemoryValidator()
    assert validator._page_size == 4096


def test_check_region_integrity():
    """Test memory region integrity checking."""
    validator = MemoryValidator()

    # Test valid aligned region
    result, error = validator.check_region_integrity(0x1000, 4096)
    assert result is True
    assert error is None

    # Test unaligned address
    result, error = validator.check_region_integrity(0x1001, 4096)
    assert result is False
    assert error is not None and "not page-aligned" in error

    # Test invalid size
    result, error = validator.check_region_integrity(0x1000, 0)
    assert result is False
    assert error is not None and "must be positive" in error

    # Test oversized region
    result, error = validator.check_region_integrity(0x1000, 4096 * 1025)
    assert result is False
    assert error is not None and "exceeds maximum" in error


def test_validate_instruction_pointer():
    """Test instruction pointer validation."""
    validator = MemoryValidator()

    # Test valid aligned pointer
    assert validator.validate_instruction_pointer(0x2000) is True

    # Test unaligned pointer
    assert validator.validate_instruction_pointer(0x2001) is False

    # Test invalid address range
    assert validator.validate_instruction_pointer(-1) is False
    assert validator.validate_instruction_pointer(2**64) is False
