from django.apps import AppConfig


# class CrmConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "crm"


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "governance.crm"   # NEW python path
    label = "crm"             # KEEP OLD label (super important)
