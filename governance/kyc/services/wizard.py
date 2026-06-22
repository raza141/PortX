"""
governance/kyc/services/wizard.py

Step registry for the resumable onboarding wizard. One ordered list defines the
flow; each step declares the one-to-one section form(s) and the repeating-group
formsets it owns. Completion per step reuses section_completion so the step
indicator and the submit gate never disagree.

The wizard is server-rendered and save-per-step: each step persists to the DRAFT
before advancing, so a closed tab or a validation error never loses prior steps.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from governance.kyc.choices import AccountHoldingType
from governance.kyc.forms.dynamic_rows import GROUP_FORMSETS, GROUP_TEMPLATES
from governance.kyc.forms.section_1 import KYCPersonalInfoForm
from governance.kyc.forms.section_2 import KYCResidenceForm
from governance.kyc.forms.section_3 import KYCEmploymentForm, KYCSourceOfWealthForm
from governance.kyc.services import section_completion as sc
from governance.kyc.choices import DocumentType
from governance.kyc.models import KYCDocument
from governance.kyc.services import document_slots


@dataclass(frozen=True)
class WizardStep:
    key: str
    label: str
    # one-to-one forms: tuples of (related_name, FormClass, needs_market)
    forms: tuple = field(default_factory=tuple)
    # repeating-group formset keys (must exist in GROUP_FORMSETS)
    groups: tuple = field(default_factory=tuple)
    review: bool = False


STEPS: tuple[WizardStep, ...] = (
    WizardStep(
        "personal", "Personal",
        forms=(("personal_info", KYCPersonalInfoForm, True),),
        groups=("identity",),
    ),
    WizardStep(
        "residence", "Residence & Tax",
        forms=(("residence", KYCResidenceForm, True),),
        groups=("residency",),
    ),
    WizardStep(
        "financial", "Financial",
        forms=(
            ("source_of_wealth", KYCSourceOfWealthForm, True),
            ("employment", KYCEmploymentForm, False),
        ),
        groups=("bank_account",),
    ),
    WizardStep(
        "parties", "Parties",
        groups=("joint_holder", "nominee", "poa"),
    ),
    WizardStep(
        "documents", "Documents",
        groups=("document",),
    ),
    WizardStep("review", "Review & Submit", review=True),
)

STEP_BY_KEY = {s.key: s for s in STEPS}
STEP_KEYS = [s.key for s in STEPS]

# Human labels for the one-to-one section cards.
FORM_LABELS = {
    "personal_info": "Personal Information",
    "residence": "Residence, FATCA & CRS",
    "source_of_wealth": "Source of Wealth & Funds",
    "employment": "Employment",
}

# Human labels for the repeating-group cards.
GROUP_LABELS = {
    "identity": "Identity Documents",
    "residency": "Tax Residencies",
    "joint_holder": "Joint Holders",
    "nominee": "Nominees",
    "bank_account": "Bank Accounts",
    "poa": "Power of Attorney",
    "document": "Documents",
}


def next_key(key: str) -> str | None:
    i = STEP_KEYS.index(key)
    return STEP_KEYS[i + 1] if i + 1 < len(STEP_KEYS) else None


def prev_key(key: str) -> str | None:
    i = STEP_KEYS.index(key)
    return STEP_KEYS[i - 1] if i > 0 else None


def groups_for(application, step: WizardStep) -> tuple[str, ...]:
    """Formset groups for a step, dropping joint-holders when holding is SINGLE."""
    groups = []
    for g in step.groups:
        if g == "joint_holder" and application.account_holding_type != AccountHoldingType.JOINT:
            continue
        groups.append(g)
    return tuple(groups)


def step_complete(application, key: str) -> bool:
    """Per-step completion, reusing section_completion (single source of truth)."""
    if key == "personal":
        return sc.section_personal_complete(application)
    if key == "residence":
        return sc.section_residence_complete(application)
    if key == "financial":
        return sc.section_source_of_wealth_complete(application)
    if key == "parties":
        ok, _ = sc.joint_holder_rules_ok(application)
        return ok
    if key == "documents":
        return sc.section_requirements_complete(application)
    if key == "review":
        ok, _ = sc.is_submittable(application)
        return ok
    return False


def steps_with_status(application) -> list[tuple[WizardStep, bool]]:
    """(step, complete?) for the indicator — avoids dict lookups in templates."""
    return [(s, step_complete(application, s.key)) for s in STEPS]


def first_incomplete_key(application) -> str:
    """Entry target: the first editable step that isn't complete, else review."""
    for s in STEPS:
        if s.review:
            continue
        if not step_complete(application, s.key):
            return s.key
    return "review"