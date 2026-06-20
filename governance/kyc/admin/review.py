"""
governance/kyc/admin/review.py

Status-log admin. The log is append-only and immutable: it is fully read-only in
the admin (no add / change / delete). Status transitions are made only through
services/workflow.py, which writes these rows.
"""
from django.contrib import admin

from governance.kyc.models import KYCStatusLog


@admin.register(KYCStatusLog)
class KYCStatusLogAdmin(admin.ModelAdmin):
    list_display = (
        "status_log_id",
        "application",
        "from_status",
        "to_status",
        "action",
        "actor",
        "created_at",
    )
    list_filter = ("action", "to_status", "from_status")
    search_fields = ("application__application_number", "actor__username", "reason")
    autocomplete_fields = ("application", "actor")
    readonly_fields = (
        "application",
        "from_status",
        "to_status",
        "action",
        "actor",
        "reason",
        "created_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False