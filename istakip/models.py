import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from parkbahce.models import Park


class Personel(models.Model):
    """
    Model representing park personnel in Turkey.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="personeller",
        verbose_name=_("Kullanıcı"),
        help_text=_("Personel ile ilişkili kullanıcıyı seçiniz."),
    )
    ad = models.CharField(
        _("Ad Soyad"),
        max_length=100,
        help_text=_("Personelin adını ve soyadını giriniz."),
    )
    telefon = models.CharField(
        _("Telefon"),
        max_length=15,
        help_text=_("Personelin telefon numarasını giriniz."),
        blank=True,
        null=True,
    )
    eposta = models.EmailField(
        _("E-posta"),
        help_text=_("Personelin e-posta adresini giriniz."),
        blank=True,
        null=True,
    )
    pozisyon = models.CharField(
        _("Pozisyon"),
        max_length=50,
        help_text=_("Personelin pozisyonunu giriniz (örn. Park Görevlisi, Yönetici)."),
        blank=True,
        null=True,
    )
    aktif = models.BooleanField(
        _("Aktif"),
        default=True,
        help_text=_("Personelin aktif olup olmadığını belirtir."),
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Oluşturulma Tarihi"), blank=True, null=True
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Güncellenme Tarihi"), blank=True, null=True
    )

    def __str__(self):
        return f"{self.ad} ({self.pozisyon or 'Tanımsız'})"

    class Meta:
        verbose_name = _("Personel")
        verbose_name_plural = _("Personeller")
        db_table = '"parkbahce"."personeller"'
        ordering = ["ad"]


class ParkPersonel(models.Model):
    """
    Many-to-Many relationship between Park and Personel with additional details.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="park_personeller",
        verbose_name=_("Park"),
        help_text=_("Personelin görevli olduğu parkı seçiniz."),
    )
    personel = models.ForeignKey(
        Personel,
        on_delete=models.CASCADE,
        related_name="park_personeller",
        verbose_name=_("Personel"),
        help_text=_("Görevli personeli seçiniz."),
    )
    atama_tarihi = models.DateTimeField(
        _("Atama Tarihi"),
        auto_now_add=True,
        help_text=_("Personelin parka atandığı tarih."),
    )
    gorev_aciklama = models.TextField(
        _("Görev Açıklaması"),
        help_text=_("Personelin parkta üstlendiği görevlerin açıklaması."),
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
        return f"{self.park.ad} - {self.personel.ad}"

    class Meta:
        verbose_name = _("Park Personel")
        verbose_name_plural = _("Park Personeller")
        db_table = '"parkbahce"."park_personeller"'
        unique_together = ["park", "personel"]
        ordering = ["park__ad", "personel__ad"]


class GunlukKontrol(models.Model):
    """
    Model for daily park checks performed by personnel with detailed status tracking.
    """

    class DurumChoices(models.TextChoices):
        SORUN_YOK = "sorun_yok", _("Sorun Yok")
        SORUN_VAR = "sorun_var", _("Sorun Var")
        ACIL = "acil", _("Acil Müdahale Gerekli")
        GOZDEN_GECIRILDI = "gozden_gecirildi", _("Gözden Geçirildi")
        ISE_DONUSTURULDU = "ise_donusturuldu", _("İşe Dönüştürüldü")
        COZULDU = "cozuldu", _("Çözüldü")

    class KontrolTipiChoices(models.TextChoices):
        RUTIN = "rutin", _("Rutin Kontrol")
        OZEL = "ozel", _("Özel Kontrol")
        DENETIM = "denetim", _("Denetim")

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="gunluk_kontroller",
        verbose_name=_("Park"),
        help_text=_("Kontrol yapılan parkı seçiniz."),
    )
    personel = models.ForeignKey(
        Personel,
        on_delete=models.CASCADE,
        related_name="gunluk_kontroller",
        verbose_name=_("Personel"),
        help_text=_("Kontrolü yapan personeli seçiniz."),
    )
    kontrol_tarihi = models.DateTimeField(
        _("Kontrol Tarihi"),
        help_text=_("Kontrol tarihini giriniz."),
        auto_now_add=True,
    )
    kontrol_tipi = models.CharField(
        _("Kontrol Tipi"),
        max_length=20,
        choices=KontrolTipiChoices.choices,
        default=KontrolTipiChoices.RUTIN,
        help_text=_("Kontrol tipini seçiniz."),
    )
    durum = models.CharField(
        _("Durum"),
        max_length=20,
        choices=DurumChoices.choices,
        help_text=_("Parkın durumunu seçiniz."),
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Sorun varsa veya ek bilgi gerekiyorsa açıklamayı giriniz."),
        blank=True,
        null=True,
    )
    geom = models.PointField(
        _("Konum"),
        srid=settings.SRID,
        help_text=_("Kontrolün yapıldığı konum."),
        blank=True,
        null=True,
    )
    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Kontrol ile ilgili ekstra verileri JSON formatında giriniz."),
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
        return f"{self.park.ad} - {self.kontrol_tarihi.strftime('%Y-%m-%d %H:%M')} - {self.get_durum_display()}"

    class Meta:
        verbose_name = _("Günlük Kontrol")
        verbose_name_plural = _("Günlük Kontroller")
        db_table = '"parkbahce"."gunluk_kontroller"'
        ordering = ["-kontrol_tarihi", "park__ad"]
        indexes = [
            models.Index(fields=["park", "kontrol_tarihi"]),
            models.Index(fields=["durum"]),
        ]


class KontrolResim(models.Model):
    """
    Model for images attached to daily checks with issues, limited to 3 per check.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    gunluk_kontrol = models.ForeignKey(
        GunlukKontrol,
        on_delete=models.CASCADE,
        related_name="resimler",
        verbose_name=_("Günlük Kontrol"),
        help_text=_("Resmin bağlı olduğu günlük kontrolü seçiniz."),
    )
    resim = models.ImageField(
        _("Resim"),
        upload_to="kontrol_resimler/%Y/%m/%d/",
        help_text=_("Sorunla ilgili resmi yükleyiniz."),
    )
    aciklama = models.CharField(
        _("Resim Açıklaması"),
        max_length=200,
        help_text=_("Resimle ilgili kısa bir açıklama giriniz."),
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
        return f"{self.gunluk_kontrol.park.ad} - Resim {self.id}"

    class Meta:
        verbose_name = _("Kontrol Resmi")
        verbose_name_plural = _("Kontrol Resimleri")
        db_table = '"parkbahce"."kontrol_resimler"'

    def save(self, *args, **kwargs):
        # Ensure no more than 3 images per GunlukKontrol
        if not self.pk and self.gunluk_kontrol.resimler.count() >= 3:
            raise ValueError(_("Bir günlük kontrol için en fazla 3 resim eklenebilir."))
        super().save(*args, **kwargs)

    def clean(self):
        # Django admin ve form validation için
        from django.core.exceptions import ValidationError

        if self.gunluk_kontrol and self.gunluk_kontrol.durum not in [
            "sorun_var",
            "acil",
        ]:
            raise ValidationError(
                _("Resim sadece sorun var veya acil durumunda eklenebilir.")
            )
        super().clean()

    def save_image(self, image_file):
        """
        Resmi kaydet ve gerekirse boyutunu küçült, UUID isim ver
        """
        import io
        import uuid

        from django.core.files.base import ContentFile
        from PIL import Image

        # UUID ile dosya adı oluştur
        file_extension = image_file.name.split(".")[-1].lower()
        new_filename = f"{uuid.uuid4()}.{file_extension}"

        # Resmi aç
        img = Image.open(image_file)

        # Resim boyutunu kontrol et ve gerekirse küçült
        max_size = (1920, 1080)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Resmi kaydet
        output = io.BytesIO()
        img_format = (
            "JPEG"
            if file_extension.lower() in ["jpg", "jpeg"]
            else file_extension.upper()
        )
        img.save(output, format=img_format, quality=85)
        output.seek(0)

        # Django dosya objesi oluştur
        content_file = ContentFile(output.read(), name=new_filename)
        self.resim.save(new_filename, content_file, save=False)

        return new_filename


class GorevTipi(models.Model):
    """
    Model for types of tasks (e.g., irrigation, mowing, maintenance).
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    ad = models.CharField(
        _("Görev Tipi"),
        max_length=50,
        unique=True,
        help_text=_("Görev tipini giriniz (örn. Sulama, Çim Biçme, Bakım)."),
    )
    deger = models.SlugField(
        _("Değer"),
        max_length=50,
        unique=True,
        help_text=_("Görev tipi için benzersiz bir değer giriniz."),
        blank=True,
        null=True,
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Görev tipi hakkında açıklama giriniz."),
        blank=True,
        null=True,
    )
    varsayilan_sure = models.DurationField(
        _("Varsayılan Süre"),
        help_text=_("Görev tipinin varsayılan tamamlanma süresi (örn. 2 hours)."),
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
        verbose_name = _("Görev Tipi")
        verbose_name_plural = _("Görev Tipleri")
        db_table = '"parkbahce"."gorev_tipleri"'
        ordering = ["ad"]


class Gorev(models.Model):
    """
    Model for tasks/processes related to park operations with detailed scheduling.
    """

    class DurumChoices(models.TextChoices):
        PLANLANMIS = "planlanmis", _("Planlanmış")
        DEVAM_EDIYOR = "devam_ediyor", _("Devam Ediyor")
        ONAYA_GONDERILDI = "onaya_gonderildi", _("Onaya Gönderildi")
        TAMAMLANDI = "tamamlandi", _("Tamamlandı")
        IPTAL = "iptal", _("İptal")
        GECIKMIS = "gecikmis", _("Gecikmiş")

    class OncelikChoices(models.TextChoices):
        DUSUK = "dusuk", _("Düşük")
        NORMAL = "normal", _("Normal")
        YUKSEK = "yuksek", _("Yüksek")
        ACIL = "acil", _("Acil")

    class TekrarlamaChoices(models.TextChoices):
        YOK = "yok", _("Tekrar Yok")
        GUNLUK = "gunluk", _("Günlük")
        HAFTALIK = "haftalik", _("Haftalık")
        AYLIK = "aylik", _("Aylık")
        YILLIK = "yillik", _("Yıllık")

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    park = models.ForeignKey(
        Park,
        on_delete=models.CASCADE,
        related_name="gorevler",
        verbose_name=_("Park"),
        help_text=_("Görevin yapılacağı parkı seçiniz."),
    )
    gorev_tipi = models.ForeignKey(
        GorevTipi,
        on_delete=models.SET_NULL,
        related_name="gorevler",
        verbose_name=_("Görev Tipi"),
        help_text=_("Görev tipini seçiniz."),
        blank=True,
        null=True,
    )
    baslik = models.CharField(
        _("Başlık"),
        max_length=100,
        help_text=_("Görevin başlığını giriniz."),
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Görev hakkında detaylı açıklama giriniz."),
        blank=True,
        null=True,
    )
    baslangic_tarihi = models.DateTimeField(
        _("Başlangıç Tarihi"),
        help_text=_("Görevin başlangıç tarihini giriniz."),
        blank=True,
        null=True,
    )
    bitis_tarihi = models.DateTimeField(
        _("Bitiş Tarihi"),
        help_text=_("Görevin bitiş tarihini giriniz."),
        blank=True,
        null=True,
    )
    durum = models.CharField(
        _("Durum"),
        max_length=20,
        choices=DurumChoices.choices,
        default=DurumChoices.PLANLANMIS,
        help_text=_("Görevin durumunu seçiniz."),
    )
    oncelik = models.CharField(
        _("Öncelik"),
        max_length=20,
        choices=OncelikChoices.choices,
        default=OncelikChoices.NORMAL,
        help_text=_("Görevin öncelik seviyesini seçiniz."),
    )
    tekrar_tipi = models.CharField(
        _("Tekrarlama Tipi"),
        max_length=20,
        choices=TekrarlamaChoices.choices,
        default=TekrarlamaChoices.YOK,
        help_text=_("Görevin tekrarlanma sıklığını seçiniz."),
    )
    tekrar_son_tarihi = models.DateTimeField(
        _("Tekrar Son Tarihi"),
        help_text=_("Tekrarlayan görevlerin biteceği tarih."),
        blank=True,
        null=True,
    )
    tamamlanma_tarihi = models.DateTimeField(
        _("Tamamlanma Tarihi"),
        help_text=_("Görevin tamamlanma tarihini giriniz."),
        blank=True,
        null=True,
    )
    atanan_personeller = models.ManyToManyField(
        Personel,
        through="GorevAtama",
        related_name="atanan_gorevler",
        verbose_name=_("Atanan Personeller"),
        help_text=_("Göreve atanan personelleri seçiniz."),
    )
    olusturan = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="olusturulan_gorevler",
        verbose_name=_("Oluşturan"),
        help_text=_("Görevi oluşturan kullanıcıyı seçiniz."),
        blank=True,
        null=True,
    )
    gunluk_kontrol = models.ForeignKey(
        GunlukKontrol,
        on_delete=models.SET_NULL,
        related_name="ilgili_gorevler",
        verbose_name=_("İlgili Günlük Kontrol"),
        help_text=_("Görevle ilişkili günlük kontrolü seçiniz."),
        blank=True,
        null=True,
    )
    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_("Görev ile ilgili ekstra verileri JSON formatında giriniz."),
        blank=True,
        null=True,
    )

    onay_tarihi = models.DateTimeField(
        _("Onay Tarihi"),
        help_text=_("Görevin onaylandığı tarihi giriniz."),
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
        return f"{self.park.ad} - {self.baslik} ({self.get_durum_display()})"

    class Meta:
        verbose_name = _("Görev")
        verbose_name_plural = _("Görevler")
        db_table = '"parkbahce"."gorevler"'
        ordering = ["-baslangic_tarihi", "park__ad"]
        indexes = [
            models.Index(fields=["park", "durum"]),
            models.Index(fields=["gorev_tipi", "oncelik"]),
        ]


class GorevAtama(models.Model):
    """
    Through model for Gorev-Personel many-to-many relationship with additional details.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    gorev = models.ForeignKey(
        Gorev,
        on_delete=models.CASCADE,
        related_name="atamalar",
        verbose_name=_("Görev"),
        help_text=_("Personelin atandığı görevi seçiniz."),
    )
    personel = models.ForeignKey(
        Personel,
        on_delete=models.CASCADE,
        related_name="atamalar",
        verbose_name=_("Personel"),
        help_text=_("Göreve atanan personeli seçiniz."),
    )
    atama_tarihi = models.DateTimeField(
        _("Atama Tarihi"),
        auto_now_add=True,
        help_text=_("Personelin göreve atandığı tarih."),
    )
    gorev_rolu = models.CharField(
        _("Görev Rolü"),
        max_length=50,
        help_text=_("Personelin görevdeki rolünü giriniz (örn. Yürütücü, Denetçi)."),
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
        return f"{self.gorev.baslik} - {self.personel.ad}"

    class Meta:
        verbose_name = _("Görev Atama")
        verbose_name_plural = _("Görev Atamaları")
        db_table = '"parkbahce"."gorev_atamalar"'
        unique_together = ["gorev", "personel"]
        ordering = ["gorev__baslik", "personel__ad"]


class GorevAsama(models.Model):
    """
    Model for tracking task process stages with detailed status updates.
    """

    class DurumChoices(models.TextChoices):
        BEKLEMEDE = "beklemede", _("Beklemede")
        BASLAMADI = "baslamadi", _("Başlamadı")
        DEVAM_EDIYOR = "devam_ediyor", _("Devam Ediyor")
        TAMAMLANDI = "tamamlandi", _("Tamamlandı")

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    gorev = models.ForeignKey(
        Gorev,
        on_delete=models.CASCADE,
        related_name="asamalar",
        verbose_name=_("Görev"),
        help_text=_("Aşamanın bağlı olduğu görevi seçiniz."),
    )
    ad = models.CharField(
        _("Aşama Adı"),
        max_length=50,
        help_text=_("Aşama adını giriniz (örn. Hazırlık, Uygulama, Kontrol)."),
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("Aşama hakkında detaylı açıklama giriniz."),
        blank=True,
        null=True,
    )
    durum = models.CharField(
        _("Durum"),
        max_length=20,
        choices=DurumChoices.choices,
        default=DurumChoices.BASLAMADI,
        help_text=_("Aşamanın durumunu seçiniz."),
    )
    baslangic_tarihi = models.DateTimeField(
        _("Başlangıç Tarihi"),
        help_text=_("Aşamanın başlangıç tarihini giriniz."),
        blank=True,
        null=True,
    )
    tamamlanma_tarihi = models.DateTimeField(
        _("Tamamlanma Tarihi"),
        help_text=_("Aşamanın tamamlanma tarihini giriniz."),
        blank=True,
        null=True,
    )
    sorumlu = models.ForeignKey(
        Personel,
        on_delete=models.SET_NULL,
        related_name="sorumlu_asamalar",
        verbose_name=_("Sorumlu Personel"),
        help_text=_("Aşamadan sorumlu personeli seçiniz."),
        blank=True,
        null=True,
    )
    resim = models.ImageField(
        _("Aşama Resmi"),
        upload_to="asama_resimler/%Y/%m/%d/",
        help_text=_("Aşama ilerlemesi ile ilgili resmi yükleyiniz."),
        blank=True,
        null=True,
    )
    konum = models.PointField(
        _("Resim Konumu"),
        srid=settings.SRID,
        help_text=_("Resmin çekildiği konum."),
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
        return f"{self.gorev.baslik} - {self.ad} ({self.get_durum_display()})"

    class Meta:
        verbose_name = _("Görev Aşaması")
        verbose_name_plural = _("Görev Aşamaları")
        db_table = '"parkbahce"."gorev_asamalari"'
        ordering = ["gorev__baslik", "created_at"]


class GorevDenetimKaydi(models.Model):
    """
    Model for audit logs to track changes and actions on tasks.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    gorev = models.ForeignKey(
        Gorev,
        on_delete=models.CASCADE,
        related_name="denetim_kayitlari",
        verbose_name=_("Görev"),
        help_text=_("Denetim kaydının bağlı olduğu görevi seçiniz."),
    )
    islem_tipi = models.CharField(
        _("İşlem Tipi"),
        max_length=50,
        help_text=_(
            "Yapılan işlemin tipini giriniz (örn. Oluşturma, Güncelleme, Durum Değişikliği)."
        ),
    )
    aciklama = models.TextField(
        _("Açıklama"),
        help_text=_("İşlem hakkında detaylı açıklama giriniz."),
        blank=True,
        null=True,
    )
    yapan = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="gorev_denetim_kayitlari",
        verbose_name=_("Yapan"),
        help_text=_("İşlemi yapan kullanıcıyı seçiniz."),
        blank=True,
        null=True,
    )
    islem_tarihi = models.DateTimeField(
        _("İşlem Tarihi"),
        auto_now_add=True,
        help_text=_("İşlemin yapıldığı tarih."),
    )
    extra_data = models.JSONField(
        _("Ekstra Veri"),
        help_text=_(
            "Denetim kaydı ile ilgili ekstra verileri JSON formatında giriniz."
        ),
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
        return f"{self.gorev.baslik} - {self.islem_tipi} ({self.islem_tarihi.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = _("Görev Denetim Kaydı")
        verbose_name_plural = _("Görev Denetim Kayıtları")
        db_table = '"parkbahce"."gorev_denetim_kayitlari"'
        ordering = ["-islem_tarihi"]


class GorevTamamlamaResim(models.Model):
    """
    Model for images attached when completing tasks, with UUID naming and size optimization.
    """

    uuid = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, blank=True, null=True
    )
    gorev = models.ForeignKey(
        Gorev,
        on_delete=models.CASCADE,
        related_name="tamamlama_resimleri",
        verbose_name=_("Görev"),
        help_text=_("Tamamlanan görevi seçiniz."),
    )
    resim = models.ImageField(
        _("Tamamlama Resmi"),
        upload_to="gorev_tamamlama_resimler/%Y/%m/%d/",
        help_text=_("Görev tamamlandığında çekilen resmi yükleyiniz."),
    )
    aciklama = models.CharField(
        _("Resim Açıklaması"),
        max_length=200,
        help_text=_("Tamamlama resmi ile ilgili açıklama giriniz."),
        blank=True,
        null=True,
    )
    konum = models.PointField(
        _("Resim Konumu"),
        srid=settings.SRID,
        help_text=_("Resmin çekildiği konum."),
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
        return f"{self.gorev.baslik} - Tamamlama Resmi {self.id}"

    class Meta:
        verbose_name = _("Görev Tamamlama Resmi")
        verbose_name_plural = _("Görev Tamamlama Resimleri")
        db_table = '"parkbahce"."gorev_tamamlama_resimleri"'
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Limit to 3 images per task completion
        if self.gorev.tamamlama_resimleri.count() >= 3 and not self.pk:
            raise ValueError(
                _("Bir görev için en fazla 3 tamamlama resmi eklenebilir.")
            )
        super().save(*args, **kwargs)

    def save_image(self, image_file):
        """
        Resmi kaydet ve gerekirse boyutunu küçült, UUID isim ver
        """
        import io
        import uuid

        from django.core.files.base import ContentFile
        from PIL import Image

        # UUID ile dosya adı oluştur
        file_extension = image_file.name.split(".")[-1].lower()
        new_filename = f"{uuid.uuid4()}.{file_extension}"

        # Resmi aç
        img = Image.open(image_file)

        # Resim boyutunu kontrol et ve gerekirse küçült
        max_size = (1920, 1080)
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Resmi kaydet
        output = io.BytesIO()
        img_format = (
            "JPEG"
            if file_extension.lower() in ["jpg", "jpeg"]
            else file_extension.upper()
        )
        img.save(output, format=img_format, quality=85)
        output.seek(0)

        # Django dosya objesi oluştur
        content_file = ContentFile(output.read(), name=new_filename)
        self.resim.save(new_filename, content_file, save=False)

        return new_filename
