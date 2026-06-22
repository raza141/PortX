"""
governance/kyc/forms/dynamic_rows.py

Inline formsets for the repeating groups, plus a registry so the wizard/AJAX
endpoints can resolve a group name to its formset and row partial. The group
string is also the formset prefix, so kyc.js's `<group>-TOTAL_FORMS` lines up.

Two formset base classes do the heavy lifting:

* KYCBaseInlineFormSet   - makes brand-new, unsaved rows OPTIONAL. A blank extra
                           row (or an added-then-removed row) is skipped entirely
                           instead of raising "this field is required". This is
                           Django's own `empty_permitted` contract, applied to
                           every new row so the behaviour is uniform across all
                           groups and resilient to TOTAL_FORMS drift on resume.
* PrincipalScopedFormSet - additionally hides the `joint_holder` selector unless
                           the parent application is JOINT. Reads holding type
                           from the formset's parent instance (reliable for new
                           rows and for the AJAX empty_form).
"""
from django import forms
from django.forms import BaseInlineFormSet, DateInput, inlineformset_factory

from governance.kyc.constants import MAX_ADDITIONAL_JOINT_HOLDERS
from governance.kyc.models import (
    KYCApplication,
    KYCBankAccount,
    KYCDocument,
    KYCIdentityDocument,
    KYCJointHolder,
    KYCNominee,
    KYCPowerOfAttorney,
    KYCResidencyTax,
)
from schwifty import IBAN
from schwifty.exceptions import SchwiftyException


# --------------------------------------------------------------------------- #
# Formset base classes
# --------------------------------------------------------------------------- #
class KYCBaseInlineFormSet(BaseInlineFormSet):
    """Make every new (unsaved) row optional.

    Django skips a blank form only when `empty_permitted=True` and the row has
    not changed. Inline formsets set this for `extra` rows, but custom add_fields
    overrides and resume/TOTAL_FORMS drift can leave a new row being validated as
    required -- which surfaces as "<model>_id: This field is required" on a blank
    trailing row. Forcing `empty_permitted` on all new rows (and dropping the
    hidden id's required flag) restores the correct contract uniformly:

      * a blank new row -> skipped, no errors, not saved;
      * a partially/fully filled new row -> validated normally;
      * a saved row (has pk) -> always validated.
    """

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if form.instance.pk is None:
            form.empty_permitted = True
            if "id" in form.fields:
                form.fields["id"].required = False


class PrincipalScopedFormSet(KYCBaseInlineFormSet):
    """Hide `joint_holder` unless the parent application is JOINT.

    Decided at the formset level so it is correct for brand-new rows and for the
    AJAX empty_form, where the child instance has no application set yet. Calls
    super().add_fields first so the empty_permitted contract above still applies.
    """

    def add_fields(self, form, index):
        super().add_fields(form, index)
        if "joint_holder" in form.fields:
            holding = getattr(self.instance, "account_holding_type", None)
            if holding != "JOINT":
                form.fields.pop("joint_holder")


# --------------------------------------------------------------------------- #
# Custom row form (bank account: IBAN validation -> field error, not a 500)
# --------------------------------------------------------------------------- #
class KYCBankAccountForm(forms.ModelForm):
    class Meta:
        model = KYCBankAccount
        fields = ["account_number", "account_title", "bank_name", "branch",
                  "branch_address", "iban", "currency", "is_primary"]

    def clean_iban(self):
        raw = (self.cleaned_data.get("iban") or "").strip()
        if not raw:
            return raw
        try:
            IBAN(raw)
        except SchwiftyException:
            raise forms.ValidationError("Enter a valid IBAN.")
        return raw.replace(" ", "").upper()


# --------------------------------------------------------------------------- #
# Formsets — every factory wires in the right base class (and form where needed)
# --------------------------------------------------------------------------- #
IdentityDocumentFormSet = inlineformset_factory(
    KYCApplication, KYCIdentityDocument, fk_name="application",
    formset=PrincipalScopedFormSet,
    fields=["joint_holder", "identity_doc_type", "document_number",
            "issue_date", "expiry_date", "issuing_country"],
    widgets={
        "issue_date": DateInput(attrs={"type": "date"}),
        "expiry_date": DateInput(attrs={"type": "date"}),
    },
    extra=1, can_delete=True,
)

ResidencyTaxFormSet = inlineformset_factory(
    KYCApplication, KYCResidencyTax, fk_name="application",
    formset=PrincipalScopedFormSet,
    fields=["joint_holder", "country", "tax_identification_number",
            "tin_unavailable_reason"],
    extra=1, can_delete=True,
)

JointHolderFormSet = inlineformset_factory(
    KYCApplication, KYCJointHolder, fk_name="application",
    formset=KYCBaseInlineFormSet,
    fields=["holder_sequence", "given_name", "middle_name", "family_name",
            "date_of_birth", "nationality", "share_percentage", "tax_status"],
    widgets={
        "date_of_birth": DateInput(attrs={"type": "date"}),
    },
    extra=0, max_num=MAX_ADDITIONAL_JOINT_HOLDERS, validate_max=True, can_delete=True,
)

NomineeFormSet = inlineformset_factory(
    KYCApplication, KYCNominee, fk_name="application",
    formset=KYCBaseInlineFormSet,
    fields=["nominee_name", "relation", "national_id_number", "share_percentage"],
    extra=1, can_delete=True,
)

BankAccountFormSet = inlineformset_factory(
    KYCApplication, KYCBankAccount, fk_name="application",
    form=KYCBankAccountForm,
    formset=KYCBaseInlineFormSet,
    extra=1, can_delete=True,
)

PowerOfAttorneyFormSet = inlineformset_factory(
    KYCApplication, KYCPowerOfAttorney, fk_name="application",
    formset=KYCBaseInlineFormSet,
    fields=["person_name", "document_type", "address", "passport_number",
            "passport_issue_date", "passport_expiry_date",
            "national_id_number", "national_id_expiry_date"],
    widgets={
        "passport_issue_date": DateInput(attrs={"type": "date"}),
        "passport_expiry_date": DateInput(attrs={"type": "date"}),
        "national_id_expiry_date": DateInput(attrs={"type": "date"}),
    },
    extra=0, can_delete=True,
)

KYCDocumentFormSet = inlineformset_factory(
    KYCApplication, KYCDocument, fk_name="application",
    formset=PrincipalScopedFormSet,
    fields=["joint_holder", "document_type", "file"],
    extra=1, can_delete=True,
)


# --------------------------------------------------------------------------- #
# Registry — group name -> formset / row partial. Name doubles as the prefix.
# --------------------------------------------------------------------------- #
GROUP_FORMSETS = {
    "identity": IdentityDocumentFormSet,
    "residency": ResidencyTaxFormSet,
    "joint_holder": JointHolderFormSet,
    "nominee": NomineeFormSet,
    "bank_account": BankAccountFormSet,
    "poa": PowerOfAttorneyFormSet,
    "document": KYCDocumentFormSet,
}

GROUP_TEMPLATES = {
    "identity": "kyc/partials/_identity_doc_row.html",
    "residency": "kyc/partials/_residency_row.html",
    "joint_holder": "kyc/partials/_joint_holder_row.html",
    "nominee": "kyc/partials/_nominee_row.html",
    "bank_account": "kyc/partials/_bank_account_row.html",
    "poa": "kyc/partials/_poa_row.html",
    "document": "kyc/partials/_document_row.html",
}


def build_formsets(application, *, data=None, files=None):
    """All repeating-group formsets bound to an application, prefixed by group name."""
    return {
        group: fs(data=data, files=files, instance=application, prefix=group)
        for group, fs in GROUP_FORMSETS.items()
    }