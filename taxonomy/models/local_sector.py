from django.db import models
from .base import AuditModel
from .gics import GicsEdition, GicsSubIndustry


class LocalSector(AuditModel):
    """
    Local exchange sector scheme (e.g., PSX sectors).
    One exchange can have many local sector codes.
    """
    # masters.Exchange already exists in your DB
    exchange = models.ForeignKey(
        "masters.Exchange",
        on_delete=models.PROTECT,
        related_name="local_sectors"
    )

    local_code = models.CharField(max_length=20)  # e.g., "820"
    name = models.CharField(max_length=200)       # e.g., "OIL & GAS EXPLORATION COMPANIES"
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "ref_local_sector"
        constraints = [
            models.UniqueConstraint(fields=["exchange", "local_code"], name="uq_local_sector_exchange_code"),
        ]
        indexes = [
            models.Index(fields=["exchange", "local_code"]),
            models.Index(fields=["name"]),
        ]
        ordering = ["exchange_id", "local_code"]

    def __str__(self) -> str:
        return f"{self.exchange_id}:{self.local_code} - {self.name}"


class LocalSectorGicsMap(AuditModel):
    """
    Mapping: local sector -> GICS subindustry (edition-aware).
    This is the 'intersection' table you mentioned.
    """
    edition = models.ForeignKey(GicsEdition, on_delete=models.PROTECT, related_name="local_sector_maps")
    local_sector = models.ForeignKey(LocalSector, on_delete=models.PROTECT, related_name="gics_maps")
    gics_subindustry = models.ForeignKey(GicsSubIndustry, on_delete=models.PROTECT, related_name="local_maps")

    # quality + governance fields (very institutional)
    source = models.CharField(max_length=50, default="manual")  # manual/vendor/import
    confidence = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)

    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "map_local_sector_gics"
        constraints = [
            models.UniqueConstraint(
                fields=["edition", "local_sector"],
                name="uq_local_sector_map_edition_sector"
            ),
        ]
        indexes = [
            models.Index(fields=["edition", "local_sector"]),
            models.Index(fields=["gics_subindustry"]),
        ]

    def __str__(self) -> str:
        return f"{self.local_sector} -> {self.gics_subindustry}"
