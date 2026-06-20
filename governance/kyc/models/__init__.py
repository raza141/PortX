"""
governance/kyc/models/__init__.py

Re-exports every model so Django can discover them and so callers can import from
`governance.kyc.models` directly.
"""
from governance.kyc.models.application import KYCApplication
from governance.kyc.models.bank_account import KYCBankAccount
from governance.kyc.models.documents import KYCDocument
from governance.kyc.models.employment import KYCEmployment
from governance.kyc.models.identity_document import KYCIdentityDocument
from governance.kyc.models.joint_holder import KYCJointHolder
from governance.kyc.models.nominee import KYCNominee
from governance.kyc.models.personal_info import KYCPersonalInfo
from governance.kyc.models.poa import KYCPowerOfAttorney
from governance.kyc.models.referral import KYCReferralSource
from governance.kyc.models.residence import KYCResidence
from governance.kyc.models.residency_tax import KYCResidencyTax
from governance.kyc.models.screening import KYCThirdPartyCheck
from governance.kyc.models.source_of_wealth import KYCSourceOfWealth
from governance.kyc.models.status_log import KYCStatusLog

__all__ = [
    "KYCApplication",
    "KYCReferralSource",
    "KYCPersonalInfo",
    "KYCIdentityDocument",
    "KYCResidence",
    "KYCResidencyTax",
    "KYCEmployment",
    "KYCSourceOfWealth",
    "KYCJointHolder",
    "KYCNominee",
    "KYCBankAccount",
    "KYCPowerOfAttorney",
    "KYCDocument",
    "KYCStatusLog",
    "KYCThirdPartyCheck",
]