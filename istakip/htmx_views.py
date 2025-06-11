from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods

from ortak.models import Mahalle
from parkbahce.models import Park

from .forms import ParkPersonelAtamaForm, PersonelKullaniciForm
from .models import (
    Gorev,
    GorevAsama,
    GorevTamamlamaResim,
    GunlukKontrol,
    KontrolResim,
    ParkPersonel,
    Personel,
)


@login_required
def kullanici_bilgileri_htmx(request, personel_uuid):
    """HTMX ile kullanıcı bilgileri sekmesi"""

    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    personel = get_object_or_404(
        Personel.objects.select_related("user").prefetch_related("user__groups"),
        uuid=personel_uuid,
    )

    context = {"personel": personel}
    return render(request, "istakip/partials/kullanici_bilgileri.html", context)


@login_required
def kullanici_parklar_htmx(request, personel_uuid):
    """HTMX ile sorumlu parklar sekmesi"""

    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    personel = get_object_or_404(Personel, uuid=personel_uuid)

    # Sorumlu parkları getir
    sorumlu_parklar = personel.park_personeller.select_related(
        "park__mahalle", "park__park_tipi"
    ).order_by("park__ad")

    context = {
        "personel": personel,
        "sorumlu_parklar": sorumlu_parklar,
    }
    return render(request, "istakip/partials/kullanici_parklar.html", context)


@login_required
def kullanici_kontroller_htmx(request, personel_uuid):
    """HTMX ile kontroller sekmesi"""

    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    personel = get_object_or_404(Personel, uuid=personel_uuid)

    # Filtreleme parametreleri
    tarih_filter = request.GET.get("tarih", "")
    park_filter = request.GET.get("park", "")
    durum_filter = request.GET.get("durum", "")

    # Temel queryset
    kontroller = personel.gunluk_kontroller.select_related("park").order_by(
        "-kontrol_tarihi"
    )

    # Filtreleme
    if tarih_filter:
        kontroller = kontroller.filter(kontrol_tarihi__date=tarih_filter)

    if park_filter:
        kontroller = kontroller.filter(park_id=park_filter)

    if durum_filter:
        kontroller = kontroller.filter(durum=durum_filter)

    # Sayfalama
    per_page = 20
    paginator = Paginator(kontroller, per_page)
    page_number = request.GET.get("page")
    kontroller_page = paginator.get_page(page_number)

    # Sorumlu parklar
    sorumlu_parklar = personel.park_personeller.select_related("park").order_by(
        "park__ad"
    )

    context = {
        "personel": personel,
        "kontroller": kontroller_page,
        "sorumlu_parklar": sorumlu_parklar,
        "tarih_filter": tarih_filter,
        "park_filter": park_filter,
        "durum_filter": durum_filter,
    }
    return render(request, "istakip/partials/kullanici_kontroller.html", context)


@login_required
def kullanici_performans_htmx(request, personel_uuid):
    """HTMX ile performans analizi sekmesi"""

    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    personel = get_object_or_404(Personel, uuid=personel_uuid)

    # Performans metrikleri
    bugun = timezone.now().date()
    bu_hafta_baslangic = bugun - timedelta(days=bugun.weekday())
    bu_ay_baslangic = bugun.replace(day=1)

    # Kontrol istatistikleri
    kontrol_stats = {
        "toplam": personel.gunluk_kontroller.count(),
        "bugun": personel.gunluk_kontroller.filter(kontrol_tarihi__date=bugun).count(),
        "bu_hafta": personel.gunluk_kontroller.filter(
            kontrol_tarihi__date__gte=bu_hafta_baslangic
        ).count(),
        "bu_ay": personel.gunluk_kontroller.filter(
            kontrol_tarihi__date__gte=bu_ay_baslangic
        ).count(),
    }

    # Sorun istatistikleri
    sorun_stats = {
        "toplam": personel.gunluk_kontroller.filter(
            durum__in=["sorun_var", "acil"]
        ).count(),
        "acil": personel.gunluk_kontroller.filter(durum="acil").count(),
        "normal": personel.gunluk_kontroller.filter(durum="sorun_var").count(),
    }

    # Performans oranları
    if kontrol_stats["toplam"] > 0:
        sorun_orani = (sorun_stats["toplam"] / kontrol_stats["toplam"]) * 100
    else:
        sorun_orani = 0

    context = {
        "personel": personel,
        "kontrol_stats": kontrol_stats,
        "sorun_stats": sorun_stats,
        "sorun_orani": round(sorun_orani, 1),
    }
    return render(request, "istakip/partials/kullanici_performans.html", context)


@login_required
def kullanici_gorevler_htmx(request, personel_uuid):
    """HTMX ile görevler sekmesi"""

    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    personel = get_object_or_404(Personel, uuid=personel_uuid)

    # Görev filtreleme
    durum_filter = request.GET.get("gorev_durum", "")

    # Görevler (şimdilik boş, ileride eklenecek)
    gorevler = (
        []
    )  # personel.atanan_gorevler.select_related("park").order_by("-created_at")

    context = {
        "personel": personel,
        "gorevler": gorevler,
        "durum_filter": durum_filter,
    }
    return render(request, "istakip/partials/kullanici_gorevler.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def park_atama_htmx(request, personel_uuid):
    """HTMX ile park atama işlemi"""

    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    personel = get_object_or_404(Personel, uuid=personel_uuid)

    if request.method == "POST":
        try:
            secili_parklar = request.POST.getlist("parklar")

            with transaction.atomic():
                # Mevcut atamaları sil
                ParkPersonel.objects.filter(personel=personel).delete()

                # Yeni atamaları oluştur
                for park_id in secili_parklar:
                    park = Park.objects.get(id=park_id)
                    ParkPersonel.objects.create(personel=personel, park=park)

            messages.success(request, f"{len(secili_parklar)} park başarıyla atandı.")

            # Güncel atanmış parkları döndür
            atanmis_parklar = personel.park_personeller.select_related(
                "park__mahalle", "park__park_tipi"
            ).order_by("park__ad")

            return render(
                request,
                "istakip/partials/atanmis_parklar.html",
                {"atanmis_parklar": atanmis_parklar, "personel": personel},
            )

        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    # GET isteği - park seçim formu
    mahalle_filter = request.GET.get("mahalle", "")
    search_query = request.GET.get("search", "").strip()

    # Tüm parklar
    parklar = Park.objects.select_related("mahalle", "park_tipi").order_by(
        "mahalle__ad", "ad"
    )

    # Filtreleme
    if mahalle_filter:
        parklar = parklar.filter(mahalle_id=mahalle_filter)

    if search_query:
        parklar = parklar.filter(
            Q(ad__icontains=search_query) | Q(mahalle__ad__icontains=search_query)
        )

    # Atanmış parklar bilgisi
    atanmis_parklar = set(
        ParkPersonel.objects.filter(personel=personel).values_list("park_id", flat=True)
    )

    # Başka personellere atanmış parklar
    diger_atamalar = {}
    for atama in ParkPersonel.objects.exclude(personel=personel).select_related(
        "personel", "park"
    ):
        if atama.park_id not in diger_atamalar:
            diger_atamalar[atama.park_id] = []
        diger_atamalar[atama.park_id].append(atama.personel.ad)

    # Mahalleler
    mahalleler = Mahalle.objects.select_related("ilce").order_by("ilce__ad", "ad")

    context = {
        "personel": personel,
        "parklar": parklar,
        "atanmis_parklar": atanmis_parklar,
        "diger_atamalar": diger_atamalar,
        "mahalleler": mahalleler,
        "mahalle_filter": mahalle_filter,
        "search_query": search_query,
    }

    return render(request, "istakip/partials/park_atama_form.html", context)


from django.http import HttpResponse


@login_required
@require_http_methods(["DELETE"])
def park_atama_sil_htmx(request, atama_uuid):
    """HTMX ile park atamasını silme işlemi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    try:
        # ParkPersonel kaydını bul ve sil
        atama = get_object_or_404(ParkPersonel, uuid=atama_uuid)
        personel = atama.personel
        atama.delete()

        # Güncel park listesini döndür
        sorumlu_parklar = personel.park_personeller.select_related(
            "park__mahalle", "park__park_tipi"
        ).order_by("park__ad")

        messages.success(request, f"'{atama.park.ad}' parkı başarıyla kaldırıldı.")

        return render(
            request,
            "istakip/partials/kullanici_parklar.html",
            {
                "personel": personel,
                "sorumlu_parklar": sorumlu_parklar,
            },
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})
