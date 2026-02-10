# core/operations/ibor/models/common.py
from __future__ import annotations

import uuid
from django.conf import settings
from django.db import models


class IborTimeStampedModel(models.Model):
    """
    Common audit fields for IBOR entities.

    Notes
    -----
    - 'as_at_ts' is the system-recorded timestamp (bi-temporal "as-at").
    - Use additional business dates like trade_dt/settle_dt/as_of_dt on each entity (bi-temporal "as-of").
    """

    id = models.BigAutoField(primary_key=True)
    as_at_ts = models.DateTimeField(
        auto_now_add=True,
        help_text="System timestamp when PortX recorded this row (bi-temporal 'as-at').",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created",
        help_text="User who created/approved this record in PortX (optional).",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Creation timestamp in PortX (audit).",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last update timestamp in PortX (audit).",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Soft-active flag. Old versions/replaced records should be set inactive.",
    )

    class Meta:
        abstract = True


class IborState(models.TextChoices):
    """
    Standard lifecycle states for IBOR canonical records.

    V1 states agreed:
    - EXEC: executed/fill captured (maybe provisional)
    - CONF: broker confirmed/contract note confirmed
    - SETTLED: settlement completed
    - CXL: canceled/voided
    - CORR: corrected/amended (new version replaces old)
    """
    EXEC = "EXEC", "Executed"
    CONF = "CONF", "Confirmed"
    SETTLED = "SETTLED", "Settled"
    CXL = "CXL", "Canceled"
    CORR = "CORR", "Corrected"
