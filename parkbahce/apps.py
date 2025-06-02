from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ParkbahceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "parkbahce"
    verbose_name = _("Park Bahçe")
