class MediaProcessingError(Exception):
    """Raised when video/image processing fails."""
    pass

class VectorDBError(Exception):
    """Raised when Vector DB operations fail."""
    pass

class FirestoreError(Exception):
    """Raised when Firestore operations fail."""
    pass
