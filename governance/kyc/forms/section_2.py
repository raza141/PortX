"""governance/kyc/forms/section_2.py — Residence / FATCA / CRS section form."""
from django import forms

from governance.kyc.models import KYCResidence


class KYCResidenceForm(forms.ModelForm):
    class Meta:
        model = KYCResidence
        exclude = ["application", "created_by", "updated_by", "created_at", "updated_at"]
        widgets = {
            "permanent_address": forms.Textarea(attrs={"rows": 2}),
            "current_residence_address": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, market=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " kyc-input").strip()
        # Province is jurisdiction-gated; only surface where the market needs it.
        if market != "PSX":
            self.fields.pop("province", None)