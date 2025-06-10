from django.conf import settings
from django.contrib import admin
from django.contrib.gis import admin as gis_admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    Gorev,
    GorevAsama,
    GorevAtama,
    GorevDenetimKaydi,
    GorevTamamlamaResim,
    GorevTipi,
    GunlukKontrol,
    KontrolResim,
    ParkPersonel,
    Personel,
)


# Inline admin classes
class ParkPersonelInline(admin.TabularInline):
    model = ParkPersonel
    extra = 1
    readonly_fields = ("uuid", "atama_tarihi", "created_at", "updated_at")
    fields = ("park", "gorev_aciklama", "atama_tarihi")


class KontrolResimInline(admin.TabularInline):
    model = KontrolResim
    extra = 0
    max_num = 3
    readonly_fields = ("uuid", "created_at", "updated_at", "resim_preview")
    fields = ("resim", "resim_preview", "aciklama")

    def resim_preview(self, obj):
        if obj.resim:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.resim.url,
            )
        return "-"

    resim_preview.short_description = _("Resim Önizleme")


class GorevAtamaInline(admin.TabularInline):
    model = GorevAtama
    extra = 1
    readonly_fields = ("uuid", "atama_tarihi", "created_at", "updated_at")
    fields = ("personel", "gorev_rolu", "atama_tarihi")


class GorevAsamaInline(admin.StackedInline):
    model = GorevAsama
    extra = 0
    readonly_fields = ("uuid", "created_at", "updated_at")
    fields = (
        ("ad", "durum"),
        ("baslangic_tarihi", "tamamlanma_tarihi"),
        "sorumlu",
        "aciklama",
    )


class GorevTamamlamaResimInline(admin.TabularInline):
    model = GorevTamamlamaResim
    extra = 0
    max_num = 3
    readonly_fields = ("uuid", "created_at", "updated_at", "resim_preview")
    fields = ("resim", "resim_preview", "aciklama", "konum")

    def resim_preview(self, obj):
        if obj.resim:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.resim.url,
            )
        return "-"

    resim_preview.short_description = _("Resim Önizleme")


# Main admin classes
@admin.register(Personel)
class PersonelAdmin(admin.ModelAdmin):
    list_display = ("ad", "pozisyon", "telefon", "eposta", "aktif", "created_at")
    list_filter = ("aktif", "pozisyon", "created_at")
    search_fields = ("ad", "telefon", "eposta", "user__username")
    readonly_fields = ("uuid", "created_at", "updated_at")
    inlines = [ParkPersonelInline]

    fieldsets = (
        (_("Temel Bilgiler"), {"fields": ("user", "ad", "pozisyon", "aktif")}),
        (_("İletişim Bilgileri"), {"fields": ("telefon", "eposta")}),
        (
            _("Sistem Bilgileri"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ParkPersonel)
class ParkPersonelAdmin(admin.ModelAdmin):
    list_display = ("park", "personel", "atama_tarihi")
    list_filter = ("atama_tarihi", "park__mahalle")
    search_fields = ("park__ad", "personel__ad")
    readonly_fields = ("uuid", "atama_tarihi", "created_at", "updated_at")
    raw_id_fields = ("park", "personel")


@admin.register(GunlukKontrol)
class GunlukKontrolAdmin(gis_admin.GISModelAdmin):
    list_display = (
        "park",
        "personel",
        "kontrol_tarihi",
        "kontrol_tipi",
        "durum",
        "resim_sayisi",
    )
    list_filter = ("durum", "kontrol_tipi", "kontrol_tarihi", "park__mahalle")
    search_fields = ("park__ad", "personel__ad", "aciklama")
    readonly_fields = ("uuid", "kontrol_tarihi", "created_at", "updated_at")
    raw_id_fields = ("park", "personel")
    inlines = [KontrolResimInline]

    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }

    fieldsets = (
        (
            _("Kontrol Bilgileri"),
            {"fields": ("park", "personel", "kontrol_tipi", "durum")},
        ),
        (_("Detaylar"), {"fields": ("aciklama", "geom")}),
        (
            _("Sistem Bilgileri"),
            {
                "fields": (
                    "uuid",
                    "kontrol_tarihi",
                    "created_at",
                    "updated_at",
                    "extra_data",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def resim_sayisi(self, obj):
        return obj.resimler.count()

    resim_sayisi.short_description = _("Resim Sayısı")


@admin.register(KontrolResim)
class KontrolResimAdmin(admin.ModelAdmin):
    list_display = ("gunluk_kontrol", "resim_preview", "aciklama", "created_at")
    list_filter = ("created_at", "gunluk_kontrol__durum")
    search_fields = ("gunluk_kontrol__park__ad", "aciklama")
    readonly_fields = ("uuid", "created_at", "updated_at", "resim_preview")
    raw_id_fields = ("gunluk_kontrol",)

    def resim_preview(self, obj):
        if obj.resim:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.resim.url,
            )
        return "-"

    resim_preview.short_description = _("Resim Önizleme")


@admin.register(GorevTipi)
class GorevTipiAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "varsayilan_sure", "created_at")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}
    readonly_fields = ("uuid", "created_at", "updated_at")

    fieldsets = (
        (_("Temel Bilgiler"), {"fields": ("ad", "deger", "varsayilan_sure")}),
        (_("Açıklama"), {"fields": ("aciklama",)}),
        (
            _("Sistem Bilgileri"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Gorev)
class GorevAdmin(admin.ModelAdmin):
    list_display = (
        "baslik",
        "park",
        "gorev_tipi",
        "durum",
        "oncelik",
        "baslangic_tarihi",
        "atanan_personel_sayisi",
    )
    list_filter = (
        "durum",
        "oncelik",
        "gorev_tipi",
        "tekrar_tipi",
        "baslangic_tarihi",
        "park__mahalle",
    )
    search_fields = ("baslik", "park__ad", "aciklama")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("park", "gorev_tipi", "olusturan", "gunluk_kontrol")
    inlines = [GorevAtamaInline, GorevAsamaInline, GorevTamamlamaResimInline]
    date_hierarchy = "baslangic_tarihi"

    fieldsets = (
        (
            _("Temel Bilgiler"),
            {"fields": ("baslik", "park", "gorev_tipi", "gunluk_kontrol")},
        ),
        (_("Durum ve Öncelik"), {"fields": ("durum", "oncelik")}),
        (_("Tarih Bilgileri"), {"fields": ("baslangic_tarihi", "bitis_tarihi")}),
        (_("Tekrarlama"), {"fields": ("tekrar_tipi", "tekrar_son_tarihi")}),
        (_("Detaylar"), {"fields": ("aciklama",)}),
        (
            _("Sistem Bilgileri"),
            {
                "fields": (
                    "uuid",
                    "olusturan",
                    "created_at",
                    "updated_at",
                    "extra_data",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def atanan_personel_sayisi(self, obj):
        return obj.atamalar.count()

    atanan_personel_sayisi.short_description = _("Atanan Personel")


@admin.register(GorevAtama)
class GorevAtamaAdmin(admin.ModelAdmin):
    list_display = ("gorev", "personel", "gorev_rolu", "atama_tarihi")
    list_filter = ("atama_tarihi", "gorev_rolu")
    search_fields = ("gorev__baslik", "personel__ad", "gorev_rolu")
    readonly_fields = ("uuid", "atama_tarihi", "created_at", "updated_at")
    raw_id_fields = ("gorev", "personel")


@admin.register(GorevAsama)
class GorevAsamaAdmin(admin.ModelAdmin):
    list_display = (
        "gorev",
        "ad",
        "durum",
        "sorumlu",
        "baslangic_tarihi",
        "tamamlanma_tarihi",
    )
    list_filter = ("durum", "baslangic_tarihi", "tamamlanma_tarihi")
    search_fields = ("gorev__baslik", "ad", "aciklama")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("gorev", "sorumlu")


@admin.register(GorevDenetimKaydi)
class GorevDenetimKaydiAdmin(admin.ModelAdmin):
    list_display = ("gorev", "islem_tipi", "yapan", "islem_tarihi")
    list_filter = ("islem_tipi", "islem_tarihi")
    search_fields = ("gorev__baslik", "islem_tipi", "aciklama")
    readonly_fields = ("uuid", "islem_tarihi", "created_at", "updated_at")
    raw_id_fields = ("gorev", "yapan")
    date_hierarchy = "islem_tarihi"


@admin.register(GorevTamamlamaResim)
class GorevTamamlamaResimAdmin(gis_admin.GISModelAdmin):
    list_display = ("gorev", "resim_preview", "aciklama", "created_at")
    list_filter = ("created_at", "gorev__durum")
    search_fields = ("gorev__baslik", "aciklama")
    readonly_fields = ("uuid", "created_at", "updated_at", "resim_preview")
    raw_id_fields = ("gorev",)

    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }

    def resim_preview(self, obj):
        if obj.resim:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.resim.url,
            )
        return "-"

    resim_preview.short_description = _("Resim Önizleme")


# Custom admin site configurations
admin.site.site_header = _("Park ve Bahçeler İş Takip Sistemi")
admin.site.site_title = _("İş Takip Sistemi")
admin.site.index_title = _("İş Takip Yönetimi")
