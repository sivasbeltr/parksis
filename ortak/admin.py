from django.contrib.gis import admin
from django.utils.translation import gettext_lazy as _

from .models import Ada, Il, Ilce, Mahalle


@admin.register(Il)
class IlAdmin(admin.GISModelAdmin):
    list_display = ("ad", "plaka_kodu", "alan", "cevre")
    search_fields = ("ad", "plaka_kodu")
    readonly_fields = ("uuid", "created_at", "updated_at")
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": 6,
            "default_lon": 35,
            "default_lat": 39,
        },
    }

    fieldsets = (
        (_("Temel Bilgiler"), {"fields": ("ad", "plaka_kodu")}),
        (_("Geometri ve Ölçümler"), {"fields": ("geom", "alan", "cevre")}),
        (_("Ekstra Veri ve Meta"), {"fields": ("extra_data", "osm_id")}),
        (
            _("Tarihçe"),
            {
                "fields": ("uuid", "created_at", "updated_at"),
                "classes": ("collapse",),  # Initially collapsed
            },
        ),
    )


@admin.register(Ilce)
class IlceAdmin(admin.GISModelAdmin):
    list_display = ("ad", "il", "alan", "cevre")
    search_fields = ("ad", "il__ad")
    list_filter = ("il",)
    readonly_fields = ("uuid", "created_at", "updated_at")
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": 8,
        },
    }

    fieldsets = (
        (_("Temel Bilgiler"), {"fields": ("il", "ad")}),
        (_("Geometri ve Ölçümler"), {"fields": ("geom", "alan", "cevre")}),
        (_("Ekstra Veri ve Meta"), {"fields": ("extra_data", "osm_id")}),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Mahalle)
class MahalleAdmin(admin.GISModelAdmin):
    list_display = (
        "ad",
        "ilce",
        "nufus",
        "muhtar",
        "muhtar_telefon",
        "alan",
        "cevre",
    )
    search_fields = ("ad", "ilce__ad", "ilce__il__ad")
    list_filter = ("ilce__il", "ilce")
    readonly_fields = ("uuid", "created_at", "updated_at")
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": 10,
        },
    }

    fieldsets = (
        (_("Temel Bilgiler"), {"fields": ("ilce", "ad", "nufus")}),
        (
            _("Muhtar Bilgileri"),
            {
                "fields": ("muhtar", "muhtar_telefon", "muhtar_email", "muhtar_adres"),
                "classes": ("collapse",),  # Optional: Collapse muhtar info by default
            },
        ),
        (_("Geometri ve Ölçümler"), {"fields": ("geom", "alan", "cevre")}),
        (_("Ekstra Veri ve Meta"), {"fields": ("extra_data", "osm_id")}),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(Ada)
class AdaAdmin(admin.GISModelAdmin):
    list_display = ("ada_no", "pafta_no", "mahalle", "alan")
    search_fields = ("ada_no", "pafta_no", "mahalle__ad", "mahalle__ilce__ad")
    list_filter = ("mahalle__ilce__il", "mahalle__ilce", "mahalle")
    readonly_fields = ("uuid", "created_at", "updated_at")
    gis_widget_kwargs = {
        "attrs": {
            "default_zoom": 12,
        },
    }

    fieldsets = (
        (_("Temel Bilgiler"), {"fields": ("mahalle", "pafta_no", "ada_no")}),
        (_("Geometri ve Ölçümler"), {"fields": ("geom", "alan", "cevre")}),
        (_("Ekstra Veri ve Meta"), {"fields": ("extra_data", "osm_id")}),
        (
            _("Tarihçe"),
            {"fields": ("uuid", "created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
