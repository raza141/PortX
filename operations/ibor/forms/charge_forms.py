from django import forms
from django.forms import inlineformset_factory

from operations.ibor.models.trade import IborChargeComponent, IborTradeEvent


class IborChargeComponentForm(forms.ModelForm):
    class Meta:
        model = IborChargeComponent
        fields = [
            "charge_type_cd",
            "description",
            "rate",
            "amount",
            "cost_ccy",
            "is_withholding",
        ]
        widgets = {
            "charge_type_cd": forms.Select(attrs={"class": "form-input"}),
            "description": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "e.g. Broker commission, SST, CDC"}
            ),
            "rate": forms.NumberInput(
                attrs={"class": "form-input", "step": "0.0001", "placeholder": "Optional"}
            ),
            "amount": forms.NumberInput(
                attrs={"class": "form-input charge-amount", "step": "0.0001", "placeholder": "0.00"}
            ),
            "cost_ccy": forms.Select(attrs={"class": "form-input"}),
            "is_withholding": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }


IborChargeFormSet = inlineformset_factory(
    parent_model=IborTradeEvent,
    model=IborChargeComponent,
    form=IborChargeComponentForm,
    extra=3,
    can_delete=True,
)