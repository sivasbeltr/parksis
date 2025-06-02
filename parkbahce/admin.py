from django.conf import settings
from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from .models import (  # Add other models if needed; Tip models
    AboneEndeks,
    AboneTipChoices,
    DonatiTip,
    ElektrikBaglantiTip,
    ElektrikHat,
    ElektrikHatTip,
    ElektrikKabloTip,
    ElektrikNokta,
    ElektrikNoktaTip,
    Habitat,
    HabitatTip,
    KanalBoruTip,
    KanalHat,
    KaplamaTip,
    OyunAlan,
    OyunGrupModel,
    OyunGrupTip,
    Park,
    ParkAbone,
    ParkBina,
    ParkBinaKullanimTip,
    ParkDonati,
    ParkHavuz,
    ParkOyunGrup,
    ParkTip,
    ParkYol,
    SporAlan,
    SporAlanTip,
    SporAletiGrup,
    SulamaBoruTip,
    SulamaHat,
    SulamaKaynak,
    SulamaNokta,
    SulamaNoktaTip,
    SulamaTip,
    YesilAlan,
)

# Register simple type models first (using standard ModelAdmin)


@admin.register(OyunGrupModel)
class OyunGrupModelAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(SporAletiGrup)
class SporAletiGrupAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(SulamaTip)
class SulamaTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(SulamaKaynak)
class SulamaKaynakAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(ParkTip)
class ParkTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(KaplamaTip)
class KaplamaTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(SporAlanTip)
class SporAlanTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(ParkBinaKullanimTip)
class ParkBinaKullanimTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(DonatiTip)
class DonatiTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(OyunGrupTip)
class OyunGrupTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(ElektrikBaglantiTip)
class ElektrikBaglantiTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(ElektrikHatTip)
class ElektrikHatTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(ElektrikKabloTip)
class ElektrikKabloTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(ElektrikNoktaTip)
class ElektrikNoktaTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(HabitatTip)
class HabitatTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(KanalBoruTip)
class KanalBoruTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(SulamaBoruTip)
class SulamaBoruTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


@admin.register(SulamaNoktaTip)
class SulamaNoktaTipAdmin(admin.ModelAdmin):
    list_display = ("ad", "deger", "aciklama")
    search_fields = ("ad", "deger")
    prepopulated_fields = {"deger": ("ad",)}


# Register main models with GIS support
@admin.register(Park)
class ParkAdmin(admin.GISModelAdmin):
    list_display = ("ad", "mahalle", "park_tipi", "alan", "yapim_tarihi")
    search_fields = ("ad", "mahalle__ad", "ada__ada_no")
    list_filter = (
        "mahalle__ilce",
        "mahalle",
        "park_tipi",
        "sulama_tipi",
        "sulama_kaynagi",
    )
    readonly_fields = ("uuid", "created_at", "updated_at", "alan", "cevre")
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (_("Temel Bilgiler"), {"fields": ("ad", "mahalle", "ada", "park_tipi")}),
        (
            _("Detaylar"),
            {
                "fields": (
                    "meclis_tarih",
                    "meclis_no",
                    "yapim_tarihi",
                    "yapan_firma",
                    "ekap_no",
                )
            },
        ),
        (_("Sulama Bilgileri"), {"fields": ("sulama_tipi", "sulama_kaynagi")}),
        (_("Geometri ve Alan"), {"fields": ("geom", "alan", "cevre")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ParkAbone)
class ParkAboneAdmin(admin.GISModelAdmin):
    list_display = ("park", "abone_tipi", "abone_no", "abone_tarihi")
    search_fields = ("park__ad", "abone_no")
    list_filter = ("abone_tipi", "park__mahalle")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "abone_tipi", "abone_no", "abone_tarihi", "geom")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(AboneEndeks)
class AboneEndeksAdmin(admin.ModelAdmin):
    list_display = ("park_abone", "endeks_tarihi", "endeks_degeri")
    search_fields = ("park_abone__park__ad", "park_abone__abone_no")
    list_filter = ("park_abone__abone_tipi", "endeks_tarihi")
    readonly_fields = ("created_at", "updated_at")
    raw_id_fields = ("park_abone",)


@admin.register(YesilAlan)
class YesilAlanAdmin(admin.GISModelAdmin):
    list_display = ("park", "alan", "cevre")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle",)
    readonly_fields = ("uuid", "created_at", "updated_at", "alan", "cevre")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "geom", "alan", "cevre")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(SporAlan)
class SporAlanAdmin(admin.GISModelAdmin):
    list_display = ("park", "spor_alan_tipi", "spor_alan_kaplama_tipi", "alan")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle", "spor_alan_tipi", "spor_alan_kaplama_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at", "alan", "cevre")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "park",
                    "spor_alan_tipi",
                    "spor_alan_kaplama_tipi",
                    "geom",
                    "alan",
                    "cevre",
                )
            },
        ),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(OyunAlan)
class OyunAlanAdmin(admin.GISModelAdmin):
    list_display = ("park", "oyun_alan_kaplama_tipi", "alan")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle", "oyun_alan_kaplama_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at", "alan", "cevre")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "oyun_alan_kaplama_tipi", "geom", "alan", "cevre")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ParkBina)
class ParkBinaAdmin(admin.GISModelAdmin):
    list_display = ("ad", "park", "bina_kullanim_tipi", "alan")
    search_fields = ("ad", "park__ad")
    list_filter = ("park__mahalle", "bina_kullanim_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at", "alan", "cevre")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (
            None,
            {"fields": ("ad", "park", "bina_kullanim_tipi", "geom", "alan", "cevre")},
        ),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ParkDonati)
class ParkDonatiAdmin(admin.GISModelAdmin):
    list_display = ("park", "donati_tipi")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle", "donati_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "donati_tipi", "geom")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ParkOyunGrup)
class ParkOyunGrupAdmin(admin.GISModelAdmin):
    list_display = ("ad", "park", "oyun_grup_tipi", "sayi")
    search_fields = ("ad", "park__ad")
    list_filter = ("park__mahalle", "oyun_grup_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("ad", "park", "oyun_grup_tipi", "sayi", "geom")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(SulamaHat)
class SulamaHatAdmin(admin.GISModelAdmin):
    list_display = ("park", "sulama_boru_tipi", "boru_cap", "uzunluk")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle", "sulama_boru_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at", "uzunluk")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "sulama_boru_tipi", "boru_cap", "geom", "uzunluk")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(SulamaNokta)
class SulamaNoktaAdmin(admin.GISModelAdmin):
    list_display = ("park", "sulama_nokta_tipi")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle", "sulama_nokta_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "sulama_nokta_tipi", "geom")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(KanalHat)
class KanalHatAdmin(admin.GISModelAdmin):
    list_display = ("park", "kanal_boru_tipi", "boru_cap", "uzunluk")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle", "kanal_boru_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at", "uzunluk")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "kanal_boru_tipi", "boru_cap", "geom", "uzunluk")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ElektrikHat)
class ElektrikHatAdmin(admin.GISModelAdmin):
    list_display = ("park", "elektrik_kablo_tipi", "elektrik_hat_tipi", "uzunluk")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle", "elektrik_kablo_tipi", "elektrik_hat_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at", "uzunluk")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "park",
                    "elektrik_kablo_tipi",
                    "elektrik_hat_tipi",
                    "boru_cap",
                    "geom",
                    "gerilim",
                    "uzunluk",
                )
            },
        ),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Habitat)
class HabitatAdmin(admin.GISModelAdmin):
    list_display = ("ad", "park", "habitat_tipi", "dikim_tarihi")
    search_fields = ("ad", "park__ad")
    list_filter = ("park__mahalle", "habitat_tipi", "dikim_tarihi")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (
            None,
            {"fields": ("ad", "park", "habitat_tipi", "dikim_tarihi", "firma", "geom")},
        ),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ElektrikNokta)
class ElektrikNoktaAdmin(admin.GISModelAdmin):
    list_display = ("park", "elektrik_nokta_tipi", "elektrik_baglanti_tipi")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle", "elektrik_nokta_tipi", "elektrik_baglanti_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "park",
                    "elektrik_nokta_tipi",
                    "elektrik_baglanti_tipi",
                    "geom",
                )
            },
        ),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ParkHavuz)
class ParkHavuzAdmin(admin.GISModelAdmin):
    list_display = ("park", "alan", "cevre")
    search_fields = ("park__ad",)
    list_filter = ("park__mahalle",)
    readonly_fields = ("uuid", "created_at", "updated_at", "alan", "cevre")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "geom", "alan", "cevre")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(ParkYol)
class ParkYolAdmin(admin.GISModelAdmin):
    list_display = ("park", "yol_tipi", "alan")
    search_fields = ("park__ad", "yol_tipi")
    list_filter = ("park__mahalle", "yol_tipi")
    readonly_fields = ("uuid", "created_at", "updated_at", "alan")
    raw_id_fields = ("park",)
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": settings.DEFAULT_MAP_ZOOM,
            "default_lat": settings.DEFAULT_MAP_LATITUDE,
            "default_lon": settings.DEFAULT_MAP_LONGITUDE,
        },
    }
    fieldsets = (
        (None, {"fields": ("park", "yol_tipi", "geom", "alan")}),
        (
            _("Ekstra Veri ve Meta"),
            {"fields": ("extra_data", "osm_id"), "classes": ("collapse",)},
        ),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
