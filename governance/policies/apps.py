from django.apps import AppConfig


class PoliciesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "governance.policies"   # <-- IMPORTANT (new path)
    label = "policies"             # <-- IMPORTANT (this is what makemigrations uses)
    verbose_name = "Governance | Policies"
