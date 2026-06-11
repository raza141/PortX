# operations/ibor/forms/trade_forms.py
from __future__ import annotations

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from operations.ibor.models.trade import IborTradeEvent


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

    def clean(self):
        cleaned = super().clean()
        trade_dt  = cleaned.get("trade_dt")
        settle_dt = cleaned.get("settle_dt")
        quantity  = cleaned.get("quantity")
        price     = cleaned.get("price")

        if trade_dt and settle_dt and settle_dt < trade_dt:
            raise ValidationError("Settlement date cannot be before trade date.")
        if quantity is not None and quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        if price is not None and price <= 0:
            raise ValidationError("Price must be greater than zero.")
        if not cleaned.get("trade_ccy"):
            raise ValidationError("Trade currency is required.")

        return cleaned


class IborTradeEntryForm(BaseTradeForm):
    """
    Full IBOR institutional trade ticket.
    """

    class Meta(BaseTradeForm.Meta):
        fields = BaseTradeForm.Meta.fields + [
            #"sleeve",   #later will implement
            "broker",
            "exec_venue",
            #"custodian", Later will implement
            "asset_class",
            "asset_sub_class",
            "source_system",
            "trader_name",
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

        if not cleaned.get("broker"):
            raise ValidationError("Broker is required.")
        if not cleaned.get("source_system"):
            raise ValidationError("Source system is required.")

        fx = cleaned.get("fx_override_rate")
        if fx is not None and fx <= Decimal("0"):
            raise ValidationError("FX override rate must be greater than zero.")

        if cleaned.get("manual_override") and not (cleaned.get("override_reason") or "").strip():
            raise ValidationError(
                "Override reason is required when manual override is selected."
            )

        return cleaned