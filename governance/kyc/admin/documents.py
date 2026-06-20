"""
governance/kyc/admin/documents.py

Document and screening admin. Verification state is visible and filterable;
upload/verify timestamps and audit columns are read-only. The screening stub is
registered read-mostly (Phase 2 wires the live provider).
"""
from django.contrib import admin

from governance.kyc.models import KYCDocument, KYCThirdPartyCheck

_AUDIT_RO = ("created_by", "updated_by", "created_at", "updated_at")


@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "document_id",
        "application",
        "document_type",
        "verification_status",
        "verified_by",
        "verified_at",
        "uploaded_at",
    )
    list_filter = ("verification_status", "document_type")
    search_fields = ("application__application_number", "original_filename")
    autocomplete_fields = ("application", "verified_by")
    raw_id_fields = ("joint_holder",)
    readonly_fields = ("uploaded_at", "original_filename", *_AUDIT_RO)
    date_hierarchy = "uploaded_at"


@admin.register(KYCThirdPartyCheck)
class KYCThirdPartyCheckAdmin(admin.ModelAdmin):
    list_display = (
        "third_party_check_id",
        "application",
        "provider",
        "outcome",
        "requested_at",
        "completed_at",
    )
    list_filter = ("provider", "outcome")
    search_fields = ("application__application_number", "reference")
    autocomplete_fields = ("application",)
    readonly_fields = ("requested_at", "completed_at", "raw_response", *_AUDIT_RO)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False