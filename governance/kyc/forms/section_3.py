"""governance/kyc/forms/section_3.py — Source of Wealth and Employment forms."""
from django import forms

from governance.kyc.models import KYCEmployment, KYCSourceOfWealth


class KYCSourceOfWealthForm(forms.ModelForm):
    class Meta:
        model = KYCSourceOfWealth
        exclude = ["application", "created_by", "updated_by", "created_at", "updated_at"]

    def __init__(self, *args, market=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " kyc-input").strip()
        if market != "PSX":
            for name in ("fbr_category", "zakat_status"):
                self.fields.pop(name, None)


class KYCEmploymentForm(forms.ModelForm):
    class Meta:
        model = KYCEmployment
        exclude = ["application", "created_by", "updated_by", "created_at", "updated_at"]
        widgets = {"employer_address": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " kyc-input").strip()