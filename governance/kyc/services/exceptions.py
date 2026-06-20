"""governance/kyc/services/exceptions.py — typed errors raised by KYC services."""


class KYCServiceError(Exception):
    """Base class for KYC service errors."""


class TransitionNotAllowed(KYCServiceError):
    """The requested (status, action) pair is not a legal transition."""


class KYCPermissionDenied(KYCServiceError):
    """The actor is not authorized to perform the requested action."""


class SeparationOfDutiesError(KYCServiceError):
    """The actor cannot approve/decide an application they submitted (maker-checker)."""


class ApplicationNumberError(KYCServiceError):
    """Failed to allocate a unique application number."""