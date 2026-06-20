"""
governance/kyc/permissions.py

Single source of KYC authorization. Capability is resolved through
`user.staff_profile`. Broad gating uses the verified StaffProfile helper
properties (is_rm / is_compliance / is_senior_mgmt); terminal authority uses the
exact verified role codes from users.choices.UserRole. No parallel role logic.

Verified UserRole codes: client, rm, compliance_l1, senior_mgmt,
compliance_final, admin.
"""
from __future__ import annotations

from governance.kyc.choices import ApplicationStatus


# Exact role codes (mirror users.choices.UserRole — verified).
ROLE_CLIENT = "client"
ROLE_RM = "rm"
ROLE_COMPLIANCE_L1 = "compliance_l1"
ROLE_SENIOR_MGMT = "senior_mgmt"
ROLE_COMPLIANCE_FINAL = "compliance_final"
ROLE_ADMIN = "admin"


# --------------------------------------------------------------------------- #
# Profile / role resolution                                                   #
# --------------------------------------------------------------------------- #
def get_staff_profile(user):
    """Return the user's StaffProfile or None (clients may not have privileged role)."""
    if not user or not user.is_authenticated:
        return None
    return getattr(user, "staff_profile", None)


def _role(user) -> str | None:
    profile = get_staff_profile(user)
    return getattr(profile, "role", None) if profile else None


def is_rm(user) -> bool:
    profile = get_staff_profile(user)
    return bool(profile and profile.is_rm)


def is_compliance(user) -> bool:
    profile = get_staff_profile(user)
    return bool(profile and profile.is_compliance)


def is_senior_mgmt(user) -> bool:
    profile = get_staff_profile(user)
    return bool(profile and profile.is_senior_mgmt)


def is_compliance_final(user) -> bool:
    return _role(user) == ROLE_COMPLIANCE_FINAL


def is_admin(user) -> bool:
    return _role(user) == ROLE_ADMIN or bool(user and user.is_superuser)


def staff_market(user) -> str | None:
    profile = get_staff_profile(user)
    return getattr(profile, "market", None) if profile else None


def in_market_scope(user, application) -> bool:
    """A reviewer sees an application only within their market, unless market == ALL."""
    market = staff_market(user)
    if market is None:
        return False
    return market == "ALL" or market == application.onboarding_market.code


def is_owner(user, application) -> bool:
    return bool(user and application.owner_user_id == user.id)


# --------------------------------------------------------------------------- #
# Capability checks                                                           #
# --------------------------------------------------------------------------- #
def can_view(user, application) -> bool:
    """Owner sees own; staff see within market scope; admin sees all."""
    if is_admin(user):
        return True
    if is_owner(user, application):
        return True
    if is_rm(user) or is_compliance(user) or is_senior_mgmt(user):
        return in_market_scope(user, application)
    return False


def can_edit(user, application) -> bool:
    """Editable only in DRAFT or ADDL_INFO, by the owner client or an RM."""
    if application.application_status not in (
        ApplicationStatus.DRAFT,
        ApplicationStatus.ADDL_INFO,
    ):
        return False
    return is_owner(user, application) or is_rm(user)


def can_submit(user, application) -> bool:
    return is_owner(user, application) or is_rm(user)


def can_start_review(user, application) -> bool:
    return is_compliance(user) and in_market_scope(user, application)


def can_request_info(user, application) -> bool:
    return is_compliance(user) and in_market_scope(user, application)


def can_escalate(user, application) -> bool:
    return is_compliance(user) and in_market_scope(user, application)


def can_approve(user, application) -> bool:
    """
    UNDER_REVIEW  -> only compliance_final may sign off.
    ESCALATED     -> senior management or compliance_final.
    """
    if not in_market_scope(user, application) and not is_admin(user):
        return False
    if application.application_status == ApplicationStatus.ESCALATED:
        return is_senior_mgmt(user) or is_compliance_final(user)
    if application.application_status == ApplicationStatus.UNDER_REVIEW:
        return is_compliance_final(user)
    return False


def can_reject(user, application) -> bool:
    if not in_market_scope(user, application) and not is_admin(user):
        return False
    return is_compliance_final(user) or is_senior_mgmt(user)


def can_supersede(user, application) -> bool:
    return is_admin(user) or is_compliance(user)