from django.core.validators import RegexValidator
from django.db import models
from .base import AuditModel


code2 = RegexValidator(r"^\d{2}$", "GICS sector code must be 2 digits (e.g., '10').")
code4 = RegexValidator(r"^\d{4}$", "GICS industry group code must be 4 digits (e.g., '1010').")
code6 = RegexValidator(r"^\d{6}$", "GICS industry code must be 6 digits (e.g., '101020').")
code8 = RegexValidator(r"^\d{8}$", "GICS subindustry code must be 8 digits (e.g., '10102010').")


class GicsEdition(AuditModel):
    """
    GICS edition (version). Example: 'GICS 2024'.
    """
    name = models.CharField(max_length=50, unique=True)
    effective_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        db_table = "ref_gics_edition"
        indexes = [models.Index(fields=["is_current", "effective_date"])]

    def __str__(self) -> str:
        return self.name


class GicsSector(AuditModel):
    """
    Top-level GICS sector (2-digit).
    """
    edition = models.ForeignKey(GicsEdition, on_delete=models.PROTECT, related_name="sectors")
    code = models.CharField(max_length=2, validators=[code2])
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "ref_gics_sector"
        constraints = [
            models.UniqueConstraint(fields=["edition", "code"], name="uq_gics_sector_edition_code"),
        ]
        indexes = [
            models.Index(fields=["edition", "code"]),
            models.Index(fields=["code"]),
        ]
        ordering = ["edition_id", "code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class GicsIndustryGroup(AuditModel):
    """
    GICS industry group (4-digit), child of sector.
    """
    edition = models.ForeignKey(GicsEdition, on_delete=models.PROTECT, related_name="industry_groups")
    sector = models.ForeignKey(GicsSector, on_delete=models.PROTECT, related_name="industry_groups")
    code = models.CharField(max_length=4, validators=[code4])
    name = models.CharField(max_length=150)

    class Meta:
        db_table = "ref_gics_industry_group"
        constraints = [
            models.UniqueConstraint(fields=["edition", "code"], name="uq_gics_group_edition_code"),
        ]
        indexes = [
            models.Index(fields=["edition", "code"]),
            models.Index(fields=["sector"]),
        ]
        ordering = ["edition_id", "code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class GicsIndustry(AuditModel):
    """
    GICS industry (6-digit), child of industry group.
    """
    edition = models.ForeignKey(GicsEdition, on_delete=models.PROTECT, related_name="industries")
    group = models.ForeignKey(GicsIndustryGroup, on_delete=models.PROTECT, related_name="industries")
    code = models.CharField(max_length=6, validators=[code6])
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "ref_gics_industry"
        constraints = [
            models.UniqueConstraint(fields=["edition", "code"], name="uq_gics_industry_edition_code"),
        ]
        indexes = [
            models.Index(fields=["edition", "code"]),
            models.Index(fields=["group"]),
        ]
        ordering = ["edition_id", "code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class GicsSubIndustry(AuditModel):
    """
    GICS subindustry (8-digit), leaf level.
    """
    edition = models.ForeignKey(GicsEdition, on_delete=models.PROTECT, related_name="subindustries")
    industry = models.ForeignKey(GicsIndustry, on_delete=models.PROTECT, related_name="subindustries")
    code = models.CharField(max_length=8, validators=[code8])
    name = models.CharField(max_length=200)

    class Meta:
        db_table = "ref_gics_subindustry"
        constraints = [
            models.UniqueConstraint(fields=["edition", "code"], name="uq_gics_subindustry_edition_code"),
        ]
        indexes = [
            models.Index(fields=["edition", "code"]),
            models.Index(fields=["industry"]),
        ]
        ordering = ["edition_id", "code"]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"
