from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .asset_class import TimeStampedModel


class Issuer(TimeStampedModel):
    """
    Issuer = legal entity that issues an instrument (equity, bond, fund, etc.).
    Used later for:
    - corporate actions (dividends/coupons/splits)
    - issuer-level reporting (sector/country.py exposure)
    - risk aggregation (issuer concentration)
    """

    class IssuerType(models.TextChoices):
        COMPANY = "COMPANY", "Company"
        SOVEREIGN = "SOVEREIGN", "Sovereign"
        FUND = "FUND", "Fund/Asset Manager"
        BANK = "BANK", "Bank"
        SPV = "SPV", "SPV/Trust"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    issuer_id = models.BigAutoField(primary_key=True,
                                    help_text="Security Issuer organization ID")

    # Human/legal name shown in reports.
    issuer_name = models.CharField(max_length=255,
                                   help_text="Security Issuer organization Name")

    # Stable short code used internally (e.g., PIBTL, AAPL, GOVT_PK).
    issuer_code = models.CharField(max_length=64, unique=True, db_index=True,
                                   help_text="Internally generated code for the issuer e.e.ISS_PK_00000123.")

    issuer_type = models.CharField(max_length=16, choices=IssuerType.choices, default=IssuerType.COMPANY)

    # NOTE: This should FK to your existing Country table in masters.
    # Replace "masters.Country" with your actual model path.
    country = models.ForeignKey(
        "masters.Country",
        on_delete=models.PROTECT,
        related_name="issuers",
        db_index=True,
        help_text="Domicile/registered country.py of the issuer.",
    )

    headquarters_city = models.CharField(max_length=128, blank=True, default="",
                                         help_text="City of the headquarters.",)

    # Legal Entity Identifier (20 chars). Not all issuers have it.
    issuer_lei = models.CharField(
        max_length=64,  # keep flexible; some data sources include formatting
        blank=True,
        default="",
        db_index=True,
        help_text="LEI (if available). Should be unique when present.",
    )
    # Issuer sector in
    local_sector = models.ForeignKey(
        "taxonomy.LocalSector",  # your PSX sector table
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="issuers",
        db_index=True,
        help_text=" Local sector classification (source: PSX).",
    )

    # Fiscal year-end month: 1-12. (June = 6)
    fiscal_year_end_month = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Issuer fiscal year end month (1-12).",
    )

    parent_issuer = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subsidiaries",
        help_text="Parent issuer/legal entity (optional).",
    )

    website = models.URLField(blank=True, default="",
                              help_text="Website of the issuer (optional).")

    issuer_status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    created_by = models.IntegerField(default=101)

    class Meta:
        db_table = "ref_issuer"
        verbose_name = "Issuer"
        verbose_name_plural = "Issuers"
        ordering = ["issuer_name"]
        constraints = [
            # Enforce unique LEI only when it is present (non-empty).
            models.UniqueConstraint(
                fields=["issuer_lei"],
                name="uq_issuer_lei_nonempty",
                condition=~models.Q(issuer_lei=""),
            ),
        ]
        indexes = [
            models.Index(fields=["issuer_status", "issuer_type"]),
            models.Index(fields=["country", "issuer_status"]),
            models.Index(fields=["country", "local_sector", "issuer_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.issuer_code} - {self.issuer_name}"


