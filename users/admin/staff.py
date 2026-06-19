from django.contrib import admin
from users.models.staff import StaffProfile


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    # ─── List View Settings ───────────────────────────────────────────
    # What columns appear on the main table
    list_display = (
        "employee_code",
        "get_user_full_name",
        "department",
        "designation",
        "role",
        "market",
        "is_active_staff",
    )

    # Creates a filter sidebar on the right
    list_filter = (
        "is_active_staff",
        "market",
        "role",
        "department",
        "designation",
        "branch",
    )

    # Adds a search bar at the top
    search_fields = (
        "employee_code",
        "rm_code",
        "user__email",
        "user__first_name",
        "user__last_name",
    )

    # ─── Detail/Edit View Settings ────────────────────────────────────
    # Organizes the form fields into clean, labeled sections
    fieldsets = (
        ("User Identity", {
            "fields": ("user", "employee_code", "is_active_staff")
        }),
        ("Organizational Placement", {
            "fields": ("department", "designation", "branch", "reports_to")
        }),
        ("System & Market Access", {
            "fields": ("role", "market", "rm_code")
        }),
        ("Audit Information", {
            "fields": ("created_by",),
            "classes": ("collapse",)  # Keeps this section hidden by default
        }),
    )

    # Use raw_id_fields for ForeignKeys to prevent the admin from loading
    # a massive dropdown menu if you have thousands of users.
    raw_id_fields = ("user", "reports_to", "created_by")

    # ─── Custom Display Methods ───────────────────────────────────────

    @admin.display(description="Full Name", ordering="user__first_name")
    def get_user_full_name(self, obj):
        """Fetches the actual name from the linked User model."""
        return obj.user.get_full_name() or obj.user.email