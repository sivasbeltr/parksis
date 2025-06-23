from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group, User
from django.contrib.gis.geos import Point
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, Q, Sum
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from ortak.models import Mahalle
from parkbahce.models import Park

from .forms import ParkPersonelAtamaForm, PersonelKullaniciForm
from .models import (
    Gorev,
    GorevAsama,
    GorevAtama,
    GorevTamamlamaResim,
    GorevTipi,
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
                    )  # Grupları ata
                    if form.cleaned_data["groups"]:
                        user.groups.set(form.cleaned_data["groups"])
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
    )  # İstatistikler
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
        "bekleyen_gorevler": Gorev.objects.filter(
            atamalar__personel=personel, durum__in=["planlanmis", "devam_ediyor"]
        )
        .distinct()
        .count(),
        "tamamlanan_gorevler": Gorev.objects.filter(
            atamalar__personel=personel, durum="tamamlandi"
        )
        .distinct()
        .count(),
        "toplam_gorevler": Gorev.objects.filter(atamalar__personel=personel)
        .distinct()
        .count(),
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


@login_required
@require_http_methods(["GET", "POST"])
def kullanici_edit(request, personel_uuid):
    """Kullanıcı bilgileri düzenleme"""
    personel = get_object_or_404(Personel, uuid=personel_uuid)

    if request.method == "POST":
        # Düzenleme modunda özel form validasyonu
        form = PersonelKullaniciForm(request.POST)

        # Şifre alanlarını opsiyonel yap
        form.fields["sifre"].required = False
        form.fields["sifre_tekrar"].required = False

        # Kullanıcı adı kontrolünü bypass et (readonly olduğu için)
        if form.is_valid():
            # Kullanıcı adı değişikliği kontrolü
            kullanici_adi = form.cleaned_data["kullanici_adi"]
            if kullanici_adi != personel.user.username:
                # Başka kullanıcı bu kullanıcı adını kullanıyor mu?
                if (
                    User.objects.filter(username=kullanici_adi)
                    .exclude(id=personel.user.id)
                    .exists()
                ):
                    messages.error(request, "Bu kullanıcı adı zaten kullanılıyor.")
                    form.add_error(
                        "kullanici_adi", "Bu kullanıcı adı zaten kullanılıyor."
                    )
                else:
                    # Kullanıcı adını güncelle
                    personel.user.username = kullanici_adi

            # Şifre kontrolü - sadece girilmişse güncelle
            sifre = form.cleaned_data.get("sifre")
            sifre_tekrar = form.cleaned_data.get("sifre_tekrar")

            if sifre and sifre_tekrar:
                if sifre != sifre_tekrar:
                    messages.error(request, "Şifreler eşleşmiyor.")
                    form.add_error("sifre_tekrar", "Şifreler eşleşmiyor.")
                elif len(sifre) < 6:
                    messages.error(request, "Şifre en az 6 karakter olmalıdır.")
                    form.add_error("sifre", "Şifre en az 6 karakter olmalıdır.")
                else:
                    # Şifreyi güncelle
                    personel.user.set_password(sifre)

            # Hata yoksa kaydet
            if not form.errors:
                try:
                    with transaction.atomic():
                        # Kullanıcı bilgilerini güncelle
                        user = personel.user
                        user.first_name = form.cleaned_data["first_name"]
                        user.last_name = form.cleaned_data["last_name"]
                        user.email = form.cleaned_data["eposta"]
                        user.is_active = form.cleaned_data["is_active"]
                        user.save()

                        # Personel bilgilerini güncelle
                        personel.ad = f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}"
                        personel.telefon = form.cleaned_data["telefon"]
                        personel.eposta = form.cleaned_data["eposta"]
                        personel.pozisyon = form.cleaned_data["pozisyon"]
                        personel.aktif = form.cleaned_data["is_active"]
                        personel.save()

                        # Grupları güncelle
                        if form.cleaned_data["groups"]:
                            user.groups.set(form.cleaned_data["groups"])

                        success_message = (
                            f"{personel.ad} bilgileri başarıyla güncellendi."
                        )
                        if sifre and sifre_tekrar:
                            success_message += " Şifre de değiştirildi."

                        messages.success(request, success_message)
                        return redirect(
                            "istakip:kullanici_detail", personel_uuid=personel.uuid
                        )

                except Exception as e:
                    messages.error(request, f"Kullanıcı güncellenirken hata: {str(e)}")
    else:
        # Formu mevcut verilerle doldur
        initial_data = {
            "kullanici_adi": personel.user.username,
            "eposta": personel.eposta,
            "first_name": personel.user.first_name,
            "last_name": personel.user.last_name,
            "telefon": personel.telefon,
            "pozisyon": personel.pozisyon,
            "is_active": personel.aktif,
            "groups": personel.user.groups.all(),
        }
        form = PersonelKullaniciForm(initial=initial_data)

        # Düzenleme modunda şifre alanlarını opsiyonel yap
        form.fields["sifre"].required = False
        form.fields["sifre_tekrar"].required = False
        form.fields["sifre"].help_text = (
            "Şifreyi değiştirmek istemiyorsanız boş bırakın."
        )
        form.fields["sifre_tekrar"].help_text = (
            "Şifreyi değiştirmek istemiyorsanız boş bırakın."
        )

    context = {
        "form": form,
        "personel": personel,
        "title": f"{personel.ad} - Bilgi Düzenleme",
        "is_edit": True,
    }
    return render(request, "istakip/kullanici_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def kullanici_password_change(request, personel_uuid):
    """Kullanıcı şifre değiştirme"""
    personel = get_object_or_404(Personel, uuid=personel_uuid)

    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        # Validasyonlar
        if not all([current_password, new_password, confirm_password]):
            messages.error(request, "Tüm alanları doldurunuz.")
        elif new_password != confirm_password:
            messages.error(request, "Yeni şifreler eşleşmiyor.")
        elif len(new_password) < 6:
            messages.error(request, "Şifre en az 6 karakter olmalıdır.")
        elif not personel.user.check_password(current_password):
            messages.error(request, "Mevcut şifre yanlış.")
        else:
            try:
                personel.user.set_password(new_password)
                personel.user.save()
                messages.success(
                    request, f"{personel.ad} şifresi başarıyla değiştirildi."
                )
                return redirect("istakip:kullanici_detail", personel_uuid=personel.uuid)
            except Exception as e:
                messages.error(request, f"Şifre değiştirilirken hata: {str(e)}")

    context = {
        "personel": personel,
        "title": f"{personel.ad} - Şifre Değiştir",
    }
    return render(request, "istakip/kullanici_password_change.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def kullanici_deactivate(request, personel_uuid):
    """Kullanıcı hesabını devre dışı bırakma"""
    personel = get_object_or_404(Personel, uuid=personel_uuid)

    # Sorumlu parklar
    sorumlu_parklar = personel.park_personeller.select_related("park").order_by(
        "park__ad"
    )

    if request.method == "POST":
        confirm = request.POST.get("confirm")
        remove_parks = request.POST.get("remove_parks") == "on"

        if confirm == "DEVRE_DISI":
            try:
                with transaction.atomic():
                    # Park sorumlulukları varsa ve kaldırılması istenmişse
                    if remove_parks and sorumlu_parklar.exists():
                        personel.park_personeller.all().delete()
                        messages.info(
                            request,
                            f"{sorumlu_parklar.count()} park sorumluluğu kaldırıldı.",
                        )

                    # Kullanıcıyı devre dışı bırak
                    personel.user.is_active = False
                    personel.aktif = False
                    personel.user.save()
                    personel.save()

                    messages.success(
                        request, f"{personel.ad} hesabı başarıyla devre dışı bırakıldı."
                    )
                    return redirect("istakip:kullanici_list")

            except Exception as e:
                messages.error(request, f"Hesap devre dışı bırakılırken hata: {str(e)}")
        else:
            messages.error(request, "Onay metni doğru girilmedi.")

    context = {
        "personel": personel,
        "sorumlu_parklar": sorumlu_parklar,
        "title": f"{personel.ad} - Hesabı Devre Dışı Bırak",
    }
    return render(request, "istakip/kullanici_deactivate.html", context)


@login_required
@require_http_methods(["GET", "POST"])
# bu metod deactivate metodından biraz farklı. Onay istemiyor ve aktif hale getiriyor. sonra da kullanıcı detayına yönlendiriyor. Herhangi bir şablon render etmiyor
def kullanici_activate(request, personel_uuid):
    """Kullanıcı hesabını aktif hale getirme"""
    personel = get_object_or_404(Personel, uuid=personel_uuid)

    try:
        with transaction.atomic():
            # Kullanıcıyı aktif hale getir
            personel.user.is_active = True
            personel.aktif = True
            personel.user.save()
            personel.save()

            messages.success(
                request, f"{personel.ad} hesabı başarıyla aktif hale getirildi."
            )
            return redirect("istakip:kullanici_detail", personel_uuid=personel.uuid)

    except Exception as e:
        messages.error(request, f"Hesap aktif hale getirilirken hata: {str(e)}")
        return redirect("istakip:kullanici_list")


@login_required
@require_http_methods(["POST"])
def park_personel_ata(request):
    """Park personel atama işlemi"""
    park_uuid = request.POST.get("park_uuid")
    personel_uuid = request.POST.get("personel_uuid")

    if not park_uuid or not personel_uuid:
        messages.error(request, "Gerekli parametreler eksik.")
        return redirect("istakip:kullanici_list")

    try:
        from parkbahce.models import Park

        park = get_object_or_404(Park, uuid=park_uuid)
        personel = get_object_or_404(Personel, uuid=personel_uuid)

        # Zaten atanmış mı kontrol et
        if ParkPersonel.objects.filter(park=park, personel=personel).exists():
            messages.warning(request, f"{personel.ad} zaten bu parka atanmış.")
        else:
            ParkPersonel.objects.create(
                park=park,
                personel=personel,
                gorev_aciklama=f"{park.ad} parkının bakım ve kontrolü",
            )
            messages.success(
                request, f"{personel.ad} başarıyla {park.ad} parkına atandı."
            )

        # HTMX request ise sorumlu sekmesini yeniden yükle
        if request.htmx:
            from parkbahce.htmx_views import park_sorumlu_tab_htmx

            return park_sorumlu_tab_htmx(request, park_uuid)

    except Exception as e:
        messages.error(request, f"Personel atama sırasında hata: {str(e)}")

    return redirect("parkbahce:park_detail", park_uuid=park_uuid)


@login_required
@require_http_methods(["DELETE"])
def park_personel_kaldir(request, atama_uuid):
    """Park personel kaldırma işlemi"""
    try:
        atama = get_object_or_404(ParkPersonel, uuid=atama_uuid)
        park_uuid = atama.park.uuid
        personel_ad = atama.personel.ad

        atama.delete()
        messages.success(request, f"{personel_ad} parktan başarıyla kaldırıldı.")

        # HTMX request ise sorumlu sekmesini yeniden yükle
        if request.htmx:
            from parkbahce.htmx_views import park_sorumlu_tab_htmx

            return park_sorumlu_tab_htmx(request, park_uuid)

    except Exception as e:
        messages.error(request, f"Personel kaldırma sırasında hata: {str(e)}")
        return redirect("istakip:kullanici_list")

    return redirect("parkbahce:park_detail", park_uuid=park_uuid)


# Sorun Bildirimleri ve Analiz Views
@login_required
def sorun_bildirimleri(request):
    """Sorun bildirimlerini listele ve filtrele"""

    # Filtreleme parametreleri
    search_query = request.GET.get("search", "").strip()
    durum_filter = request.GET.get("durum", "")
    personel_filter = request.GET.get("personel", "")
    park_filter = request.GET.get("park", "")
    mahalle_filter = request.GET.get("mahalle", "")
    gorev_filter = request.GET.get("gorev", "")  # işe dönüştürülmüş mü
    tarih_filter = request.GET.get("tarih", "")
    sort_by = request.GET.get("sort", "kontrol_tarihi")
    sort_direction = request.GET.get(
        "direction", "desc"
    )  # Temel queryset - tüm sorun durumları (sorun_yok hariç)
    kontroller = (
        GunlukKontrol.objects.exclude(durum="sorun_yok")
        .select_related("park", "park__mahalle", "personel")
        .prefetch_related("resimler", "ilgili_gorevler")
    )

    # Arama
    if search_query:
        kontroller = kontroller.filter(
            Q(aciklama__icontains=search_query)
            | Q(park__ad__icontains=search_query)
            | Q(personel__ad__icontains=search_query)
        )

    # Durum filtresi
    if durum_filter:
        kontroller = kontroller.filter(durum=durum_filter)

    # Personel filtresi
    if personel_filter:
        kontroller = kontroller.filter(personel__uuid=personel_filter)

    # Park filtresi
    if park_filter:
        kontroller = kontroller.filter(park__uuid=park_filter)

    # Mahalle filtresi
    if mahalle_filter:
        kontroller = kontroller.filter(park__mahalle__uuid=mahalle_filter)

    # Görev dönüştürme filtresi
    if gorev_filter == "var":
        kontroller = kontroller.filter(ilgili_gorevler__isnull=False).distinct()
    elif gorev_filter == "yok":
        kontroller = kontroller.filter(ilgili_gorevler__isnull=True)

    # Tarih filtresi
    if tarih_filter:
        try:
            if tarih_filter == "bugun":
                kontroller = kontroller.filter(
                    kontrol_tarihi__date=timezone.now().date()
                )
            elif tarih_filter == "bu_hafta":
                bugun = timezone.now().date()
                hafta_baslangic = bugun - timedelta(days=bugun.weekday())
                kontroller = kontroller.filter(
                    kontrol_tarihi__date__gte=hafta_baslangic
                )
            elif tarih_filter == "bu_ay":
                bugun = timezone.now().date()
                ay_baslangic = bugun.replace(day=1)
                kontroller = kontroller.filter(kontrol_tarihi__date__gte=ay_baslangic)
        except:
            pass

    # Sıralama
    if sort_direction == "desc":
        sort_by = f"-{sort_by}"

    valid_sorts = ["kontrol_tarihi", "park__ad", "personel__ad", "durum"]
    if sort_by.lstrip("-") in valid_sorts:
        kontroller = kontroller.order_by(sort_by)
    else:
        kontroller = kontroller.order_by("-kontrol_tarihi")

    # Sayfalama
    per_page = request.GET.get("per_page", 20)
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 30, 50]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20

    paginator = Paginator(kontroller, per_page)
    page_number = request.GET.get("page")
    kontroller_page = paginator.get_page(page_number)  # İstatistikler
    bugun = timezone.now().date()
    stats = {
        "toplam_sorun": kontroller.count(),
        "acil_sorun": kontroller.filter(durum="acil").count(),
        "sorun_var": kontroller.filter(durum="sorun_var").count(),
        "bugun_sorun": kontroller.filter(kontrol_tarihi__date=bugun).count(),
        "gorev_donusen": kontroller.filter(durum="ise_donusturuldu").count(),
        "cozuldu": kontroller.filter(durum="cozuldu").count(),
        "bekleyen_sorun": kontroller.filter(durum__in=["sorun_var", "acil"]).count(),
    }

    # Filtre seçenekleri
    personeller = Personel.objects.filter(aktif=True).order_by("ad")
    parklar = Park.objects.select_related("mahalle").order_by("ad")[
        :100
    ]  # Limit for performance
    mahalleler = Mahalle.objects.order_by("ad")

    context = {
        "kontroller": kontroller_page,
        "stats": stats,
        "search_query": search_query,
        "durum_filter": durum_filter,
        "personel_filter": personel_filter,
        "park_filter": park_filter,
        "mahalle_filter": mahalle_filter,
        "gorev_filter": gorev_filter,
        "tarih_filter": tarih_filter,
        "sort_by": request.GET.get("sort", "kontrol_tarihi"),
        "sort_direction": sort_direction,
        "per_page": per_page,
        "personeller": personeller,
        "parklar": parklar,
        "mahalleler": mahalleler,
    }

    return render(request, "istakip/sorun_bildirimleri.html", context)


@login_required
def sorun_analiz(request):
    """Sorun analizleri ve raporları"""

    # Tarih aralığı
    bugun = timezone.now().date()
    gecen_ay = bugun - timedelta(days=30)
    gecen_hafta = bugun - timedelta(days=7)

    # Tüm günlük kontroller (sorun_yok dahil)
    tum_kontroller = GunlukKontrol.objects.all()

    # Sorun bildirimleri (sorun_yok hariç)
    sorun_kontroller = tum_kontroller.exclude(durum="sorun_yok")

    # Kapsamlı durum bazlı analiz
    durum_stats = {
        "sorun_yok": tum_kontroller.filter(durum="sorun_yok").count(),
        "sorun_var": tum_kontroller.filter(durum="sorun_var").count(),
        "acil": tum_kontroller.filter(durum="acil").count(),
        "ise_donusturuldu": tum_kontroller.filter(durum="ise_donusturuldu").count(),
        "cozuldu": tum_kontroller.filter(durum="cozuldu").count(),
        "gozden_gecirildi": tum_kontroller.filter(durum="gozden_gecirildi").count(),
        "toplam": tum_kontroller.count(),
        "toplam_sorun": sorun_kontroller.count(),
    }

    # Park bazlı analiz (sorun olan kontroller)
    park_stats = (
        sorun_kontroller.values("park__ad", "park__uuid")
        .annotate(
            sorun_sayisi=Count("id"),
            acil_sayisi=Count("id", filter=Q(durum="acil")),
            cozulen_sayisi=Count("id", filter=Q(durum="cozuldu")),
            devam_eden_sayisi=Count("id", filter=Q(durum__in=["sorun_var", "acil"])),
        )
        .order_by("-sorun_sayisi")[:10]
    )

    # Personel bazlı analiz
    personel_stats = (
        sorun_kontroller.values("personel__ad", "personel__uuid")
        .annotate(
            bildirilen_sorun=Count("id"),
            acil_bildirilen=Count("id", filter=Q(durum="acil")),
            cozulen_bildirilen=Count("id", filter=Q(durum="cozuldu")),
        )
        .order_by("-bildirilen_sorun")[:10]
    )

    # Günlük trend analizi (son 30 gün) - tüm durumlar
    gunluk_trend = []
    for i in range(30):
        tarih = bugun - timedelta(days=i)
        gun_sorun = sorun_kontroller.filter(kontrol_tarihi__date=tarih).count()
        gun_normal = tum_kontroller.filter(
            kontrol_tarihi__date=tarih, durum="sorun_yok"
        ).count()
        gunluk_trend.append(
            {
                "tarih": tarih.strftime("%d.%m"),
                "sorun_sayisi": gun_sorun,
                "normal_sayisi": gun_normal,
                "toplam_kontrol": gun_sorun + gun_normal,
            }
        )
    gunluk_trend.reverse()

    # Çözüm oranları
    gorev_donusen = durum_stats["ise_donusturuldu"]
    cozuldu = durum_stats["cozuldu"]
    toplam_sorun = durum_stats["toplam_sorun"]

    cozum_orani = (cozuldu / toplam_sorun * 100) if toplam_sorun > 0 else 0
    gorev_donusum_orani = (
        (gorev_donusen / toplam_sorun * 100) if toplam_sorun > 0 else 0
    )

    # Mahalle bazlı detaylı analiz
    mahalle_stats = (
        sorun_kontroller.values("park__mahalle__ad", "park__mahalle__uuid")
        .annotate(
            sorun_sayisi=Count("id"),
            acil_sayisi=Count("id", filter=Q(durum="acil")),
            cozulen_sayisi=Count("id", filter=Q(durum="cozuldu")),
            park_sayisi=Count("park", distinct=True),
        )
        .order_by("-sorun_sayisi")[:15]
    )

    # En problemli parklar (çözülmemiş sorunlar)
    problemli_parklar = (
        sorun_kontroller.filter(durum__in=["sorun_var", "acil"])
        .values("park__ad", "park__uuid")
        .annotate(
            bekleyen_sorun=Count("id"), acil_sorun=Count("id", filter=Q(durum="acil"))
        )
        .order_by("-bekleyen_sorun")[:10]
    )

    # En başarılı parklar (düşük sorun oranı)
    basarili_parklar = []
    park_kontrol_stats = (
        tum_kontroller.values("park__ad", "park__uuid")
        .annotate(
            toplam_kontrol=Count("id"),
            sorun_kontrol=Count("id", filter=~Q(durum="sorun_yok")),
        )
        .filter(toplam_kontrol__gte=5)  # En az 5 kontrol olan parklar
    )

    for park in park_kontrol_stats:
        sorun_orani = (park["sorun_kontrol"] / park["toplam_kontrol"]) * 100
        park["sorun_orani"] = round(sorun_orani, 1)
        basarili_parklar.append(park)

    basarili_parklar = sorted(basarili_parklar, key=lambda x: x["sorun_orani"])[:10]

    context = {
        "durum_stats": durum_stats,
        "park_stats": park_stats,
        "personel_stats": personel_stats,
        "gunluk_trend": gunluk_trend,
        "cozum_orani": round(cozum_orani, 1),
        "gorev_donusum_orani": round(gorev_donusum_orani, 1),
        "mahalle_stats": mahalle_stats,
        "problemli_parklar": problemli_parklar,
        "basarili_parklar": basarili_parklar,
        "gecen_hafta_sorun": sorun_kontroller.filter(
            kontrol_tarihi__date__gte=gecen_hafta
        ).count(),
        "gecen_ay_sorun": sorun_kontroller.filter(
            kontrol_tarihi__date__gte=gecen_ay
        ).count(),
    }
    return render(request, "istakip/sorun_analiz.html", context)


@login_required
def sorun_detay(request, kontrol_uuid):
    """Sorun bildirimi detay sayfası"""

    kontrol = get_object_or_404(
        GunlukKontrol.objects.select_related(
            "park", "park__mahalle", "park__park_tipi", "personel"
        ).prefetch_related("resimler", "ilgili_gorevler__atamalar__personel"),
        uuid=kontrol_uuid,
    )

    # İlgili görevler varsa detaylarını getir
    ilgili_gorevler = kontrol.ilgili_gorevler.all()

    # Sorun için istatistikler
    ayni_parkta_sorunlar = (
        GunlukKontrol.objects.filter(
            park=kontrol.park,
            durum__in=["sorun_var", "acil", "ise_donusturuldu", "cozuldu"],
        )
        .exclude(uuid=kontrol_uuid)
        .order_by("-kontrol_tarihi")[:5]
    )

    # Aynı personelin son bildirimleri
    personel_son_bildirimleri = (
        GunlukKontrol.objects.filter(
            personel=kontrol.personel,
            durum__in=["sorun_var", "acil", "ise_donusturuldu", "cozuldu"],
        )
        .exclude(uuid=kontrol_uuid)
        .order_by("-kontrol_tarihi")[:5]
    )

    geom = None
    # geom 5256 dan 4326 çevir
    if kontrol.geom:
        geom = kontrol.geom.transform(4326, clone=True)

    context = {
        "kontrol": kontrol,
        "ilgili_gorevler": ilgili_gorevler,
        "ayni_parkta_sorunlar": ayni_parkta_sorunlar,
        "personel_son_bildirimleri": personel_son_bildirimleri,
        "geom": geom,
    }

    return render(request, "istakip/sorun_detay.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def sorun_gorev_donustur(request, kontrol_uuid):
    """Sorun bildirimini göreve dönüştür"""

    kontrol = get_object_or_404(
        GunlukKontrol.objects.select_related("park", "personel"), uuid=kontrol_uuid
    )

    if request.method == "POST":
        try:
            baslik = request.POST.get("baslik")
            aciklama = request.POST.get("aciklama", "")
            oncelik = request.POST.get("oncelik", "normal")
            baslangic_tarihi = request.POST.get("baslangic_tarihi")
            bitis_tarihi = request.POST.get("bitis_tarihi")
            atanan_personeller = request.POST.getlist("atanan_personeller")
            gorev_tipi = request.POST.get("gorev_tipi")

            # Gerekli alanları kontrol et
            if not all([baslik, baslangic_tarihi]):
                messages.error(request, "Başlık ve başlangıç tarihi zorunludur.")
                return redirect("istakip:sorun_bildirimleri")

            with transaction.atomic():
                # Görev oluştur
                gorev = Gorev.objects.create(
                    park=kontrol.park,
                    baslik=baslik,
                    aciklama=aciklama,
                    oncelik=oncelik,
                    baslangic_tarihi=baslangic_tarihi,
                    bitis_tarihi=bitis_tarihi if bitis_tarihi else None,
                    olusturan=request.user,
                    gunluk_kontrol=kontrol,
                    gorev_tipi=GorevTipi.objects.get(id=gorev_tipi),
                    durum="planlanmis",
                )

                # Personel atamalarını yap
                for personel_uuid in atanan_personeller:
                    try:
                        personel = Personel.objects.get(uuid=personel_uuid)
                        GorevAtama.objects.create(
                            gorev=gorev, personel=personel, gorev_rolu="Yürütücü"
                        )
                    except Personel.DoesNotExist:
                        continue

                # Kontrol durumunu güncelle
                kontrol.durum = "ise_donusturuldu"
                kontrol.save()

                messages.success(
                    request, f"Sorun başarıyla göreve dönüştürüldü: {gorev.baslik}"
                )
                return redirect("istakip:gorev_detail", gorev_uuid=gorev.uuid)

        except Exception as e:
            messages.error(request, f"Görev oluşturulurken hata: {str(e)}")
            return redirect("istakip:sorun_bildirimleri")

    # GET request - Form göster
    personeller = Personel.objects.filter(aktif=True).order_by("ad")

    # Varsayılan değerler
    initial_data = {
        "baslik": f"{kontrol.park.ad} - {kontrol.get_durum_display()}",
        "aciklama": kontrol.aciklama or "",
        "oncelik": "yuksek" if kontrol.durum == "acil" else "normal",
    }

    context = {
        "kontrol": kontrol,
        "gorev_tipleri": GorevTipi.objects.all(),
        "personeller": personeller,
        "initial_data": initial_data,
    }

    return render(request, "istakip/sorun_gorev_donustur.html", context)


# Görev Yönetimi Views
@login_required
def gorev_list(request):
    """Görev listesi sayfası"""

    # Filtreleme parametreleri
    search_query = request.GET.get("search", "").strip()
    durum_filter = request.GET.get("durum", "")
    oncelik_filter = request.GET.get("oncelik", "")
    personel_filter = request.GET.get("personel", "")
    gorev_tipi_filter = request.GET.get("gorev_tipi", "")
    tarih_filter = request.GET.get("tarih", "")
    sort_by = request.GET.get("sort", "baslangic_tarihi")
    sort_direction = request.GET.get("direction", "desc")

    # Temel queryset
    gorevler = Gorev.objects.select_related(
        "park", "park__mahalle", "gorev_tipi", "olusturan"
    ).prefetch_related("atamalar__personel")

    # Arama
    if search_query:
        gorevler = gorevler.filter(
            Q(baslik__icontains=search_query)
            | Q(aciklama__icontains=search_query)
            | Q(park__ad__icontains=search_query)
        )

    # Filtreleme
    if durum_filter:
        gorevler = gorevler.filter(durum=durum_filter)

    if oncelik_filter:
        gorevler = gorevler.filter(oncelik=oncelik_filter)

    if personel_filter:
        gorevler = gorevler.filter(atamalar__personel__uuid=personel_filter)

    if gorev_tipi_filter:
        gorevler = gorevler.filter(gorev_tipi__uuid=gorev_tipi_filter)

    # Tarih filtresi
    if tarih_filter:
        try:
            bugun = timezone.now().date()
            if tarih_filter == "bugun":
                gorevler = gorevler.filter(baslangic_tarihi__date=bugun)
            elif tarih_filter == "bu_hafta":
                hafta_baslangic = bugun - timedelta(days=bugun.weekday())
                gorevler = gorevler.filter(baslangic_tarihi__date__gte=hafta_baslangic)
            elif tarih_filter == "bu_ay":
                ay_baslangic = bugun.replace(day=1)
                gorevler = gorevler.filter(baslangic_tarihi__date__gte=ay_baslangic)
        except:
            pass

    # Sıralama
    if sort_direction == "desc":
        sort_by = f"-{sort_by}"

    valid_sorts = ["baslik", "created_at", "baslangic_tarihi", "durum", "oncelik"]
    if sort_by.lstrip("-") in valid_sorts:
        gorevler = gorevler.order_by(sort_by)
    else:
        gorevler = gorevler.order_by("-created_at")

    # Sayfalama
    per_page = request.GET.get("per_page", 20)
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 30, 50]:
            per_page = 20
    except (ValueError, TypeError):
        per_page = 20

    paginator = Paginator(gorevler, per_page)
    page_number = request.GET.get("page")
    gorevler_page = paginator.get_page(page_number)

    # İstatistikler
    stats = {
        "toplam_gorev": gorevler.count(),
        "planlanmis": gorevler.filter(durum="planlanmis").count(),
        "devam_ediyor": gorevler.filter(durum="devam_ediyor").count(),
        "tamamlandi": gorevler.filter(durum="tamamlandi").count(),
        "iptal": gorevler.filter(durum="iptal").count(),
        "acil": gorevler.filter(oncelik="acil").count(),
    }

    # Filtre seçenekleri
    personeller = Personel.objects.filter(aktif=True).order_by("ad")
    gorev_tipleri = GorevTipi.objects.order_by("ad")

    context = {
        "gorevler": gorevler_page,
        "stats": stats,
        "search_query": search_query,
        "durum_filter": durum_filter,
        "oncelik_filter": oncelik_filter,
        "personel_filter": personel_filter,
        "gorev_tipi_filter": gorev_tipi_filter,
        "tarih_filter": tarih_filter,
        "sort_by": request.GET.get("sort", "baslangic_tarihi"),
        "sort_direction": sort_direction,
        "per_page": per_page,
        "personeller": personeller,
        "gorev_tipleri": gorev_tipleri,
    }

    return render(request, "istakip/gorev_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def gorev_create(request):
    """Yeni görev oluşturma"""

    if request.method == "POST":
        try:
            baslik = request.POST.get("baslik")
            aciklama = request.POST.get("aciklama", "")
            park_uuid = request.POST.get("park")
            gorev_tipi_uuid = request.POST.get("gorev_tipi")
            oncelik = request.POST.get("oncelik", "normal")
            tekrar_tipi = request.POST.get("tekrar_tipi", "yok")
            baslangic_tarihi = request.POST.get("baslangic_tarihi")
            bitis_tarihi = request.POST.get("bitis_tarihi")
            atanan_personeller = request.POST.getlist("atanan_personeller")

            # Aşama bilgileri
            step_names = request.POST.getlist("step_name[]")
            step_descriptions = request.POST.getlist("step_description[]")
            step_responsibles = request.POST.getlist("step_responsible[]")

            if not baslik or not park_uuid:
                messages.error(request, "Başlık ve park seçimi zorunludur.")
                return redirect("istakip:gorev_create")

            park = get_object_or_404(Park, uuid=park_uuid)
            gorev_tipi = None
            if gorev_tipi_uuid:
                gorev_tipi = get_object_or_404(GorevTipi, uuid=gorev_tipi_uuid)

            with transaction.atomic():
                gorev = Gorev.objects.create(
                    baslik=baslik,
                    aciklama=aciklama,
                    park=park,
                    gorev_tipi=gorev_tipi,
                    oncelik=oncelik,
                    tekrar_tipi=tekrar_tipi,
                    baslangic_tarihi=baslangic_tarihi if baslangic_tarihi else None,
                    bitis_tarihi=bitis_tarihi if bitis_tarihi else None,
                    olusturan=request.user,
                    durum="planlanmis",
                )

                # Personel atamalarını oluştur
                for personel_uuid in atanan_personeller:
                    try:
                        personel = Personel.objects.get(uuid=personel_uuid)
                        GorevAtama.objects.create(
                            gorev=gorev, personel=personel, gorev_rolu="Yürütücü"
                        )
                    except Personel.DoesNotExist:
                        continue

                # Aşamaları oluştur
                for i, step_name in enumerate(step_names):
                    if step_name.strip():  # Boş olmayan aşama adları için
                        step_description = (
                            step_descriptions[i] if i < len(step_descriptions) else ""
                        )
                        step_responsible_uuid = (
                            step_responsibles[i] if i < len(step_responsibles) else ""
                        )

                        sorumlu = None
                        if step_responsible_uuid:
                            try:
                                sorumlu = Personel.objects.get(
                                    uuid=step_responsible_uuid
                                )
                            except Personel.DoesNotExist:
                                pass

                        GorevAsama.objects.create(
                            gorev=gorev,
                            ad=step_name.strip(),
                            aciklama=step_description.strip(),
                            sorumlu=sorumlu,
                            durum="beklemede",
                        )

            messages.success(request, f"'{baslik}' görevi başarıyla oluşturuldu.")
            return redirect("istakip:gorev_detail", gorev_uuid=gorev.uuid)

        except Exception as e:
            messages.error(request, f"Görev oluşturma sırasında hata: {str(e)}")

    # GET request - Form göster
    parklar = Park.objects.select_related("mahalle").order_by("ad")
    gorev_tipleri = GorevTipi.objects.order_by("ad")
    personeller = Personel.objects.filter(aktif=True).order_by("ad")

    context = {
        "parklar": parklar,
        "gorev_tipleri": gorev_tipleri,
        "personeller": personeller,
        "is_edit": False,
    }

    return render(request, "istakip/gorev_create.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def gorev_edit(request, gorev_uuid):
    """Görev düzenleme"""

    gorev = get_object_or_404(Gorev, uuid=gorev_uuid)

    if request.method == "POST":
        try:
            gorev.baslik = request.POST.get("baslik", gorev.baslik)
            gorev.aciklama = request.POST.get("aciklama", "")

            gorev_tipi_uuid = request.POST.get("gorev_tipi")
            if gorev_tipi_uuid:
                gorev.gorev_tipi = get_object_or_404(GorevTipi, uuid=gorev_tipi_uuid)
            else:
                gorev.gorev_tipi = None

            gorev.oncelik = request.POST.get("oncelik", gorev.oncelik)

            # Durum güncellemesi sadece edit modunda
            durum = request.POST.get("durum")
            if durum:
                gorev.durum = durum

            baslangic_tarihi = request.POST.get("baslangic_tarihi")
            if baslangic_tarihi:
                gorev.baslangic_tarihi = baslangic_tarihi

            bitis_tarihi = request.POST.get("bitis_tarihi")
            gorev.bitis_tarihi = bitis_tarihi if bitis_tarihi else None

            # Personel atamalarını güncelle
            atanan_personeller = request.POST.getlist("atanan_personeller")

            # Aşama bilgileri
            step_names = request.POST.getlist("step_name[]")
            step_descriptions = request.POST.getlist("step_description[]")
            step_responsibles = request.POST.getlist("step_responsible[]")
            step_ids = request.POST.getlist("step_id[]")

            with transaction.atomic():
                gorev.save()

                # Mevcut atamaları sil ve yenilerini oluştur
                gorev.atamalar.all().delete()
                for personel_uuid in atanan_personeller:
                    try:
                        personel = Personel.objects.get(uuid=personel_uuid)
                        GorevAtama.objects.create(
                            gorev=gorev, personel=personel, gorev_rolu="Yürütücü"
                        )
                    except Personel.DoesNotExist:
                        continue

                # Aşamaları güncelle
                # Önce mevcut aşamaları sakla
                mevcut_asama_ids = set()

                for i, step_name in enumerate(step_names):
                    if step_name.strip():
                        step_description = (
                            step_descriptions[i] if i < len(step_descriptions) else ""
                        )
                        step_responsible_uuid = (
                            step_responsibles[i] if i < len(step_responsibles) else ""
                        )
                        step_id = step_ids[i] if i < len(step_ids) else ""

                        sorumlu = None
                        if step_responsible_uuid:
                            try:
                                sorumlu = Personel.objects.get(
                                    uuid=step_responsible_uuid
                                )
                            except Personel.DoesNotExist:
                                pass

                        if step_id:  # Mevcut aşamayı güncelle
                            try:
                                asama = GorevAsama.objects.get(
                                    uuid=step_id, gorev=gorev
                                )
                                asama.ad = step_name.strip()
                                asama.aciklama = step_description.strip()
                                asama.sorumlu = sorumlu
                                asama.save()
                                mevcut_asama_ids.add(step_id)
                            except GorevAsama.DoesNotExist:
                                pass
                        else:  # Yeni aşama oluştur
                            yeni_asama = GorevAsama.objects.create(
                                gorev=gorev,
                                ad=step_name.strip(),
                                aciklama=step_description.strip(),
                                sorumlu=sorumlu,
                                durum="beklemede",
                            )
                            mevcut_asama_ids.add(str(yeni_asama.uuid))

                # Silinmesi gereken aşamaları bul ve sil
                tum_asamalar = gorev.asamalar.all()
                for asama in tum_asamalar:
                    if str(asama.uuid) not in mevcut_asama_ids:
                        asama.delete()

            messages.success(request, "Görev başarıyla güncellendi.")
            return redirect("istakip:gorev_detail", gorev_uuid=gorev.uuid)

        except Exception as e:
            messages.error(request, f"Görev güncelleme sırasında hata: {str(e)}")

    # GET request
    parklar = Park.objects.select_related("mahalle").order_by("ad")
    gorev_tipleri = GorevTipi.objects.order_by("ad")
    personeller = Personel.objects.filter(aktif=True).order_by("ad")

    # Atanmış personellerin UUID listesi
    atanan_personeller = list(gorev.atamalar.values_list("personel__uuid", flat=True))

    context = {
        "gorev": gorev,
        "parklar": parklar,
        "gorev_tipleri": gorev_tipleri,
        "personeller": personeller,
        "atanan_personeller": atanan_personeller,
        "is_edit": True,
    }

    return render(request, "istakip/gorev_create.html", context)


@login_required
def gorev_detail(request, gorev_uuid):
    """Görev detay sayfası"""

    gorev = get_object_or_404(
        Gorev.objects.select_related(
            "park", "park__mahalle", "gorev_tipi", "olusturan", "gunluk_kontrol"
        ).prefetch_related("atamalar__personel", "asamalar", "tamamlama_resimleri"),
        uuid=gorev_uuid,
    )

    # Aşama istatistikleri
    asamalar = gorev.asamalar.all()
    asama_stats = {
        "toplam": asamalar.count(),
        "tamamlanan": asamalar.filter(durum="tamamlandi").count(),
        "devam_eden": asamalar.filter(durum="devam_ediyor").count(),
        "bekleyen": asamalar.filter(durum="beklemede").count(),
    }

    # İlerleme yüzdesi
    ilerleme = 0
    if asama_stats["toplam"] > 0:
        ilerleme = int((asama_stats["tamamlanan"] / asama_stats["toplam"]) * 100)

    context = {
        "gorev": gorev,
        "asama_stats": asama_stats,
        "ilerleme": round(ilerleme, 1),
    }

    return render(request, "istakip/gorev_detail.html", context)


@login_required
def gorev_planlama(request):
    """Görev planlama ve takvim görünümü"""

    # Planlama sayfası için temel görevler
    gorevler = Gorev.objects.select_related("park", "gorev_tipi").prefetch_related(
        "atamalar__personel"
    )

    # Bugünkü görevler
    bugun = timezone.now().date()
    bugun_gorevler = gorevler.filter(baslangic_tarihi__date=bugun)

    # Bu haftaki görevler
    hafta_baslangic = bugun - timedelta(days=bugun.weekday())
    hafta_bitis = hafta_baslangic + timedelta(days=6)
    hafta_gorevler = gorevler.filter(
        baslangic_tarihi__date__range=[hafta_baslangic, hafta_bitis]
    )

    context = {
        "bugun_gorevler": bugun_gorevler,
        "hafta_gorevler": hafta_gorevler,
        "bugun": bugun,
    }

    return render(request, "istakip/gorev_planlama.html", context)


@login_required
def gorev_rapor(request):
    """Görev raporları ve analiz"""

    # Tarih aralığı
    bugun = timezone.now().date()
    gecen_ay = bugun - timedelta(days=30)

    # Temel istatistikler
    gorevler = Gorev.objects.all()

    stats = {
        "toplam": gorevler.count(),
        "tamamlanan": gorevler.filter(durum="tamamlandi").count(),
        "devam_eden": gorevler.filter(durum="devam_ediyor").count(),
        "planlanmis": gorevler.filter(durum="planlanmis").count(),
        "iptal": gorevler.filter(durum="iptal").count(),
    }

    # Öncelik bazlı analiz
    oncelik_stats = {
        "acil": gorevler.filter(oncelik="acil").count(),
        "yuksek": gorevler.filter(oncelik="yuksek").count(),
        "normal": gorevler.filter(oncelik="normal").count(),
        "dusuk": gorevler.filter(oncelik="dusuk").count(),
    }

    # Park bazlı analiz
    park_stats = (
        gorevler.values("park__ad")
        .annotate(gorev_sayisi=Count("id"))
        .order_by("-gorev_sayisi")[:10]
    )

    context = {
        "stats": stats,
        "oncelik_stats": oncelik_stats,
        "park_stats": park_stats,
    }

    return render(request, "istakip/gorev_rapor.html", context)


@login_required
@require_http_methods(["POST"])
def gorev_durum_degistir(request, gorev_uuid):
    """Görev durumu değiştirme"""

    gorev = get_object_or_404(Gorev, uuid=gorev_uuid)

    try:
        yeni_durum = request.POST.get("durum")
        not_text = request.POST.get("not", "")

        if not yeni_durum:
            messages.error(request, "Durum seçimi zorunludur.")
            return redirect("istakip:gorev_detail", gorev_uuid=gorev_uuid)

        valid_durumlar = [
            "planlanmis",
            "devam_ediyor",
            "onaya_gonderildi",
            "tamamlandi",
            "iptal",
            "gecikmis",
        ]
        if yeni_durum not in valid_durumlar:
            messages.error(request, "Geçersiz durum.")
            return redirect("istakip:gorev_detail", gorev_uuid=gorev_uuid)

        # Tamamlandı durumuna geçmek için kontrol
        if yeni_durum == "tamamlandi":
            # Tüm aşamalar tamamlanmış mı kontrol et
            tum_asamalar = gorev.asamalar.all()
            if tum_asamalar.exists():
                tamamlanan_asamalar = tum_asamalar.filter(durum="tamamlandi")
                if tum_asamalar.count() != tamamlanan_asamalar.count():
                    messages.error(
                        request,
                        "Görevi tamamlamak için önce tüm aşamaların tamamlanmış olması gerekir.",
                    )
                    return redirect("istakip:gorev_detail", gorev_uuid=gorev_uuid)

        eski_durum = gorev.durum
        gorev.durum = yeni_durum

        # Tarihleri mantıklı şekilde güncelle
        if yeni_durum == "tamamlandi":
            # Sadece tamamlandı durumunda tamamlanma tarihi set et
            if not gorev.tamamlanma_tarihi:
                gorev.tamamlanma_tarihi = timezone.now()
        else:
            # Diğer durumlarda tamamlanma tarihini sıfırla
            gorev.tamamlanma_tarihi = None

        if yeni_durum == "onaya_gonderildi":
            # Onaya gönderildiğinde onay tarihi sıfırla
            gorev.onay_tarihi = None
        elif yeni_durum == "tamamlandi":
            # Tamamlandığında onay tarihi set et
            gorev.onay_tarihi = timezone.now()
        else:
            # Diğer durumlarda onay tarihini sıfırla
            gorev.onay_tarihi = None

        gorev.save()

        # Eğer bağlı bir sorun bildirimi varsa onun da durumunu güncelle
        if gorev.gunluk_kontrol:
            if yeni_durum == "tamamlandi":
                gorev.gunluk_kontrol.durum = "cozuldu"
            elif yeni_durum in [
                "devam_ediyor",
                "planlanmis",
                "onaya_gonderildi",
                "iptal",
            ]:
                gorev.gunluk_kontrol.durum = "ise_donusturuldu"
            gorev.gunluk_kontrol.save()

        messages.success(
            request, f"Görev durumu '{gorev.get_durum_display()}' olarak güncellendi."
        )

    except Exception as e:
        messages.error(request, f"Durum güncelleme sırasında hata: {str(e)}")

    return redirect("istakip:gorev_detail", gorev_uuid=gorev_uuid)


@login_required
@require_http_methods(["POST"])
def gorev_onayla(request, gorev_uuid):
    """Görev onaylama (onaya_gonderildi -> tamamlandi)"""

    gorev = get_object_or_404(Gorev, uuid=gorev_uuid)

    if gorev.durum != "onaya_gonderildi":
        return JsonResponse(
            {"success": False, "message": "Bu görev onay beklemede değil."}
        )

    try:
        gorev.durum = "tamamlandi"
        gorev.tamamlanma_tarihi = timezone.now()
        gorev.onay_tarihi = timezone.now()
        gorev.save()

        # Eğer bağlı bir sorun bildirimi varsa onun da durumunu güncelle
        if gorev.gunluk_kontrol:
            gorev.gunluk_kontrol.durum = "cozuldu"
            gorev.gunluk_kontrol.save()

        return JsonResponse({"success": True, "message": "Görev başarıyla onaylandı."})

    except Exception as e:
        return JsonResponse({"success": False, "message": f"Hata: {str(e)}"})


@login_required
@require_http_methods(["POST"])
def gorev_asama_ekle(request, gorev_uuid):
    """Yeni görev aşaması ekleme"""

    gorev = get_object_or_404(Gorev, uuid=gorev_uuid)

    try:
        ad = request.POST.get("ad")
        aciklama = request.POST.get("aciklama", "")
        sorumlu_id = request.POST.get("sorumlu")

        if not ad:
            messages.error(request, "Aşama adı zorunludur.")
            return redirect("istakip:gorev_detail", gorev_uuid=gorev_uuid)

        sorumlu = None
        if sorumlu_id:
            sorumlu = get_object_or_404(Personel, id=sorumlu_id)

        GorevAsama.objects.create(
            gorev=gorev, ad=ad, aciklama=aciklama, sorumlu=sorumlu, durum="beklemede"
        )

        messages.success(request, f"'{ad}' aşaması başarıyla eklendi.")

    except Exception as e:
        messages.error(request, f"Aşama ekleme sırasında hata: {str(e)}")

    return redirect("istakip:gorev_detail", gorev_uuid=gorev_uuid)


@login_required
@require_http_methods(["POST"])
def gorev_asama_durum_degistir(request, asama_uuid):
    """Görev aşama durumu değiştirme"""

    asama = get_object_or_404(GorevAsama, uuid=asama_uuid)

    try:
        yeni_durum = request.POST.get("durum")

        if not yeni_durum:
            messages.error(request, "Durum seçimi zorunludur.")
            return redirect("istakip:gorev_detail", gorev_uuid=asama.gorev.uuid)

        valid_durumlar = ["beklemede", "baslamadi", "devam_ediyor", "tamamlandi"]
        if yeni_durum not in valid_durumlar:
            messages.error(request, "Geçersiz durum.")
            return redirect("istakip:gorev_detail", gorev_uuid=asama.gorev.uuid)

        eski_durum = asama.durum
        asama.durum = yeni_durum

        # Tarihleri mantıklı şekilde güncelle
        if yeni_durum == "devam_ediyor":
            # Devam ediyor durumunda başlangıç tarihi set et
            if not asama.baslangic_tarihi:
                asama.baslangic_tarihi = timezone.now()
            # Tamamlanma tarihini sıfırla (geri alınmış olabilir)
            asama.tamamlanma_tarihi = None
        elif yeni_durum == "tamamlandi":
            # Tamamlandı durumunda tamamlanma tarihi set et
            if not asama.tamamlanma_tarihi:
                asama.tamamlanma_tarihi = timezone.now()
            # Başlangıç tarihi yoksa set et
            if not asama.baslangic_tarihi:
                asama.baslangic_tarihi = timezone.now()
        else:
            # Beklemede veya başlamadı durumlarında tarihleri sıfırla
            if yeni_durum in ["beklemede", "baslamadi"]:
                asama.baslangic_tarihi = None
                asama.tamamlanma_tarihi = None

        asama.save()

        # Ana görevi de güncelle
        if yeni_durum == "devam_ediyor" and asama.gorev.durum == "planlanmis":
            asama.gorev.durum = "devam_ediyor"
            asama.gorev.save()

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
            asama.gorev.onay_tarihi = timezone.now()
            asama.gorev.save()

            # Eğer bağlı bir sorun bildirimi varsa onun da durumunu güncelle
            if asama.gorev.gunluk_kontrol:
                asama.gorev.gunluk_kontrol.durum = "cozuldu"
                asama.gorev.gunluk_kontrol.save()
        else:
            # Eğer aşama geri alındıysa ve görev tamamlandı durumundaysa, görev durumunu güncelle
            if asama.gorev.durum == "tamamlandi" and yeni_durum != "tamamlandi":
                asama.gorev.durum = "devam_ediyor"
                asama.gorev.tamamlanma_tarihi = None
                asama.gorev.onay_tarihi = None
                asama.gorev.save()

                # Sorun bildirimi durumunu da güncelle
                if asama.gorev.gunluk_kontrol:
                    asama.gorev.gunluk_kontrol.durum = "ise_donusturuldu"
                    asama.gorev.gunluk_kontrol.save()

        messages.success(
            request,
            f"'{asama.ad}' aşaması '{asama.get_durum_display()}' olarak güncellendi.",
        )

    except Exception as e:
        messages.error(request, f"Aşama durum güncelleme sırasında hata: {str(e)}")

    return redirect("istakip:gorev_detail", gorev_uuid=asama.gorev.uuid)


@login_required
@require_http_methods(["POST"])
def sorun_durum_degistir(request, kontrol_uuid):
    """Sorun durumu değiştirme"""

    kontrol = get_object_or_404(GunlukKontrol, uuid=kontrol_uuid)

    try:
        yeni_durum = request.POST.get("durum")

        if not yeni_durum:
            messages.error(request, "Durum seçimi zorunludur.")
            return redirect("istakip:sorun_detay", kontrol_uuid=kontrol_uuid)

        valid_durumlar = [
            "sorun_var",
            "acil",
            "gozden_gecirildi",
            "ise_donusturuldu",
            "cozuldu",
        ]
        if yeni_durum not in valid_durumlar:
            messages.error(request, "Geçersiz durum.")
            return redirect("istakip:sorun_detay", kontrol_uuid=kontrol_uuid)

        eski_durum = kontrol.durum
        kontrol.durum = yeni_durum
        kontrol.save()

        # Durum değişikliği mesajı
        durum_mesajlari = {
            "sorun_var": "Sorun Var",
            "acil": "Acil Müdahale",
            "gozden_gecirildi": "Gözden Geçirildi",
            "ise_donusturuldu": "İşe Dönüştürüldü",
            "cozuldu": "Çözüldü",
        }

        messages.success(
            request,
            f"Sorun durumu '{durum_mesajlari.get(yeni_durum, yeni_durum)}' olarak güncellendi.",
        )

    except Exception as e:
        messages.error(request, f"Durum güncelleme sırasında hata: {str(e)}")

    return redirect("istakip:sorun_detay", kontrol_uuid=kontrol_uuid)


class GorevOnayaGonderView(LoginRequiredMixin, TemplateView):
    """
    Desktop görev tamamlama ve onaya gönderme sayfası
    """

    template_name = "istakip/gorev_onaya_gonder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        gorev_uuid = kwargs.get("gorev_uuid")
        gorev = get_object_or_404(
            Gorev.objects.select_related(
                "park", "park__mahalle", "gorev_tipi", "olusturan"
            ).prefetch_related("atamalar__personel", "asamalar", "tamamlama_resimleri"),
            uuid=gorev_uuid,
        )

        # Görev durumu kontrolü
        if gorev.durum in ["tamamlandi", "iptal", "onaya_gonderildi"]:
            messages.warning(self.request, "Bu görev için tamamlama işlemi yapılamaz.")
            return redirect("istakip:gorev_detail", gorev_uuid=gorev.uuid)

        # Aşama istatistikleri
        asamalar = gorev.asamalar.all()
        asama_stats = {
            "toplam": asamalar.count(),
            "tamamlanan": asamalar.filter(durum="tamamlandi").count(),
        }

        # İlerleme yüzdesi
        ilerleme = 0
        if asama_stats["toplam"] > 0:
            ilerleme = int((asama_stats["tamamlanan"] / asama_stats["toplam"]) * 100)

        context.update(
            {
                "gorev": gorev,
                "asama_stats": asama_stats,
                "ilerleme": ilerleme,
            }
        )

        return context

    def post(self, request, *args, **kwargs):
        """
        Desktop görev tamamlama formu işleme
        """
        try:
            gorev_uuid = kwargs.get("gorev_uuid")
            gorev = get_object_or_404(Gorev, uuid=gorev_uuid)

            # Görev durumu kontrolü
            if gorev.durum in ["tamamlandi", "iptal", "onaya_gonderildi"]:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bu görev için tamamlama işlemi yapılamaz.",
                    }
                )

            # Tüm aşamalar tamamlandı mı kontrol et
            tum_asamalar = gorev.asamalar.all()
            tamamlanan_asamalar = tum_asamalar.filter(durum="tamamlandi")

            if (
                tum_asamalar.count() > 0
                and tum_asamalar.count() != tamamlanan_asamalar.count()
            ):
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Tüm aşamalar tamamlanmadan görev onaya gönderilemez.",
                    }
                )

            # Tamamlama açıklaması
            tamamlama_aciklama = request.POST.get("tamamlama_aciklama", "")

            with transaction.atomic():
                # Resimleri kaydet
                for i in range(1, 4):  # En fazla 3 resim
                    resim_field = f"resim_{i}"
                    if resim_field in request.FILES:
                        resim_file = request.FILES[resim_field]
                        resim_aciklama = request.POST.get(f"resim_aciklama_{i}", "")
                        resim_lat = request.POST.get(f"resim_lat_{i}")
                        resim_lng = request.POST.get(f"resim_lng_{i}")

                        # Konum oluştur
                        konum = None
                        if resim_lat and resim_lng:
                            try:
                                konum = Point(
                                    float(resim_lng), float(resim_lat), srid=4326
                                )
                                konum.transform(5256)
                            except (ValueError, TypeError):
                                pass

                        # Tamamlama resmi kaydet
                        GorevTamamlamaResim.objects.create(
                            gorev=gorev,
                            resim=resim_file,
                            aciklama=resim_aciklama or f"Tamamlama resmi {i}",
                            konum=konum,
                        )

                # Görev açıklamasını güncelle
                if tamamlama_aciklama:
                    if gorev.aciklama:
                        gorev.aciklama += (
                            f"\n\nTamamlama Açıklaması: {tamamlama_aciklama}"
                        )
                    else:
                        gorev.aciklama = f"Tamamlama Açıklaması: {tamamlama_aciklama}"

                # Görevi onaya gönder
                gorev.durum = "onaya_gonderildi"
                gorev.tamamlanma_tarihi = timezone.now()
                gorev.onay_tarihi = None
                gorev.save()

                # Eğer bağlı bir sorun bildirimi varsa onun da durumunu güncelle
                if gorev.gunluk_kontrol:
                    gorev.gunluk_kontrol.durum = "gozden_gecirildi"
                    gorev.gunluk_kontrol.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "Görev başarıyla onaya gönderildi.",
                    "redirect_url": reverse(
                        "istakip:gorev_detail", kwargs={"gorev_uuid": gorev.uuid}
                    ),
                }
            )

        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Bir hata oluştu: {str(e)}"}
            )
