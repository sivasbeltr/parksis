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
                ParkPersonel.objects.filter(
                    personel=personel
                ).delete()  # Yeni atamaları oluştur
                for park_id in secili_parklar:
                    park = Park.objects.get(id=park_id)
                    ParkPersonel.objects.create(personel=personel, park=park)

            messages.success(request, f"{len(secili_parklar)} park başarıyla atandı.")

            # Güncel sorumlu parkları döndür
            sorumlu_parklar = personel.park_personeller.select_related(
                "park__mahalle", "park__park_tipi"
            ).order_by("park__ad")

            return render(
                request,
                "istakip/partials/kullanici_parklar.html",
                {"personel": personel, "sorumlu_parklar": sorumlu_parklar},
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": str(e)}
            )  # GET isteği - park seçim formu
    mahalle_filter = request.GET.get("mahalle", "")
    search_query = request.GET.get("search", "").strip()
    atama_durumu_filter = request.GET.get("atama_durumu", "")

    # Tüm parklar - geom alanını defer ile performans optimizasyonu
    parklar = (
        Park.objects.select_related("mahalle", "park_tipi")
        .defer("geom")
        .order_by("mahalle__ad", "ad")
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

    # Atama durumu filtrelemesi
    if atama_durumu_filter:
        if atama_durumu_filter == "atanmis":
            # Sadece bu kullanıcıya atanmış parklar
            parklar = parklar.filter(id__in=atanmis_parklar)
        elif atama_durumu_filter == "atanmamis":
            # Bu kullanıcıya atanmamış parklar
            parklar = parklar.exclude(id__in=atanmis_parklar)
        elif atama_durumu_filter == "baska_atanmis":
            # Başka kullanıcıya atanmış parklar
            diger_atanan_park_ids = set(diger_atamalar.keys())
            parklar = parklar.filter(id__in=diger_atanan_park_ids)
        elif atama_durumu_filter == "hic_atanmamis":
            # Hiç kimseye atanmamış parklar
            tum_atanan_park_ids = set(atanmis_parklar).union(set(diger_atamalar.keys()))
            parklar = parklar.exclude(id__in=tum_atanan_park_ids)  # Mahalleler
    mahalleler = Mahalle.objects.select_related("ilce").order_by("ilce__ad", "ad")

    context = {
        "personel": personel,
        "parklar": parklar,
        "atanmis_parklar": list(atanmis_parklar),  # Set'i liste'ye çevir
        "diger_atamalar": diger_atamalar,
        "mahalleler": mahalleler,
        "mahalle_filter": mahalle_filter,
        "search_query": search_query,
        "atama_durumu_filter": atama_durumu_filter,
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


@login_required
def gorev_asamalar_htmx(request, gorev_uuid):
    """Görev aşamalarını HTMX ile getir"""
    gorev = get_object_or_404(
        Gorev.objects.prefetch_related("asamalar"), uuid=gorev_uuid
    )  # Yeni aşama ekleme
    if request.method == "POST":
        try:
            baslik = request.POST.get("baslik")
            aciklama = request.POST.get("aciklama", "")

            if not baslik:
                return HttpResponse("Aşama başlığı zorunludur.", status=400)

            GorevAsama.objects.create(
                gorev=gorev,
                ad=baslik,
                aciklama=aciklama,
                durum="beklemede",
            )

            # Aşamaları yeniden getir
            asamalar = gorev.asamalar.all().order_by("created_at")
            return render(
                request,
                "istakip/htmx/gorev_asamalar.html",
                {"gorev": gorev, "asamalar": asamalar},
            )

        except Exception as e:
            return HttpResponse(f"Hata: {str(e)}", status=400)

    # GET request
    asamalar = gorev.asamalar.all().order_by("created_at")
    return render(
        request,
        "istakip/htmx/gorev_asamalar.html",
        {"gorev": gorev, "asamalar": asamalar},
    )


@login_required
def gorev_durum_guncelle_htmx(request, gorev_uuid):
    gorev = get_object_or_404(Gorev, uuid=gorev_uuid)

    if request.method == "POST":
        try:
            yeni_durum = request.POST.get("durum")
            not_text = request.POST.get("not", "")

            if not yeni_durum:
                return render(
                    request,
                    "istakip/htmx/gorev_durum.html",
                    {
                        "gorev": gorev,
                        "success_message": "Durum seçimi zorunludur.",
                    },
                )

            valid_durumlar = ["planlanmis", "devam_ediyor", "tamamlandi", "iptal"]
            if yeni_durum not in valid_durumlar:
                return render(
                    request,
                    "istakip/htmx/gorev_durum.html",
                    {
                        "gorev": gorev,
                        "success_message": "Geçersiz durum.",
                    },
                )

            eski_durum = gorev.durum
            gorev.durum = yeni_durum

            if yeni_durum == "tamamlandi" and not gorev.tamamlanma_tarihi:
                gorev.tamamlanma_tarihi = timezone.now()

            gorev.save()

            return render(
                request,
                "istakip/htmx/gorev_durum.html",
                {
                    "gorev": gorev,
                    "success_message": f"Görev durumu '{gorev.get_durum_display()}' olarak güncellendi.",
                },
            )
        except Exception as e:
            return render(
                request,
                "istakip/htmx/gorev_durum.html",
                {
                    "gorev": gorev,
                    "success_message": f"Hata: {str(e)}",
                },
            )

    # GET request
    edit_mode = request.GET.get("edit", "false") == "true"
    if edit_mode:
        return render(request, "istakip/htmx/gorev_durum_form.html", {"gorev": gorev})
    else:
        return render(request, "istakip/htmx/gorev_durum.html", {"gorev": gorev})


@login_required
@require_http_methods(["POST"])
def gorev_asama_baslat_htmx(request, asama_uuid):
    """Görev aşamasını başlat"""
    from .models import GorevAsama

    try:
        asama = get_object_or_404(GorevAsama, uuid=asama_uuid)

        # Sadece beklemede olan aşamalar başlatılabilir
        if asama.durum != "beklemede":
            return HttpResponse("Bu aşama zaten başlatılmış.", status=400)

        # Aşamayı başlat
        asama.durum = "devam_ediyor"
        asama.baslangic_tarihi = timezone.now()
        asama.save()  # Ana görevi de devam ediyor yap (eğer planlanmış ise)
        if asama.gorev.durum == "planlanmis":
            asama.gorev.durum = "devam_ediyor"
            asama.gorev.save()

        # Aşamaları yeniden getir
        asamalar = asama.gorev.asamalar.all().order_by("created_at")
        return render(
            request,
            "istakip/htmx/gorev_asamalar.html",
            {"gorev": asama.gorev, "asamalar": asamalar},
        )

    except Exception as e:
        return HttpResponse(f"Hata: {str(e)}", status=400)


@login_required
@require_http_methods(["POST"])
def gorev_asama_tamamla_htmx(request, asama_uuid):
    """Görev aşamasını tamamla"""
    from .models import GorevAsama

    try:
        asama = get_object_or_404(GorevAsama, uuid=asama_uuid)

        # Sadece devam eden aşamalar tamamlanabilir
        if asama.durum != "devam_ediyor":
            return HttpResponse("Bu aşama tamamlanabilir durumda değil.", status=400)

        # Aşamayı tamamla
        asama.durum = "tamamlandi"
        asama.tamamlanma_tarihi = timezone.now()
        asama.save()

        # Tüm aşamalar tamamlandı mı kontrol et
        tum_asamalar = asama.gorev.asamalar.all()
        tamamlanan_asamalar = tum_asamalar.filter(durum="tamamlandi")
        if (
            tum_asamalar.count() > 0
            and tum_asamalar.count() == tamamlanan_asamalar.count()
        ):
            # Tüm aşamalar tamamlandıysa görevi de tamamla
            asama.gorev.durum = "tamamlandi"
            asama.gorev.tamamlanma_tarihi = timezone.now()
            asama.gorev.save()

        # Aşamaları yeniden getir
        asamalar = asama.gorev.asamalar.all().order_by("created_at")
        return render(
            request,
            "istakip/htmx/gorev_asamalar.html",
            {"gorev": asama.gorev, "asamalar": asamalar},
        )

    except Exception as e:
        return HttpResponse(f"Hata: {str(e)}", status=400)
