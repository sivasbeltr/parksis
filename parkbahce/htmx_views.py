import json
from datetime import timedelta

from django.db.models import Count, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (
    ElektrikHat,
    Habitat,
    KanalHat,
    Park,
    ParkBina,
    ParkDonati,
    ParkOyunGrup,
    SporAlan,
    SulamaHat,
    SulamaNokta,
    YesilAlan,
)


def recent_parks_htmx(request):
    """Son eklenen parklar bileşeni"""
    if request.htmx:
        recent_parks = Park.objects.select_related("mahalle", "park_tipi").order_by(
            "-created_at"
        )[:5]
        return render(
            request,
            "dashboard/partials/recent_parks.html",
            {"recent_parks": recent_parks},
        )
    return render(request, "dashboard/partials/loading_error.html")


def quick_actions_htmx(request):
    """Hızlı işlemler bileşeni"""
    if request.htmx:
        return render(request, "dashboard/partials/quick_actions.html")
    return render(request, "dashboard/partials/loading_error.html")


def park_types_distribution_htmx(request):
    """Park tipi dağılımı bileşeni"""
    if request.htmx:
        park_types_distribution = (
            Park.objects.values("park_tipi__ad")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        context = {"park_types_distribution": park_types_distribution}
        return render(
            request, "dashboard/partials/park_types_distribution.html", context
        )
    return render(request, "dashboard/partials/loading_error.html")


def neighborhood_distribution_htmx(request):
    """Mahalle dağılımı bileşeni"""
    if request.htmx:
        neighborhood_distribution = (
            Park.objects.values("mahalle__ad", "mahalle__ilce__ad")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )
        context = {"neighborhood_distribution": neighborhood_distribution}
        return render(
            request, "dashboard/partials/neighborhood_distribution.html", context
        )
    return render(request, "dashboard/partials/loading_error.html")


def infrastructure_status_htmx(request):
    """Altyapı durumu bileşeni"""
    if request.htmx:
        # Altyapı istatistikleri
        total_irrigation_points = SulamaNokta.objects.count()
        total_irrigation_lines = SulamaHat.objects.count()
        total_electric_lines = ElektrikHat.objects.count()
        total_canal_lines = KanalHat.objects.count()

        # Elektrik noktaları (model varsa)
        try:
            from .models import ElektrikNokta

            total_electric_points = ElektrikNokta.objects.count()
        except ImportError:
            total_electric_points = 0

        context = {
            "total_irrigation_points": total_irrigation_points,
            "total_electric_points": total_electric_points,
            "total_irrigation_lines": total_irrigation_lines,
            "total_electric_lines": total_electric_lines,
            "total_canal_lines": total_canal_lines,
        }
        return render(request, "dashboard/partials/infrastructure_status.html", context)
    return render(request, "dashboard/partials/loading_error.html")


@require_http_methods(["GET"])
def park_detail_htmx(request, park_uuid):
    """Park detay bilgilerini HTMX ile getir"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(
        Park.objects.select_related(
            "mahalle",
            "mahalle__ilce",
            "mahalle__ilce__il",
            "park_tipi",
            "sulama_tipi",
            "sulama_kaynagi",
            "ada",
        ).prefetch_related(
            "yesil_alanlar",
            "spor_alanlar",
            "donatilar",
            "oyun_gruplari",
            "sulama_noktalari",
            "elektrik_noktalar",
            "habitatlar",
            "binalar",
        ),
        uuid=park_uuid,
    )

    # Park istatistikleri
    park_stats = {
        "habitatlar_sayisi": park.habitatlar.count(),
        "donatilar_sayisi": park.donatilar.count(),
        "oyun_gruplari_sayisi": park.oyun_gruplari.count(),
        "bina_sayisi": park.binalar.count(),
        "yesil_alan_toplam": park.yesil_alanlar.aggregate(total=Sum("alan"))["total"]
        or 0,
        "spor_alan_toplam": park.spor_alanlar.aggregate(total=Sum("alan"))["total"]
        or 0,
        "sulama_nokta_sayisi": park.sulama_noktalari.count(),
        "elektrik_nokta_sayisi": park.elektrik_noktalar.count(),
    }

    context = {
        "park": park,
        "park_stats": park_stats,
    }

    return render(request, "parkbahce/partials/park_detail_modal.html", context)


@require_http_methods(["GET"])
def mahalle_detail_htmx(request, mahalle_uuid):
    """Mahalle detay bilgilerini HTMX ile getir - UUID ile"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    from ortak.models import Mahalle

    try:
        # Gerçek mahalle objesini UUID ile al
        mahalle = get_object_or_404(
            Mahalle.objects.select_related("ilce", "ilce__il"), uuid=mahalle_uuid
        )

        # Mahalle istatistiklerini hesapla
        try:
            # Mahalle sınırları içindeki parkları bul
            parklar_count = Park.objects.filter(mahalle=mahalle).count()

            total_area = (
                Park.objects.filter(mahalle=mahalle).aggregate(total=Sum("alan"))[
                    "total"
                ]
                or 0
            )

            # Son eklenen parkları al
            recent_parks = (
                Park.objects.filter(mahalle=mahalle)
                .select_related("park_tipi")
                .order_by("-created_at")[:5]
            )

            mahalle_stats = {
                "park_sayisi": parklar_count,
                "toplam_alan": total_area,
                "nufus": mahalle.nufus,
            }

        except Exception as e:
            print(f"Mahalle istatistikleri hesaplanırken hata: {e}")
            mahalle_stats = {"park_sayisi": 0, "toplam_alan": 0, "nufus": mahalle.nufus}
            recent_parks = []

    except Exception as e:
        print(f"Mahalle bulunamadı: {e}")
        return HttpResponseBadRequest("Mahalle bulunamadı.")

    context = {
        "mahalle": mahalle,
        "mahalle_stats": mahalle_stats,
        "recent_parks": recent_parks,
    }

    return render(request, "parkbahce/partials/mahalle_detail_modal.html", context)


@require_http_methods(["GET"])
def park_habitatlar_tab_htmx(request, park_uuid):
    """Park habitatlar sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)

    # Habitat tipine göre gruplama ve sayma
    habitat_gruplari = (
        park.habitatlar.values("habitat_tipi__ad", "habitat_tipi__deger")
        .annotate(adet=Count("id"))
        .order_by("habitat_tipi__ad")
    )

    toplam_habitat = park.habitatlar.count()

    context = {
        "park": park,
        "habitat_gruplari": habitat_gruplari,
        "toplam_habitat": toplam_habitat,
    }

    return render(request, "parkbahce/tabs/park_habitatlar_tab.html", context)


@require_http_methods(["GET"])
def park_donatilar_tab_htmx(request, park_uuid):
    """Park donatılar sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)

    # Donatı tipine göre gruplama ve sayma
    donati_gruplari = (
        park.donatilar.values("donati_tipi__ad", "donati_tipi__deger")
        .annotate(adet=Count("id"))
        .order_by("donati_tipi__ad")
    )

    toplam_donati = park.donatilar.count()

    context = {
        "park": park,
        "donati_gruplari": donati_gruplari,
        "toplam_donati": toplam_donati,
    }

    return render(request, "parkbahce/tabs/park_donatilar_tab.html", context)


@require_http_methods(["GET"])
def park_oyun_gruplari_tab_htmx(request, park_uuid):
    """Park oyun grupları sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)
    oyun_gruplari = park.oyun_gruplari.select_related(
        "oyun_grup_tipi", "oyun_grup_model"
    ).order_by("-created_at")

    context = {
        "park": park,
        "oyun_gruplari": oyun_gruplari,
    }

    return render(request, "parkbahce/tabs/park_oyun_gruplari_tab.html", context)


@require_http_methods(["GET"])
def park_aboneler_tab_htmx(request, park_uuid):
    """Park aboneler sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)
    aboneler = park.aboneler.order_by("-created_at")

    context = {
        "park": park,
        "aboneler": aboneler,
    }

    return render(request, "parkbahce/tabs/park_aboneler_tab.html", context)


@require_http_methods(["GET"])
def park_altyapi_tab_htmx(request, park_uuid):
    """Park altyapı sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)

    # Altyapı istatistikleri
    altyapi_stats = {
        "sulama_noktalari": park.sulama_noktalari.count(),
        "elektrik_noktalari": park.elektrik_noktalar.count(),
        "sulama_hatlari": SulamaHat.objects.filter(park=park).count(),
        "elektrik_hatlari": ElektrikHat.objects.filter(park=park).count(),
        "kanal_hatlari": KanalHat.objects.filter(park=park).count(),
    }

    context = {
        "park": park,
        "altyapi_stats": altyapi_stats,
    }

    return render(request, "parkbahce/tabs/park_altyapi_tab.html", context)


@require_http_methods(["GET"])
def park_alanlar_tab_htmx(request, park_uuid):
    """Park alanlar sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)

    yesil_alanlar = park.yesil_alanlar.order_by("-created_at")
    spor_alanlar = park.spor_alanlar.select_related(
        "spor_alan_tipi", "spor_aleti_grup"
    ).order_by("-created_at")
    oyun_alanlar = park.oyun_alanlar.select_related("oyun_alan_kaplama_tipi").order_by(
        "-created_at"
    )
    binalar = park.binalar.select_related("bina_kullanim_tipi").order_by("-created_at")

    context = {
        "park": park,
        "yesil_alanlar": yesil_alanlar,
        "spor_alanlar": spor_alanlar,
        "oyun_alanlar": oyun_alanlar,
        "binalar": binalar,
    }

    return render(request, "parkbahce/tabs/park_alanlar_tab.html", context)
