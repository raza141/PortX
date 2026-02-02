from django.db import models

# from masters.models.country import  Country
from refdata.masters.models.country import Country

# Create your models here.
class RM(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACT", "Active"
        INACTIVE = "INA", "Inactive"

    rm_name = models.CharField(max_length=120)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)
    team = models.CharField(max_length=80, null=True, blank=True)
    branch = models.CharField(max_length=80, null=True, blank=True)
    status = models.CharField(max_length=3, choices=Status.choices, default=Status.ACTIVE)

    # audit fields
    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rm"

    def __str__(self) -> str:
        return self.rm_name


class Investor(models.Model):
    investor_id = models.BigAutoField(primary_key=True)

    class ClientClassification(models.TextChoices):
        RETAIL = "RET", "Retail"
        PROFESSIONAL = "PRO", "Professional"
        ELIGIBLE_COUNTERPARTY = "ECP", "Eligible Counterparty"

    class KycStatus(models.TextChoices):
        OPENED = "OPN", "Opened"
        IN_PROGRESS = "IPR", "In Progress"
        COMPLETED = "CMP", "Completed"
        EXPIRED = "EXP", "Expired"
        REJECTED = "RJD", "Rejected"
        WAITING_CLIENT_DOCS = "WCD", "Waiting Client Docs"

    class InvestorStatus(models.TextChoices):
        ACTIVE = "ACT", "Active"
        INACTIVE = "INA", "Inactive"
        PROSPECT = "PRO", "Prospect"
        CLOSED = "CLS", "Closed"
        DORMANT = "DOR", "Dormant"

    class AmlRisk(models.TextChoices):
        LOW = "L", "Low"
        MEDIUM = "M", "Medium"
        HIGH = "H", "High"

    class IdType(models.TextChoices):
        PASSPORT = "PASS", "Passport"
        EMIRATES_ID = "EID", "Emirates ID"
        NATIONAL_ID = "NID", "National ID"
        OTHER = "OTR", "Other"

    class TaxStatus(models.TextChoices):
        FILER = "FIL", "Filer"
        NON_FILER = "NFI", "Non-Filer"
        NA = "NA", "N/A"

    investor_name = models.CharField(max_length=200)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=30, null=True, blank=True)

    client_classification = models.CharField(
        max_length=3, choices=ClientClassification.choices, default=ClientClassification.RETAIL
    )

    id_type = models.CharField(max_length=4, choices=IdType.choices, null=True, blank=True)
    id_number = models.CharField(max_length=80, null=True, blank=True)
    id_expiry = models.DateField(null=True, blank=True)

    investor_status = models.CharField(
        max_length=3, choices=InvestorStatus.choices, default=InvestorStatus.PROSPECT
    )

    kyc_status = models.CharField(
        max_length=3, choices=KycStatus.choices, default=KycStatus.OPENED
    )
    kyc_review_date = models.DateField(null=True, blank=True)
    next_kyc_review_due = models.DateField(null=True, blank=True)

    aml_risk_rating = models.CharField(
        max_length=1, choices=AmlRisk.choices, default=AmlRisk.LOW
    )
    pep_flag = models.BooleanField(default=False)
    sanctions_screened_date = models.DateField(null=True, blank=True)

    # ✅ Use string references to avoid circular imports
    address_country = models.ForeignKey(
        "masters.Country",
        db_column="address_country",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="investors_address",
    )
    tax_residency_country = models.ForeignKey(
        "masters.Country",
        db_column="tax_residency_country",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="investors_tax_residency",
    )

    source_of_funds = models.CharField(max_length=120, null=True, blank=True)
    source_of_wealth = models.CharField(max_length=120, null=True, blank=True)

    tax = models.CharField(max_length=3, choices=TaxStatus.choices, default=TaxStatus.NA)
    assumed_tax_rate = models.DecimalField(max_digits=7, decimal_places=4, default=0)

    # Placeholder (we can remove later and use IPS/Mandate instead)
    risk_profile_id = models.IntegerField(null=True, blank=True)

    rm = models.ForeignKey(
        "crm.RM",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="investors",
    )

    inception_date = models.DateField(null=True, blank=True)

    created_by = models.IntegerField(default=101)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "investor"
        indexes = [
            models.Index(fields=["investor_status", "kyc_status"]),
            models.Index(fields=["aml_risk_rating", "pep_flag"]),
        ]

    def __str__(self) -> str:
        return self.investor_name
