from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.gis.geos import GEOSGeometry
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page

from ortak.models import Mahalle

from .forms import EndeksForm
from .models import (
    ElektrikHat,
    ElektrikNokta,
    Habitat,
    KanalHat,
    Park,
    ParkAbone,
    ParkBina,
    ParkDonati,
    ParkOyunGrup,
    ParkTip,
    ParkYol,
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


def mahalle_detail(request, mahalle_uuid):
    """Mahalle detay sayfası"""
    mahalle = get_object_or_404(
        Mahalle.objects.select_related("ilce", "ilce__il"),
        uuid=mahalle_uuid,
    )

    # Mahalle parkları
    parklar = (
        Park.objects.filter(mahalle=mahalle)
        .select_related("park_tipi", "sulama_tipi", "sulama_kaynagi")
        .order_by("ad")
    )

    # İstatistikler
    total_parks = parklar.count()
    total_area = parklar.aggregate(total=Sum("alan"))["total"] or 0

    # Park tiplerine göre istatistikler
    park_stats = (
        parklar.values("park_tipi__ad")
        .annotate(count=Count("id"), total_area=Sum("alan"))
        .order_by("-count")
    )

    # Son eklenen parklar
    recent_parks = parklar.order_by("-created_at")[:6]

    # Günlük/haftalık/aylık istatistikler için tarih filtreleri
    from datetime import datetime, timedelta

    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    stats = {
        "total_parks": total_parks,
        "total_area": total_area,
        "nufus": mahalle.nufus,
        "park_per_person": round(total_area / mahalle.nufus, 2) if mahalle.nufus else 0,
        "recent_count": parklar.filter(created_at__gte=month_ago).count(),
    }

    context = {
        "mahalle": mahalle,
        "parklar": parklar,
        "stats": stats,
        "park_stats": park_stats,
        "recent_parks": recent_parks,
    }

    return render(request, "parkbahce/mahalle_detail.html", context)


def mahalle_list(request):
    """Mahalle listesi sayfası"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Q, Sum

    from ortak.models import Il, Ilce, Mahalle

    # Filtreleme parametreleri
    search_query = request.GET.get("search", "").strip()
    il_filter = request.GET.get("il", "")
    ilce_filter = request.GET.get("ilce", "")
    sort_by = request.GET.get("sort", "ad")
    sort_direction = request.GET.get("direction", "asc")
    per_page = int(request.GET.get("per_page", 25))

    # Ana sorgu
    mahalleler = Mahalle.objects.select_related("ilce", "ilce__il").annotate(
        park_sayisi=Count("parklar"), toplam_park_alani=Sum("parklar__alan")
    )

    # Arama filtresi
    if search_query:
        mahalleler = mahalleler.filter(
            Q(ad__icontains=search_query)
            | Q(ilce__ad__icontains=search_query)
            | Q(ilce__il__ad__icontains=search_query)
            | Q(muhtar__icontains=search_query)
        )

    # İl filtresi
    if il_filter:
        mahalleler = mahalleler.filter(ilce__il_id=il_filter)

    # İlçe filtresi
    if ilce_filter:
        mahalleler = mahalleler.filter(ilce_id=ilce_filter)

    # Sıralama
    if sort_direction == "desc":
        sort_by = f"-{sort_by}"

    mahalleler = mahalleler.order_by(sort_by)

    # Sayfalama
    paginator = Paginator(mahalleler, per_page)
    page_number = request.GET.get("page")
    mahalleler_page = paginator.get_page(page_number)

    # Filtre seçenekleri
    iller = Il.objects.all().order_by("ad")
    ilceler = Ilce.objects.select_related("il").order_by("il__ad", "ad")

    # İstatistikler
    total_mahalleler = mahalleler.count()
    total_nufus = mahalleler.aggregate(total=Sum("nufus"))["total"] or 0
    total_parks = mahalleler.aggregate(total=Sum("park_sayisi"))["total"] or 0

    context = {
        "mahalleler": mahalleler_page,
        "search_query": search_query,
        "il_filter": il_filter,
        "ilce_filter": ilce_filter,
        "sort_by": sort_by.lstrip("-"),
        "sort_direction": sort_direction,
        "per_page": per_page,
        "iller": iller,
        "ilceler": ilceler,
        "total_mahalleler": total_mahalleler,
        "total_nufus": total_nufus,
        "total_parks": total_parks,
    }

    return render(request, "parkbahce/mahalle_list.html", context)


def donatilar_list(request):
    """Donatılar listesi ve istatistikleri sayfası"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Q

    # Doğrudan ParkDonati tablosundan sorgula
    donatilar = ParkDonati.objects.select_related("park", "donati_tipi").order_by(
        "park__ad"
    )

    # Filtreleme
    search_query = request.GET.get("search", "").strip()
    mahalle_filter = request.GET.get("mahalle", "")
    donati_tipi_filter = request.GET.get("donati_tipi", "")

    if search_query:
        donatilar = donatilar.filter(
            Q(park__ad__icontains=search_query)
            | Q(donati_tipi__ad__icontains=search_query)
        )

    if mahalle_filter:
        donatilar = donatilar.filter(park__mahalle_id=mahalle_filter)

    if donati_tipi_filter:
        donatilar = donatilar.filter(donati_tipi_id=donati_tipi_filter)

    # Sayfalama
    per_page = int(request.GET.get("per_page", 25))
    paginator = Paginator(donatilar, per_page)
    page_number = request.GET.get("page")
    donatilar_page = paginator.get_page(page_number)

    # İstatistikler - Doğrudan donatı tablosundan
    total_donatilar = donatilar.count()

    # Donatı tiplerine göre dağılım
    donati_tipi_stats = (
        donatilar.values("donati_tipi__ad")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # Parklara göre donatı dağılımı
    park_donati_stats = (
        donatilar.values("park__ad", "park__uuid")
        .annotate(donati_count=Count("id"))
        .order_by("-donati_count")[:10]
    )

    # Mahallelere göre donatı dağılımı
    mahalle_donati_stats = (
        donatilar.values(
            "park__mahalle__ad", "park__mahalle__uuid", "park__mahalle__ilce__ad"
        )
        .annotate(donati_count=Count("id"))
        .order_by("-donati_count")[:10]
    )

    # Filtre seçenekleri
    mahalleler = Mahalle.objects.select_related("ilce").order_by("ilce__ad", "ad")
    from parkbahce.models import DonatiTip

    donati_tipleri = DonatiTip.objects.all().order_by("ad")

    context = {
        "donatilar": donatilar_page,
        "search_query": search_query,
        "mahalle_filter": mahalle_filter,
        "donati_tipi_filter": donati_tipi_filter,
        "per_page": per_page,
        "total_donatilar": total_donatilar,
        "donati_tipi_stats": donati_tipi_stats,
        "park_donati_stats": park_donati_stats,
        "mahalle_donati_stats": mahalle_donati_stats,
        "mahalleler": mahalleler,
        "donati_tipleri": donati_tipleri,
    }

    return render(request, "parkbahce/donatilar_list.html", context)


def habitatlar_list(request):
    """Habitatlar listesi ve istatistikleri sayfası"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Q

    # Doğrudan Habitat tablosundan sorgula
    habitatlar = Habitat.objects.select_related("park", "habitat_tipi").order_by(
        "park__ad"
    )

    # Filtreleme
    search_query = request.GET.get("search", "").strip()
    mahalle_filter = request.GET.get("mahalle", "")
    habitat_tipi_filter = request.GET.get("habitat_tipi", "")

    if search_query:
        habitatlar = habitatlar.filter(
            Q(park__ad__icontains=search_query)
            | Q(habitat_tipi__ad__icontains=search_query)
        )

    if mahalle_filter:
        habitatlar = habitatlar.filter(park__mahalle_id=mahalle_filter)

    if habitat_tipi_filter:
        habitatlar = habitatlar.filter(habitat_tipi_id=habitat_tipi_filter)

    # Sayfalama
    per_page = int(request.GET.get("per_page", 25))
    paginator = Paginator(habitatlar, per_page)
    page_number = request.GET.get("page")
    habitatlar_page = paginator.get_page(page_number)

    # İstatistikler - Doğrudan habitat tablosundan
    total_habitatlar = habitatlar.count()

    # Habitat tiplerine göre dağılım
    habitat_tipi_stats = (
        habitatlar.values("habitat_tipi__ad")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    # Parklara göre habitat dağılımı
    park_habitat_stats = (
        habitatlar.values("park__ad", "park__uuid")
        .annotate(habitat_count=Count("id"))
        .order_by("-habitat_count")[:10]
    )

    # Mahallelere göre habitat dağılımı
    mahalle_habitat_stats = (
        habitatlar.values(
            "park__mahalle__ad", "park__mahalle__uuid", "park__mahalle__ilce__ad"
        )
        .annotate(habitat_count=Count("id"))
        .order_by("-habitat_count")[:10]
    )

    # Aylık dikim istatistikleri
    from datetime import datetime, timedelta

    from django.db.models.functions import TruncMonth

    monthly_stats = (
        habitatlar.filter(dikim_tarihi__gte=datetime.now() - timedelta(days=365))
        .annotate(month=TruncMonth("dikim_tarihi"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Filtre seçenekleri
    mahalleler = Mahalle.objects.select_related("ilce").order_by("ilce__ad", "ad")
    from parkbahce.models import HabitatTip

    habitat_tipleri = HabitatTip.objects.all().order_by("ad")

    context = {
        "habitatlar": habitatlar_page,
        "search_query": search_query,
        "mahalle_filter": mahalle_filter,
        "habitat_tipi_filter": habitat_tipi_filter,
        "per_page": per_page,
        "total_habitatlar": total_habitatlar,
        "habitat_tipi_stats": habitat_tipi_stats,
        "park_habitat_stats": park_habitat_stats,
        "mahalle_habitat_stats": mahalle_habitat_stats,
        "monthly_stats": monthly_stats,
        "mahalleler": mahalleler,
        "habitat_tipleri": habitat_tipleri,
    }

    return render(request, "parkbahce/habitatlar_list.html", context)


def park_donati_habitat_list(request):
    """Park Donatı ve Habitat Listesi - ViewParklarDonatilarHabitatlar ile"""
    from django.core.paginator import Paginator
    from django.db.models import Q

    from parkbahce.viewmodels import ViewParklarDonatilarHabitatlar

    # ViewParklarDonatilarHabitatlar modeli ile temel sorgu
    parklar_view = ViewParklarDonatilarHabitatlar.objects.all()  # Filtreleme
    search_query = request.GET.get("search", "").strip()
    filter_type = request.GET.get(
        "filter_type", "all"
    )  # all, donati, habitat, both, none

    if search_query:
        parklar_view = parklar_view.filter(Q(ad__icontains=search_query))

    # Filtre tipine göre filtreleme
    if filter_type == "donati":
        # Sadece donatısı olan parklar
        parklar_view = parklar_view.extra(
            where=["donatilar IS NOT NULL AND jsonb_array_length(donatilar) > 0"]
        )
    elif filter_type == "habitat":
        # Sadece habitatı olan parklar
        parklar_view = parklar_view.extra(
            where=["habitatlar IS NOT NULL AND jsonb_array_length(habitatlar) > 0"]
        )
    elif filter_type == "both":
        # Hem donatısı hem habitatı olan parklar
        parklar_view = parklar_view.extra(
            where=[
                "donatilar IS NOT NULL AND jsonb_array_length(donatilar) > 0",
                "habitatlar IS NOT NULL AND jsonb_array_length(habitatlar) > 0",
            ]
        )
    elif filter_type == "none":
        # Ne donatısı ne habitatı olan parklar
        parklar_view = parklar_view.extra(
            where=[
                "(donatilar IS NULL OR jsonb_array_length(donatilar) = 0)",
                "(habitatlar IS NULL OR jsonb_array_length(habitatlar) = 0)",
            ]
        )

    # Sayfalama
    per_page = int(request.GET.get("per_page", 20))
    paginator = Paginator(parklar_view, per_page)
    page_number = request.GET.get("page")
    parklar_page = paginator.get_page(page_number)  # İstatistikler
    total_parks = parklar_view.count()

    # Donatı istatistikleri
    total_donatilar = 0
    donati_types = {}

    # Habitat istatistikleri
    total_habitatlar = 0
    habitat_types = {}

    # Park kategori sayıları
    parks_with_donati = 0
    parks_with_habitat = 0
    parks_with_both = 0
    parks_with_none = 0

    for park in parklar_view:
        has_donati = False
        has_habitat = False

        # Donatı hesaplamaları
        donatilar = park.donatilar if park.donatilar else []
        if donatilar:
            has_donati = True
            parks_with_donati += 1
            for donati in donatilar:
                donati_tipi = donati.get("donati_tipi", "Belirtilmemiş")
                sayi = donati.get("sayi", 0)
                total_donatilar += sayi
                donati_types[donati_tipi] = donati_types.get(donati_tipi, 0) + sayi

        # Habitat hesaplamaları
        habitatlar = park.habitatlar if park.habitatlar else []
        if habitatlar:
            has_habitat = True
            parks_with_habitat += 1
            for habitat in habitatlar:
                habitat_tipi = habitat.get("habitat_tipi", "Belirtilmemiş")
                sayi = habitat.get("sayi", 0)
                total_habitatlar += sayi
                habitat_types[habitat_tipi] = habitat_types.get(habitat_tipi, 0) + sayi

        # Kategori sayıları
        if has_donati and has_habitat:
            parks_with_both += 1
        elif not has_donati and not has_habitat:
            parks_with_none += 1

    # Park kategori istatistikleri
    park_categories = {
        "donati_only": parks_with_donati - parks_with_both,
        "habitat_only": parks_with_habitat - parks_with_both,
        "both": parks_with_both,
        "none": parks_with_none,
    }
    context = {
        "parklar": parklar_page,
        "search_query": search_query,
        "filter_type": filter_type,
        "per_page": per_page,
        "total_parks": total_parks,
        "total_donatilar": total_donatilar,
        "total_habitatlar": total_habitatlar,
        "donati_types": sorted(donati_types.items(), key=lambda x: x[1], reverse=True)[
            :10
        ],
        "habitat_types": sorted(
            habitat_types.items(), key=lambda x: x[1], reverse=True
        )[:10],
        "park_categories": park_categories,
        "filter_options": [
            ("all", "Tüm Parklar"),
            ("donati", "Sadece Donatısı Olanlar"),
            ("habitat", "Sadece Habitatı Olanlar"),
            ("both", "Hem Donatı Hem Habitat Olanlar"),
            ("none", "Ne Donatı Ne Habitat Olanlar"),
        ],
    }

    return render(request, "parkbahce/park_donati_habitat_list.html", context)


def sulama_sistemi(request):
    """Sulama sistemi yönetimi sayfası"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Sum

    # Sulama noktaları
    sulama_noktalari = SulamaNokta.objects.select_related(
        "park", "sulama_nokta_tipi"
    ).order_by("park__ad")

    # Sulama hatları
    sulama_hatlari = SulamaHat.objects.select_related(
        "park", "sulama_boru_tipi"
    ).order_by("park__ad")

    # Filtreleme
    search_query = request.GET.get("search", "").strip()
    park_filter = request.GET.get("park", "")

    if search_query:
        sulama_noktalari = sulama_noktalari.filter(park__ad__icontains=search_query)
        sulama_hatlari = sulama_hatlari.filter(park__ad__icontains=search_query)

    if park_filter:
        sulama_noktalari = sulama_noktalari.filter(park_id=park_filter)
        sulama_hatlari = sulama_hatlari.filter(park_id=park_filter)

    # Sayfalama
    per_page = int(request.GET.get("per_page", 20))
    paginator_nokta = Paginator(sulama_noktalari, per_page)
    paginator_hat = Paginator(sulama_hatlari, per_page)

    page_number = request.GET.get("page")
    nokta_page = paginator_nokta.get_page(page_number)
    hat_page = paginator_hat.get_page(page_number)

    # İstatistikler
    total_nokta = sulama_noktalari.count()
    total_hat = sulama_hatlari.count()
    total_uzunluk = sulama_hatlari.aggregate(total=Sum("uzunluk"))["total"] or 0

    # Park seçenekleri
    parklar = Park.objects.all().order_by("ad")

    context = {
        "sulama_noktalari": nokta_page,
        "sulama_hatlari": hat_page,
        "search_query": search_query,
        "park_filter": park_filter,
        "per_page": per_page,
        "total_nokta": total_nokta,
        "total_hat": total_hat,
        "total_uzunluk": total_uzunluk,
        "parklar": parklar,
    }

    return render(request, "parkbahce/altyapi/sulama_sistemi.html", context)


def elektrik_altyapisi(request):
    """Elektrik altyapısı yönetimi sayfası"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Sum

    # Elektrik noktaları
    elektrik_noktalari = ElektrikNokta.objects.select_related(
        "park", "elektrik_nokta_tipi"
    ).order_by("park__ad")

    # Elektrik hatları
    elektrik_hatlari = ElektrikHat.objects.select_related(
        "park", "elektrik_kablo_tipi"
    ).order_by("park__ad")

    # Filtreleme
    search_query = request.GET.get("search", "").strip()
    park_filter = request.GET.get("park", "")

    if search_query:
        elektrik_noktalari = elektrik_noktalari.filter(park__ad__icontains=search_query)
        elektrik_hatlari = elektrik_hatlari.filter(park__ad__icontains=search_query)

    if park_filter:
        elektrik_noktalari = elektrik_noktalari.filter(park_id=park_filter)
        elektrik_hatlari = elektrik_hatlari.filter(park_id=park_filter)

    # Sayfalama
    per_page = int(request.GET.get("per_page", 20))
    paginator_nokta = Paginator(elektrik_noktalari, per_page)
    paginator_hat = Paginator(elektrik_hatlari, per_page)

    page_number = request.GET.get("page")
    nokta_page = paginator_nokta.get_page(page_number)
    hat_page = paginator_hat.get_page(page_number)

    # İstatistikler
    total_nokta = elektrik_noktalari.count()
    total_hat = elektrik_hatlari.count()
    total_uzunluk = elektrik_hatlari.aggregate(total=Sum("uzunluk"))["total"] or 0

    # Park seçenekleri
    parklar = Park.objects.all().order_by("ad")

    context = {
        "elektrik_noktalari": nokta_page,
        "elektrik_hatlari": hat_page,
        "search_query": search_query,
        "park_filter": park_filter,
        "per_page": per_page,
        "total_nokta": total_nokta,
        "total_hat": total_hat,
        "total_uzunluk": total_uzunluk,
        "parklar": parklar,
    }

    return render(request, "parkbahce/altyapi/elektrik_altyapisi.html", context)


def kanal_hatlari(request):
    """Kanal hatları yönetimi sayfası"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Sum

    # Kanal hatları
    kanal_hatlari = KanalHat.objects.select_related("park", "kanal_boru_tipi").order_by(
        "park__ad"
    )

    # Filtreleme
    search_query = request.GET.get("search", "").strip()
    park_filter = request.GET.get("park", "")

    if search_query:
        kanal_hatlari = kanal_hatlari.filter(park__ad__icontains=search_query)

    if park_filter:
        kanal_hatlari = kanal_hatlari.filter(park_id=park_filter)

    # Sayfalama
    per_page = int(request.GET.get("per_page", 20))
    paginator = Paginator(kanal_hatlari, per_page)
    page_number = request.GET.get("page")
    kanal_page = paginator.get_page(page_number)

    # İstatistikler
    total_hat = kanal_hatlari.count()
    total_uzunluk = (
        kanal_hatlari.aggregate(total=Sum("uzunluk"))["total"] or 0
    )  # Park seçenekleri
    parklar = Park.objects.all().order_by("ad")

    context = {
        "kanal_hatlari": kanal_page,
        "search_query": search_query,
        "park_filter": park_filter,
        "per_page": per_page,
        "total_hat": total_hat,
        "total_uzunluk": total_uzunluk,
        "parklar": parklar,
    }

    return render(request, "parkbahce/altyapi/kanal_hatlari.html", context)


def yol_agi(request):
    """Yol ağı yönetimi sayfası"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Sum

    # Park yolları - yeni tablo yapısına göre
    park_yollari = ParkYol.objects.select_related("park").order_by("park__ad")

    # Filtreleme
    search_query = request.GET.get("search", "").strip()
    park_filter = request.GET.get("park", "")
    yol_tipi_filter = request.GET.get("yol_tipi", "")

    if search_query:
        park_yollari = park_yollari.filter(park__ad__icontains=search_query)

    if park_filter:
        park_yollari = park_yollari.filter(park_id=park_filter)

    if yol_tipi_filter:
        park_yollari = park_yollari.filter(yol_tipi__icontains=yol_tipi_filter)

    # Sayfalama
    per_page = int(request.GET.get("per_page", 20))
    paginator = Paginator(park_yollari, per_page)
    page_number = request.GET.get("page")
    yol_page = paginator.get_page(page_number)

    # İstatistikler
    total_yol = park_yollari.count()
    total_alan = park_yollari.aggregate(total=Sum("alan"))["total"] or 0

    # Yol tipi istatistikleri
    yol_tipi_stats = (
        park_yollari.values("yol_tipi")
        .annotate(count=Count("id"), total_alan=Sum("alan"))
        .order_by("-count")
    )

    # Park seçenekleri
    parklar = Park.objects.all().order_by("ad")

    # Yol tipi seçenekleri
    yol_tipleri = (
        ParkYol.objects.values_list("yol_tipi", flat=True)
        .distinct()
        .exclude(yol_tipi__isnull=True)
        .exclude(yol_tipi="")
        .order_by("yol_tipi")
    )

    context = {
        "park_yollari": yol_page,
        "search_query": search_query,
        "park_filter": park_filter,
        "yol_tipi_filter": yol_tipi_filter,
        "per_page": per_page,
        "total_yol": total_yol,
        "total_alan": total_alan,
        "yol_tipi_stats": yol_tipi_stats,
        "parklar": parklar,
        "yol_tipleri": yol_tipleri,
    }

    return render(request, "parkbahce/altyapi/yol_agi.html", context)


def abonelik_takibi(request):
    """Abonelik takibi sayfası"""
    from django.core.paginator import Paginator
    from django.db.models import Count, Q

    # Park aboneleri
    park_aboneleri = ParkAbone.objects.select_related("park").order_by(
        "park__ad", "abone_tipi"
    )

    # Filtreleme
    search_query = request.GET.get("search", "").strip()
    park_filter = request.GET.get("park", "")
    abone_tipi_filter = request.GET.get("abone_tipi", "")

    if search_query:
        park_aboneleri = park_aboneleri.filter(
            Q(park__ad__icontains=search_query) | Q(abone_no__icontains=search_query)
        )

    if park_filter:
        park_aboneleri = park_aboneleri.filter(park_id=park_filter)

    if abone_tipi_filter:
        park_aboneleri = park_aboneleri.filter(abone_tipi=abone_tipi_filter)

    # Sayfalama
    per_page = int(request.GET.get("per_page", 20))
    paginator = Paginator(park_aboneleri, per_page)
    page_number = request.GET.get("page")
    abone_page = paginator.get_page(page_number)

    # İstatistikler
    total_abone = park_aboneleri.count()
    abone_tipi_stats = (
        park_aboneleri.values("abone_tipi")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    # Park seçenekleri
    parklar = Park.objects.all().order_by("ad")

    context = {
        "park_aboneleri": abone_page,
        "search_query": search_query,
        "park_filter": park_filter,
        "abone_tipi_filter": abone_tipi_filter,
        "per_page": per_page,
        "total_abone": total_abone,
        "abone_tipi_stats": abone_tipi_stats,
        "parklar": parklar,
    }

    return render(request, "parkbahce/altyapi/abonelik_takibi.html", context)


def abone_detail(request, abone_uuid):
    """Abone detay sayfası - endeks geçmişi ile birlikte"""
    from datetime import datetime, timedelta

    from django.db import models
    from django.db.models import Sum

    abone = get_object_or_404(ParkAbone, uuid=abone_uuid)

    # Son 12 aylık endeks kayıtları (en son eklenen üstte)
    endeksler = abone.endeksler.order_by("-endeks_tarihi")[:12]

    # Son endeks değeri ve tarihi
    son_endeks = endeksler.first() if endeksler else None

    # Endeksler listesini view'da tüketim bilgisi ile birlikte hazırla
    endeks_listesi = []
    endeks_list = list(endeksler)

    for i, endeks in enumerate(endeks_list):
        endeks_dict = {
            "endeks": endeks,
            "tuketim": None,
            "is_last": i == len(endeks_list) - 1,
        }

        # Tüketim hesaplaması (bir önceki endeks ile)
        if i < len(endeks_list) - 1:
            onceki_endeks = endeks_list[i + 1]
            if endeks.endeks_degeri and onceki_endeks.endeks_degeri:
                tuketim = endeks.endeks_degeri - onceki_endeks.endeks_degeri
                endeks_dict["tuketim"] = tuketim

        endeks_listesi.append(endeks_dict)

    # Endeks istatistikleri
    endeks_stats = {
        "toplam_kayit": endeksler.count(),
        "ortalama": endeksler.aggregate(ortalama=models.Avg("endeks_degeri"))[
            "ortalama"
        ],
    }

    # Tüketim hesaplamaları
    tuketimler = [
        e["tuketim"]
        for e in endeks_listesi
        if e["tuketim"] is not None and e["tuketim"] > 0
    ]

    # Aylık ortalama tüketim
    aylik_tuketim = None
    if tuketimler:
        aylik_tuketim = sum(tuketimler) / len(tuketimler)

    # Yıllık ortalama tüketim (12 aylık toplam)
    yillik_tuketim = None
    if tuketimler:
        # Son 12 aydaki toplam tüketim
        yillik_tuketim = sum(tuketimler)

    # Su abonesi için yeşil alan başına tüketim hesaplaması
    yesil_alan_stats = {}
    if abone.abone_tipi == "su":
        # Parka ait toplam yeşil alan
        toplam_yesil_alan = (
            abone.park.yesil_alanlar.aggregate(toplam=Sum("alan"))["toplam"] or 0
        )

        if toplam_yesil_alan > 0:
            yesil_alan_stats = {
                "toplam_yesil_alan": toplam_yesil_alan,
                "aylik_m2_tuketim": (
                    aylik_tuketim / toplam_yesil_alan if aylik_tuketim else None
                ),
                "yillik_m2_tuketim": (
                    yillik_tuketim / toplam_yesil_alan if yillik_tuketim else None
                ),
            }

    context = {
        "abone": abone,
        "endeks_listesi": endeks_listesi,
        "son_endeks": son_endeks,
        "endeks_stats": endeks_stats,
        "aylik_tuketim": aylik_tuketim,
        "yillik_tuketim": yillik_tuketim,
        "yesil_alan_stats": yesil_alan_stats,
    }

    return render(request, "parkbahce/abone_detail.html", context)


def endeks_ekle(request, abone_uuid):
    """Abone için yeni endeks ekleme sayfası"""
    abone = get_object_or_404(ParkAbone, uuid=abone_uuid)

    # Son 5 endeks kaydını form sayfasında göstermek için
    son_endeksler = abone.endeksler.order_by("-endeks_tarihi")[:5]

    if request.method == "POST":
        form = EndeksForm(request.POST, park_abone=abone)
        if form.is_valid():
            endeks = form.save(commit=False)
            endeks.park_abone = abone
            endeks.save()

            messages.success(
                request,
                f"{abone.get_abone_tipi_display()} abonesi için yeni endeks başarıyla eklendi.",
            )
            return redirect("parkbahce:abone_detail", abone_uuid=abone.uuid)
    else:
        # Son endeks değerini varsayılan olarak getir
        son_endeks = abone.endeksler.order_by("-endeks_tarihi").first()
        initial_data = {"endeks_tarihi": timezone.now().date()}

        form = EndeksForm(initial=initial_data, park_abone=abone)

    context = {
        "abone": abone,
        "form": form,
        "son_endeksler": son_endeksler,
    }

    return render(request, "parkbahce/endeks_ekle.html", context)
