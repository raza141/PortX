"""governance/kyc/forms/section_4.py — Requirements / Attachments upload form."""
from django import forms

from governance.kyc.models import KYCDocument


class KYCDocumentForm(forms.ModelForm):
    class Meta:
        model = KYCDocument
        fields = ["document_type", "file", "joint_holder"]
        widgets = {
            "document_type": forms.Select(attrs={"class": "kyc-input"}),
            "joint_holder": forms.Select(attrs={"class": "kyc-input"}),
        }

    def __init__(self, *args, application=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["joint_holder"].queryset = self.fields["joint_holder"].queryset.none()
        self.fields["joint_holder"].required = False
        if application is not None:
            self.fields["joint_holder"].queryset = application.joint_holders.all()