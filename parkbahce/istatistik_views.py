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
    ParkTip,
    SporAlan,
    SulamaKaynak,
    SulamaTip,
    YesilAlan,
)


def istatistik_index(request):
    """
    İstatistikler ana sayfası - kategorize edilmiş istatistik kartları
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

    # Alan İstatistikleri
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

    # Altyapı İstatistikleri
    altyapi_stats = {
        "sulama_sistemli_park": Park.objects.filter(sulama_tipi__isnull=False).count(),
        "elektrik_abonesi": ParkAbone.objects.filter(abone_tipi="ELEKTRIK").count(),
        "su_abonesi": ParkAbone.objects.filter(abone_tipi="SU").count(),
        "dogalgaz_abonesi": ParkAbone.objects.filter(abone_tipi="DOGALGAZ").count(),
    }

    # Donatı & Habitat İstatistikleri
    donati_stats = {
        "toplam_donati": (
            ParkDonati.objects.count() if hasattr(ParkDonati, "objects") else 0
        ),
        "toplam_habitat": Habitat.objects.count() if hasattr(Habitat, "objects") else 0,
        "donati_cesitleri": 0,  # ParkDonati modeli tamamlandığında güncellenecek
        "habitat_cesitleri": 0,  # Habitat modeli tamamlandığında güncellenecek
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
    }

    # Bakım & Kullanım İstatistikleri (gelecek için hazırlanmış)
    bakim_stats = {
        "bakim_bekleyen": 0,  # Bakım modeli eklendikinde güncellenecek
        "aktif_sorun": 0,  # Sorun modeli eklendikinde güncellenecek
        "tamamlanan_is": 0,  # İş takip modeli eklendikinde güncellenecek
        "geciken_is": 0,  # İş takip modeli eklendikinde güncellenecek
    }

    context = {
        "park_stats": park_stats,
        "alan_stats": alan_stats,
        "altyapi_stats": altyapi_stats,
        "donati_stats": donati_stats,
        "cografi_stats": cografi_stats,
        "bakim_stats": bakim_stats,
    }

    return render(request, "istatistik/index.html", context)
