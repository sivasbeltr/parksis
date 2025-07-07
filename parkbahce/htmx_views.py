import json
from datetime import datetime, timedelta

from django.db import models
from django.db.models import Count, Sum
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from auth.decorators import roles_required

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


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
def quick_actions_htmx(request):
    """Hızlı işlemler bileşeni"""
    if request.htmx:
        return render(request, "dashboard/partials/quick_actions.html")
    return render(request, "dashboard/partials/loading_error.html")


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
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
    )  # Park istatistikleri
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

    # Park personellerini getir
    try:
        from istakip.models import ParkPersonel

        park_personelleri = (
            ParkPersonel.objects.filter(park=park)
            .select_related("personel", "personel__user")
            .order_by("-atama_tarihi")
        )
    except ImportError:
        park_personelleri = []

    context = {
        "park": park,
        "park_stats": park_stats,
        "park_personelleri": park_personelleri,
    }

    return render(request, "parkbahce/partials/park_detail_modal.html", context)


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
@require_http_methods(["GET"])
def park_aboneler_tab_htmx(request, park_uuid):
    """Park aboneler sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)

    # Aboneleri endeks bilgileri ile birlikte getir - en son endeks üstte olacak şekilde
    from .models import AboneEndeks

    aboneler = park.aboneler.prefetch_related(
        models.Prefetch(
            "endeksler", queryset=AboneEndeks.objects.order_by("-endeks_degeri")
        )
    ).order_by("abone_tipi", "abone_no")

    # AboneTipChoices'dan abone tipi istatistikleri
    from .models import AboneTipChoices

    abone_stats = {choice[0]: 0 for choice in AboneTipChoices.choices}

    for abone in aboneler:
        if abone.abone_tipi in abone_stats:
            abone_stats[abone.abone_tipi] += 1

    context = {
        "park": park,
        "aboneler": aboneler,
        "abone_stats": abone_stats,
    }

    return render(request, "parkbahce/tabs/park_aboneler_tab.html", context)


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
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


@roles_required("admin", "mudur", "ofis")
@require_http_methods(["GET"])
def park_istatistikler_tab_htmx(request, park_uuid):
    """Park istatistikleri sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)  # Temel istatistikler
    from datetime import datetime, timedelta

    from django.db.models import Avg, Count, Sum

    from .models import AboneEndeks

    # Son 12 ay tarihi (tüm hesaplamalar için ortak)
    son_yil = datetime.now() - timedelta(days=365)

    # Yeşil alan istatistikleri
    yesil_alan_stats = {
        "toplam_alan": park.yesil_alanlar.aggregate(total=Sum("alan"))["total"] or 0,
        "adet": park.yesil_alanlar.count(),
    }  # Habitat istatistikleri
    habitat_stats = {
        "toplam_adet": park.habitatlar.count(),
        "cesit_sayisi": park.habitatlar.values("habitat_tipi").distinct().count(),
    }

    # Habitat yoğunluğu hesaplama
    if yesil_alan_stats["toplam_alan"] > 0 and habitat_stats["toplam_adet"] > 0:
        habitat_stats["habitat_yogunlugu"] = (
            habitat_stats["toplam_adet"] / yesil_alan_stats["toplam_alan"]
        )
        habitat_stats["yesil_alan_verimliligi"] = (
            habitat_stats["toplam_adet"] * 100
        ) / yesil_alan_stats["toplam_alan"]
    else:
        habitat_stats["habitat_yogunlugu"] = 0
        habitat_stats["yesil_alan_verimliligi"] = 0

    # Su abonesi istatistikleri (varsa)
    su_aboneleri = park.aboneler.filter(abone_tipi="su")
    su_tuketim_stats = {
        "toplam_abone": su_aboneleri.count(),
        "aylik_ortalama": 0,
        "yillik_toplam": 0,
        "m2_aylik": 0,
        "m2_yillik": 0,
    }
    if su_aboneleri.exists():
        endeksler = AboneEndeks.objects.filter(
            park_abone__in=su_aboneleri, endeks_tarihi__gte=son_yil
        ).order_by("park_abone", "endeks_tarihi")

        # Tüketim hesaplama
        tuketimler = []
        for abone in su_aboneleri:
            abone_endeksleri = endeksler.filter(park_abone=abone).order_by(
                "endeks_tarihi"
            )
            if abone_endeksleri.count() >= 2:
                for i in range(1, len(abone_endeksleri)):
                    tuketim = (
                        abone_endeksleri[i].endeks_degeri
                        - abone_endeksleri[i - 1].endeks_degeri
                    )
                    if tuketim > 0:
                        tuketimler.append(tuketim)

        if tuketimler:
            su_tuketim_stats["aylik_ortalama"] = sum(tuketimler) / len(tuketimler)
            su_tuketim_stats["yillik_toplam"] = sum(tuketimler)

            # Yeşil alan başına tüketim
            if yesil_alan_stats["toplam_alan"] > 0:
                su_tuketim_stats["m2_aylik"] = (
                    su_tuketim_stats["aylik_ortalama"] / yesil_alan_stats["toplam_alan"]
                )
                su_tuketim_stats["m2_yillik"] = (
                    su_tuketim_stats["yillik_toplam"] / yesil_alan_stats["toplam_alan"]
                )

    # Elektrik abonesi istatistikleri (varsa)
    elektrik_aboneleri = park.aboneler.filter(abone_tipi="elektrik")
    elektrik_tuketim_stats = {
        "toplam_abone": elektrik_aboneleri.count(),
        "aylik_ortalama": 0,
        "yillik_toplam": 0,
        "oyun_alani_orani": 0,
    }

    if elektrik_aboneleri.exists():
        # Oyun alanları sayısı
        oyun_alani_sayisi = park.oyun_alanlar.count() + park.oyun_gruplari.count()

        # Elektrik tüketimi hesaplama (benzer mantık)
        elektrik_endeksleri = AboneEndeks.objects.filter(
            park_abone__in=elektrik_aboneleri, endeks_tarihi__gte=son_yil
        ).order_by("park_abone", "endeks_tarihi")

        elektrik_tuketimler = []
        for abone in elektrik_aboneleri:
            abone_endeksleri = elektrik_endeksleri.filter(park_abone=abone).order_by(
                "endeks_tarihi"
            )
            if abone_endeksleri.count() >= 2:
                for i in range(1, len(abone_endeksleri)):
                    tuketim = (
                        abone_endeksleri[i].endeks_degeri
                        - abone_endeksleri[i - 1].endeks_degeri
                    )
                    if tuketim > 0:
                        elektrik_tuketimler.append(tuketim)

        if elektrik_tuketimler:
            elektrik_tuketim_stats["aylik_ortalama"] = sum(elektrik_tuketimler) / len(
                elektrik_tuketimler
            )
            elektrik_tuketim_stats["yillik_toplam"] = sum(elektrik_tuketimler)

            # Oyun alanı başına elektrik tüketimi
            if oyun_alani_sayisi > 0:
                elektrik_tuketim_stats["oyun_alani_orani"] = (
                    elektrik_tuketim_stats["aylik_ortalama"] / oyun_alani_sayisi
                )

    # Ek istatistikler hesapla
    ek_istatistikler = {
        "toplam_alan": park.alan or 0,
        "toplam_donati": park.donatilar.count(),
        "toplam_oyun_grubu": park.oyun_gruplari.count(),
        "sulama_nokta_sayisi": park.sulama_noktalari.count(),
        "elektrik_nokta_sayisi": park.elektrik_noktalar.count(),
    }

    # Sulama sistemi verimliliği
    if (
        ek_istatistikler["sulama_nokta_sayisi"] > 0
        and yesil_alan_stats["toplam_alan"] > 0
    ):
        ek_istatistikler["m2_basina_sulama_noktasi"] = (
            yesil_alan_stats["toplam_alan"] / ek_istatistikler["sulama_nokta_sayisi"]
        )
    else:
        ek_istatistikler["m2_basina_sulama_noktasi"] = 0

    # Oyun grubu yoğunluğu
    if (
        ek_istatistikler["toplam_alan"] > 0
        and ek_istatistikler["toplam_oyun_grubu"] > 0
    ):
        ek_istatistikler["hectar_basina_oyun_grubu"] = (
            ek_istatistikler["toplam_oyun_grubu"] * 10000
        ) / ek_istatistikler["toplam_alan"]
    else:
        ek_istatistikler["hectar_basina_oyun_grubu"] = 0

    # Donatı yoğunluğu
    if ek_istatistikler["toplam_alan"] > 0 and ek_istatistikler["toplam_donati"] > 0:
        ek_istatistikler["m2_basina_donati"] = (
            ek_istatistikler["toplam_alan"] / ek_istatistikler["toplam_donati"]
        )
    else:
        ek_istatistikler["m2_basina_donati"] = 0

    context = {
        "park": park,
        "yesil_alan_stats": yesil_alan_stats,
        "habitat_stats": habitat_stats,
        "su_tuketim_stats": su_tuketim_stats,
        "elektrik_tuketim_stats": elektrik_tuketim_stats,
        "ek_istatistikler": ek_istatistikler,
    }

    return render(request, "parkbahce/tabs/park_istatistikler_tab.html", context)


@roles_required("admin", "mudur", "ofis")
@require_http_methods(["GET"])
def park_sorumlu_tab_htmx(request, park_uuid):
    """Park sorumlu bilgileri sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)

    # Park personellerini getir
    from istakip.models import ParkPersonel, Personel

    park_personelleri = (
        ParkPersonel.objects.filter(park=park)
        .select_related("personel", "personel__user")
        .order_by("-atama_tarihi")
    )

    # Atanabilir personelleri getir (aktif ve henüz atanmamış)
    atanmis_personel_ids = park_personelleri.values_list("personel_id", flat=True)
    atanabilir_personeller = (
        Personel.objects.filter(aktif=True)
        .exclude(id__in=atanmis_personel_ids)
        .select_related("user")
        .order_by("ad")
    )

    context = {
        "park": park,
        "park_personelleri": park_personelleri,
        "atanabilir_personeller": atanabilir_personeller,
    }

    return render(request, "parkbahce/tabs/park_sorumlu_tab.html", context)


@roles_required("admin", "mudur", "ofis")
@require_http_methods(["GET"])
def park_sorun_gecmisi_tab_htmx(request, park_uuid):
    """Park sorun geçmişi sekmesi"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    park = get_object_or_404(Park, uuid=park_uuid)

    # Son 30 günlük timeline oluştur
    from datetime import datetime, timedelta

    from django.db.models import Count

    from istakip.models import GunlukKontrol

    # Son 30 günün tarih listesini oluştur
    bugun = datetime.now().date()
    baslangic_tarihi = bugun - timedelta(days=29)  # 30 gün (bugün dahil)

    # Tüm günleri listele (bugünden geriye doğru)
    gun_listesi = []
    for i in range(30):
        tarih = bugun - timedelta(days=i)
        gun_listesi.append(tarih)

    # Bu tarihlerdeki kontrolleri al
    kontroller = (
        GunlukKontrol.objects.filter(
            park=park,
            kontrol_tarihi__date__gte=baslangic_tarihi,
            kontrol_tarihi__date__lte=bugun,
        )
        .select_related("personel")
        .prefetch_related("resimler")
        .order_by("-kontrol_tarihi")
    )

    # Tarihe göre gruplama
    from collections import defaultdict

    tarih_gruplar = defaultdict(list)
    for kontrol in kontroller:
        tarih_gruplar[kontrol.kontrol_tarihi.date()].append(kontrol)

    # Timeline verisi oluştur (tüm günler için)
    gunluk_kontrol_timeline = []
    for tarih in gun_listesi:
        gunluk_kontrol_timeline.append(
            {
                "tarih": tarih,
                "kontroller": tarih_gruplar[
                    tarih
                ],  # Eğer o gün kontrol yoksa boş liste
            }
        )

    # Durum istatistikleri - son 30 günlük
    durum_stats_query = GunlukKontrol.objects.filter(
        park=park,
        kontrol_tarihi__date__gte=baslangic_tarihi,
        kontrol_tarihi__date__lte=bugun,
    )

    # Tüm durumlar için sayıları hesapla
    durum_stats = {
        "sorun_yok": durum_stats_query.filter(durum="sorun_yok").count(),
        "sorun_var": durum_stats_query.filter(durum="sorun_var").count(),
        "acil": durum_stats_query.filter(durum="acil").count(),
        "gozden_gecirildi": durum_stats_query.filter(durum="gozden_gecirildi").count(),
        "ise_donusturuldu": durum_stats_query.filter(durum="ise_donusturuldu").count(),
        "cozuldu": durum_stats_query.filter(durum="cozuldu").count(),
    }

    # Toplam kontrol sayısı
    toplam_kontrol = sum(durum_stats.values())

    context = {
        "park": park,
        "gunluk_kontrol_timeline": gunluk_kontrol_timeline,
        "durum_stats": durum_stats,
        "toplam_kontrol": toplam_kontrol,
        "baslangic_tarihi": baslangic_tarihi,
        "bitis_tarihi": bugun,
    }

    return render(request, "parkbahce/tabs/park_sorun_gecmisi_tab.html", context)


@roles_required("admin", "mudur", "ofis")
@require_http_methods(["GET"])
def gorev_detail_htmx(request, gorev_uuid):
    """Görev detay bilgilerini HTMX ile getir"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    try:
        from istakip.models import Gorev

        gorev = get_object_or_404(
            Gorev.objects.select_related(
                "park", "park__mahalle", "gorev_tipi", "olusturan", "gunluk_kontrol"
            ).prefetch_related(
                "atanan_personeller",
                "asamalar",
                "tamamlama_resimleri",
                "denetim_kayitlari",
            ),
            uuid=gorev_uuid,
        )

        # Görev istatistikleri
        gorev_stats = {
            "atanan_personel_sayisi": gorev.atanan_personeller.count(),
            "asama_sayisi": gorev.asamalar.count(),
            "tamamlanan_asama_sayisi": gorev.asamalar.filter(
                durum="tamamlandi"
            ).count(),
            "devam_eden_asama_sayisi": gorev.asamalar.filter(
                durum="devam_ediyor"
            ).count(),
            "resim_sayisi": gorev.tamamlama_resimleri.count(),
            "denetim_kaydi_sayisi": gorev.denetim_kayitlari.count(),
        }

        # Durum rengini al
        from istakip.choices import get_gorev_durum_color, get_gorev_oncelik_color

        durum_color = get_gorev_durum_color(gorev.durum)
        oncelik_color = get_gorev_oncelik_color(gorev.oncelik)

        # İlerleme yüzdesi hesapla
        if gorev_stats["asama_sayisi"] > 0:
            ilerleme_yuzdesi = int(
                (gorev_stats["tamamlanan_asama_sayisi"] / gorev_stats["asama_sayisi"])
                * 100
            )
        else:
            ilerleme_yuzdesi = (
                0
                if gorev.durum == "planlanmis"
                else (100 if gorev.durum == "tamamlandi" else 50)
            )

        context = {
            "gorev": gorev,
            "gorev_stats": gorev_stats,
            "durum_color": durum_color,
            "oncelik_color": oncelik_color,
            "ilerleme_yuzdesi": ilerleme_yuzdesi,
        }

        return render(request, "istakip/partials/gorev_detail_modal.html", context)

    except Exception as e:
        print(f"Görev detayı yüklenirken hata: {e}")
        return HttpResponseBadRequest("Görev bulunamadı.")


@roles_required("admin", "mudur", "ofis")
@require_http_methods(["GET"])
def kontrol_detail_htmx(request, kontrol_uuid):
    """Günlük kontrol detay bilgilerini HTMX ile getir"""
    if not request.htmx:
        return HttpResponseBadRequest("Bu endpoint sadece HTMX istekleri için.")

    try:
        from istakip.models import GunlukKontrol

        kontrol = get_object_or_404(
            GunlukKontrol.objects.select_related(
                "park", "park__mahalle", "personel", "personel__user"
            ).prefetch_related("resimler", "ilgili_gorevler"),
            uuid=kontrol_uuid,
        )

        # Kontrol istatistikleri
        kontrol_stats = {
            "resim_sayisi": kontrol.resimler.count(),
            "ilgili_gorev_sayisi": kontrol.ilgili_gorevler.count(),
            "konum_var": bool(kontrol.geom),
        }

        # Durum rengini al
        from istakip.choices import get_kontrol_durum_color

        durum_color = get_kontrol_durum_color(kontrol.durum)

        # Kontrol sonrası oluşturulan görevler
        ilgili_gorevler = kontrol.ilgili_gorevler.select_related("gorev_tipi").order_by(
            "-created_at"
        )[:3]

        # Aynı parkta son kontroller (son 5 kontrol)
        son_kontroller = (
            GunlukKontrol.objects.filter(park=kontrol.park)
            .exclude(uuid=kontrol.uuid)
            .select_related("personel")
            .order_by("-kontrol_tarihi")[:5]
        )

        context = {
            "kontrol": kontrol,
            "kontrol_stats": kontrol_stats,
            "durum_color": durum_color,
            "ilgili_gorevler": ilgili_gorevler,
            "son_kontroller": son_kontroller,
        }

        return render(request, "istakip/partials/kontrol_detail_modal.html", context)

    except Exception as e:
        print(f"Kontrol detayı yüklenirken hata: {e}")
        return HttpResponseBadRequest("Kontrol bulunamadı.")
