from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ortak.models import Mahalle

from .models import (
    ElektrikHat,
    ElektrikNokta,
    Habitat,
    KanalHat,
    Park,
    ParkBina,
    ParkDonati,
    ParkOyunGrup,
    ParkTip,
    SporAlan,
    SulamaHat,
    SulamaNokta,
    SulamaTip,
    YesilAlan,
)


@cache_page(60 * 5)  # 5 dakika cache
def index(request):
    """Dashboard ana sayfa view'i - Park yönetim sistemi istatistikleri"""

    # Temel istatistikler
    total_parks = Park.objects.count()
    total_equipment = ParkDonati.objects.count()
    total_habitats = Habitat.objects.count()
    total_users = User.objects.filter(is_active=True).count()

    # Ek istatistikler
    total_playground_groups = ParkOyunGrup.objects.count()
    total_sports_areas = SporAlan.objects.count()
    total_green_areas = YesilAlan.objects.count()
    total_buildings = ParkBina.objects.count()

    # Altyapı istatistikleri
    total_irrigation_points = SulamaNokta.objects.count()
    total_electric_points = (
        ElektrikNokta.objects.count() if "ElektrikNokta" in globals() else 0
    )
    total_irrigation_lines = SulamaHat.objects.count()
    total_electric_lines = ElektrikHat.objects.count()
    total_canal_lines = KanalHat.objects.count()

    # Son eklenen parklar (limit 5)
    recent_parks = Park.objects.select_related("mahalle", "park_tipi").order_by(
        "-created_at"
    )[:5]

    # Park tipi dağılımı
    park_types_distribution = (
        Park.objects.values("park_tipi__ad")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Mahalle bazında park dağılımı
    neighborhood_distribution = (
        Park.objects.values("mahalle__ad", "mahalle__ilce__ad")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )

    # Alan bazında istatistikler
    total_park_area = Park.objects.aggregate(total_area=Sum("alan"))["total_area"] or 0
    total_green_area = (
        YesilAlan.objects.aggregate(total_area=Sum("alan"))["total_area"] or 0
    )
    total_sports_area = (
        SporAlan.objects.aggregate(total_area=Sum("alan"))["total_area"] or 0
    )

    # Son 30 günde eklenen parklar
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_parks_count = Park.objects.filter(created_at__gte=thirty_days_ago).count()

    # Bakım gereken parklar (örnek: 6 aydan eski parklar)
    six_months_ago = timezone.now() - timedelta(days=180)
    maintenance_needed = Park.objects.filter(created_at__lte=six_months_ago).count()

    # En büyük parklar (alan bazında)
    largest_parks = (
        Park.objects.filter(alan__isnull=False, alan__gt=0)
        .select_related("mahalle", "park_tipi")
        .order_by("-alan")[:10]
    )

    # Sulama sistemi analizi
    irrigation_coverage = {
        "total_points": total_irrigation_points,
        "total_lines_length": SulamaHat.objects.aggregate(total_length=Sum("uzunluk"))[
            "total_length"
        ]
        or 0,
        "parks_with_irrigation": Park.objects.filter(sulama_noktalari__isnull=False)
        .distinct()
        .count(),
    }

    # Elektrik sistemi analizi
    electrical_coverage = {
        "total_points": total_electric_points,
        "total_lines_length": ElektrikHat.objects.aggregate(
            total_length=Sum("uzunluk")
        )["total_length"]
        or 0,
        "parks_with_electricity": Park.objects.filter(elektrik_hatlari__isnull=False)
        .distinct()
        .count(),
    }

    # Kullanıcı grupları
    user_groups = request.user.groups.all() if request.user.is_authenticated else []

    context = {
        # Ana istatistikler
        "total_parks": total_parks,
        "total_equipment": total_equipment,
        "total_habitats": total_habitats,
        "total_users": total_users,
        # Ek istatistikler
        "total_playground_groups": total_playground_groups,
        "total_sports_areas": total_sports_areas,
        "total_green_areas": total_green_areas,
        "total_buildings": total_buildings,
        # Altyapı istatistikleri
        "total_irrigation_points": total_irrigation_points,
        "total_electric_points": total_electric_points,
        "total_irrigation_lines": total_irrigation_lines,
        "total_electric_lines": total_electric_lines,
        "total_canal_lines": total_canal_lines,
        # Listeler ve dağılımlar
        "recent_parks": recent_parks,
        "park_types_distribution": park_types_distribution,
        "neighborhood_distribution": neighborhood_distribution,
        "largest_parks": largest_parks,
        # Alan istatistikleri
        "total_park_area": round(total_park_area, 2),
        "total_green_area": round(total_green_area, 2),
        "total_sports_area": round(total_sports_area, 2),
        # Tarih bazlı istatistikler
        "recent_parks_count": recent_parks_count,
        "maintenance_needed": maintenance_needed,
        # Sistem analizleri
        "irrigation_coverage": irrigation_coverage,
        "electrical_coverage": electrical_coverage,
        # Kullanıcı bilgileri
        "user_groups": user_groups,
    }

    return render(request, "index.html", context)


def park_list(request):
    """Park listesi view'i - Filtreleme, arama, sayfalama ve sıralama özellikleri ile"""

    # Temel queryset - optimize edilmiş
    parks_queryset = (
        Park.objects.select_related(
            "mahalle",
            "mahalle__ilce",
            "mahalle__ilce__il",
            "park_tipi",
            "sulama_tipi",
            "sulama_kaynagi",
        )
        .prefetch_related("yesil_alanlar")
        .annotate(toplam_yesil_alan=Sum("yesil_alanlar__alan"))
    )

    # Arama
    search_query = request.GET.get("search", "").strip()
    if search_query:
        parks_queryset = parks_queryset.filter(
            Q(ad__icontains=search_query)
            | Q(mahalle__ad__icontains=search_query)
            | Q(mahalle__ilce__ad__icontains=search_query)
        )

    # Filtreleme
    mahalle_filter = request.GET.get("mahalle", "")
    park_tipi_filter = request.GET.get("park_tipi", "")
    sulama_tipi_filter = request.GET.get("sulama_tipi", "")

    if mahalle_filter:
        parks_queryset = parks_queryset.filter(mahalle_id=mahalle_filter)

    if park_tipi_filter:
        parks_queryset = parks_queryset.filter(park_tipi_id=park_tipi_filter)

    if sulama_tipi_filter:
        parks_queryset = parks_queryset.filter(sulama_tipi_id=sulama_tipi_filter)

    # Sıralama
    sort_by = request.GET.get("sort", "ad")
    sort_direction = request.GET.get("direction", "asc")

    if sort_direction == "desc":
        sort_by = f"-{sort_by}"

    valid_sort_fields = [
        "ad",
        "alan",
        "toplam_yesil_alan",
        "created_at",
        "mahalle__ad",
    ]
    if sort_by.lstrip("-") in valid_sort_fields:
        parks_queryset = parks_queryset.order_by(sort_by)
    else:
        parks_queryset = parks_queryset.order_by("ad")

    # Sayfalama
    per_page = request.GET.get("per_page", "12")
    try:
        per_page = int(per_page)
        if per_page not in [6, 12, 24, 48]:
            per_page = 12
    except (ValueError, TypeError):
        per_page = 12
    paginator = Paginator(parks_queryset, per_page)
    page_number = request.GET.get("page")
    parklar = paginator.get_page(page_number)

    # Filtre seçenekleri
    mahalleler = Mahalle.objects.select_related("ilce", "ilce__il").order_by(
        "ilce__il__ad", "ilce__ad", "ad"
    )
    park_tipleri = ParkTip.objects.all().order_by("ad")
    sulama_tipleri = SulamaTip.objects.all().order_by("ad")

    # İstatistikler
    total_parks = parks_queryset.count()
    total_area = parks_queryset.aggregate(total=Sum("alan"))["total"] or 0
    total_green_area = (
        parks_queryset.aggregate(total=Sum("toplam_yesil_alan"))["total"] or 0
    )

    context = {
        "parklar": parklar,
        "search_query": search_query,
        "mahalle_filter": mahalle_filter,
        "park_tipi_filter": park_tipi_filter,
        "sulama_tipi_filter": sulama_tipi_filter,
        "sort_by": request.GET.get("sort", "ad"),
        "sort_direction": sort_direction,
        "per_page": per_page,
        "mahalleler": mahalleler,
        "park_tipleri": park_tipleri,
        "sulama_tipleri": sulama_tipleri,
        "total_parks": total_parks,
        "total_area": round(total_area, 2),
        "total_green_area": round(total_green_area, 2),
    }

    return render(request, "parkbahce/park_list.html", context)


def park_detail(request, park_uuid):
    """Park detay view'i"""

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
    yesil_alan_toplam = park.yesil_alanlar.aggregate(total=Sum("alan"))["total"] or 0
    spor_alan_toplam = park.spor_alanlar.aggregate(total=Sum("alan"))["total"] or 0
    donati_sayisi = park.donatilar.count()
    oyun_grup_sayisi = park.oyun_gruplari.count()
    sulama_nokta_sayisi = park.sulama_noktalari.count()
    elektrik_nokta_sayisi = park.elektrik_noktalar.count()
    habitat_sayisi = park.habitatlar.count()
    bina_sayisi = (
        park.binalar.count()
    )  # Park geometrisini SRID 5256'dan 4326'ya dönüştür (harita için)
    park_geom_4326 = None
    if park.geom:
        park_geom_4326 = park.geom.transform(4326, clone=True)

    context = {
        "park": park,
        "park_geom_4326": park_geom_4326,
        "yesil_alan_toplam": round(yesil_alan_toplam, 2),
        "spor_alan_toplam": round(spor_alan_toplam, 2),
        "donati_sayisi": donati_sayisi,
        "oyun_grup_sayisi": oyun_grup_sayisi,
        "sulama_nokta_sayisi": sulama_nokta_sayisi,
        "elektrik_nokta_sayisi": elektrik_nokta_sayisi,
        "habitat_sayisi": habitat_sayisi,
        "bina_sayisi": bina_sayisi,
    }

    return render(request, "parkbahce/park_detail.html", context)


def park_harita(request):
    """Park harita sayfası"""
    return render(request, "parkbahce/park_harita.html")


# HTMX Tab Views
def park_is_takip_tab_htmx(request, park_uuid):
    """Park İş Takip sekmesi HTMX view'i"""
    park = get_object_or_404(Park, uuid=park_uuid)

    # İş takip verilerini simüle ediyoruz (gerçek modeller eklendikten sonra güncellenecek)
    is_takip_data = {
        "aktif_isler": 5,
        "bekleyen_isler": 3,
        "tamamlanan_isler": 12,
        "son_isler": [
            {
                "ad": "Çim Biçme İşi",
                "tarih": "15.11.2024",
                "durum": "Devam Ediyor",
            },
            {"ad": "Ağaç Budama", "tarih": "14.11.2024", "durum": "Tamamlandı"},
            {
                "ad": "Sulama Sistemi Kontrolü",
                "tarih": "13.11.2024",
                "durum": "Bekliyor",
            },
        ],
    }

    context = {"park": park, "is_takip_data": is_takip_data}
    return render(request, "parkbahce/tabs/park_is_takip_tab.html", context)


def park_habitatlar_tab_htmx(request, park_uuid):
    """Park Habitatlar sekmesi HTMX view'i"""
    park = get_object_or_404(Park, uuid=park_uuid)

    # Parka ait habitatları getir
    habitatlar = park.habitatlar.select_related("habitat_tipi").all()

    context = {"park": park, "habitatlar": habitatlar}
    return render(request, "parkbahce/tabs/park_habitatlar_tab.html", context)


def park_donatilar_tab_htmx(request, park_uuid):
    """Park Donatılar sekmesi HTMX view'i"""
    park = get_object_or_404(Park, uuid=park_uuid)

    # Parka ait donatıları getir
    donatilar = park.donatilar.select_related("donati_tipi").all()

    context = {"park": park, "donatilar": donatilar}
    return render(request, "parkbahce/tabs/park_donatilar_tab.html", context)


def park_oyun_gruplari_tab_htmx(request, park_uuid):
    """Park Oyun Grupları sekmesi HTMX view'i"""
    park = get_object_or_404(Park, uuid=park_uuid)

    # Parka ait oyun gruplarını getir
    oyun_gruplari = park.oyun_gruplari.select_related(
        "oyun_grup_tipi", "oyun_grup_model"
    ).all()

    context = {"park": park, "oyun_gruplari": oyun_gruplari}
    return render(request, "parkbahce/tabs/park_oyun_gruplari_tab.html", context)


def park_alanlar_tab_htmx(request, park_uuid):
    """Park Alanlar sekmesi HTMX view'i"""
    park = get_object_or_404(Park, uuid=park_uuid)

    # Parka ait alanları getir
    yesil_alanlar = park.yesil_alanlar.all()
    spor_alanlar = park.spor_alanlar.select_related(
        "spor_alan_tipi", "spor_aleti_grup"
    ).all()
    oyun_alanlar = (
        park.oyun_alanlar.select_related("oyun_alan_kaplama_tipi").all()
        if hasattr(park, "oyun_alanlar")
        else []
    )
    binalar = park.binalar.select_related("bina_kullanim_tipi").all()

    context = {
        "park": park,
        "yesil_alanlar": yesil_alanlar,
        "spor_alanlar": spor_alanlar,
        "oyun_alanlar": oyun_alanlar,
        "binalar": binalar,
    }
    return render(request, "parkbahce/tabs/park_alanlar_tab.html", context)


def park_altyapi_tab_htmx(request, park_uuid):
    """Park Altyapı sekmesi HTMX view'i"""
    park = get_object_or_404(Park, uuid=park_uuid)

    # Altyapı istatistiklerini hesapla
    altyapi_stats = {
        "sulama_noktalari": park.sulama_noktalari.count(),
        "elektrik_noktalari": (
            park.elektrik_noktalar.count() if hasattr(park, "elektrik_noktalar") else 0
        ),
        "sulama_hatlari": (
            park.sulama_hatlari.count() if hasattr(park, "sulama_hatlari") else 0
        ),
        "elektrik_hatlari": (
            park.elektrik_hatlari.count() if hasattr(park, "elektrik_hatlari") else 0
        ),
        "kanal_hatlari": (
            park.kanal_hatlari.count() if hasattr(park, "kanal_hatlari") else 0
        ),
    }

    context = {"park": park, "altyapi_stats": altyapi_stats}
    return render(request, "parkbahce/tabs/park_altyapi_tab.html", context)


def park_aboneler_tab_htmx(request, park_uuid):
    """Park Aboneler sekmesi HTMX view'i"""
    park = get_object_or_404(Park, uuid=park_uuid)

    # Parka ait aboneleri getir
    aboneler = []
    if hasattr(park, "aboneler"):
        aboneler = park.aboneler.all()

    context = {"park": park, "aboneler": aboneler}
    return render(request, "parkbahce/tabs/park_aboneler_tab.html", context)
