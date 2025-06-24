from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import EndeksForm, ParkAboneForm
from .models import Park, ParkAbone


def abonelik_takibi(request):
    """Abonelik takibi sayfası"""

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


@login_required
def abone_ekle(request, park_uuid=None):
    """Yeni abone ekleme sayfası"""
    park = None
    if park_uuid:
        park = get_object_or_404(Park, uuid=park_uuid)

    if request.method == "POST":
        form = ParkAboneForm(request.POST, park_uuid=park_uuid)
        if form.is_valid():
            abone = form.save()
            messages.success(
                request,
                f"{abone.get_abone_tipi_display()} abonesi başarıyla eklendi.",
            )

            # Eğer park belirtilmişse park detayına, değilse abone detayına yönlendir
            if park:
                return redirect("parkbahce:park_detail", park_uuid=park.uuid)
            else:
                return redirect("parkbahce:abone_detail", abone_uuid=abone.uuid)
    else:
        initial_data = {}
        if park:
            initial_data["park"] = park
            initial_data["abone_tarihi"] = timezone.now().date()

        form = ParkAboneForm(initial=initial_data, park_uuid=park_uuid)

    context = {
        "form": form,
        "park": park,
        "page_title": f"Yeni Abone Ekle{f' - {park.ad}' if park else ''}",
    }

    return render(request, "parkbahce/abone_ekle.html", context)


def abone_detail(request, abone_uuid):
    """Abone detay sayfası - endeks geçmişi ile birlikte"""

    abone = get_object_or_404(ParkAbone, uuid=abone_uuid)

    # Son 12 aylık endeks kayıtları (en son eklenen üstte)
    endeksler = abone.endeksler.order_by("-endeks_degeri")[:12]

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


@login_required
def endeks_ekle(request, abone_uuid):
    """Abone için yeni endeks ekleme sayfası"""
    abone = get_object_or_404(ParkAbone, uuid=abone_uuid)

    # Son 5 endeks kaydını form sayfasında göstermek için
    son_endeksler = abone.endeksler.order_by("-endeks_degeri")[:5]

    if request.method == "POST":
        form = EndeksForm(request.POST, park_abone=abone)
        if form.is_valid():
            endeks = form.save(commit=False)
            endeks.park_abone = abone
            endeks.save()

            messages.success(
                request,
                f"✅ {abone.get_abone_tipi_display()} abonesi ({abone.abone_no}) için "
                f"endeks değeri {endeks.endeks_degeri} başarıyla eklendi. "
                f"Okuma tarihi: {endeks.endeks_tarihi.strftime('%d.%m.%Y')}",
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


@login_required
def abone_duzenle(request, abone_uuid):
    """Abone düzenleme sayfası"""
    abone = get_object_or_404(ParkAbone, uuid=abone_uuid)

    if request.method == "POST":
        form = ParkAboneForm(request.POST, instance=abone)
        if form.is_valid():
            form.save()
            messages.success(request, "Abone bilgileri başarıyla güncellendi.")
            return redirect("parkbahce:abone_detail", abone_uuid=abone.uuid)
    else:
        form = ParkAboneForm(instance=abone)

    context = {
        "form": form,
        "abone": abone,
        "page_title": f"Abone Düzenle - {abone.get_abone_tipi_display()}",
    }

    return render(request, "parkbahce/abone_duzenle.html", context)


@login_required
def abone_sil(request, abone_uuid):
    """Abone silme işlemi"""
    abone = get_object_or_404(ParkAbone, uuid=abone_uuid)
    park_uuid = abone.park.uuid

    if request.method == "POST":
        abone_ad = f"{abone.park.ad} - {abone.get_abone_tipi_display()}"
        abone.delete()
        messages.success(request, f"{abone_ad} abonesi başarıyla silindi.")
        return redirect("parkbahce:park_detail", park_uuid=park_uuid)

    context = {
        "abone": abone,
    }

    return render(request, "parkbahce/abone_sil_confirm.html", context)
