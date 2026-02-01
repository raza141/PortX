from django.apps import AppConfig

#
# class SecuritesConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'instruments'


class InstrumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "refdata.instruments"
    label = "instruments"
