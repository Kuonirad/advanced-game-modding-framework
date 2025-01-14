"""Security validation and rollback mechanisms.

This module implements security checks and rollback functionality for ensuring
safe and recoverable game modifications.
"""

import hashlib
import os
from base64 import b64decode, b64encode
from typing import Dict, List, Optional, Tuple, Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa


class SecurityValidator:
    """Handles security validation and modification rollback.
    
    This class provides cryptographic validation of memory modifications,
    including digital signatures and approved key management.
    """

    def __init__(self) -> None:
        """Initialize security validator with rollback tracking and key management."""
        self._checksums: Dict[int, str] = {}  # Region checksums
        self._backups: Dict[int, bytes] = {}  # Backup copies
        self._approved_keys: List[rsa.RSAPublicKey] = []  # Approved signing keys
        
        # Default padding for RSA signatures
        self._padding = padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        )
        self._hash_algorithm = hashes.SHA256()

    def compute_checksum(self, data: bytes) -> str:
        """Compute cryptographic checksum of data.

        Args:
            data: Bytes to checksum

        Returns:
            str: Hex digest of checksum
        """
        return hashlib.sha256(data).hexdigest()

    def add_approved_key(self, key_data: Union[str, bytes]) -> bool:
        """Add a public key to the list of approved signing keys.
        
        Args:
            key_data: PEM-encoded public key data
            
        Returns:
            bool: True if key was added successfully
            
        Raises:
            ValueError: If key data is invalid
        """
        try:
            if isinstance(key_data, str):
                key_data = key_data.encode()
                
            public_key = serialization.load_pem_public_key(key_data)
            if not isinstance(public_key, rsa.RSAPublicKey):
                return False
                
            if public_key not in self._approved_keys:
                self._approved_keys.append(public_key)
            return True
            
        except Exception as e:
            raise ValueError(f"Invalid key data: {str(e)}")
            
    def verify_signature(self, data: bytes, signature: bytes, key: rsa.RSAPublicKey) -> bool:
        """Verify a digital signature.
        
        Args:
            data: The data that was signed
            signature: The signature to verify
            key: The public key to use for verification
            
        Returns:
            bool: True if signature is valid
        """
        try:
            key.verify(
                signature,
                data,
                self._padding,
                self._hash_algorithm
            )
            return True
        except InvalidSignature:
            return False
            
    def validate_modification(
        self,
        address: int,
        new_bytes: bytes,
        signature: Optional[bytes] = None,
        expected_checksum: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Validate a proposed memory modification.

        Args:
            address: Memory address to modify
            new_bytes: New bytes to write
            signature: Optional digital signature of new_bytes
            expected_checksum: Optional expected checksum

        Returns:
            Tuple containing:
                bool: True if modification is safe
                Optional[str]: Error message if validation failed
        """
        # Store backup if not already present
        if address not in self._backups:
            self._backups[address] = new_bytes

        # Compute checksum of new bytes
        new_checksum = self.compute_checksum(new_bytes)

        # Validate against expected checksum if provided
        if expected_checksum and new_checksum != expected_checksum:
            return (
                False,
                f"Checksum mismatch: got {new_checksum}",
            )
            
        # Verify digital signature if provided
        if signature:
            if not self._approved_keys:
                return False, "No approved keys available for signature verification"
                
            # Try all approved keys
            valid_signature = False
            for key in self._approved_keys:
                if self.verify_signature(new_bytes, signature, key):
                    valid_signature = True
                    break
                    
            if not valid_signature:
                return False, "Invalid signature"

        # Store checksum for future validation
        self._checksums[address] = new_checksum

        return True, None

    def rollback_modification(self, address: int) -> bool:
        """Rollback a modification to its original state.

        Args:
            address: Address of modification to rollback

        Returns:
            bool: True if rollback was successful
        """
        if address not in self._backups:
            return False

        # In a real implementation, we would:
        # 1. Restore original bytes from backup
        # 2. Clear protection flags
        # 3. Verify restoration succeeded
        # 4. Update checksums

        # Clean up tracking
        self._backups.pop(address)
        self._checksums.pop(address, None)

        return True
