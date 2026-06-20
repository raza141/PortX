"""
governance/kyc/models/joint_holder.py

Additional joint holders (J2..J5 in Phase 1). Each joint holder owns its own
identity documents and tax-residency rows via the nullable joint_holder FK on
those child tables, so one mechanism serves the principal and joint holders.
"""
from django.db import models
from django.core.exceptions import ValidationError

from governance.kyc.choices import TaxApplicability, AccountHoldingType
from governance.kyc.models.base import KYCAuditBase


class KYCJointHolder(KYCAuditBase):
    """A joint account holder attached to a JOINT application."""

    joint_holder_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the joint holder.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="joint_holders",
        help_text="Parent application this joint holder belongs to.",
    )
    holder_sequence = models.PositiveSmallIntegerField(
        help_text="Position of this joint holder (2..5; principal is implicit holder 1).",
    )

    given_name = models.CharField(
        max_length=100,
        help_text="Joint holder given/first name.",
    )
    middle_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Joint holder middle name (optional).",
    )
    family_name = models.CharField(
        max_length=100,
        help_text="Joint holder family/last name.",
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="Joint holder date of birth.",
    )
    # TODO: Replace place_of_birth_city CharField with FK to masters.City
    # after City master is introduced and backfill migration is ready.
    place_of_birth_city = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Joint holder city of birth.",
    )
    place_of_birth_country = models.ForeignKey(
        "masters.Country",
        on_delete=models.PROTECT,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="kyc_joint_holder_birth_countries",
        help_text="Joint holder country of birth (FK to reference country).",
    )
    nationality = models.ForeignKey(
        "masters.Country",
        on_delete=models.PROTECT,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="kyc_joint_holder_nationalities",
        help_text="Joint holder nationality (FK to reference country).",
    )

    share_percentage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Ownership share for this holder; all shares must total 100%.",
    )
    tax_status = models.CharField(
        max_length=16,
        choices=TaxApplicability.choices,
        default=TaxApplicability.NON_APPLICABLE,
        help_text="Whether FATCA/CRS tax reporting applies to this holder.",
    )

    class Meta:
        db_table = "px_kyc_joint_holder"
        verbose_name = "KYC Joint Holder"
        verbose_name_plural = "KYC Joint Holders"
        ordering = ["application", "holder_sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["application", "holder_sequence"],
                name="uq_kyc_joint_seq_per_app",
            ),
            models.CheckConstraint(
                condition=models.Q(holder_sequence__gte=2) & models.Q(holder_sequence__lte=5),
                name="ck_kyc_joint_holder_sequence_2_5",
            ),
            models.CheckConstraint(
                condition=models.Q(share_percentage__gte=0) & models.Q(share_percentage__lte=100),
                name="ck_kyc_joint_holder_share_0_100",
            ),
        ]

    def clean(self):
        if self.application_id and self.application.account_holding_type != AccountHoldingType.JOINT:
            raise ValidationError(
                {"application": "Joint holders are allowed only for JOINT applications."}
            )

    def __str__(self) -> str:
        return f"JointHolder#{self.holder_sequence} {self.given_name} {self.family_name}"