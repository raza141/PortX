"""
governance/kyc/choices.py

Single source of truth for every KYC enumeration. No TextChoices are defined
anywhere else in the app. Codes are short and stable; human labels carry the
readable text. Where a concept already exists in the CRM app, the same codes are
reused so the downstream handoff needs no translation.
"""
from django.db import models


# --------------------------------------------------------------------------- #
# Market / workflow                                                           #
# --------------------------------------------------------------------------- #
class Market(models.TextChoices):
    """Target market a KYC application is raised for (market-agnostic key)."""
    PSX = "PSX", "Pakistan Stock Exchange"
    US = "US", "US Equities"
    GCC = "GCC", "GCC Region"
    SARWA = "SARWA", "SARWA / Digital Wealth"


class ApplicationStatus(models.TextChoices):
    """KYC application lifecycle. KYC is the sole owner of this lifecycle."""
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    ADDL_INFO = "ADDL_INFO", "Additional Info Required"
    ESCALATED = "ESCALATED", "Escalated"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class StatusAction(models.TextChoices):
    """Named workflow transitions consumed by services/workflow.py."""
    INITIATE = "INITIATE", "Initiate"      # <-- add this line
    SUBMIT = "SUBMIT", "Submit"
    START_REVIEW = "START_REVIEW", "Start Review"
    REQUEST_INFO = "REQUEST_INFO", "Request Additional Info"
    RESUBMIT = "RESUBMIT", "Resubmit"
    ESCALATE = "ESCALATE", "Escalate"
    APPROVE = "APPROVE", "Approve"
    REJECT = "REJECT", "Reject"
    SUPERSEDE = "SUPERSEDE", "Supersede (Re-KYC)"


class InitiationChannel(models.TextChoices):
    """Who initiated onboarding. Both modes share one code path."""
    SELF = "SELF", "Self-Service"
    RM_ASSISTED = "RM_ASSISTED", "RM-Assisted"


# --------------------------------------------------------------------------- #
# Account / classification                                                    #
# --------------------------------------------------------------------------- #
class AccountHoldingType(models.TextChoices):
    """Holding structure of the account. Drives the joint-holder subsection."""
    SINGLE = "SINGLE", "Single"
    JOINT = "JOINT", "Joint"


class PersonType(models.TextChoices):
    """
    Natural-person discriminator. Phase 1 is INDIVIDUAL only and this field is
    not exposed in the UI; it is retained for the corporate phase.
    """
    INDIVIDUAL = "INDIVIDUAL", "Individual"
    CORPORATE = "CORPORATE", "Corporate"


class ClientClassification(models.TextChoices):
    """Regulatory client classification. Reuses CRM codes (RET/PRO/ECP)."""
    RETAIL = "RET", "Retail"
    PROFESSIONAL = "PRO", "Professional"
    ELIGIBLE_COUNTERPARTY = "ECP", "Market Counter Party / Eligible Counterparty"


# --------------------------------------------------------------------------- #
# Personal                                                                    #
# --------------------------------------------------------------------------- #
class Salutation(models.TextChoices):
    MR = "MR", "Mr."
    MRS = "MRS", "Mrs."
    MS = "MS", "Ms."
    DR = "DR", "Dr."
    OTHER = "OTH", "Other"


class Gender(models.TextChoices):
    """Business-valid gender values only (the raw 'R' note was source noise)."""
    MALE = "M", "Male"
    FEMALE = "F", "Female"


class MaritalStatus(models.TextChoices):
    SINGLE = "SINGLE", "Single"
    MARRIED = "MARRIED", "Married"
    DIVORCED = "DIVORCED", "Divorced"
    WIDOWED = "WIDOWED", "Widowed"


# --------------------------------------------------------------------------- #
# Tax / residency                                                             #
# --------------------------------------------------------------------------- #
class TaxApplicability(models.TextChoices):
    """Whether FATCA/CRS tax-residency reporting applies to the holder."""
    APPLICABLE = "APPLICABLE", "Applicable"
    NON_APPLICABLE = "NON_APPLICABLE", "Non-Applicable"


# --------------------------------------------------------------------------- #
# Identity documents                                                          #
# --------------------------------------------------------------------------- #
class IdentityDocType(models.TextChoices):
    """Market-agnostic identity document taxonomy."""
    PASSPORT = "PASSPORT", "Passport"
    NATIONAL_ID = "NATIONAL_ID", "National ID"
    CNIC = "CNIC", "CNIC (Pakistan)"
    NICOP = "NICOP", "NICOP (Pakistan, Overseas)"
    EMIRATES_ID = "EMIRATES_ID", "Emirates ID"
    SSN = "SSN", "US SSN / ITIN"
    OTHER = "OTHER", "Other"


# --------------------------------------------------------------------------- #
# Source of wealth                                                            #
# --------------------------------------------------------------------------- #
class SourceClassification(models.TextChoices):
    INDIVIDUAL = "INDIVIDUAL", "Individual"
    CORPORATE = "CORPORATE", "Corporate"



class SourceOfWealthType(models.TextChoices):
    SALARY = "SALARY", "Salary / Employment Income"
    BUSINESS = "BUSINESS", "Business Income / Business Ownership"
    SAVINGS = "SAVINGS", "Savings / Deposits"
    INVESTMENTS = "INVEST", "Investments / Capital Gains"
    DIVIDENDS = "DIV", "Dividends"
    BONUS = "BONUS", "Bonus"
    RENTAL = "RENTAL", "Rental Income"
    INHERITANCE = "INHERIT", "Inheritance"
    GIFT = "GIFT", "Gift"
    PROPERTY_SALE = "PROP_SALE", "Sale of Property"
    BUSINESS_SALE = "BIZ_SALE", "Sale of Business"
    ASSET_SALE = "ASSET_SALE", "Sale of Shares / Assets"
    PENSION = "PENSION", "Pension / Retirement Benefits"
    OTHER = "OTHER", "Other"


class SourceOfFundsType(models.TextChoices):
    SALARY = "SALARY", "Salary / Employment Income"
    BUSINESS = "BUSINESS", "Business Income"
    SAVINGS = "SAVINGS", "Savings / Deposits"
    INVESTMENT_PROCEEDS = "INVEST", "Investment Proceeds"
    DIVIDENDS = "DIV", "Dividends"
    BONUS = "BONUS", "Bonus"
    RENTAL = "RENTAL", "Rental Income"
    INHERITANCE = "INHERIT", "Inheritance"
    GIFT = "GIFT", "Gift"
    PROPERTY_SALE = "PROP_SALE", "Sale of Property"
    ASSET_SALE = "ASSET_SALE", "Sale of Shares / Assets"
    LOAN = "LOAN", "Loan / Borrowing"
    PENSION = "PENSION", "Pension / Retirement Benefits"
    OTHER = "OTHER", "Other"

# --------------------------------------------------------------------------- #
# Risk (AML/compliance) — NOT investment suitability                          #
# --------------------------------------------------------------------------- #
class RiskRating(models.TextChoices):
    """AML / compliance screening risk. Reuses CRM AmlRisk codes."""
    LOW = "L", "Low"
    MEDIUM = "M", "Medium"
    HIGH = "H", "High"


# --------------------------------------------------------------------------- #
# Frequencies                                                                 #
# --------------------------------------------------------------------------- #
class Frequency(models.TextChoices):
    MONTHLY = "MON", "Monthly"
    QUARTERLY = "QTR", "Quarterly"
    SEMI_ANNUAL = "SAA", "Semi-Annual"
    ANNUAL = "ANN", "Annual"
    AD_HOC = "ADH", "Ad hoc"


# --------------------------------------------------------------------------- #
# Nominee / POA                                                               #
# --------------------------------------------------------------------------- #
class NomineeRelation(models.TextChoices):
    SPOUSE = "SPOUSE", "Spouse"
    CHILD = "CHILD", "Child"
    PARENT = "PARENT", "Parent"
    SIBLING = "SIBLING", "Sibling"
    OTHER = "OTHER", "Other"


class POADocumentType(models.TextChoices):
    COMPANY_LETTER = "COMPANY_LETTER", "Company Letter"
    COUNTRY_DOCUMENT = "COUNTRY_DOCUMENT", "Country Document"
    POWER_OF_ATTORNEY = "POWER_OF_ATTORNEY", "Power of Attorney"


# --------------------------------------------------------------------------- #
# Referral / distribution                                                     #
# --------------------------------------------------------------------------- #
class ReferralType(models.TextChoices):
    """Source of the referral; decouples KYC from internal-staff identity."""
    INTERNAL_STAFF = "INTERNAL_STAFF", "Internal Staff / RM"
    EXTERNAL_DISTRIBUTOR = "EXTERNAL_DISTRIBUTOR", "External Distributor"
    DIRECT = "DIRECT", "Direct / Walk-in"
    OTHER = "OTHER", "Other"


# --------------------------------------------------------------------------- #
# Attachments                                                                 #
# --------------------------------------------------------------------------- #
class DocumentType(models.TextChoices):
    NATIONAL_ID_COPY = "NATIONAL_ID_COPY", "National ID / CNIC / NICOP Copy"
    PASSPORT_COPY = "PASSPORT_COPY", "Passport"
    TIN_PROOF = "TIN_PROOF", "TIN Proof"
    BANK_STATEMENT = "BANK_STATEMENT", "Bank Statement"
    SALARY_STATEMENT = "SALARY_STATEMENT", "Salary Statement"
    ADDRESS_PROOF = "ADDRESS_PROOF", "Address Proof / Utility Bill"
    SOW_PROOF = "SOW_PROOF", "Source-of-Wealth Proof"
    POA_DOCUMENT = "POA_DOCUMENT", "Power-of-Attorney Document"
    COMPANY_LETTER = "COMPANY_LETTER", "Company Letter"
    MARKET_SPECIFIC = "MARKET_SPECIFIC", "Market-Specific Supporting Document"


class VerificationStatus(models.TextChoices):
    UNVERIFIED = "UNVERIFIED", "Unverified"
    VERIFIED = "VERIFIED", "Verified"
    REJECTED = "REJECTED", "Rejected"


# --------------------------------------------------------------------------- #
# Screening (Phase-2 stub surface)                                            #
# --------------------------------------------------------------------------- #
class ScreeningProvider(models.TextChoices):
    WORLD_CHECK = "WORLD_CHECK", "World-Check"
    DOC_API = "DOC_API", "Document Validation API"
    LIVENESS = "LIVENESS", "Liveness / Face Match API"


class ScreeningOutcome(models.TextChoices):
    PENDING = "PENDING", "Pending"
    CLEAR = "CLEAR", "Clear"
    HIT = "HIT", "Potential Hit"
    ERROR = "ERROR", "Error"


# --------------------------------------------------------------------------- #
# PSX-specific value sets (surfaced only when market == PSX)                  #
# --------------------------------------------------------------------------- #
class Religion(models.TextChoices):
    ISLAM = "ISLAM", "Islam"
    OTHER = "OTHER", "Other"


class ZakatStatus(models.TextChoices):
    APPLICABLE = "APPLICABLE", "Applicable"
    NON_APPLICABLE = "NON_APPLICABLE", "Non-Applicable"


class FBRCategory(models.TextChoices):
    """Pakistan Federal Board of Revenue filing status."""
    FILER = "FILER", "Filer"
    NON_FILER = "NON_FILER", "Non-Filer"
    NA = "NA", "N/A"