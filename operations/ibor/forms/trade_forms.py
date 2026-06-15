# operations/ibor/forms/trade_forms.py
from __future__ import annotations

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.forms import DateInput

from operations.ibor.models.trade import IborTradeEvent
from operations.ibor.models.trade import InitiatedBy


class BaseTradeForm(forms.ModelForm):
    """
    Core economic trade fields.
    All fields confirmed present on IborTradeEvent model.
    """

    class Meta:
        model = IborTradeEvent
        fields = [
            "portfolio",
            "account",
            "instrument",
            "side",
            "quantity",
            "price",
            "trade_dt",
            "settle_dt",
            "trade_ccy",
            "external_ref",
            "memo",
        ]

    settle_offset = forms.IntegerField(
        label="Settlement Offset",
        required=False,
        widget=forms.HiddenInput(),
    )

    def clean(self):
        cleaned = super().clean()
        errors = []

        trade_dt  = cleaned.get("trade_dt")
        settle_dt = cleaned.get("settle_dt")
        quantity  = cleaned.get("quantity")
        price     = cleaned.get("price")

        if trade_dt and settle_dt and settle_dt < trade_dt:
            errors.append("Settlement date cannot be before trade date.")
        if quantity is not None and quantity <= 0:
            errors.append("Quantity must be greater than zero.")
        if price is not None and price <= 0:
            errors.append("Price must be greater than zero.")
        if not cleaned.get("trade_ccy"):
            errors.append("Trade currency is required.")

        if errors:
            raise ValidationError(errors)

        return cleaned


class IborTradeEntryForm(BaseTradeForm):
    """
    Full IBOR institutional trade ticket.
    Extends BaseTradeForm with execution, settlement, and lifecycle fields.
    """

    class Meta(BaseTradeForm.Meta):
        widgets = {
            "trade_dt":  DateInput(attrs={"type": "date", "class": "form-input"}),
            "settle_dt": DateInput(attrs={"type": "date", "class": "form-input"}),
            "trading_enabled": forms.CheckboxInput(attrs={"onclick": "return false;"}),
            "pm_discretion_used": forms.CheckboxInput(attrs={"onclick": "return false;"}),
        }
        fields = BaseTradeForm.Meta.fields + [
            # "sleeve",        # reserved — implement later
            "broker",
            "exec_venue",
            # "custodian",     # reserved — implement later
            "asset_class",
            "asset_sub_class",
            "source_system",
            "trader",
            "trading_enabled",
            "discretion_enabled",
            "pm_discretion_used",
            "initiated_by",
            "order_type",
            "order_id",
            "execution_id",
            "settle_ccy",
            "fx_override_rate",
            "state_cd",
            "book_sts_cd",
            "imported_flag",
            "manual_override",
            "override_reason",
        ]

    def clean(self):
        cleaned = super().clean()
        errors = {}

        # Compliance checks
        portfolio = cleaned.get("portfolio")
        pm_discretion_used = cleaned.get("pm_discretion_used")
        initiated_by = cleaned.get("initiated_by")

        if portfolio and not portfolio.trd_enbl_flg:
            raise ValidationError("Trading is disabled for this portfolio.")

        if portfolio and portfolio.mandate:
            mandate = portfolio.mandate
            if pm_discretion_used and not mandate.pm_discretion_allowed:
                self.add_error("pm_discretion_used", "PM discretion is not allowed under this mandate.")
            if not mandate.pm_discretion_allowed and initiated_by != InitiatedBy.CLIENT:
                self.add_error("initiated_by", "Non-discretionary mandates require trades to be tagged as client-directed.")

        # Existing validation
        general_errors = []
        if not cleaned.get("broker"):
            general_errors.append("Broker is required.")
        if not cleaned.get("source_system"):
            general_errors.append("Source system is required.")

        fx = cleaned.get("fx_override_rate")
        if fx is not None and fx <= Decimal("0"):
            general_errors.append("FX override rate must be greater than zero.")

        if cleaned.get("manual_override") and not (cleaned.get("override_reason") or "").strip():
            general_errors.append("Override reason is required when manual override is selected.")

        if general_errors:
            raise ValidationError(general_errors)

        return cleaned