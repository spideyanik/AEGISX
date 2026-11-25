"""Application exceptions translated into safe CLI errors."""


class AegisXError(Exception):
    """Base class for expected AEGISX errors."""


class WorkspaceNotInitializedError(AegisXError):
    """Raised when a command needs an initialized workspace."""


class ConfigurationError(AegisXError):
    """Raised when workspace configuration is invalid."""


class ValidationError(AegisXError):
    """Raised when a domain value fails validation."""


class AuthorizationError(AegisXError):
    """Raised when explicit authorization is missing or expired."""


class NotFoundError(AegisXError):
    """Raised when an entity cannot be found."""


class ConflictError(AegisXError):
    """Raised when an entity conflicts with an existing record."""
