from datetime import timedelta

from django.contrib.gis.geos import GEOSGeometry
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import cache_page

from .models import Habitat, Park, ParkDonati


def index(request):  # İstatistikler
    toplam_park = Park.objects.count()
    toplam_donati = ParkDonati.objects.count()
    toplam_habitat = Habitat.objects.count()

    # Son 30 günde eklenen parklar (bakım gereken simülasyonu)
    son_30_gun = timezone.now() - timedelta(days=30)
    bakim_gereken = Park.objects.filter(created_at__gte=son_30_gun).count()

    # Park tiplerine göre dağılım (top 5)
    park_tipleri_raw = (
        Park.objects.values("park_tipi__ad")
        .annotate(sayi=Count("id"))
        .order_by("-sayi")[:5]
    )

    # Mahalle dağılımı (top 5)
    mahalle_dagilimi_raw = (
        Park.objects.values("mahalle__ad")
        .annotate(sayi=Count("id"))
        .order_by("-sayi")[:5]
    )

    # Progress bar için yüzde hesaplama
    max_park_tipi = park_tipleri_raw[0]["sayi"] if park_tipleri_raw else 1
    max_mahalle = mahalle_dagilimi_raw[0]["sayi"] if mahalle_dagilimi_raw else 1

    park_tipleri = [
        {
            "park_tipi__ad": item["park_tipi__ad"],
            "sayi": item["sayi"],
            "yuzde": int((item["sayi"] / max_park_tipi) * 100),
        }
        for item in park_tipleri_raw
    ]

    mahalle_dagilimi = [
        {
            "mahalle__ad": item["mahalle__ad"],
            "sayi": item["sayi"],
            "yuzde": int((item["sayi"] / max_mahalle) * 100),
        }
        for item in mahalle_dagilimi_raw
    ]

    # Son aktiviteler (son 5 park)
    son_parklar = Park.objects.order_by("-created_at")[:5]

    # En büyük yeşil alana sahip parklar (top 10)
    en_buyuk_parklar = Park.objects.filter(alan__isnull=False).order_by("-alan")[:10]

    context = {
        "toplam_park": toplam_park,
        "toplam_donati": toplam_donati,
        "toplam_habitat": toplam_habitat,
        "bakim_gereken": bakim_gereken,
        "park_tipleri": park_tipleri,
        "mahalle_dagilimi": mahalle_dagilimi,
        "son_parklar": son_parklar,
        "en_buyuk_parklar": en_buyuk_parklar,
    }

    return render(request, "parkbahce/index.html", context)


def park_list(request):
    # Filtreleme parametreleri
    search_query = request.GET.get("search", "")
    mahalle_filter = request.GET.get("mahalle", "")
    park_tipi_filter = request.GET.get("park_tipi", "")
    ordering = request.GET.get("ordering", "ad")

    # Base queryset
    parklar = Park.objects.select_related("mahalle", "park_tipi").defer("geom")

    # Arama filtresi
    if search_query:
        parklar = parklar.filter(
            Q(ad__icontains=search_query)
            | Q(mahalle__ad__icontains=search_query)
            | Q(yapan_firma__icontains=search_query)
        )

    # Mahalle filtresi
    if mahalle_filter:
        parklar = parklar.filter(mahalle__id=mahalle_filter)

    # Park tipi filtresi
    if park_tipi_filter:
        parklar = parklar.filter(park_tipi__id=park_tipi_filter)

    # Sıralama
    if ordering == "alan":
        parklar = parklar.order_by("-alan")
    elif ordering == "tarih":
        parklar = parklar.order_by("-yapim_tarihi")
    else:
        parklar = parklar.order_by("ad")

    # Sayfalama
    paginator = Paginator(parklar, 20)  # Her sayfada 20 park
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Filtreleme için mahalle ve park tipi listesi
    from ortak.models import Mahalle

    from .models import ParkTip

    mahalleler = Mahalle.objects.all().order_by("ad")
    park_tipleri = ParkTip.objects.all().order_by("ad")

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "mahalle_filter": mahalle_filter,
        "park_tipi_filter": park_tipi_filter,
        "ordering": ordering,
        "mahalleler": mahalleler,
        "park_tipleri": park_tipleri,
    }

    return render(request, "parkbahce/parklar/list.html", context)


# get by uuid
def park_detail(request, uuid):
    park = Park.objects.get(uuid=uuid)

    # Donatıları tipine göre grupla ve say
    donati_gruplari = (
        ParkDonati.objects.filter(park=park)
        .values("donati_tipi__ad")
        .annotate(toplam=Sum("extra_data__sayi"))
        .order_by("donati_tipi__ad")
    )

    # Habitatları tipine göre grupla ve say
    habitat_gruplari = (
        Habitat.objects.filter(park=park)
        .values("habitat_tipi__ad")
        .annotate(toplam=Count("id"))
        .order_by("habitat_tipi__ad")
    )

    # Park geometrisini EPSG:5256'dan EPSG:4326'ya dönüştür
    if park.geom:
        # Geometriyi 5256 (TUREF) olarak ayarla
        park.geom.srid = 5256
        # WGS84 (4326) koordinat sistemine dönüştür
        park.geom.transform(4326)

    return render(
        request,
        "parkbahce/parklar/detail.html",
        {
            "park": park,
            "donati_gruplari": donati_gruplari,
            "habitat_gruplari": habitat_gruplari,
        },
    )


def park_edit(request, uuid):
    park = Park.objects.get(uuid=uuid)
    if request.method == "POST":
        park.name = request.POST.get("name")
        park.description = request.POST.get("description")
        park.save()
        return render(request, "parkbahce/parklar/detail.html", {"park": park})
    return render(request, "parkbahce/park_edit.html", {"park": park})


def park_delete(request, uuid):
    park = Park.objects.get(uuid=uuid)
    if request.method == "POST":
        park.delete()
        return render(
            request, "parkbahce/park_list.html", {"parklar": Park.objects.all()}
        )
    return render(request, "parkbahce/park_delete.html", {"park": park})
