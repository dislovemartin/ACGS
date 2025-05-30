# Import models from shared module to maintain consistency across services
try:
    from backend.shared.models import (
        Principle,
        ACMetaRule,
        ACAmendment,
        ACAmendmentVote,
        ACAmendmentComment,
        ACConflictResolution,
        User
    )
except ImportError:
    # Fallback for when shared models are not available
    # Define placeholder classes for development/testing
    class Principle:
        pass

    class ACMetaRule:
        pass

    class ACAmendment:
        pass

    class ACAmendmentVote:
        pass

    class ACAmendmentComment:
        pass

    class ACConflictResolution:
        pass

    class User:
        pass

# Re-export models for use in this service
__all__ = [
    "Principle",
    "ACMetaRule",
    "ACAmendment",
    "ACAmendmentVote",
    "ACAmendmentComment",
    "ACConflictResolution",
    "User"
]
