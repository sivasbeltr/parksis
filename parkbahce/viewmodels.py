import json

from django.contrib.postgres.fields import JSONField
from django.db import models
from django.utils.translation import gettext_lazy as _


class ViewParklarDonatilarHabitatlar(models.Model):
    """
    {
      "id": 1,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "ad": "Park 1",
      "donatilar": [
        {"donati_tipi": "Bank", "sayi": 5},
        {"donati_tipi": "Çöp Kutusu", "sayi": 3}
      ],
      "habitatlar": [
        {"habitat_tipi": "Ağaç", "sayi": 10},
        {"habitat_tipi": "Çalı", "sayi": 20}
      ]
    }
    """

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(
        verbose_name=_("UUID"),
        help_text=_("Park için benzersiz tanımlayıcı."),
        editable=False,
        unique=True,
    )
    ad = models.CharField(
        max_length=255,
        verbose_name=_("Park Adı"),
    )

    habitatlar = models.JSONField(
        verbose_name=_("Habitatlar"),
        help_text=_("Parka ait habitat verilerinin tutulduğu JSON alanı."),
        default=dict,
    )

    donatilar = models.JSONField(
        verbose_name=_("Donatılar"),
        help_text=_("Parka ait donatı verilerinin tutulduğu JSON alanı."),
        default=dict,
    )

    class Meta:
        verbose_name = _("Parklar Donatılar Habitatlar")
        verbose_name_plural = _("Parklar Donatılar Habitatlar")
        db_table = '"parkbahce"."view_parklar_donatilar_habitatlar"'
        managed = False
        ordering = ["ad"]

    def __str__(self):
        return self.ad
