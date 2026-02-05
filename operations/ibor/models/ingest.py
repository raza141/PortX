# core/operations/ibor/models/ingest.py
from __future__ import annotations

import uuid
from django.db import models
from .common import IborTimeStampedModel


class IborSourceDoc(IborTimeStampedModel):
    """
    A source document used for ingestion into IBOR (e.g., broker PDF, CSV, email attachment).

    Design intent
    ------------
    - IBOR canonical records should NOT be created directly from external docs.
    - External docs go to Ops Inbox -> parsed to staged rows -> approved -> posted to canonical.
    """

    class DocType(models.TextChoices):
        PDF = "PDF", "PDF"
        CSV = "CSV", "CSV"
        EMAIL = "EMAIL", "Email"
        API = "API", "API"
        OTHER = "OTHER", "Other"

    doc_type = models.CharField(
        max_length=10,
        choices=DocType.choices,
        default=DocType.PDF,
        help_text="Type of source document used in ingestion.",
    )
    source_system = models.CharField(
        max_length=40,
        help_text="Adapter/system identifier (e.g., 'psx_broker_x', 'sarwa', 'manual').",
    )
    source_ref = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="External reference for the doc (email msg-id, broker statement id, etc.).",
    )
    file_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Original filename (if uploaded).",
    )
    file_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Optional hash for deduplication and audit.",
    )
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the doc was received (email time, download time, etc.).",
    )
    raw_text = models.TextField(
        blank=True,
        default="",
        help_text="Optional extracted raw text (store only if helpful for audit/debug).",
    )

    class Meta:
        db_table = "ibor_src_doc"
        indexes = [
            models.Index(fields=["source_system", "source_ref"]),
            models.Index(fields=["file_sha256"]),
        ]

    def __str__(self) -> str:
        return f"{self.source_system}:{self.doc_type}:{self.source_ref or self.file_name}"


class IborIngestBatch(IborTimeStampedModel):
    """
    Groups a single ingestion run.

    Example
    -------
    - One PDF upload => one batch
    - One email pull run => one batch
    - One Sarwa export file => one batch
    """

    batch_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    source_doc = models.ForeignKey(
        IborSourceDoc,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ingest_batches",
        help_text="The document that produced this batch (optional).",
    )
    source_system = models.CharField(
        max_length=40,
        help_text="Adapter/system identifier (same meaning as on source doc).",
    )
    run_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes about parsing run, errors, warnings, etc.",
    )

    class Meta:
        db_table = "ibor_ing_batch"
        indexes = [models.Index(fields=["source_system", "created_at"])]

    def __str__(self) -> str:
        return f"IBOR Ingest {self.source_system} {self.batch_id}"


class IborStagedTrade(IborTimeStampedModel):
    """
    Staged trade candidate (Ops Inbox).

    Design intent
    ------------
    - Holds parsed trade data BEFORE it becomes canonical.
    - Ops can fix mapping issues (instrument/portfolio/ccy) and approve/reject.
    - After approval, posting creates canonical TradeEvent + ChargeComponents + CashEvents.

    Notes
    -----
    Keep it broker-agnostic. Store raw parsed fields + normalized candidates.
    """

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        NEEDS_REVIEW = "REVIEW", "Needs review"
        REJECTED = "REJ", "Rejected"
        APPROVED = "APP", "Approved"
        POSTED = "POSTED", "Posted"

    ingest_batch = models.ForeignKey(
        IborIngestBatch,
        on_delete=models.CASCADE,
        related_name="staged_trades",
        help_text="Which ingest batch produced this staged record.",
    )
    source_system = models.CharField(
        max_length=40,
        help_text="Adapter/system identifier (e.g., 'psx_broker_x').",
    )
    external_ref = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Broker voucher/contract note id (or best available unique ref).",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Ops Inbox status for review/approval lifecycle.",
    )

    # Parsed payload & normalized candidate fields
    raw_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw parsed fields from the source (keep broker-specific info here).",
    )

    # Minimal normalized candidate fields (strings to avoid FK mapping failures during staging)
    portfolio_code = models.CharField(
        max_length=60,
        blank=True,
        default="",
        help_text="Portfolio identifier from broker/source (to be mapped).",
    )
    instrument_code = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="Symbol/ISIN/ticker from broker/source (to be mapped).",
    )
    side = models.CharField(
        max_length=4,
        blank=True,
        default="",
        help_text="BUY/SELL as parsed (normalize during posting).",
    )
    quantity = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Trade quantity (supports fractional shares for platforms like Sarwa).",
    )
    price = models.DecimalField(
        max_digits=28,
        decimal_places=10,
        null=True,
        blank=True,
        help_text="Trade price (as parsed).",
    )
    trade_ccy = models.CharField(
        max_length=3,
        blank=True,
        default="",
        help_text="Trade currency ISO3 (e.g., PKR, USD, AED).",
    )
    trade_dt = models.DateField(
        null=True,
        blank=True,
        help_text="Trade date (as parsed).",
    )
    settle_dt = models.DateField(
        null=True,
        blank=True,
        help_text="Settlement date (as parsed).",
    )

    mapping_errors = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mapping/validation errors (instrument not found, bad currency, duplicates etc.).",
    )

    class Meta:
        db_table = "ibor_stg_trd"
        indexes = [
            models.Index(fields=["source_system", "external_ref"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"STG {self.source_system}:{self.external_ref} ({self.status})"
