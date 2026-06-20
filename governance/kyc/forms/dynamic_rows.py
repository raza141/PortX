"""
governance/kyc/forms/dynamic_rows.py

Inline formsets for the repeating groups, plus a registry so the AJAX add/save
endpoints can resolve a group name to its formset and row partial. The group
string is also the formset prefix, so kyc.js's `<group>-TOTAL_FORMS` lines up.
"""
from django.forms import inlineformset_factory

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

IdentityDocumentFormSet = inlineformset_factory(
    KYCApplication, KYCIdentityDocument, fk_name="application",
    fields=["joint_holder", "identity_doc_type", "document_number",
            "issue_date", "expiry_date", "issuing_country"],
    extra=1, can_delete=True,
)

ResidencyTaxFormSet = inlineformset_factory(
    KYCApplication, KYCResidencyTax, fk_name="application",
    fields=["joint_holder", "country", "tax_identification_number", "tin_unavailable_reason"],
    extra=1, can_delete=True,
)

JointHolderFormSet = inlineformset_factory(
    KYCApplication, KYCJointHolder, fk_name="application",
    fields=["holder_sequence", "given_name", "middle_name", "family_name",
            "date_of_birth", "nationality", "share_percentage", "tax_status"],
    extra=0, max_num=MAX_ADDITIONAL_JOINT_HOLDERS, validate_max=True, can_delete=True,
)

NomineeFormSet = inlineformset_factory(
    KYCApplication, KYCNominee, fk_name="application",
    fields=["nominee_name", "relation", "national_id_number", "share_percentage"],
    extra=1, can_delete=True,
)

BankAccountFormSet = inlineformset_factory(
    KYCApplication, KYCBankAccount, fk_name="application",
    fields=["account_number", "account_title", "bank_name", "branch",
            "branch_address", "iban", "currency", "is_primary"],
    extra=1, can_delete=True,
)

PowerOfAttorneyFormSet = inlineformset_factory(
    KYCApplication, KYCPowerOfAttorney, fk_name="application",
    fields=["person_name", "document_type", "address", "passport_number",
            "passport_issue_date", "passport_expiry_date",
            "national_id_number", "national_id_expiry_date"],
    extra=0, can_delete=True,
)

KYCDocumentFormSet = inlineformset_factory(
    KYCApplication, KYCDocument, fk_name="application",
    fields=["joint_holder", "document_type", "file"],
    extra=1, can_delete=True,
)

# group name -> formset; the name doubles as the formset prefix.
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