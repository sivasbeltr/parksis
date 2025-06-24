import uuid

from django.conf import settings
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from ortak.models import Ada, Mahalle


class AboneTipChoices(models.TextChoices):
    ELEKTRIK = "elektrik", _("Elektrik")
    SU = "su", _("Su")
    DOGALGAZ = "dogalgaz", _("Doğalgaz")
    TELEFON = "telefon", _("Telefon")
    INTERNET = "internet", _("İnternet")
    KABLOTV = "kablovt", _("Kablovt")


class SulamaTip(models.Model):
    ad = models.CharField(
        _("Sulama Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Sulama tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Sulama tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Sulama tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Sulama Tipi")
        verbose_name_plural = _("Sulama Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."sulama_tipleri"'


class SulamaKaynak(models.Model):

    ad = models.CharField(
        _("Sulama Kaynağı"),
        max_length=50,
        unique=True,
        help_text=_("Sulama kaynağı giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Sulama kaynağı için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Sulama kaynağı hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Sulama Kaynağı")
        verbose_name_plural = _("Sulama Kaynakları")
        ordering = ["ad"]
        db_table = '"parkbahce"."sulama_kaynaklari"'


class ParkTip(models.Model):
    ad = models.CharField(
        _("Park Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Park tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Park tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )

    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Park tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Park Tipi")
        verbose_name_plural = _("Park Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."park_tipleri"'


class KaplamaTip(models.Model):
    ad = models.CharField(
        _("Kaplama Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Kaplama tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Kaplama tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Kaplama tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Kaplama Tipi")
        verbose_name_plural = _("Kaplama Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."kaplama_tipleri"'


class SporAlanTip(models.Model):
    ad = models.CharField(
        _("Spor Alanı Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Spor alanı tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Spor alanı tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Spor alanı tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Spor Alanı Tipi")
        verbose_name_plural = _("Spor Alanı Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."spor_alan_tipleri"'


class ParkBinaKullanimTip(models.Model):
    """
    Model representing a building usage type in Turkey.
    """

    ad = models.CharField(
        _("Bina Kullanım Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Bina kullanım tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Bina kullanım tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Bina kullanım tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Bina Kullanım Tipi")
        verbose_name_plural = _("Bina Kullanım Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."bina_kullanim_tipleri"'


class DonatiTip(models.Model):
    """
    This model represents the type of park furniture within the park.
    """

    ad = models.CharField(
        _("Donatı Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Donatı tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Donatı tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Donatı tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Donatı Tipi")
        verbose_name_plural = _("Donatı Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."donati_tipleri"'


class OyunGrupTip(models.Model):
    """
    Model representing a playground group type in Turkey.
    """

    ad = models.CharField(
        _("Oyun Grubu Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Oyun grubu tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Oyun grubu tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Oyun grubu tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Oyun Grubu Tipi")
        verbose_name_plural = _("Oyun Grubu Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."oyun_grubu_tipleri"'


class OyunGrupModel(models.Model):
    """
    Model representing a playground group model in Turkey.
    """

    ad = models.CharField(
        _("Oyun Grubu Modeli"),
        max_length=50,
        unique=True,
        help_text=_("Oyun grubu modeli giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Oyun grubu modeli için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Oyun grubu modeli hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Oyun Grubu Modeli")
        verbose_name_plural = _("Oyun Grubu Modelleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."oyun_grubu_modelleri"'


class SulamaBoruTip(models.Model):
    """
    Model representing a pipe type in Turkey.
    """

    ad = models.CharField(
        _("Boru Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Boru tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Boru tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Boru tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Sulama Boru Tipi")
        verbose_name_plural = _("Sulama Boru Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."sulama_boru_tipleri"'


class SulamaNoktaTip(models.Model):
    """
    Model representing a irrigation point type in Turkey.
    """

    ad = models.CharField(
        _("Sulama Noktası Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Sulama noktası tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Sulama noktası tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Sulama noktası tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Sulama Noktası Tipi")
        verbose_name_plural = _("Sulama Noktası Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."sulama_noktasi_tipleri"'


class KanalBoruTip(models.Model):
    """
    Model representing a pipe type in Turkey.
    """

    ad = models.CharField(
        _("Kanalizasyon Boru Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Kanalizasyon boru tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Kanalizasyon boru tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Kanalizasyon boru tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Kanalizasyon Boru Tipi")
        verbose_name_plural = _("Kanalizasyon Boru Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."kanalizasyon_boru_tipleri"'


class ElektrikKabloTip(models.Model):
    """
    Model representing a cable type in Turkey.
    """

    ad = models.CharField(
        _("Elektrik Kablo Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Elektrik kablo tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Elektrik kablo tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Elektrik kablo tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Elektrik Kablo Tipi")
        verbose_name_plural = _("Elektrik Kablo Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."elektrik_kablo_tipleri"'


class ElektrikHatTip(models.Model):
    """
    Model representing a cable type in Turkey.
    """

    ad = models.CharField(
        _("Elektrik Hat Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Elektrik hat tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Elektrik hat tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Elektrik hat tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Elektrik Hat Tipi")
        verbose_name_plural = _("Elektrik Hat Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."elektrik_hat_tipleri"'


class HabitatTip(models.Model):
    """
    Model representing a habitat type in Turkey.
    """

    ad = models.CharField(
        _("Habitat Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Habitat tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Habitat tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Habitat tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Habitat Tipi")
        verbose_name_plural = _("Habitat Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."habitat_tipleri"'


class ElektrikNoktaTip(models.Model):
    """
    Model representing a point type in Turkey.
    """

    ad = models.CharField(
        _("Elektrik Noktası Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Elektrik noktası tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Elektrik noktası tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Elektrik noktası tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Elektrik Noktası Tipi")
        verbose_name_plural = _("Elektrik Noktası Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."elektrik_noktasi_tipleri"'


class ElektrikBaglantiTip(models.Model):
    """
    Model representing a connection type in Turkey.
    """

    ad = models.CharField(
        _("Elektrik Bağlantı Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Elektrik bağlantı tipi giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Elektrik bağlantı tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Elektrik bağlantı tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Elektrik Bağlantı Tipi")
        verbose_name_plural = _("Elektrik Bağlantı Tipleri")
        ordering = ["ad"]
        db_table = '"parkbahce"."elektrik_baglanti_tipleri"'


class SporAletiGrup(models.Model):
    """
    Model representing a sports equipment group in Turkey.
    """

    ad = models.CharField(
        _("Spor Aleti Grubu"),
        max_length=50,
        unique=True,
        help_text=_("Spor aleti grubunu giriniz."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Spor aleti grubu için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Spor aleti grubu hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = _("Spor Aleti Grubu")
        verbose_name_plural = _("Spor Aleti Grupları")
        ordering = ["ad"]
        db_table = '"parkbahce"."spor_aleti_gruplari"'


class Park(models.Model):
    """
    Model representing a park in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    ad = models.CharField(
        _("Park Adı"), max_length=50, help_text=_("Park adı giriniz.")
    )
    ada = models.ForeignKey(
        Ada,
        on_delete=models.SET_NULL,
        related_name="parklar",
        verbose_name=_("Ada"),
        help_text=_("Parkın bulunduğu ada."),
        blank=True,
        null=True,
    )
    mahalle = models.ForeignKey(
        Mahalle,
        on_delete=models.CASCADE,
        related_name="parklar",
        verbose_name=_("Mahalle"),
        help_text=_("Parkın bulunduğu mahalle."),
    )
    meclis_tarih = models.DateField(
        _("Meclis Tarihi"),
        help_text=_("Parkın meclis karar tarihini giriniz."),
        blank=True,
        null=True,
    )
    meclis_no = models.CharField(
        _("Meclis No"),
        max_length=50,
        help_text=_("Parkın meclis karar numarasını giriniz."),
        blank=True,
        null=True,
    )
    yapim_tarihi = models.DateField(
        _("Yapım Tarihi"),
        help_text=_("Parkın yapım tarihini giriniz."),
        blank=True,
        null=True,
    )
    yapan_firma = models.CharField(
        _("Yapan Firma"),
        max_length=100,
        help_text=_("Parkı yapan firmanın adını giriniz."),
        blank=True,
        null=True,
    )

    ekap_no = models.CharField(
        _("Ekap No"),
        max_length=50,
        help_text=_("Parkın ekap numarasını giriniz."),
        blank=True,
        null=True,
    )

    park_tipi = models.ForeignKey(
        ParkTip,
        on_delete=models.SET_NULL,
        related_name="parklar",
        verbose_name=_("Park Tipi"),
        help_text=_("Park tipi seçiniz."),
        blank=True,
        null=True,
    )
    sulama_tipi = models.ForeignKey(
        SulamaTip,
        on_delete=models.SET_NULL,
        related_name="parklar",
        verbose_name=_("Sulama Tipi"),
        help_text=_("Sulama tipi seçiniz."),
        blank=True,
        null=True,
    )
    sulama_kaynagi = models.ForeignKey(
        SulamaKaynak,
        on_delete=models.SET_NULL,
        related_name="parklar",
        verbose_name=_("Sulama Kaynağı"),
        help_text=_("Sulama kaynağı seçiniz."),
        blank=True,
        null=True,
    )
    geom = models.MultiPolygonField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Park sınırlarını belirten geometri alanı."),
    )
    alan = models.FloatField(
        _("Alan"),
        help_text=_("Park alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )
    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("Park çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Park ile ilgili ekstra verileri JSON formatında giriniz."),
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
        # ad mahalle adı ile birlikte gösterilecek
        return f"{self.ad} - ({self.mahalle.ad})"

    class Meta:
        verbose_name = _("Park")
        verbose_name_plural = _("Parklar")
        ordering = ["mahalle__ilce__il__ad", "mahalle__ilce__ad", "mahalle__ad", "ad"]
        db_table = '"parkbahce"."parklar"'


class ParkAbone(models.Model):
    """
    Model representing a park subscription in Turkey. Su Elektrik Doğalgaz vs.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="aboneler",
        verbose_name=_("Park"),
        help_text=_("Abone olduğu parkı seçiniz."),
    )
    abone_tipi = models.CharField(
        _("Abone Tipi"),
        max_length=50,
        choices=AboneTipChoices.choices,
        help_text=_("Abone tipi seçiniz."),
    )
    abone_no = models.CharField(
        _("Abone No"),
        max_length=50,
        help_text=_("Abone numarasını giriniz."),
    )
    abone_tarihi = models.DateField(
        _("Abone Tarihi"),
        help_text=_("Abone tarihini giriniz."),
        blank=True,
        null=True,
    )
    ilk_endeks = models.FloatField(
        _("İlk Endeks"),
        help_text=_("Abonenin ilk endeks değerini giriniz."),
        blank=True,
        null=True,
        default=0.0,
    )

    geom = models.PointField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Abone noktasını belirten geometri alanı."),
        blank=True,
        null=True,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Abone ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - {self.get_abone_tipi_display()} ({self.abone_no})"

    class Meta:
        verbose_name = _("Park Abone")
        verbose_name_plural = _("Park Aboneleri")
        ordering = ["park__ad", "abone_tipi", "abone_no"]
        db_table = '"parkbahce"."park_aboneleri"'


class AboneEndeks(models.Model):
    """
    Model representing a subscription index in Turkey. Su Elektrik Doğalgaz vs.
    """

    park_abone = models.ForeignKey(
        ParkAbone,
        on_delete=models.CASCADE,
        related_name="endeksler",
        verbose_name=_("Park Abone"),
        help_text=_("Abone olduğu parkı seçiniz."),
    )
    endeks_tarihi = models.DateField(
        _("Endeks Tarihi"),
        help_text=_("Endeks tarihini giriniz."),
        blank=True,
        null=True,
    )
    endeks_degeri = models.FloatField(
        _("Endeks Değeri"),
        help_text=_("Endeks değerini giriniz."),
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
        return f"{self.park_abone.park.ad} - {self.park_abone.abone_tipi} - {self.endeks_degeri}"

    class Meta:
        verbose_name = _("Abone Endeks")
        verbose_name_plural = _("Abone Endeksleri")
        db_table = '"parkbahce"."abone_endeksleri"'


class YesilAlan(models.Model):
    """
    Model representing a green area in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="yesil_alanlar",
        verbose_name=_("Park"),
        help_text=_("Yeşil alanın bulunduğu park."),
    )
    geom = models.MultiPolygonField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Yeşil alan sınırlarını belirten geometri alanı."),
    )
    alan = models.FloatField(
        _("Alan"),
        help_text=_("Yeşil alan alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )
    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("Yeşil alan çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Yeşil alan ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.ad} - ({self.park.ad})"

    class Meta:
        verbose_name = _("Yeşil Alan")
        verbose_name_plural = _("Yeşil Alanlar")
        db_table = '"parkbahce"."yesil_alanlar"'


class SporAlan(models.Model):
    """
    Model representing a sports area in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="spor_alanlar",
        verbose_name=_("Park"),
        help_text=_("Spor alanının bulunduğu park."),
    )
    spor_alan_tipi = models.ForeignKey(
        SporAlanTip,
        on_delete=models.SET_NULL,
        related_name="spor_alanlar",
        verbose_name=_("Spor Alanı Tipi"),
        help_text=_("Spor alanı tipi seçiniz."),
        blank=True,
        null=True,
    )
    spor_aleti_grup = models.ForeignKey(
        SporAletiGrup,
        on_delete=models.SET_NULL,
        related_name="spor_alanlar",
        verbose_name=_("Spor Aleti Grubu"),
        help_text=_("Spor aleti grubunu seçiniz."),
        blank=True,
        null=True,
    )

    spor_alan_kaplama_tipi = models.ForeignKey(
        KaplamaTip,
        on_delete=models.SET_NULL,
        related_name="spor_alanlar",
        verbose_name=_("Kaplama Tipi"),
        help_text=_("Kaplama tipi seçiniz."),
        blank=True,
        null=True,
    )
    geom = models.MultiPolygonField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Spor alanı sınırlarını belirten geometri alanı."),
    )
    alan = models.FloatField(
        _("Alan"),
        help_text=_("Spor alanı alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )
    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("Spor alanı çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Spor alanı ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.spor_alan_tipi.ad} - ({self.park.ad})"

    class Meta:
        verbose_name = _("Spor Alanı")
        verbose_name_plural = _("Spor Alanları")
        db_table = '"parkbahce"."spor_alanlar"'


class OyunAlan(models.Model):
    """
    Model representing a playground in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="oyun_alanlar",
        verbose_name=_("Park"),
        help_text=_("Oyun alanının bulunduğu park."),
    )
    oyun_alan_kaplama_tipi = models.ForeignKey(
        KaplamaTip,
        on_delete=models.SET_NULL,
        related_name="oyun_alanlar",
        verbose_name=_("Kaplama Tipi"),
        help_text=_("Kaplama tipi seçiniz."),
        blank=True,
        null=True,
    )

    geom = models.MultiPolygonField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Oyun alanı sınırlarını belirten geometri alanı."),
    )
    alan = models.FloatField(
        _("Alan"),
        help_text=_("Oyun alanı alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )
    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("Oyun alanı çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Oyun alanı ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.oyun_alan_kaplama_tipi.ad})"

    class Meta:
        verbose_name = _("Oyun Alanı")
        verbose_name_plural = _("Oyun Alanları")
        db_table = '"parkbahce"."oyun_alanlar"'


class ParkBina(models.Model):
    """
    Model representing a building in a park in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    ad = models.CharField(
        _("Bina Adı"),
        max_length=50,
        help_text=_("Bina adını giriniz."),
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="binalar",
        verbose_name=_("Park"),
        help_text=_("Bina'nın bulunduğu park."),
    )
    bina_kullanim_tipi = models.ForeignKey(
        ParkBinaKullanimTip,
        on_delete=models.SET_NULL,
        related_name="binalar",
        verbose_name=_("Bina Kullanım Tipi"),
        help_text=_("Bina kullanım tipi seçiniz."),
        blank=True,
        null=True,
    )
    geom = models.MultiPolygonField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Bina sınırlarını belirten geometri alanı."),
    )
    alan = models.FloatField(
        _("Alan"),
        help_text=_("Bina alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )
    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("Bina çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Bina ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.bina_kullanim_tipi.ad})"

    class Meta:
        verbose_name = _("Bina")
        verbose_name_plural = _("Binalar")
        db_table = '"parkbahce"."binalar"'


class ParkDonati(models.Model):
    """
    Model representing a park furniture in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="donatilar",
        verbose_name=_("Park"),
        help_text=_("Donatının bulunduğu park."),
    )
    donati_tipi = models.ForeignKey(
        DonatiTip,
        on_delete=models.SET_NULL,
        related_name="donatilar",
        verbose_name=_("Donatı Tipi"),
        help_text=_("Donatı tipi seçiniz."),
        blank=True,
        null=True,
    )
    geom = models.PointField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Donatı noktasını belirten geometri alanı."),
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Donatı ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.donati_tipi.ad})"

    class Meta:
        verbose_name = _("Donatı")
        verbose_name_plural = _("Donatılar")
        db_table = '"parkbahce"."donatilar"'


class ParkOyunGrup(models.Model):
    """
    Model representing a playground group in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="oyun_gruplari",
        verbose_name=_("Park"),
        help_text=_("Oyun grubunun bulunduğu park."),
    )
    oyun_grup_tipi = models.ForeignKey(
        OyunGrupTip,
        on_delete=models.SET_NULL,
        related_name="oyun_gruplari",
        verbose_name=_("Oyun Grubu Tipi"),
        help_text=_("Oyun grubu tipi seçiniz."),
        blank=True,
        null=True,
    )

    oyun_grup_model = models.ForeignKey(
        OyunGrupModel,
        on_delete=models.SET_NULL,
        related_name="oyun_alanlar",
        verbose_name=_("Oyun Grubu Modeli"),
        help_text=_("Oyun grubu modeli seçiniz."),
        blank=True,
        null=True,
    )
    ad = models.CharField(
        _("Oyun Grubu Adı"),
        max_length=50,
        help_text=_("Oyun grubunun adını giriniz."),
        blank=True,
        null=True,
    )
    sayi = models.IntegerField(
        _("Oyun Grubu Sayısı"),
        help_text=_("Oyun grubunun sayısını giriniz."),
        blank=True,
        null=True,
    )
    geom = models.PointField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Oyun grubu noktasını belirten geometri alanı."),
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Oyun grubu ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.oyun_grup_tipi.ad})"

    class Meta:
        verbose_name = _("Oyun Grubu")
        verbose_name_plural = _("Oyun Grupları")
        db_table = '"parkbahce"."oyun_gruplari"'


class SulamaHat(models.Model):
    """
    Model representing an irrigation line in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="sulama_hatlari",
        verbose_name=_("Park"),
        help_text=_("Sulama hattının bulunduğu park."),
    )
    sulama_boru_tipi = models.ForeignKey(
        SulamaBoruTip,
        on_delete=models.SET_NULL,
        related_name="sulama_hatlari",
        verbose_name=_("Boru Tipi"),
        help_text=_("Boru tipi seçiniz."),
        blank=True,
        null=True,
    )

    boru_cap = models.FloatField(
        _("Boru Çapı"),
        help_text=_("Boru çapını giriniz."),
        blank=True,
        null=True,
    )

    geom = models.LineStringField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Sulama hattı sınırlarını belirten geometri alanı."),
    )
    uzunluk = models.FloatField(
        _("Uzunluk"),
        help_text=_("Sulama hattının uzunluğunu giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Sulama hattı ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.sulama_boru_tipi.ad})"

    class Meta:
        verbose_name = _("Sulama Hattı")
        verbose_name_plural = _("Sulama Hatları")
        db_table = '"parkbahce"."sulama_hatlari"'


class SulamaNokta(models.Model):
    """
    Model representing an irrigation point in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="sulama_noktalari",
        verbose_name=_("Park"),
        help_text=_("Sulama noktasının bulunduğu park."),
    )
    sulama_nokta_tipi = models.ForeignKey(
        SulamaNoktaTip,
        on_delete=models.SET_NULL,
        related_name="sulama_noktalari",
        verbose_name=_("Sulama Noktası Tipi"),
        help_text=_("Sulama noktası tipi seçiniz."),
        blank=True,
        null=True,
    )
    geom = models.PointField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Sulama noktasını belirten geometri alanı."),
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_(
            "Sulama noktası ile ilgili ekstra verileri JSON formatında giriniz."
        ),
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
        return f"{self.park.ad} - ({self.sulama_nokta_tipi.ad})"

    class Meta:
        verbose_name = _("Sulama Noktası")
        verbose_name_plural = _("Sulama Noktaları")
        db_table = '"parkbahce"."sulama_noktasi"'


class KanalHat(models.Model):
    """
    Model representing a canal line in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="kanal_hatlari",
        verbose_name=_("Park"),
        help_text=_("Kanal hattının bulunduğu park."),
    )
    kanal_boru_tipi = models.ForeignKey(
        KanalBoruTip,
        on_delete=models.SET_NULL,
        related_name="kanal_hatlari",
        verbose_name=_("Boru Tipi"),
        help_text=_("Boru tipi seçiniz."),
        blank=True,
        null=True,
    )
    boru_cap = models.FloatField(
        _("Boru Çapı"),
        help_text=_("Boru çapını giriniz."),
        blank=True,
        null=True,
    )
    geom = models.LineStringField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Kanal hattı sınırlarını belirten geometri alanı."),
    )

    uzunluk = models.FloatField(
        _("Uzunluk"),
        help_text=_("Kanal hattının uzunluğunu giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Kanal hattı ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.kanal_boru_tipi.ad})"

    class Meta:
        verbose_name = _("Kanal Hattı")
        verbose_name_plural = _("Kanal Hatları")
        db_table = '"parkbahce"."kanal_hatlari"'


class ElektrikHat(models.Model):
    """
    Model representing an electricity line in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="elektrik_hatlari",
        verbose_name=_("Park"),
        help_text=_("Elektrik hattının bulunduğu park."),
    )
    elektrik_kablo_tipi = models.ForeignKey(
        ElektrikKabloTip,
        on_delete=models.SET_NULL,
        related_name="elektrik_hatlari",
        verbose_name=_("Kablo Tipi"),
        help_text=_("Kablo tipi seçiniz."),
        blank=True,
        null=True,
    )
    elektrik_hat_tipi = models.ForeignKey(
        ElektrikHatTip,
        on_delete=models.SET_NULL,
        related_name="elektrik_hatlari",
        verbose_name=_("Hat Tipi"),
        help_text=_("Hat tipi seçiniz."),
        blank=True,
        null=True,
    )
    boru_cap = models.FloatField(
        _("Boru Çapı"),
        help_text=_("Boru çapını giriniz."),
        blank=True,
        null=True,
    )
    geom = models.LineStringField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Elektrik hattı sınırlarını belirten geometri alanı."),
    )

    gerilim = models.FloatField(
        _("Gerilim"),
        help_text=_("Elektrik hattının gerilimini giriniz."),
        blank=True,
        null=True,
    )

    uzunluk = models.FloatField(
        _("Uzunluk"),
        help_text=_("Elektrik hattının uzunluğunu giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_(
            "Elektrik hattı ile ilgili ekstra verileri JSON formatında giriniz."
        ),
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
        return f"{self.park.ad} - ({self.elektrik_kablo_tipi.ad})"

    class Meta:
        verbose_name = _("Elektrik Hattı")
        verbose_name_plural = _("Elektrik Hatları")
        db_table = '"parkbahce"."elektrik_hatlari"'


class ParkHavuz(models.Model):
    """

    Model representing a pool in a park in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="havuzlar",
        verbose_name=_("Park"),
        help_text=_("Havuzun bulunduğu park."),
    )
    geom = models.MultiPolygonField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Havuz sınırlarını belirten geometri alanı."),
    )

    alan = models.FloatField(
        _("Alan"),
        help_text=_("Havuz alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    cevre = models.FloatField(
        _("Çevre"),
        help_text=_("Havuz çevresini giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Havuz ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.alan})"

    class Meta:
        verbose_name = _("Havuz")
        verbose_name_plural = _("Havuzlar")
        db_table = '"parkbahce"."havuzlar"'


class Habitat(models.Model):
    """
    Model representing a habitat in Sivas.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="habitatlar",
        verbose_name=_("Park"),
        help_text=_("Habitatın bulunduğu park."),
    )
    habitat_tipi = models.ForeignKey(
        HabitatTip,
        on_delete=models.SET_NULL,
        related_name="habitatlar",
        verbose_name=_("Habitat Tipi"),
        help_text=_("Habitat tipi seçiniz."),
        blank=True,
        null=True,
    )
    ad = models.CharField(
        _("Habitat Adı"),
        max_length=50,
        help_text=_("Habitatın adını giriniz."),
        blank=True,
        null=True,
    )

    dikim_tarihi = models.DateField(
        _("Dikim Tarihi"),
        help_text=_("Habitatın dikim tarihini giriniz."),
        blank=True,
        null=True,
    )

    firma = models.CharField(
        _("Firma"),
        max_length=100,
        help_text=_("Habitatın satın alındığı firmanın adını giriniz."),
        blank=True,
        null=True,
    )

    geom = models.PointField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Habitat noktasını belirten geometri alanı."),
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Habitat ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.habitat_tipi.ad})"

    class Meta:
        verbose_name = _("Habitat")
        verbose_name_plural = _("Habitatlar")
        db_table = '"parkbahce"."habitatlar"'


class ElektrikNokta(models.Model):
    """
    Model representing an electricity point in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="elektrik_noktalar",
        verbose_name=_("Park"),
        help_text=_("Elektrik noktasının bulunduğu park."),
    )
    elektrik_nokta_tipi = models.ForeignKey(
        ElektrikNoktaTip,
        on_delete=models.SET_NULL,
        related_name="elektrik_noktalar",
        verbose_name=_("Elektrik Noktası Tipi"),
        help_text=_("Elektrik noktası tipi seçiniz."),
        blank=True,
        null=True,
    )

    elektrik_baglanti_tipi = models.ForeignKey(
        ElektrikBaglantiTip,
        on_delete=models.SET_NULL,
        related_name="elektrik_noktalar",
        verbose_name=_("Elektrik Bağlantı Tipi"),
        help_text=_("Elektrik bağlantı tipi seçiniz."),
        blank=True,
        null=True,
    )

    sayi = models.IntegerField(
        _("Elektrik Noktası Sayısı"),
        help_text=_("Elektrik noktasının sayısını giriniz."),
        blank=True,
        null=True,
        default=1,
    )

    geom = models.PointField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Elektrik noktasını belirten geometri alanı."),
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_(
            "Elektrik noktası ile ilgili ekstra verileri JSON formatında giriniz."
        ),
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
        return f"{self.park.ad} - ({self.elektrik_nokta_tipi.ad})"

    class Meta:
        verbose_name = _("Elektrik Noktası")
        verbose_name_plural = _("Elektrik Noktaları")
        db_table = '"parkbahce"."elektrik_noktalar"'


class ParkYol(models.Model):
    """
    Model representing a road in a park in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="yollar",
        verbose_name=_("Park"),
        help_text=_("Yolun bulunduğu park."),
    )
    yol_tipi = models.CharField(
        _("Yol Tipi"),
        max_length=50,
        help_text=_("Yol tipini giriniz."),
        blank=True,
        null=True,
    )
    geom = models.MultiPolygonField(
        _("Geometri"),
        srid=settings.SRID,
        help_text=_("Yol sınırlarını belirten geometri alanı."),
    )

    alan = models.FloatField(
        _("Alan"),
        help_text=_("Yol alanını giriniz."),
        blank=True,
        null=True,
        default=0,
    )

    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Yol ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - ({self.yol_tipi})"

    class Meta:
        verbose_name = _("Yol")
        verbose_name_plural = _("Yollar")
        db_table = '"parkbahce"."yollar"'
