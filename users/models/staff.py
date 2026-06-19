# users/models/staff.py
from django.conf import settings
from django.db import models

from users.choices import (
    UserRole,
    UserMarket,
    DepartmentChoices,
    DesignationChoices,
)

class StaffProfile(models.Model):
    """
    Extends the base user model to store employment, role, and market-specific
    details for staff members operating within the platform.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_profile",
        help_text="The base user account linked to this staff profile."
    )
    employee_code = models.CharField(
        max_length=50,
        unique=True,
        help_text="A unique {P00100} code assigned to the employee."
    )
    department = models.CharField(
        max_length=30,
        choices=DepartmentChoices.choices,
        help_text="The specific functional department within the financial institution."
    )
    designation = models.CharField(
        max_length=30,
        choices=DesignationChoices.choices,
        help_text="The employee's official role and structural hierarchy level."
    )
    branch = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The physical or localized branch office the employee belongs to."
    )
    rm_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="The specific Relationship Manager (RM) code, if applicable."
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,  # BUG FIX: Removed parentheses
        default=UserRole.CLIENT,
        help_text="The system access role defining permissions and workflows for this user."
    )
    market = models.CharField(
        max_length=10,
        choices=UserMarket.choices, # BUG FIX: Removed parentheses
        default=UserMarket.PSX,
        help_text="The primary financial market this staff member is authorized to operate in (e.g., PSX)."
    )
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="subordinates",
        help_text="The direct manager this employee reports to. Creates the Org Chart."
    )
    is_active_staff = models.BooleanField(
        default=True,
        help_text="Designates whether this staff member is currently active in the organization."
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_staff",
        help_text="The administrative user who initially created this staff profile."
    )

    class Meta:
        db_table = "users_staff_profile"

    def __str__(self):
        return f"{self.employee_code} – {self.user.get_full_name()}"

    # ── Convenience role checks (Updated for logical consistency) ──────

    @property
    def is_client(self):
        return self.role == UserRole.CLIENT

    @property
    def is_rm(self):
        # Checks both the system role and the actual designation
        return (
            self.role == UserRole.RM or
            self.designation in (DesignationChoices.RM, DesignationChoices.SENIOR_RM, DesignationChoices.WEALTH_MGR)
        )

    @property
    def is_compliance(self):
        # Critical for KYC: Checks role OR if they sit in the Compliance department
        return (
            self.role in (UserRole.COMPLIANCE_L1, UserRole.COMPLIANCE_FINAL) or
            self.department == DepartmentChoices.COMPLIANCE_LEGAL # Update string to match your DepartmentChoices
        )

    @property
    def is_senior_mgmt(self):
        return (
            self.role == UserRole.SENIOR_MGMT or
            self.designation in (DesignationChoices.CEO, DesignationChoices.CIO, DesignationChoices.CCO) # Update strings to match your DesignationChoices
        )