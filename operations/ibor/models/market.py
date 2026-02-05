# core/operations/ibor/models/market.py
from __future__ import annotations

from django.db import models
from .common import IborTimeStampedModel


class IborPriceSnapshot(IborTimeStampedModel):
    """
    Market price snapshot used for IBOR valuation.

    Notes
    -----
    - For equities, prices are typically listing-level (SecurityListing), not abstract instrument-level.
    - V1: manual CSV upload is fine.
    - V2: vendor/API integration can load into the same model.
    """

    security_listing = models.ForeignKey(
        "instruments.SecurityListing",
        on_delete=models.PROTECT,
        related_name="ibor_price_snaps",
        help_text="Security listing being priced (e.g., BOP@PSX).",
    )
    price_dt = models.DateField(
        help_text="Price as-of date (EOD close for daily valuation in V1).",
    )
    price = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Price value for the listing.",
    )
    price_ccy = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        related_name="ibor_price_snaps",
        help_text="Currency of the price (usually listing currency).",
    )
    source = models.CharField(
        max_length=60,
        blank=True,
        default="MANUAL",
        help_text="Price source identifier (ExchangeRate-API, MANUAL, PSX, Bloomberg, etc.).",
    )

    class Meta:
        db_table = "ibor_px_snap"
        indexes = [
            models.Index(fields=["security_listing", "price_dt"]),
            models.Index(fields=["price_dt", "source"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["security_listing", "price_dt", "source"],
                name="uq_ibor_px_snap_list_dt_src",
            )
        ]

    def __str__(self) -> str:
        return f"{self.security_listing_id} {self.price} {self.price_ccy_id} @ {self.price_dt}"

class IborFxOverride(IborTimeStampedModel):
    """
    Optional IBOR FX override layer.

    Use cases
    ---------
    - Masters FX is missing for a day and ops sets a manual rate
    - Ops overrides a vendor rate for a specific portfolio/date
    - Later PBOR/GIPS: freeze 'rate used' for audit
    """

    portfolio = models.ForeignKey(
        "portfolio.Portfolio",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ibor_fx_overrides",
        help_text="Optional: restrict override to one portfolio. Null = global override.",
    )
    currency_pair = models.ForeignKey(
        "masters.CurrencyPair",
        on_delete=models.PROTECT,
        related_name="ibor_fx_overrides",
        help_text="Currency pair being overridden.",
    )
    rate_dt = models.DateField(
        help_text="Date this override applies to.",
    )
    rate = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        help_text="Override rate with the same convention as masters: 1 base = rate quote.",
    )
    reason = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Why override was needed (missing rate, vendor issue, etc.).",
    )

    class Meta:
        db_table = "ibor_fx_ovr"
        indexes = [
            models.Index(fields=["currency_pair", "rate_dt"]),
            models.Index(fields=["portfolio", "rate_dt"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "currency_pair", "rate_dt"],
                name="uq_ibor_fx_ovr_pf_pair_dt",
            )
        ]
