from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrtakConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ortak"
    verbose_name = _("Ortak Veriler")
