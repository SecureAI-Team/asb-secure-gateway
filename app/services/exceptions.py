"""Shared service-layer exceptions."""


class PolicyDeniedError(Exception):
    """Raised when OPA denies a request."""

    def __init__(self, reason: str | None = None) -> None:
        message = reason or "Request blocked by policy"
        super().__init__(message)
        self.reason = reason

