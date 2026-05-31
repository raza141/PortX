from django.contrib import admin
from .models import ReportRequest


@admin.register(ReportRequest)
class ReportRequestAdmin(admin.ModelAdmin):

    list_display = [
        "rpt_req_id",
        "portfolio_id",
        "period_end_dt",
        "sts_cd",
        "sent_to_email",
        "generated_at",
        "sent_at",
    ]
    list_filter  = ["sts_cd", "period_end_dt"]
    search_fields = ["portfolio_id__icontains", "sent_to_email"]
    ordering     = ["-period_end_dt"]
    readonly_fields = [
        "generated_at", "sent_at", "pdf_path",
        "error_txt", "created_at", "updated_at",
    ]
    fieldsets = (
        ("Report Identity", {
            "fields": ("portfolio_id", "period_end_dt")
        }),
        ("PM Commentary", {
            "fields": ("market_commentary", "portfolio_commentary", "outlook")
        }),
        ("Delivery", {
            "fields": ("sts_cd", "sent_to_email", "generated_at", "sent_at")
        }),
        ("File & Errors", {
            "fields": ("pdf_path", "error_txt"),
            "classes": ("collapse",)
        }),
        ("Audit", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )