# ibor/forms/charge_forms.py
from __future__ import annotations

from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from operations.ibor.models.trade import IborChargeComponent, IborTradeEvent


class TradeChargeForm(forms.ModelForm):
    """
    Single charge row on a trade.
    """

    class Meta:
        model = IborChargeComponent
        fields = [
            "charge_type_cd",
            "description",
            "rate",
            "amount",
            "cost_ccy",
            "is_withholding",
            "override_flag",
            "source_reference",
        ]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "charge-amount"}),
        }


class BaseTradeChargeFormSet(BaseInlineFormSet):
    """
    Inline formset for flexible breakdown of trade charges.
    """

    def clean(self):
        super().clean()

        for form in self.forms:
            # Skip empty/marked-for-delete forms
            if not hasattr(form, "cleaned_data") or not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue

            amount = form.cleaned_data.get("amount")
            if amount is not None and amount < 0:
                raise forms.ValidationError("Charge amount cannot be negative.")


TradeChargeFormSet = inlineformset_factory(
    IborTradeEvent,
    IborChargeComponent,
    form=TradeChargeForm,
    formset=BaseTradeChargeFormSet,
    extra=1,
    can_delete=True,
)

# Alias — IborChargeFormSet is the public name used across views/templates
IborChargeFormSet = TradeChargeFormSet