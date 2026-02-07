"""Duplicate document detection service."""

from backend.domain.value_objects import FileHash


class DuplicateChecker:
    """Service to detect duplicate documents by file hash.

    Uses a simple in-memory set of known hashes. In production,
    this would query the DocumentRepository.
    """

    def __init__(self, known_hashes: set[str] | None = None) -> None:
        """Initialize checker with known hashes.

        Args:
            known_hashes: Set of hash values already in the system
        """
        self._known_hashes = known_hashes or set()

    def is_duplicate(self, file_hash: FileHash) -> bool:
        """Check if a file hash already exists.

        Args:
            file_hash: Hash of the file to check

        Returns:
            True if the hash is already known (duplicate)
        """
        return file_hash.value in self._known_hashes

    def add_hash(self, file_hash: FileHash) -> None:
        """Add a hash to the known set.

        Args:
            file_hash: Hash to add
        """
        self._known_hashes.add(file_hash.value)

    def remove_hash(self, file_hash: FileHash) -> None:
        """Remove a hash from the known set.

        Args:
            file_hash: Hash to remove
        """
        self._known_hashes.discard(file_hash.value)
