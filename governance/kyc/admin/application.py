"""
governance/kyc/admin/application.py

Application admin. Status is read-only here — it must only change through
services/workflow.py — and audit columns are protected. Child records appear as
inlines for operational review.
"""
from django.contrib import admin
# This will create updated_at, created_at like time-stamp
from governance.kyc.admin.base import KYCAuditAdminMixin

from governance.kyc.models import (
    KYCApplication,
    KYCBankAccount,
    KYCEmployment,
    KYCIdentityDocument,
    KYCJointHolder,
    KYCNominee,
    KYCPersonalInfo,
    KYCPowerOfAttorney,
    KYCReferralSource,
    KYCResidence,
    KYCResidencyTax,
    KYCSourceOfWealth,
)

_AUDIT_RO = ("created_by", "updated_by", "created_at", "updated_at")


class PersonalInfoInline(admin.StackedInline):
    model = KYCPersonalInfo
    extra = 0
    readonly_fields = _AUDIT_RO


class ResidenceInline(admin.StackedInline):
    model = KYCResidence
    extra = 0
    readonly_fields = _AUDIT_RO


class EmploymentInline(admin.StackedInline):
    model = KYCEmployment
    extra = 0
    readonly_fields = _AUDIT_RO


class SourceOfWealthInline(admin.StackedInline):
    model = KYCSourceOfWealth
    extra = 0
    readonly_fields = _AUDIT_RO


class IdentityDocumentInline(admin.TabularInline):
    model = KYCIdentityDocument
    extra = 0
    readonly_fields = _AUDIT_RO


class ResidencyTaxInline(admin.TabularInline):
    model = KYCResidencyTax
    extra = 0
    readonly_fields = _AUDIT_RO


class JointHolderInline(admin.TabularInline):
    model = KYCJointHolder
    extra = 0
    readonly_fields = _AUDIT_RO


class NomineeInline(admin.TabularInline):
    model = KYCNominee
    extra = 0
    readonly_fields = _AUDIT_RO


class BankAccountInline(admin.TabularInline):
    model = KYCBankAccount
    extra = 0
    readonly_fields = _AUDIT_RO


class PowerOfAttorneyInline(admin.TabularInline):
    model = KYCPowerOfAttorney
    extra = 0
    readonly_fields = _AUDIT_RO


@admin.register(KYCApplication)
class KYCApplicationAdmin(KYCAuditAdminMixin, admin.ModelAdmin):
    list_display = (
        "application_number",
        "onboarding_market",
        "application_status",
        "client_classification",
        "account_holding_type",
        "aml_risk_rating",
        "kyc_opening_date",
    )
    list_filter = ("onboarding_market", "application_status", "client_classification", "account_holding_type")
    search_fields = ("application_number", "owner_user__username", "investor__inv_nm")
    readonly_fields = ("application_number", "application_status", "version", "supersedes", *_AUDIT_RO)
    autocomplete_fields = ("owner_user", "referral_source")
    raw_id_fields = ("investor",)
    date_hierarchy = "kyc_opening_date"
    inlines = [
        PersonalInfoInline,
        IdentityDocumentInline,
        ResidenceInline,
        ResidencyTaxInline,
        EmploymentInline,
        SourceOfWealthInline,
        JointHolderInline,
        NomineeInline,
        BankAccountInline,
        PowerOfAttorneyInline,
    ]


@admin.register(KYCReferralSource)
class KYCReferralSourceAdmin(KYCAuditAdminMixin, admin.ModelAdmin):
    list_display = ("referral_source_id", "referral_type", "staff_profile", "external_party_name", "external_branch_name")
    list_filter = ("referral_type",)
    search_fields = ("external_party_name", "external_party_code", "external_branch_name")
    readonly_fields = _AUDIT_RO