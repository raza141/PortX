"""
governance/kyc/models/employment.py

Occupation/employer data. Kept separate from Source of Wealth because employment
is conceptually distinct from source-of-funds/wealth and is queried independently
for AML.
"""
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError

from governance.kyc.models.base import KYCAuditBase


class KYCEmployment(KYCAuditBase):
    """One-to-one employment/occupation record for a KYC application."""

    employment_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the employment record.",
    )
    application = models.OneToOneField(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="employment",
        help_text="Application this employment record belongs to (1:1).",
    )
    # TODO(KYC-EMP-003): Consider migrating profession to generic lookup/master data
    # once controlled values are agreed for reporting and search.
    profession = models.CharField(
        max_length=120, null=True, blank=True, help_text="Stated profession."
    )
    # TODO(KYC-EMP-004): Consider migrating occupation to generic lookup/master data
    # once controlled values are agreed for reporting and search.
    occupation = models.CharField(
        max_length=120, null=True, blank=True, help_text="Occupation/role."
    )
    employer_name = models.CharField(
        max_length=200, null=True, blank=True, help_text="Employer / business name."
    )
    employer_address = models.TextField(
        null=True, blank=True, help_text="Employer address."
    )
    business_category = models.CharField(
        max_length=120,
        null=True,
        blank=True,
        help_text="Business/industry category.",
    )
    business_category_other = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Specified category when business_category is 'Other'.",
    )

    class Meta:
        db_table = "px_kyc_employment"
        verbose_name = "KYC Employment"
        verbose_name_plural = "KYC Employment"

    def clean(self):
        if self.business_category == "Other" and not self.business_category_other:
            raise ValidationError(
                {"business_category_other": "Please specify the category when business category is Other."}
            )

    def __str__(self) -> str:
        return f"Employment(app {self.application_id})"