import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class Il(models.Model):
    """
    Model representing a province in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    ad = models.CharField(
        _("İl Adı"), max_length=50, unique=True, help_text=_("İl adı giriniz.")
    )
    plaka_kodu = models.IntegerField(
        _("Plaka Kodu"),
        unique=True,
        help_text=_("Plaka kodu giriniz."),
        error_messages={"unique": _("Bu plaka kodu zaten mevcut.")},
    )
    geom = models.PolygonField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("İl sınırlarını belirten geometri alanı."),
    )
    # Alan field calculated from the geometry field using QGIS
    alan = models.FloatField(
        _("Alan"),
        help_text=_("İl alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )
    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("İl çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("İl ile ilgili ekstra verileri JSON formatında giriniz."),
        blank=True,
        null=True,
    )

    osm_id = models.CharField(
        _("OSM ID"),
        max_length=50,
        unique=True,
        help_text=_("OpenStreetMap'den alınan benzersiz kimlik."),
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Oluşturulma Tarihi"), blank=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Güncellenme Tarihi"), blank=True, null=True
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("İl")
        verbose_name_plural = _("İller")
        ordering = ["ad"]
        db_table = '"ortak"."iller"'


class Ilce(models.Model):
    """
    Model representing a district in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    ad = models.CharField(
        _("İlçe Adı"), max_length=50, help_text=_("İlçe adı giriniz.")
    )
    il = models.ForeignKey(
        Il,
        on_delete=models.CASCADE,
        related_name="ilceler",
        verbose_name=_("İl"),
        help_text=_("İl seçiniz."),
    )

    geom = models.PolygonField(
        srid=settings.SRID,
        help_text=_("İlçe sınırlarını belirten geometri alanı."),
    )

    alan = models.FloatField(
        _("Alan"),
        help_text=_("İlçe alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )
    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("İlçe çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("İlçe ile ilgili ekstra verileri JSON formatında giriniz."),
        blank=True,
        null=True,
    )

    osm_id = models.CharField(
        _("OSM ID"),
        max_length=50,
        unique=True,
        help_text=_("OpenStreetMap'den alınan benzersiz kimlik."),
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Oluşturulma Tarihi"), blank=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Güncellenme Tarihi"), blank=True, null=True
    )

    def __str__(self):
        return f"{self.il.ad} - {self.ad}"

    class Meta:
        verbose_name = _("İlçe")
        verbose_name_plural = _("İlçeler")
        ordering = ["il__ad", "ad"]
        db_table = '"ortak"."ilceler"'


class Mahalle(models.Model):
    """
    Model representing a neighborhood in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    ad = models.CharField(
        _("Mahalle Adı"), max_length=50, help_text=_("Mahalle adı giriniz.")
    )
    ilce = models.ForeignKey(
        Ilce,
        on_delete=models.CASCADE,
        related_name="mahalleler",
        verbose_name=_("İlçe"),
        help_text=_("İlçe seçiniz."),
    )
    muhtar = models.CharField(
        _("Muhtar Adı"),
        max_length=50,
        help_text=_("Muhtar adı giriniz."),
        blank=True,
        null=True,
    )
    muhtar_telefon = models.CharField(
        _("Muhtar Telefonu"),
        max_length=15,
        help_text=_("Muhtar telefonunu giriniz."),
        blank=True,
        null=True,
    )
    muhtar_email = models.EmailField(
        _("Muhtar E-posta"),
        help_text=_("Muhtar e-posta adresini giriniz."),
        blank=True,
        null=True,
    )
    muhtar_adres = models.CharField(
        _("Muhtar Adresi"),
        max_length=255,
        help_text=_("Muhtar adresini giriniz."),
        blank=True,
        null=True,
    )
    nufus = models.IntegerField(
        _("Nüfus"),
        help_text=_("Mahalle nüfusunu giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    geom = models.PolygonField(
        srid=settings.SRID,
        help_text=_("Mahalle sınırlarını belirten geometri alanı."),
    )
    alan = models.FloatField(
        _("Alan"),
        help_text=_("Mahalle alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )
    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("Mahalle çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Mahalle ile ilgili ekstra verileri JSON formatında giriniz."),
        blank=True,
        null=True,
    )
    osm_id = models.CharField(
        _("OSM ID"),
        max_length=50,
        unique=True,
        help_text=_("OpenStreetMap'den alınan benzersiz kimlik."),
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Oluşturulma Tarihi"), blank=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Güncellenme Tarihi"), blank=True, null=True
    )

    def __str__(self):
        return f"{self.ilce.il.ad} - {self.ilce.ad} - {self.ad}"

    class Meta:
        verbose_name = _("Mahalle")
        verbose_name_plural = _("Mahalleler")
        ordering = ["ilce__il__ad", "ilce__ad", "ad"]
        db_table = '"ortak"."mahalleler"'


class Ada(models.Model):
    """
    Model representing a parcel in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    pafta_no = models.CharField(
        _("Pafta No"),
        max_length=50,
        help_text=_("Pafta numarasını giriniz."),
    )
    ada_no = models.CharField(
        _("Ada No"),
        max_length=50,
        help_text=_("Ada numarasını giriniz."),
    )
    mahalle = models.ForeignKey(
        Mahalle,
        on_delete=models.CASCADE,
        related_name="adalar",
        verbose_name=_("Mahalle"),
        help_text=_("Mahalle seçiniz."),
    )

    geom = models.PolygonField(
        srid=settings.SRID,
        help_text=_("Ada sınırlarını belirten geometri alanı."),
    )
    alan = models.FloatField(
        _("Alan"),
        help_text=_("Ada alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("Ada çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Ada ile ilgili ekstra verileri JSON formatında giriniz."),
        blank=True,
        null=True,
    )
    osm_id = models.CharField(
        _("OSM ID"),
        max_length=50,
        unique=True,
        help_text=_("OpenStreetMap'den alınan benzersiz kimlik."),
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Oluşturulma Tarihi"), blank=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Güncellenme Tarihi"), blank=True, null=True
    )

    def __str__(self):
        return f"{self.mahalle.ilce.il.ad} - {self.mahalle.ilce.ad} - {self.mahalle.ad} - {self.ad}"

    class Meta:
        verbose_name = _("Ada")
        verbose_name_plural = _("Adalar")
        ordering = [
            "mahalle__ilce__il__ad",
            "mahalle__ilce__ad",
            "mahalle__ad",
            "ada_no",
        ]
        db_table = '"ortak"."adalar"'
