from django.contrib.auth.decorators import login_required
from django.contrib.gis.db.models import Union
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import render

from ortak.models import Il, Ilce, Mahalle

from .models import (
    AboneEndeks,
    Habitat,
    OyunAlan,
    Park,
    ParkAbone,
    ParkBina,
    ParkDonati,
    ParkOyunGrup,
    ParkTip,
    SporAlan,
    SulamaKaynak,
    SulamaTip,
    YesilAlan,
)


def istatistik_index(request):
    """
    İstatistikler ana sayfası - gerçek verilerle kategorize edilmiş istatistik kartları
    """

    # Temel Park İstatistikleri
    park_stats = {
        "toplam_park": Park.objects.count(),
        "toplam_alan": Park.objects.aggregate(toplam=Sum("alan"))["toplam"] or 0,
        "ortalama_alan": Park.objects.aggregate(ortalama=Avg("alan"))["ortalama"] or 0,
        "park_tipleri": Park.objects.values("park_tipi__ad")
        .annotate(sayi=Count("id"))
        .order_by("-sayi")[:5],
    }

    # Alan İstatistikleri - Gerçek veriler
    alan_stats = {
        "yesil_alan_sayisi": YesilAlan.objects.count(),
        "toplam_yesil_alan": YesilAlan.objects.aggregate(toplam=Sum("alan"))["toplam"]
        or 0,
        "spor_alan_sayisi": SporAlan.objects.count(),
        "toplam_spor_alan": SporAlan.objects.aggregate(toplam=Sum("alan"))["toplam"]
        or 0,
        "oyun_alan_sayisi": OyunAlan.objects.count(),
        "toplam_oyun_alan": OyunAlan.objects.aggregate(toplam=Sum("alan"))["toplam"]
        or 0,
        "bina_sayisi": ParkBina.objects.count(),
        "toplam_bina_alan": ParkBina.objects.aggregate(toplam=Sum("alan"))["toplam"]
        or 0,
    }

    # Altyapı İstatistikleri - Mevcut modellere göre
    altyapi_stats = {
        "sulama_sistemli_park": Park.objects.filter(sulama_tipi__isnull=False).count(),
        "toplam_abone": ParkAbone.objects.count(),
        "elektrik_abonesi": ParkAbone.objects.filter(abone_tipi="ELEKTRIK").count(),
        "su_abonesi": ParkAbone.objects.filter(abone_tipi="SU").count(),
        "dogalgaz_abonesi": ParkAbone.objects.filter(abone_tipi="DOGALGAZ").count(),
    }

    # Donatı & Habitat İstatistikleri - Gerçek modeller
    donati_stats = {
        "toplam_donati": ParkDonati.objects.count(),
        "toplam_habitat": Habitat.objects.count(),
        "toplam_oyun_grup": ParkOyunGrup.objects.count(),
        "donati_cesitleri": ParkDonati.objects.values("donati_tipi").distinct().count(),
        "habitat_cesitleri": Habitat.objects.values("habitat_tipi").distinct().count(),
    }

    # Coğrafi Dağılım İstatistikleri
    cografi_stats = {
        "mahalle_sayisi": Mahalle.objects.filter(parklar__isnull=False)
        .distinct()
        .count(),
        "ilce_sayisi": Ilce.objects.filter(mahalleler__parklar__isnull=False)
        .distinct()
        .count(),
        "en_fazla_parkli_mahalle": Mahalle.objects.annotate(
            park_sayisi=Count("parklar")
        )
        .order_by("-park_sayisi")
        .first(),
        "mahalle_park_dagilimi": Mahalle.objects.annotate(park_sayisi=Count("parklar"))
        .filter(park_sayisi__gt=0)
        .order_by("-park_sayisi")[:5],
    }

    context = {
        "park_stats": park_stats,
        "alan_stats": alan_stats,
        "altyapi_stats": altyapi_stats,
        "donati_stats": donati_stats,
        "cografi_stats": cografi_stats,
    }

    return render(request, "istatistik/index.html", context)
