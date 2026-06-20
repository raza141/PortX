"""governance/kyc/forms — ModelForms (1:1 sections) and formsets (repeating groups)."""
from governance.kyc.forms.section_1 import KYCStartForm, KYCPersonalInfoForm
from governance.kyc.forms.section_2 import KYCResidenceForm
from governance.kyc.forms.section_3 import KYCSourceOfWealthForm, KYCEmploymentForm
from governance.kyc.forms.dynamic_rows import (
    IdentityDocumentFormSet,
    ResidencyTaxFormSet,
    JointHolderFormSet,
    NomineeFormSet,
    BankAccountFormSet,
    PowerOfAttorneyFormSet,
)

__all__ = [
    "KYCStartForm",
    "KYCPersonalInfoForm",
    "KYCResidenceForm",
    "KYCSourceOfWealthForm",
    "KYCEmploymentForm",
    "IdentityDocumentFormSet",
    "ResidencyTaxFormSet",
    "JointHolderFormSet",
    "NomineeFormSet",
    "BankAccountFormSet",
    "PowerOfAttorneyFormSet",
]