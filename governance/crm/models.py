from django.db import models


class RM(models.Model):
    """
    px_rm_dim: Relationship Manager (coverage)
    """

    class Status(models.TextChoices):
        ACTIVE = "ACT", "Active"
        INACTIVE = "INA", "Inactive"

    rm_id = models.BigAutoField(primary_key=True, db_column="rm_id", help_text="RM key, e.g. 1001")
    rm_cd = models.CharField(max_length=24, unique=True, db_index=True, db_column="rm_cd",
                             help_text="RM code, e.g. RM_UAE_001")
    rm_nm = models.CharField(max_length=120, db_column="rm_nm",
                             help_text="RM name, e.g. Ali Khan")

    email = models.EmailField(null=True, blank=True, db_column="email",
                              help_text="RM email, e.g. ali@firm.com")
    phone = models.CharField(max_length=30, null=True, blank=True, db_column="phone",
                             help_text="RM phone, e.g. +971501234567")
    team_nm = models.CharField(max_length=80, null=True, blank=True, db_column="team_nm",
                               help_text="Team, e.g. Private Wealth")
    branch_nm = models.CharField(max_length=80, null=True, blank=True, db_column="branch_nm",
                                 help_text="Branch, e.g. Abu Dhabi")
    sts_cd = models.CharField(max_length=3, choices=Status.choices, default=Status.ACTIVE,
                              db_column="sts_cd", help_text="Status, e.g. ACT")

    created_by = models.IntegerField(default=101, db_column="created_by", help_text="User id, e.g. 101")
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at", help_text="Created timestamp")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at", help_text="Updated timestamp")


    class Meta:
        db_table = "px_rm_dim"
        indexes = [
            models.Index(fields=["rm_cd"], name="ix_rm_cd"),
            models.Index(fields=["sts_cd"], name="ix_rm_sts"),
        ]

    def __str__(self) -> str:
        return f"{self.rm_nm} - {self.rm_cd} @ {self.team_nm}"


class Investor(models.Model):
    """
    px_inv_dim: Investor / client entity
    """

    inv_id = models.BigAutoField(primary_key=True, db_column="inv_id", help_text="Investor key, e.g. 2001")

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

    inv_cd = models.CharField(
        max_length=24,
        unique=True,
        db_index=True,
        db_column="inv_cd",
        null=True,
        blank=True,
        help_text="Investor code, e.g. INV_000123"
    )

    inv_nm = models.CharField(max_length=200, db_column="inv_nm",
                              help_text="Investor name, e.g. Raza Family Office")

    email = models.EmailField(null=True, blank=True, db_column="email",
                              help_text="Investor email, e.g. raza@email.com")
    phone = models.CharField(max_length=30, null=True, blank=True, db_column="phone",
                             help_text="Investor phone, e.g. +971501234567")

    client_class_cd = models.CharField(max_length=3, choices=ClientClassification.choices,
                                       default=ClientClassification.RETAIL,
                                       db_column="client_class_cd", help_text="Client class, e.g. RET")

    id_tp_cd = models.CharField(max_length=4, choices=IdType.choices, null=True, blank=True,
                                db_column="id_tp_cd", help_text="ID type, e.g. PASS")
    id_no = models.CharField(max_length=80, null=True, blank=True, db_column="id_no",
                             help_text="ID number, e.g. A12345678")
    id_exp_dt = models.DateField(null=True, blank=True, db_column="id_exp_dt",
                                 help_text="ID expiry date, e.g. 2030-12-31")

    inv_sts_cd = models.CharField(max_length=3, choices=InvestorStatus.choices,
                                  default=InvestorStatus.PROSPECT,
                                  db_column="inv_sts_cd", help_text="Investor status, e.g. PRO")

    kyc_sts_cd = models.CharField(max_length=3, choices=KycStatus.choices,
                                  default=KycStatus.OPENED,
                                  db_column="kyc_sts_cd", help_text="KYC status, e.g. OPN")
    kyc_rvw_dt = models.DateField(null=True, blank=True, db_column="kyc_rvw_dt",
                                  help_text="KYC last review date, e.g. 2026-01-15")
    kyc_nxt_due_dt = models.DateField(null=True, blank=True, db_column="kyc_nxt_due_dt",
                                      help_text="Next KYC due date, e.g. 2027-01-15")

    aml_risk_cd = models.CharField(max_length=1, choices=AmlRisk.choices, default=AmlRisk.LOW,
                                   db_column="aml_risk_cd", help_text="AML risk, e.g. M")
    pep_flg = models.BooleanField(default=False, db_column="pep_flg", help_text="PEP flag, e.g. False")
    sanc_scrn_dt = models.DateField(null=True, blank=True, db_column="sanc_scrn_dt",
                                    help_text="Sanctions screened date, e.g. 2026-02-01")

    addr_ctry = models.ForeignKey(
        "masters.Country",
        db_column="addr_ctry_id",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="investors_address",
        help_text="Address country, e.g. UAE",
    )
    tax_res_ctry = models.ForeignKey(
        "masters.Country",
        db_column="tax_res_ctry_id",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="investors_tax_residency",
        help_text="Tax residency country, e.g. PAK",
    )

    sof_txt = models.CharField(max_length=120, null=True, blank=True, db_column="sof_txt",
                               help_text="Source of funds, e.g. Salary / Business")
    sow_txt = models.CharField(max_length=120, null=True, blank=True, db_column="sow_txt",
                               help_text="Source of wealth, e.g. Real estate / Inheritance")

    tax_sts_cd = models.CharField(max_length=3, choices=TaxStatus.choices, default=TaxStatus.NA,
                                  db_column="tax_sts_cd", help_text="Tax status, e.g. FIL")
    assum_tax_rt = models.DecimalField(max_digits=7, decimal_places=4, default=0,
                                       db_column="assum_tax_rt", help_text="Assumed tax rate, e.g. 0.0500")

    rm = models.ForeignKey(
        "crm.RM",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="investors",
        db_column="rm_id",
        help_text="Coverage RM, e.g. RM_UAE_001",
    )

    incp_dt = models.DateField(null=True, blank=True, db_column="incp_dt",
                               help_text="Investor onboarding date, e.g. 2026-02-09")

    # existing columns in your table: created_by, created_at, updated_at
    created_by = models.IntegerField(default=101, db_column="created_by", help_text="User id, e.g. 101")
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at", help_text="Created timestamp")
    updated_at = models.DateTimeField(auto_now=True, db_column="updated_at", help_text="Updated timestamp")

    class Meta:
        db_table = "px_inv_dim"
        indexes = [
            models.Index(fields=["inv_sts_cd", "kyc_sts_cd"], name="ix_inv_sts_kyc"),
            models.Index(fields=["aml_risk_cd", "pep_flg"], name="ix_inv_aml_pep"),
            models.Index(fields=["rm"], name="ix_inv_rm"),
        ]

    def __str__(self) -> str:
        return f"{self.inv_nm} - {self.inv_cd} - {self.inv_sts_cd}"
