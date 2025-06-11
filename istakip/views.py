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
def kullanici_list(request):
    """Kullanıcı listesi sayfası"""

    # Filtreleme ve arama
    search_query = request.GET.get("search", "").strip()
    grup_filter = request.GET.get("grup", "")
    aktif_filter = request.GET.get("aktif", "")
    sort_by = request.GET.get("sort", "ad")
    sort_direction = request.GET.get("direction", "asc")

    # Temel queryset
    kullanicilar = Personel.objects.select_related("user").prefetch_related(
        "user__groups", "park_personeller__park"
    )

    # Arama
    if search_query:
        kullanicilar = kullanicilar.filter(
            Q(ad__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(eposta__icontains=search_query)
            | Q(telefon__icontains=search_query)
        )

    # Filtreleme
    if grup_filter:
        kullanicilar = kullanicilar.filter(user__groups=grup_filter)

    if aktif_filter:
        is_active = aktif_filter == "true"
        kullanicilar = kullanicilar.filter(aktif=is_active)

    # Sıralama
    if sort_direction == "desc":
        sort_by = f"-{sort_by}"

    valid_sorts = ["ad", "user__username", "created_at", "aktif"]
    if sort_by.lstrip("-") in valid_sorts:
        kullanicilar = kullanicilar.order_by(sort_by)
    else:
        kullanicilar = kullanicilar.order_by("ad")

    # Sayfalama
    per_page = request.GET.get("per_page", 15)
    try:
        per_page = int(per_page)
        if per_page not in [10, 15, 25, 50]:
            per_page = 15
    except (ValueError, TypeError):
        per_page = 15

    paginator = Paginator(kullanicilar, per_page)
    page_number = request.GET.get("page")
    kullanicilar_page = paginator.get_page(page_number)

    # Filtre seçenekleri
    gruplar = Group.objects.all().order_by("name")

    context = {
        "kullanicilar": kullanicilar_page,
        "search_query": search_query,
        "grup_filter": grup_filter,
        "aktif_filter": aktif_filter,
        "sort_by": request.GET.get("sort", "ad"),
        "sort_direction": sort_direction,
        "per_page": per_page,
        "gruplar": gruplar,
        "total_kullanicilar": kullanicilar.count(),
    }

    return render(request, "istakip/kullanici_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def kullanici_create(request):
    """Yeni kullanıcı oluşturma"""

    if request.method == "POST":
        form = PersonelKullaniciForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Kullanıcı oluştur
                    user = User.objects.create_user(
                        username=form.cleaned_data["kullanici_adi"],
                        email=form.cleaned_data["eposta"],
                        password=form.cleaned_data["sifre"],
                        first_name=form.cleaned_data["first_name"],
                        last_name=form.cleaned_data["last_name"],
                        is_active=form.cleaned_data["is_active"],
                    )

                    # Personel oluştur
                    personel = Personel.objects.create(
                        user=user,
                        ad=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",
                        telefon=form.cleaned_data["telefon"],
                        eposta=form.cleaned_data["eposta"],
                        pozisyon=form.cleaned_data["pozisyon"],
                        aktif=form.cleaned_data["is_active"],
                    )

                    # Grupları ata
                    if form.cleaned_data["groups"]:
                        user.groups.set(form.cleaned_data["groups"])

                    messages.success(request, f"{personel.ad} başarıyla oluşturuldu.")
                    return redirect(
                        "istakip:kullanici_detail", personel_uuid=personel.uuid
                    )

            except Exception as e:
                messages.error(request, f"Kullanıcı oluşturulurken hata: {str(e)}")
    else:
        form = PersonelKullaniciForm()

    context = {"form": form, "title": "Yeni Kullanıcı Oluştur"}

    return render(request, "istakip/kullanici_form.html", context)


@login_required
def kullanici_detail(request, personel_uuid):
    """Kullanıcı detay sayfası"""

    personel = get_object_or_404(
        Personel.objects.select_related("user").prefetch_related(
            "user__groups",
            "park_personeller__park__mahalle",
            "gunluk_kontroller",
            "atanan_gorevler",
        ),
        uuid=personel_uuid,
    )

    # İstatistikler
    bugun = timezone.now().date()
    bu_hafta_baslangic = bugun - timedelta(days=bugun.weekday())
    bu_ay_baslangic = bugun.replace(day=1)

    stats = {
        "toplam_kontrol": personel.gunluk_kontroller.count(),
        "bugun_kontrol": personel.gunluk_kontroller.filter(
            kontrol_tarihi__date=bugun
        ).count(),
        "bu_hafta_kontrol": personel.gunluk_kontroller.filter(
            kontrol_tarihi__date__gte=bu_hafta_baslangic
        ).count(),
        "bu_ay_kontrol": personel.gunluk_kontroller.filter(
            kontrol_tarihi__date__gte=bu_ay_baslangic
        ).count(),
        "toplam_sorun": personel.gunluk_kontroller.filter(
            durum__in=["sorun_var", "acil"]
        ).count(),
        "bekleyen_gorevler": personel.atanan_gorevler.filter(
            durum="devam_ediyor"
        ).count(),
        "tamamlanan_gorevler": personel.atanan_gorevler.filter(
            durum="tamamlandi"
        ).count(),
        "sorumlu_park_sayisi": personel.park_personeller.count(),
    }

    # Son kontroller
    son_kontroller = personel.gunluk_kontroller.select_related("park").order_by(
        "-kontrol_tarihi"
    )[:10]

    # Son görevler
    son_gorevler = personel.atanan_gorevler.select_related("park").order_by(
        "-created_at"
    )[:5]

    # Performans analizi
    if stats["toplam_kontrol"] > 0:
        sorun_orani = (stats["toplam_sorun"] / stats["toplam_kontrol"]) * 100
    else:
        sorun_orani = 0

    # Sorumlu parkları ekle
    sorumlu_parklar = personel.park_personeller.select_related(
        "park__mahalle", "park__park_tipi"
    ).order_by("park__ad")

    context = {
        "personel": personel,
        "stats": stats,
        "son_kontroller": son_kontroller,
        "son_gorevler": son_gorevler,
        "sorun_orani": round(sorun_orani, 1),
        "sorumlu_parklar": sorumlu_parklar,
    }

    return render(request, "istakip/kullanici_detail.html", context)
