from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    # Purely cosmetic label for the Django Admin panel.
    # We use verbose_name so we don't break the database migrations or imports.
    verbose_name = "Organization & Staff"