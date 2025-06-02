from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IstakipConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "istakip"
    verbose_name = _("İş Takip ve Talep Yönetimi")
