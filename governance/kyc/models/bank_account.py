"""
governance/kyc/models/bank_account.py

Bank accounts attached to an application. Currency is an FK to reference data.
Exactly one account per application may be flagged primary.
"""
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import models

# For IBAN validation
from schwifty import IBAN

from governance.kyc.models.base import KYCAuditBase


def validate_iban(value):
    """
    Validates an International Bank Account Number (IBAN) using the `schwifty` library.

    This function is intended for use as a validator on a Django model field. It
    instantiates the `schwifty.IBAN` class, which raises a `ValueError` if the
    IBAN is invalid.

    Args:
        value: The IBAN string to validate.

    Raises:
        ValidationError: If the IBAN is not valid.
    """
    if not value:
        return
    try:
        IBAN(value)
    except Exception as exc:
        raise ValidationError("Enter a valid IBAN.") from exc

class KYCBankAccount(KYCAuditBase):
    """A bank account declared on a KYC application."""

    bank_account_id = models.BigAutoField(
        primary_key=True,
        help_text="Surrogate primary key for the bank account.",
    )
    application = models.ForeignKey(
        "kyc.KYCApplication",
        on_delete=models.CASCADE,
        related_name="bank_accounts",
        help_text="Application this bank account belongs to.",
    )
    # TODO(KYC-BANK-002): Decide whether account_number must be unique within an
    # application and add a UniqueConstraint if duplicates are not allowed.
    account_number = models.CharField(
        max_length=64, help_text="Bank account number."
    )
    account_title = models.CharField(
        max_length=200, help_text="Account title (name on the account)."
    )
    bank_name = models.CharField(max_length=200, help_text="Bank name.")
    branch = models.CharField(
        max_length=200, null=True, blank=True, help_text="Bank branch name."
    )
    branch_address = models.TextField(
        null=True, blank=True, help_text="Bank branch address."
    )
    iban = models.CharField(
        max_length=64, null=True, blank=True,
        validators=[validate_iban],
        help_text="IBAN (validated per market)."
    )
    currency = models.ForeignKey(
        "masters.Currency",
        on_delete=models.PROTECT,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="kyc_bank_accounts",
        help_text="Account currency (FK to reference currency).",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="True for the primary settlement account (max one per application).",
    )

    class Meta:
        db_table = "px_kyc_bank_account"
        verbose_name = "KYC Bank Account"
        verbose_name_plural = "KYC Bank Accounts"
        constraints = [
            models.UniqueConstraint(
                fields=["application"],
                condition=Q(is_primary=True),
                name="uq_kyc_one_primary_bank_per_app",
            ),
            models.UniqueConstraint(
                fields=["application", "account_number"],
                name="uq_kyc_bank_app_account_number",
            ),
        ]
        indexes = [
            models.Index(fields=["application"], name="ix_kyc_bank_app"),
        ]

    def clean(self):
        super().clean()
        if self.iban:
            self.iban = IBAN(self.iban).compact

    def __str__(self) -> str:
        return f"{self.bank_name} {self.account_number}"