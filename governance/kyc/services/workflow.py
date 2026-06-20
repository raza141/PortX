"""
governance/kyc/services/workflow.py

The single place `application_status` changes. Validates the transition, checks
authorization (permissions.py), enforces maker-checker separation of duties,
mutates status, writes an append-only KYCStatusLog row, and triggers the minimal
CRM handoff on approval.
"""
from __future__ import annotations

from django.db import transaction

from governance.kyc import permissions
from governance.kyc.choices import ApplicationStatus as S
from governance.kyc.choices import StatusAction as A
from governance.kyc.services.exceptions import (
    KYCPermissionDenied,
    SeparationOfDutiesError,
    TransitionNotAllowed,
)

# Legal transitions: (from_status, action) -> to_status
TRANSITIONS: dict[tuple[str, str], str] = {
    (S.DRAFT, A.SUBMIT): S.SUBMITTED,
    (S.SUBMITTED, A.START_REVIEW): S.UNDER_REVIEW,
    (S.UNDER_REVIEW, A.REQUEST_INFO): S.ADDL_INFO,
    (S.ADDL_INFO, A.RESUBMIT): S.UNDER_REVIEW,
    (S.UNDER_REVIEW, A.ESCALATE): S.ESCALATED,
    (S.UNDER_REVIEW, A.APPROVE): S.APPROVED,
    (S.ESCALATED, A.APPROVE): S.APPROVED,
    (S.UNDER_REVIEW, A.REJECT): S.REJECTED,
    (S.ESCALATED, A.REJECT): S.REJECTED,
}

# Action -> permission predicate (user, application) -> bool
_PERMISSION_FOR_ACTION = {
    A.SUBMIT: permissions.can_submit,
    A.RESUBMIT: permissions.can_submit,
    A.START_REVIEW: permissions.can_start_review,
    A.REQUEST_INFO: permissions.can_request_info,
    A.ESCALATE: permissions.can_escalate,
    A.APPROVE: permissions.can_approve,
    A.REJECT: permissions.can_reject,
}

# Decisions that must not be made by the person who submitted the version.
_CHECKER_ACTIONS = {A.APPROVE, A.REJECT}
_SUBMIT_ACTIONS = {A.SUBMIT, A.RESUBMIT}


def get_allowed_actions(application, user) -> list[str]:
    """Actions currently permitted for this user on this application."""
    allowed = []
    for (from_status, action), _to in TRANSITIONS.items():
        if from_status != application.application_status:
            continue
        predicate = _PERMISSION_FOR_ACTION.get(action)
        if predicate and predicate(user, application):
            allowed.append(action)
    return allowed


def _last_submitter_id(application):
    """User id of the most recent SUBMIT/RESUBMIT actor (the 'maker')."""
    log = (
        application.status_logs.filter(action__in=list(_SUBMIT_ACTIONS))
        .order_by("-created_at")
        .values_list("actor_id", flat=True)
        .first()
    )
    return log


@transaction.atomic
def transition(application, action: str, actor, reason: str | None = None):
    """
    Apply a workflow transition.
    Raises TransitionNotAllowed / KYCPermissionDenied / SeparationOfDutiesError.
    Returns the updated application.
    """
    # Lock the row for the duration of the transition.
    application = type(application).objects.select_for_update().get(pk=application.pk)

    from_status = application.application_status
    key = (from_status, action)
    if key not in TRANSITIONS:
        raise TransitionNotAllowed(f"{action} is not allowed from {from_status}.")

    predicate = _PERMISSION_FOR_ACTION.get(action)
    if predicate is None or not predicate(actor, application):
        raise KYCPermissionDenied(f"User not authorized for {action} on {application.application_number}.")

    # Maker-checker: an approver/rejecter cannot be the submitter of this version.
    if action in _CHECKER_ACTIONS:
        submitter_id = _last_submitter_id(application)
        if submitter_id is not None and submitter_id == getattr(actor, "id", None):
            raise SeparationOfDutiesError("The submitter cannot decide their own application.")

    to_status = TRANSITIONS[key]
    application.application_status = to_status
    application.updated_by = actor
    application.save(update_fields=["application_status", "updated_by", "updated_at"])

    application.status_logs.create(
        from_status=from_status,
        to_status=to_status,
        action=action,
        actor=actor,
        reason=reason,
    )

    if to_status == S.APPROVED:
        from governance.kyc.services import crm_handoff
        transaction.on_commit(lambda: crm_handoff.on_approved(application, actor))

    return application


@transaction.atomic
def supersede(application, actor, reason: str | None = None):
    """
    Re-KYC: create a new DRAFT version linked to the (APPROVED/REJECTED) prior one.
    Permission via permissions.can_supersede. Returns the new application.
    """
    if application.application_status not in (S.APPROVED, S.REJECTED):
        raise TransitionNotAllowed("Only approved or rejected applications can be superseded.")
    if not permissions.can_supersede(actor, application):
        raise KYCPermissionDenied("User not authorized to supersede.")

    from governance.kyc.models import KYCApplication
    from governance.kyc.services import application_number

    new_app = KYCApplication.objects.create(
        owner_user=application.owner_user,
        investor=application.investor,
        referral_source=application.referral_source,
        application_number=application_number.allocate(application.onboarding_market.code),
        onboarding_market=application.onboarding_market,
        application_status=S.DRAFT,
        account_holding_type=application.account_holding_type,
        client_classification=application.client_classification,
        initiation_channel=application.initiation_channel,
        version=application.version + 1,
        supersedes=application,
        created_by=actor,
    )
    new_app.status_logs.create(
        from_status=None,
        to_status=S.DRAFT,
        action=A.SUPERSEDE,
        actor=actor,
        reason=reason,
    )
    return new_app