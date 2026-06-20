"""
governance/kyc/models/personal_info.py

Universal identity and contact data for the principal applicant. Identity
documents are normalized into a separate child table (KYCIdentityDocument).
"""
from django.db import models
from django.core.exceptions import ValidationError

from governance.kyc.choices import (
    AccountHoldingType,
    Gender,
    MaritalStatus,
    Religion,
    Salutation,
)
from governance.kyc.models.base import KYCAuditBase


class KYCPersonalInfo(KYCAuditBase):
    """One-to-one personal/contact record for a KYC application."""

    personal_info_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the personal-info record.",
    )
    application = models.OneToOneField(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="personal_info",
        help_text="Application this personal-info record belongs to (1:1).",
    )

    salutation = models.CharField(
        max_length=3,
        choices=Salutation.choices,
        null=True,
        blank=True,
        help_text="Title/salutation (Mr., Mrs., etc.).",
    )
    first_name = models.CharField(max_length=100, help_text="Applicant first name.")
    middle_name = models.CharField(
        max_length=100, null=True, blank=True, help_text="Applicant middle name (optional)."
    )
    last_name = models.CharField(max_length=100, help_text="Applicant last name.")

    nationality = models.ForeignKey(
        "masters.Country",
        on_delete=models.PROTECT,
        db_constraint=False,
        related_name="kyc_personal_nationalities",
        help_text="Applicant nationality (FK to reference country).",
    )
    date_of_birth = models.DateField(help_text="Applicant date of birth.")
    # TODO(KYC-LOC-001): Replace with FK to masters.City after City master is introduced.
    # Migration plan: add nullable FK, backfill from text values, switch reads/writes, then retire text field.
    place_of_birth_city = models.CharField(
        max_length=100, null=True, blank=True, help_text="City of birth."
    )
    place_of_birth_country = models.ForeignKey(
        "masters.Country",
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="kyc_personal_birth_countries",
        help_text="Country of birth (FK to reference country).",
    )
    gender = models.CharField(
        max_length=1, choices=Gender.choices, help_text="Applicant gender."
    )
    marital_status = models.CharField(
        max_length=10,
        choices=MaritalStatus.choices,
        null=True,
        blank=True,
        help_text="Applicant marital status.",
    )
    # TODO(KYC-EDU-001): Convert education to controlled reference data.
    # Target design: dropdown/reference table with standard education levels plus
    # an "Other" option and free-text detail field when needed.
    # Migration plan: create master list, add FK/choice field + education_other_text,
    # backfill common values, then retire free-text-only usage.
    education = models.CharField(
        max_length=120, null=True, blank=True, help_text="Highest education / qualification."
    )

    # TODO(KYC-CONTACT-002): Migrate phone/mobile to PhoneNumberField
    # using django-phonenumber-field for validation and E.164-style normalization.
    # Migration plan: install dependency, add normalized fields, backfill/clean legacy
    # values, switch forms/services, then retire plain CharField usage.
    phone = models.CharField(
        max_length=30, null=True, blank=True, help_text="Landline phone number."
    )
    # TODO(KYC-CONTACT-003): Migrate to PhoneNumberField after dependency rollout.
    mobile = models.CharField(max_length=30, help_text="Mobile number (primary contact).")

    # TODO(KYC-CONTACT-001): Review whether fax is still needed beyond legacy onboarding flows.
    fax = models.CharField(
        max_length=30, null=True, blank=True, help_text="Fax number (optional/legacy)."
    )
    email = models.EmailField(help_text="Primary email address.")

    principal_share_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=100,
        help_text="Principal holder's ownership share (joint shares must total 100%).",
    )

    # PSX-gated (surfaced only when market == PSX)
    religion = models.CharField(
        max_length=10,
        choices=Religion.choices,
        null=True,
        blank=True,
        help_text="Religion (PSX market; drives Zakat applicability).",
    )
    father_or_husband_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Father's or husband's name (PSX market requirement).",
    )

    # Conditional (minor)
    guardian_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Guardian name; required when the applicant is a minor.",
    )

    class Meta:
        db_table = "px_kyc_personal_info"
        verbose_name = "KYC Personal Info"
        verbose_name_plural = "KYC Personal Info"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(principal_share_percentage__gte=0)
                & models.Q(principal_share_percentage__lte=100),
                name="ck_kyc_personal_principal_share_0_100",
            ),
        ]

    def clean(self):
        today = date.today()

        if self.date_of_birth and self.date_of_birth > today:
            raise ValidationError({"date_of_birth": "Date of birth cannot be in the future."})

        if self.date_of_birth:
            age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
            if age < 18 and not self.guardian_name:
                raise ValidationError({"guardian_name": "Guardian name is required for minors."})

        if (
            self.application_id
            and self.application.account_holding_type == AccountHoldingType.SINGLE
            and self.principal_share_percentage != 100
        ):
            raise ValidationError(
                {"principal_share_percentage": "Principal share must be 100 for single-holder applications."}
            )

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} (app {self.application_id})"
