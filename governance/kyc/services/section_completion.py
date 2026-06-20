"""
governance/kyc/services/section_completion.py

Computes wizard-section completion and whether an application may be submitted.
Pure read logic plus validation rules; never mutates status.
"""
from __future__ import annotations

from decimal import Decimal

from governance.kyc.choices import AccountHoldingType
from governance.kyc.constants import (
    MAX_ADDITIONAL_JOINT_HOLDERS,
    SECTION_PERSONAL,
    SECTION_REQUIREMENTS,
    SECTION_RESIDENCE,
    SECTION_SOURCE_OF_WEALTH,
    SHARE_TOLERANCE,
    SHARE_TOTAL,
)
from governance.kyc.services import document_rules


def _has(application, attr) -> bool:
    return getattr(application, attr, None) is not None and hasattr(
        getattr(application, attr), "pk"
    )


def section_personal_complete(application) -> bool:
    if not _has(application, "personal_info"):
        return False
    pi = application.personal_info
    required = [pi.first_name, pi.last_name, pi.date_of_birth, pi.gender, pi.mobile, pi.email]
    if not all(required) or pi.nationality_id is None:
        return False
    # At least one identity document for the principal.
    return application.identity_documents.filter(joint_holder__isnull=True).exists()


def section_residence_complete(application) -> bool:
    if not _has(application, "residence"):
        return False
    res = application.residence
    if not res.permanent_address or res.permanent_country_id is None:
        return False
    if res.tax_status == "APPLICABLE" or res.fatca_applicable or res.crs_applicable:
        # Require at least one principal tax-residency row.
        if not application.residency_tax_rows.filter(joint_holder__isnull=True).exists():
            return False
    return True


def section_source_of_wealth_complete(application) -> bool:
    if not _has(application, "source_of_wealth"):
        return False
    sow = application.source_of_wealth
    return bool(sow.source_of_wealth and sow.source_of_funds)


def section_requirements_complete(application) -> bool:
    return not document_rules.missing_documents(application)


def joint_holder_rules_ok(application) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if application.account_holding_type != AccountHoldingType.JOINT:
        return True, errors

    holders = list(application.joint_holders.all())
    if len(holders) > MAX_ADDITIONAL_JOINT_HOLDERS:
        errors.append(
            f"At most {MAX_ADDITIONAL_JOINT_HOLDERS} additional joint holders are allowed."
        )

    principal_share = Decimal("0")
    if _has(application, "personal_info"):
        principal_share = application.personal_info.principal_share_percentage or Decimal("0")

    total = principal_share + sum((h.share_percentage or Decimal("0")) for h in holders)
    share_total = Decimal(str(SHARE_TOTAL))
    share_tolerance = Decimal(str(SHARE_TOLERANCE))

    if abs(total - share_total) > share_tolerance:
        errors.append(f"Holder shares must total {SHARE_TOTAL}% (currently {total}%).")

    return (not errors), errors


def section_status(application) -> dict[str, bool]:
    return {
        SECTION_PERSONAL: section_personal_complete(application),
        SECTION_RESIDENCE: section_residence_complete(application),
        SECTION_SOURCE_OF_WEALTH: section_source_of_wealth_complete(application),
        SECTION_REQUIREMENTS: section_requirements_complete(application),
    }


def is_submittable(application) -> tuple[bool, list[str]]:
    errors: list[str] = []
    status = section_status(application)
    for name, ok in status.items():
        if not ok:
            errors.append(f"Section '{name}' is incomplete.")
    _, joint_errors = joint_holder_rules_ok(application)
    errors.extend(joint_errors)
    return (not errors), errors