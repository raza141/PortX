from django.apps import AppConfig


class KycConfig(AppConfig):
    """Governance :: KYC application configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "governance.kyc"
    label = "kyc"
    # This is lable in Django app, however, app name and relationship is "kyc" define.
    verbose_name = "KYC / Compliance Onboarding"