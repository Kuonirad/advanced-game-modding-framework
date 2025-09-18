"""Base classes and utilities for the game modding framework.

This module provides core functionality and base classes for implementing
safe game modifications with memory integrity checks.
"""

from typing import Dict, List, Optional, Set, Tuple


import threading


class ModFramework:
    """Base class for the game modding framework.

    Provides core functionality for managing memory modifications and
    security validation in game modding operations.

    Attributes:
        _memory_regions (Set[int]): Set of addresses of modified memory regions
        _hooks (Dict[int, bytes]): Maps hook addresses to original bytes
        _assets (Dict[str, List[str]]): Maps asset IDs to their dependencies
    """

    def __init__(self) -> None:
        """Initialize the modding framework with empty tracking structures.

        Returns:
            None
        """
        self._hooks: Dict[int, bytes] = {}
        self._assets: Dict[str, List[str]] = {}
        self._regions: List[Tuple[int, int]] = []   # (start, end) pairs
        self._lock = threading.Lock()

    def validate_memory_region(self, address: int, size: int) -> Tuple[bool, Optional[str]]:
        """Validate if a memory region is safe to modify.

        Args:
            address: Starting address of memory region
            size: Size of region in bytes

        Returns:
            Tuple[bool, Optional[str]]: A tuple containing:
                - bool: True if region is safe to modify, False otherwise
                - Optional[str]: Error message if validation failed, None if successful

        Raises:
            ValueError: If address is negative or size is not positive
        """
        if address < 0:
            raise ValueError("Memory address cannot be negative")
        if size <= 0:
            raise ValueError("Memory region size must be positive")

        new_start = address
        new_end   = address + size

        with self._lock:
            for existing_start, existing_end in self._regions:
                if not (new_end <= existing_start or new_start >= existing_end):
                    return False, f"Region overlaps with existing region " \
                                  f"0x{existing_start:x}-0x{existing_end:x}"
            # safe → reserve
            self._regions.append((new_start, new_end))
            return True, None

    def register_hook(self, address: int, original_bytes: bytes) -> bool:
        """Register a new hook at the specified address.

        Args:
            address: Memory address for hook
            original_bytes: Original bytes at hook location

        Returns:
            bool: True if hook was registered successfully

        Raises:
            ValueError: If address is None or original_bytes is empty
        """
        if address is None:
            raise ValueError("Hook address cannot be None")
        if not original_bytes:
            raise ValueError("Original bytes cannot be empty")
            
        # Check if hook already exists
        if address in self._hooks:
            return False
            
        # Store original bytes for potential restoration
        self._hooks[address] = original_bytes
        return True

    def reset_regions(self) -> None:
        with self._lock:
            self._regions.clear()
