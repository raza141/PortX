from django.apps import AppConfig

class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "governance.crm"   # NEW python path
    label = "crm"             # KEEP OLD label (super important)
    verbose_name = "Governance | CRM"   # name that we see on django admin panel
