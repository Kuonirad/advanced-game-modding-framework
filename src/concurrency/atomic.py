"""Atomic operations and thread synchronization utilities.

This module implements atomic memory modifications and thread synchronization
mechanisms for safe game modding in multi-threaded environments.
"""

from threading import Lock
from typing import Callable, Dict, Optional


class AtomicModifier:
    """Handles atomic memory modifications with thread safety."""

    def __init__(self) -> None:
        """Initialize atomic modifier with synchronization primitives."""
        self._global_lock = Lock()
        self._region_locks: Dict[int, Lock] = {}
        self._active_regions: Dict[int, int] = {}  # Map address to size

    def atomic_patch(
        self,
        address: int,
        new_bytes: bytes,
        verify_callback: Optional[Callable[[bytes], bool]] = None,
    ) -> bool:
        """Apply a patch atomically with verification.

        Args:
            address: Memory address to patch
            new_bytes: New bytes to write
            verify_callback: Optional verification function

        Returns:
            bool: True if patch was applied successfully
        """
        # Acquire global lock first to prevent concurrent patches
        with self._global_lock:
            # Get or create region-specific lock
            region_lock = self._region_locks.setdefault(address, Lock())

            # Acquire region lock
            with region_lock:
                try:
                    # In a real implementation, we would:
                    # 1. Use OS-specific atomic write mechanisms
                    # 2. Ensure cache coherency with memory barriers
                    # 3. Handle partial write recovery

                    # Verify the patch if callback provided
                    if verify_callback and not verify_callback(new_bytes):
                        return False

                    # Simulate atomic write (use OS mechanisms in real impl)
                    # memory[address:address+len(new_bytes)] = new_bytes

                    return True
                except Exception:
                    # In real implementation: rollback partial changes
                    return False

    def ensure_thread_safety(self, address: int, size: int) -> bool:
        """Ensure thread-safe access to a memory region.

        Args:
            address: Start of memory region
            size: Size of region in bytes

        Returns:
            bool: True if thread safety can be guaranteed
        """
        # Check if region overlaps with any locked regions
        region_end = address + size

        with self._global_lock:
            # Check each active region for overlap
            for locked_addr, locked_size in list(self._active_regions.items()):
                locked_end = locked_addr + locked_size

                # Check for overlap - regions overlap if:
                # 1. New region starts before locked region ends AND
                # 2. Locked region starts before new region ends
                if address < locked_end and locked_addr < region_end:
                    return False

            # Region is safe, create a new lock for it
            self._region_locks[address] = Lock()
            self._active_regions[address] = size
            return True

    def release_region(self, address: int) -> None:
        """Release a previously locked memory region.

        Args:
            address: Start address of region to release

        Raises:
            KeyError: If the address is not an active region.
        """
        with self._global_lock:
            if address not in self._active_regions:
                raise KeyError(f"Address {hex(address)} is not an active region.")
            del self._region_locks[address]
            del self._active_regions[address]
