"""
governance/kyc/forms/section_1.py

Start (initiation) form and the Personal Information section form. AJAX-first:
forms render section-by-section and validate without full-page reloads.
"""
from django import forms

from governance.kyc.models import KYCApplication, KYCPersonalInfo


class KYCStartForm(forms.ModelForm):
    """Initiation form. `person_type` is implicit INDIVIDUAL and not exposed."""

    class Meta:
        model = KYCApplication
        fields = [
            "onboarding_market",
            "account_holding_type",
            "client_classification",
            "initiation_channel",
            "referral_source",
        ]
        widgets = {
            "onboarding_market": forms.Select(attrs={"class": "kyc-input"}),
            "account_holding_type": forms.Select(attrs={"class": "kyc-input"}),
            "client_classification": forms.Select(attrs={"class": "kyc-input"}),
            "initiation_channel": forms.Select(attrs={"class": "kyc-input"}),
            "referral_source": forms.Select(attrs={"class": "kyc-input"}),
        }


class KYCPersonalInfoForm(forms.ModelForm):
    class Meta:
        model = KYCPersonalInfo
        exclude = ["application", "created_by", "updated_by", "created_at", "updated_at"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "kyc-input"}),
            "permanent_address": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, market=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (css + " kyc-input").strip()
        # PSX-gated fields hidden for non-PSX markets.
        if market and market != "PSX":
            for name in ("religion", "father_or_husband_name"):
                self.fields.pop(name, None)