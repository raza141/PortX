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
            "description": forms.TextInput(attrs={"class": "form-input", "placeholder": "e.g. Broker commission, SST, CDC"}),
            "rate": forms.NumberInput(attrs={"class": "form-input", "step": "0.0001", "placeholder": "Optional"}),
            "amount": forms.NumberInput(attrs={"class": "form-input charge-amount", "step": "0.0001", "placeholder": "0.00"}),
            "is_withholding": forms.CheckboxInput(attrs={"class": "form-checkbox"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            if name not in {"description", "rate", "amount", "is_withholding"}:
                existing = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing} form-input".strip()


IborChargeFormSet = inlineformset_factory(
    IborTradeEvent,
    IborChargeComponent,
    form=IborChargeComponentForm,
    extra=2,
    can_delete=True,
)