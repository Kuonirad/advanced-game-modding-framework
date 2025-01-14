# API Documentation

## Overview

The Advanced Game Modding Framework provides a comprehensive API for safe and controlled game modifications. This documentation covers the core interfaces and their mathematical foundations.

## Core APIs

### Memory Management API

#### validate_memory_region
```python
def validate_memory_region(address: int, size: int) -> bool:
    """Validate if a memory region is safe to modify.
    
    Args:
        address (int): Starting address of the memory region to validate.
            Must be page-aligned (typically 4096 bytes).
        size (int): Size of the region in bytes. Must be non-zero and
            not exceed system memory limits.
    
    Returns:
        bool: True if the region is safe to modify, False if the region
            overlaps with protected memory or other hooks.
    
    Raises:
        ValueError: If address is not page-aligned or size is invalid.
        MemoryError: If unable to query memory protection status.
    
    Example:
        ```python
        # Check if a region is safe before patching
        if mod.validate_memory_region(0x140001000, 16):
            mod.atomic_patch(0x140001000, new_bytes)
        ```
    
    See Also:
        - [Memory Safety](../architecture/README.md#memory-safety)
        - atomic_patch() for applying modifications
        - register_hook() for function hooks
    """
```

#### register_hook
```python
def register_hook(address: int, original_bytes: bytes) -> bool:
    """Register a new hook at the specified memory address.
    
    Args:
        address (int): Target memory address for the hook. Must be a valid
            instruction boundary and executable memory region.
        original_bytes (bytes): Original instructions at the hook location.
            Used for validation and restoration.
    
    Returns:
        bool: True if hook was registered successfully, False if the
            location is already hooked or invalid.
    
    Raises:
        ValueError: If address is invalid or original_bytes is empty.
        SecurityError: If memory verification fails.
    
    Example:
        ```python
        # Hook a function entry point
        original = mod.read_memory(func_addr, 5)
        if mod.register_hook(func_addr, original):
            print("Hook registered successfully")
        ```
    
    Notes:
        - Hooks are applied atomically to prevent race conditions
        - Original bytes are verified before hook installation
        - Multiple hooks at the same location are not supported
    
    See Also:
        - [Hook Management](../architecture/README.md#hook-management)
        - validate_memory_region() for safety checks
        - atomic_patch() for applying the hook
    """
```

### Asset Management API

#### add_asset_dependency
```python
def add_asset_dependency(asset_id: str, depends_on: str) -> bool:
    """Add a dependency relationship between two assets.
    
    Args:
        asset_id (str): Identifier of the dependent asset.
        depends_on (str): Identifier of the required asset.
    
    Returns:
        bool: True if dependency was added, False if it would create
            a cycle or if either asset doesn't exist.
    
    Raises:
        ValueError: If either asset_id or depends_on is invalid.
        CyclicDependencyError: If adding the dependency would create a cycle.
    
    Example:
        ```python
        # Define asset dependencies
        mod.add_asset_dependency("custom_model.mdl", "textures.pak")
        mod.add_asset_dependency("textures.pak", "base_assets.pak")
        ```
    
    Notes:
        - Dependencies form a Directed Acyclic Graph (DAG)
        - Circular dependencies are not allowed
        - Missing assets are treated as errors
    
    See Also:
        - [Asset Dependencies](../architecture/README.md#asset-dependency-system)
        - verify_asset_graph() for validation
        - load_assets_topological() for ordered loading
    """
```

#### verify_asset_graph
```python
def verify_asset_graph() -> bool:
    """Verify the asset dependency graph's properties.
    
    Returns:
        bool: True if the graph is a valid DAG with all assets present,
            False if cycles exist or assets are missing.
    
    Raises:
        AssetError: If critical assets are missing or corrupted.
    
    Example:
        ```python
        # Verify dependencies before loading
        if mod.verify_asset_graph():
            mod.load_assets_topological()
        ```
    
    Notes:
        - Performs cycle detection using Kahn's algorithm
        - Validates all asset references exist
        - Checks asset version compatibility
    
    See Also:
        - [Asset Graph Verification](../models/README.md#asset-node)
        - add_asset_dependency() for adding edges
        - load_assets_topological() for loading
    """
```

### Concurrency Control API

#### atomic_patch
```python
def atomic_patch(address: int, new_bytes: bytes) -> bool:
    """Apply changes to memory with transactional guarantees.
    
    Args:
        address (int): Target memory address for the patch.
        new_bytes (bytes): New instructions or data to write.
    
    Returns:
        bool: True if patch was applied atomically, False if the
            operation failed or was rolled back.
    
    Raises:
        ValueError: If address or new_bytes is invalid.
        ConcurrencyError: If atomic operation fails.
    
    Example:
        ```python
        # Apply a patch atomically
        nop_sequence = b"\x90" * 5  # 5 NOP instructions
        if mod.atomic_patch(func_addr, nop_sequence):
            print("Patch applied successfully")
        ```
    
    Notes:
        - Uses hardware transactional memory when available
        - Falls back to spinlock-protected updates
        - Includes automatic rollback on failure
    
    See Also:
        - [Concurrency Control](../architecture/README.md#concurrency-control)
        - validate_memory_region() for safety checks
        - create_snapshot() for backup
    """
```

#### ensure_thread_safety
```python
def ensure_thread_safety(region: MemoryRegion) -> bool:
    """Verify thread-safe access to a memory region.
    
    Args:
        region (MemoryRegion): Memory region descriptor containing
            address, size, and protection flags.
    
    Returns:
        bool: True if the region can be accessed safely, False if
            concurrent access is detected.
    
    Raises:
        ValueError: If region is invalid.
        ThreadSafetyError: If safety guarantees cannot be established.
    
    Example:
        ```python
        # Check thread safety before modification
        region = MemoryRegion(addr=0x140001000, size=16)
        if mod.ensure_thread_safety(region):
            mod.atomic_patch(region.address, new_bytes)
        ```
    
    Notes:
        - Implements lock-free synchronization
        - Detects potential race conditions
        - Validates memory barriers
    
    See Also:
        - [Thread Safety](../architecture/README.md#concurrency-control)
        - atomic_patch() for safe modifications
        - validate_memory_region() for validation
    """
```

### Security API

#### verify_modification
```python
def verify_modification(patch: bytes, signature: bytes) -> bool:
    """Cryptographically verify a modification's authenticity.
    
    Args:
        patch (bytes): The modification payload to verify.
        signature (bytes): Cryptographic signature of the patch.
    
    Returns:
        bool: True if the signature is valid and patch is unmodified,
            False if verification fails.
    
    Raises:
        ValueError: If patch or signature is invalid.
        SecurityError: If cryptographic operations fail.
    
    Example:
        ```python
        # Verify a signed patch
        if mod.verify_modification(patch_data, patch_signature):
            mod.apply_verified_patch(patch_data)
        ```
    
    Notes:
        - Supports both classical and post-quantum signatures
        - Includes timestamp validation
        - Verifies against trusted authority keys
    
    See Also:
        - [Security Layer](../architecture/README.md#security-layer)
        - create_snapshot() for backup
        - atomic_patch() for applying verified changes
    """
```

#### create_snapshot
```python
def create_snapshot() -> bytes:
    """Create a restorable system snapshot.
    
    Returns:
        bytes: Serialized snapshot data that can be used for rollback.
    
    Raises:
        SnapshotError: If snapshot creation fails.
        ResourceError: If insufficient resources for snapshot.
    
    Example:
        ```python
        # Create backup before modifications
        snapshot = mod.create_snapshot()
        try:
            mod.apply_patches(patches)
        except Exception:
            mod.restore_snapshot(snapshot)
        ```
    
    Notes:
        - Includes memory state and asset references
        - Uses incremental storage for efficiency
        - Thread-safe snapshot creation
    
    See Also:
        - [Rollback System](../architecture/README.md#security-layer)
        - restore_snapshot() for recovery
        - verify_modification() for validation
    """
```

## Mathematical Foundations

### Memory Safety
- Region overlap detection using interval arithmetic
- Page alignment validation
- Instruction pointer safety verification

### Concurrency Guarantees
- Happens-before relation establishment
- Memory barrier placement
- Lock hierarchy maintenance

### Asset Dependencies
- DAG cycle detection algorithms
- Topological sorting implementation
- Version constraint satisfaction

For detailed implementation examples and best practices, see the [Architecture Documentation](../architecture/README.md).
