"""
governance/kyc/services/document_rules.py

Data-driven attachment requirements. Determines which document types are required
for an application given its flags and market, and which are still missing.
Market/document rules live here, never branched at the API boundary.
"""
from __future__ import annotations

from governance.kyc.choices import DocumentType, Market, POADocumentType


def required_documents(application) -> list[str]:
    """Return the set of DocumentType codes required for this application."""
    required: set[str] = {
        DocumentType.ADDRESS_PROOF,
        DocumentType.SOW_PROOF,
    }

    # Identity-driven copies.
    id_types = set(
        application.identity_documents.values_list("identity_doc_type", flat=True)
    )
    if "PASSPORT" in id_types:
        required.add(DocumentType.PASSPORT_COPY)
    if id_types & {"NATIONAL_ID", "CNIC", "NICOP", "EMIRATES_ID"}:
        required.add(DocumentType.NATIONAL_ID_COPY)

    # Tax / FATCA / CRS driven.
    residence = getattr(application, "residence", None)
    if residence and (
        residence.tax_status == "APPLICABLE"
        or residence.fatca_applicable
        or residence.crs_applicable
    ):
        required.add(DocumentType.TIN_PROOF)

    # Bank account present -> bank statement.
    if application.bank_accounts.exists():
        required.add(DocumentType.BANK_STATEMENT)

    # Source of funds = salary/employment -> salary statement.
    sow = getattr(application, "source_of_wealth", None)
    if sow and sow.source_of_funds and "salary" in sow.source_of_funds.lower():
        required.add(DocumentType.SALARY_STATEMENT)

    # POA-driven.
    poa_qs = application.power_of_attorney_holders.all()
    if poa_qs.exists():
        required.add(DocumentType.POA_DOCUMENT)
        if poa_qs.filter(document_type=POADocumentType.COMPANY_LETTER).exists():
            required.add(DocumentType.COMPANY_LETTER)

    # Market-specific hook (extend per jurisdiction in Phase 1.1).
    if application.onboarding_market and application.onboarding_market.code == Market.PSX:
        pass  # e.g. add a PSX-specific document code here when confirmed.

    return sorted(required)


def missing_documents(application) -> list[str]:
    """Required document types that have no uploaded file yet."""
    present = set(application.documents.values_list("document_type", flat=True))
    return [doc for doc in required_documents(application) if doc not in present]