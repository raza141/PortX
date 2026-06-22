"""
governance/kyc/models/referral.py

Decoupled referral / distribution source. A sales/referral agent is not always
the internal RM — it may be an external distributor or a rebate/reward source —
so this is modelled as its own reference rather than binding to crm.RM or
StaffProfile alone. The raw distributor / distributor-branch fields fold in here.
"""

from django.core.exceptions import ValidationError
from django.db import models

from governance.kyc.choices import ReferralType
from governance.kyc.models.base import KYCAuditBase


class KYCReferralSource(KYCAuditBase):
    """How the applicant was sourced or introduced."""

    referral_source_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the referral source.",
    )
    referral_type = models.CharField(
        max_length=24,
        choices=ReferralType.choices,
        default=ReferralType.DIRECT,
        help_text="Origin of the referral (internal staff, external distributor, direct).",
    )
    staff_profile = models.ForeignKey(
        "users.StaffProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="kyc_referrals",
        help_text="Internal staff member who sourced the client, when referral type is internal staff.",
    )
    external_party_name = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Name of the external distributor or introducing party, when applicable.",
    )
    external_party_code = models.CharField(
        max_length=60,
        null=True,
        blank=True,
        help_text="Code or identifier of the external party for rebate or reward tracking.",
    )
    external_branch_name = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="External distributor branch or location, where applicable.",
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Operational notes about the referral arrangement.",
    )

    class Meta:
        db_table = "px_kyc_referral_source"
        verbose_name = "KYC Referral Source"
        verbose_name_plural = "KYC Referral Sources"
        indexes = [
            models.Index(fields=["referral_type"], name="ix_kyc_ref_type"),
        ]

    def clean(self):
        """
        Validate cross-field business rules for the referral source.

        Purpose:
        - Enforce valid field combinations based on `referral_type`.
        - Prevent contradictory data, such as an internal referral with external-party fields,
          or a direct referral carrying referral details.

        Usage:
        - Runs when `full_clean()` is called.
        - Usually triggered automatically by Django forms/admin.
        - In service code or scripts, call `instance.full_clean()` before `save()`.

        Rules:
        - INTERNAL_STAFF requires `staff_profile` and forbids external-party fields.
        - EXTERNAL_DISTRIBUTOR requires `external_party_name` and forbids `staff_profile`.
        - DIRECT requires all referral-detail fields to remain blank.
        """
        if self.referral_type == ReferralType.INTERNAL_STAFF:
            if not self.staff_profile_id:
                raise ValidationError({"staff_profile": "Staff profile is required for internal staff referrals."})
            if self.external_party_name or self.external_party_code or self.external_branch_name:
                raise ValidationError("External party fields must be blank for internal staff referrals.")

        elif self.referral_type == ReferralType.EXTERNAL_DISTRIBUTOR:
            if not self.external_party_name:
                raise ValidationError({"external_party_name": "External party name is required for external distributor referrals."})
            if self.staff_profile_id:
                raise ValidationError({"staff_profile": "Staff profile must be blank for external distributor referrals."})

        elif self.referral_type == ReferralType.DIRECT:
            if self.staff_profile_id or self.external_party_name or self.external_party_code or self.external_branch_name:
                raise ValidationError("Referral details must be blank for direct referrals.")

    def __str__(self) -> str:
        label = self.external_party_name or (
            str(self.staff_profile) if self.staff_profile_id else self.get_referral_type_display()
        )
        return f"Referral - {self.referral_type} -  {label}"