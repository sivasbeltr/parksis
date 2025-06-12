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
    GorevAtama,
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
# bu metod deactivate metodundan biraz farklı. Onay istemiyor ve aktif hale getiriyor. sonra da kullanıcı detayına yönlendiriyor. Herhangi bir şablon render etmiyor
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

    # Temel istatistikler
    sorun_kontroller = GunlukKontrol.objects.filter(durum__in=["sorun_var", "acil"])

    # Durum bazlı analiz
    durum_stats = {
        "sorun_var": sorun_kontroller.filter(durum="sorun_var").count(),
        "acil": sorun_kontroller.filter(durum="acil").count(),
        "toplam": sorun_kontroller.count(),
    }

    # Park bazlı analiz
    park_stats = (
        sorun_kontroller.values("park__ad", "park__uuid")
        .annotate(
            sorun_sayisi=Count("id"), acil_sayisi=Count("id", filter=Q(durum="acil"))
        )
        .order_by("-sorun_sayisi")[:10]
    )

    # Personel bazlı analiz
    personel_stats = (
        sorun_kontroller.values("personel__ad", "personel__uuid")
        .annotate(
            bildirilen_sorun=Count("id"),
            acil_bildirilen=Count("id", filter=Q(durum="acil")),
        )
        .order_by("-bildirilen_sorun")[:10]
    )

    # Günlük trend analizi (son 30 gün)
    gunluk_trend = []
    for i in range(30):
        tarih = bugun - timedelta(days=i)
        gun_sorunu = sorun_kontroller.filter(kontrol_tarihi__date=tarih).count()
        gunluk_trend.append(
            {"tarih": tarih.strftime("%d.%m"), "sorun_sayisi": gun_sorunu}
        )
    gunluk_trend.reverse()

    # Çözüm oranları
    gorev_donusen = (
        sorun_kontroller.filter(ilgili_gorevler__isnull=False).distinct().count()
    )
    cozum_orani = (
        (gorev_donusen / sorun_kontroller.count() * 100)
        if sorun_kontroller.count() > 0
        else 0
    )

    # Mahalle bazlı analiz
    mahalle_stats = (
        sorun_kontroller.values("park__mahalle__ad")
        .annotate(sorun_sayisi=Count("id"))
        .order_by("-sorun_sayisi")[:10]
    )

    context = {
        "durum_stats": durum_stats,
        "park_stats": park_stats,
        "personel_stats": personel_stats,
        "gunluk_trend": gunluk_trend,
        "cozum_orani": round(cozum_orani, 1),
        "mahalle_stats": mahalle_stats,
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

    context = {
        "kontrol": kontrol,
        "ilgili_gorevler": ilgili_gorevler,
        "ayni_parkta_sorunlar": ayni_parkta_sorunlar,
        "personel_son_bildirimleri": personel_son_bildirimleri,
    }

    return render(request, "istakip/sorun_detay.html", context)


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

    context = {
        "kontrol": kontrol,
        "ilgili_gorevler": ilgili_gorevler,
        "ayni_parkta_sorunlar": ayni_parkta_sorunlar,
        "personel_son_bildirimleri": personel_son_bildirimleri,
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
    park_filter = request.GET.get("park", "")
    personel_filter = request.GET.get("personel", "")
    gorev_tipi_filter = request.GET.get("gorev_tipi", "")
    tarih_filter = request.GET.get("tarih", "")
    sort_by = request.GET.get("sort", "baslangic_tarihi")
    sort_direction = request.GET.get("direction", "desc")

    # Temel queryset
    gorevler = Gorev.objects.select_related(
        "park", "gorev_tipi", "olusturan"
    ).prefetch_related("atamalar__personel", "asamalar")

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

    if park_filter:
        gorevler = gorevler.filter(park__uuid=park_filter)

    if personel_filter:
        gorevler = gorevler.filter(atamalar__personel__uuid=personel_filter).distinct()

    if gorev_tipi_filter:
        gorevler = gorevler.filter(gorev_tipi__uuid=gorev_tipi_filter)

    # Tarih filtresi
    if tarih_filter:
        try:
            if tarih_filter == "bugun":
                gorevler = gorevler.filter(baslangic_tarihi__date=timezone.now().date())
            elif tarih_filter == "bu_hafta":
                bugun = timezone.now().date()
                hafta_baslangic = bugun - timedelta(days=bugun.weekday())
                gorevler = gorevler.filter(baslangic_tarihi__date__gte=hafta_baslangic)
            elif tarih_filter == "bu_ay":
                bugun = timezone.now().date()
                ay_baslangic = bugun.replace(day=1)
                gorevler = gorevler.filter(baslangic_tarihi__date__gte=ay_baslangic)
        except:
            pass

    # Sıralama
    if sort_direction == "desc":
        sort_by = f"-{sort_by}"

    valid_sorts = ["baslangic_tarihi", "bitis_tarihi", "baslik", "oncelik", "durum"]
    if sort_by.lstrip("-") in valid_sorts:
        gorevler = gorevler.order_by(sort_by)
    else:
        gorevler = gorevler.order_by("-baslangic_tarihi")

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
        "acil": gorevler.filter(oncelik="acil").count(),
    }

    # Filtre seçenekleri
    from .models import GorevTipi

    personeller = Personel.objects.filter(aktif=True).order_by("ad")
    parklar = Park.objects.select_related("mahalle").order_by("ad")[:100]
    gorev_tipleri = GorevTipi.objects.order_by("ad")

    context = {
        "gorevler": gorevler_page,
        "stats": stats,
        "search_query": search_query,
        "durum_filter": durum_filter,
        "oncelik_filter": oncelik_filter,
        "park_filter": park_filter,
        "personel_filter": personel_filter,
        "gorev_tipi_filter": gorev_tipi_filter,
        "tarih_filter": tarih_filter,
        "sort_by": request.GET.get("sort", "baslangic_tarihi"),
        "sort_direction": sort_direction,
        "per_page": per_page,
        "personeller": personeller,
        "parklar": parklar,
        "gorev_tipleri": gorev_tipleri,
    }

    return render(request, "istakip/gorev_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def gorev_create(request):
    """Yeni görev oluşturma"""

    if request.method == "POST":
        try:
            with transaction.atomic():
                # Form verilerini al
                park_uuid = request.POST.get("park")
                gorev_tipi_uuid = request.POST.get("gorev_tipi")
                baslik = request.POST.get("baslik")
                aciklama = request.POST.get("aciklama", "")
                oncelik = request.POST.get("oncelik", "normal")
                baslangic_tarihi = request.POST.get("baslangic_tarihi")
                bitis_tarihi = request.POST.get("bitis_tarihi")
                tekrar_tipi = request.POST.get("tekrar_tipi", "yok")
                atanan_personeller = request.POST.getlist("atanan_personeller")

                # Gerekli alanları kontrol et
                if not all([park_uuid, baslik, baslangic_tarihi]):
                    messages.error(
                        request, "Park, başlık ve başlangıç tarihi zorunludur."
                    )
                    return redirect("istakip:gorev_create")

                # İlişkili modelleri getir
                park = get_object_or_404(Park, uuid=park_uuid)
                gorev_tipi = None
                if gorev_tipi_uuid:
                    try:
                        from .models import GorevTipi

                        gorev_tipi = GorevTipi.objects.get(uuid=gorev_tipi_uuid)
                    except GorevTipi.DoesNotExist:
                        pass

                # Görev oluştur
                gorev = Gorev.objects.create(
                    park=park,
                    gorev_tipi=gorev_tipi,
                    baslik=baslik,
                    aciklama=aciklama,
                    oncelik=oncelik,
                    baslangic_tarihi=baslangic_tarihi,
                    bitis_tarihi=bitis_tarihi if bitis_tarihi else None,
                    tekrar_tipi=tekrar_tipi,
                    olusturan=request.user,
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

                messages.success(
                    request, f"Görev başarıyla oluşturuldu: {gorev.baslik}"
                )
                return redirect("istakip:gorev_detail", gorev_uuid=gorev.uuid)

        except Exception as e:
            messages.error(request, f"Görev oluşturulurken hata: {str(e)}")

    # GET request - Form göster
    from .models import GorevTipi

    parklar = Park.objects.select_related("mahalle").order_by("ad")
    personeller = Personel.objects.filter(aktif=True).order_by("ad")
    gorev_tipleri = GorevTipi.objects.order_by("ad")

    context = {
        "parklar": parklar,
        "personeller": personeller,
        "gorev_tipleri": gorev_tipleri,
    }

    return render(request, "istakip/gorev_create.html", context)


@login_required
def gorev_detail(request, gorev_uuid):
    """Görev detay sayfası"""

    gorev = get_object_or_404(
        Gorev.objects.select_related(
            "park", "gorev_tipi", "olusturan", "gunluk_kontrol"
        ).prefetch_related(
            "atamalar__personel", "asamalar", "tamamlama_resimleri", "denetim_kayitlari"
        ),
        uuid=gorev_uuid,
    )

    # Aşama istatistikleri
    asama_stats = {
        "toplam": gorev.asamalar.count(),
        "tamamlanan": gorev.asamalar.filter(durum="tamamlandi").count(),
        "devam_eden": gorev.asamalar.filter(durum="devam_ediyor").count(),
    }

    # İlerleme yüzdesi
    ilerleme = 0
    if asama_stats["toplam"] > 0:
        ilerleme = (asama_stats["tamamlanan"] / asama_stats["toplam"]) * 100

    context = {
        "gorev": gorev,
        "asama_stats": asama_stats,
        "ilerleme": round(ilerleme, 1),
    }

    return render(request, "istakip/gorev_detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def gorev_edit(request, gorev_uuid):
    """Görev düzenleme"""

    gorev = get_object_or_404(Gorev, uuid=gorev_uuid)

    if request.method == "POST":
        try:
            with transaction.atomic():
                # Form verilerini al ve güncelle
                gorev.baslik = request.POST.get("baslik", gorev.baslik)
                gorev.aciklama = request.POST.get("aciklama", gorev.aciklama)
                gorev.oncelik = request.POST.get("oncelik", gorev.oncelik)
                gorev.durum = request.POST.get("durum", gorev.durum)

                baslangic_tarihi = request.POST.get("baslangic_tarihi")
                if baslangic_tarihi:
                    gorev.baslangic_tarihi = baslangic_tarihi

                bitis_tarihi = request.POST.get("bitis_tarihi")
                if bitis_tarihi:
                    gorev.bitis_tarihi = bitis_tarihi

                gorev.save()

                # Personel atamalarını güncelle
                atanan_personeller = request.POST.getlist("atanan_personeller")
                # Mevcut atamaları sil
                gorev.atamalar.all().delete()

                # Yeni atamaları ekle
                for personel_uuid in atanan_personeller:
                    try:
                        personel = Personel.objects.get(uuid=personel_uuid)
                        GorevAtama.objects.create(
                            gorev=gorev, personel=personel, gorev_rolu="Yürütücü"
                        )
                    except Personel.DoesNotExist:
                        continue

                messages.success(request, "Görev başarıyla güncellendi.")
                return redirect("istakip:gorev_detail", gorev_uuid=gorev.uuid)

        except Exception as e:
            messages.error(request, f"Görev güncellenirken hata: {str(e)}")

    # GET request - Form göster
    from .models import GorevTipi

    parklar = Park.objects.select_related("mahalle").order_by("ad")
    personeller = Personel.objects.filter(aktif=True).order_by("ad")
    gorev_tipleri = GorevTipi.objects.order_by("ad")

    # Mevcut atamalar
    atanan_personeller = [atama.personel.uuid for atama in gorev.atamalar.all()]

    context = {
        "gorev": gorev,
        "parklar": parklar,
        "personeller": personeller,
        "gorev_tipleri": gorev_tipleri,
        "atanan_personeller": atanan_personeller,
        "is_edit": True,
    }

    return render(request, "istakip/gorev_create.html", context)


@login_required
def gorev_planlama(request):
    """Görev planlama takvimi"""

    # Aktif görevleri getir
    gorevler = (
        Gorev.objects.filter(durum__in=["planlanmis", "devam_ediyor"])
        .select_related("park", "gorev_tipi")
        .prefetch_related("atamalar__personel")
        .order_by("baslangic_tarihi")
    )

    # Takvim için görevleri hazırla
    takvim_gorevler = []
    for gorev in gorevler:
        takvim_gorevler.append(
            {
                "id": str(gorev.uuid),
                "title": gorev.baslik,
                "start": (
                    gorev.baslangic_tarihi.isoformat()
                    if gorev.baslangic_tarihi
                    else None
                ),
                "end": gorev.bitis_tarihi.isoformat() if gorev.bitis_tarihi else None,
                "color": {
                    "acil": "#ef4444",
                    "yuksek": "#f97316",
                    "normal": "#10b981",
                    "dusuk": "#6b7280",
                }.get(gorev.oncelik, "#10b981"),
                "description": gorev.aciklama or "",
                "park": gorev.park.ad,
                "durum": gorev.get_durum_display(),
                "oncelik": gorev.get_oncelik_display(),
            }
        )

    context = {
        "gorevler": gorevler,
        "takvim_gorevler": takvim_gorevler,
    }

    return render(request, "istakip/gorev_planlama.html", context)


@login_required
def gorev_rapor(request):
    """Görev raporları ve analizleri"""

    # Tarih aralığı
    bugun = timezone.now().date()
    gecen_ay = bugun - timedelta(days=30)
    gecen_hafta = bugun - timedelta(days=7)

    # Temel istatistikler
    tum_gorevler = Gorev.objects.all()

    # Durum bazlı analiz
    durum_stats = {
        "planlanmis": tum_gorevler.filter(durum="planlanmis").count(),
        "devam_ediyor": tum_gorevler.filter(durum="devam_ediyor").count(),
        "tamamlandi": tum_gorevler.filter(durum="tamamlandi").count(),
        "iptal": tum_gorevler.filter(durum="iptal").count(),
        "toplam": tum_gorevler.count(),
    }

    # Öncelik bazlı analiz
    oncelik_stats = {
        "acil": tum_gorevler.filter(oncelik="acil").count(),
        "yuksek": tum_gorevler.filter(oncelik="yuksek").count(),
        "normal": tum_gorevler.filter(oncelik="normal").count(),
        "dusuk": tum_gorevler.filter(oncelik="dusuk").count(),
    }

    # Park bazlı analiz
    park_stats = (
        tum_gorevler.values("park__ad", "park__uuid")
        .annotate(
            gorev_sayisi=Count("id"),
            tamamlanan=Count("id", filter=Q(durum="tamamlandi")),
        )
        .order_by("-gorev_sayisi")[:10]
    )

    # Personel bazlı analiz
    personel_stats = (
        GorevAtama.objects.values("personel__ad", "personel__uuid")
        .annotate(
            atanan_gorev=Count("id"),
            tamamlanan=Count("id", filter=Q(gorev__durum="tamamlandi")),
        )
        .order_by("-atanan_gorev")[:10]
    )

    # Aylık trend analizi
    aylik_trend = []
    for i in range(12):
        ay_oncesi = bugun.replace(day=1) - timedelta(days=30 * i)
        ay_baslangic = ay_oncesi.replace(day=1)
        ay_bitis = (
            ay_baslangic.replace(month=ay_baslangic.month % 12 + 1)
            if ay_baslangic.month < 12
            else ay_baslangic.replace(year=ay_baslangic.year + 1, month=1)
        ) - timedelta(days=1)

        ay_gorevler = tum_gorevler.filter(
            baslangic_tarihi__date__gte=ay_baslangic,
            baslangic_tarihi__date__lte=ay_bitis,
        ).count()

        aylik_trend.append(
            {"ay": ay_baslangic.strftime("%m/%Y"), "gorev_sayisi": ay_gorevler}
        )
    aylik_trend.reverse()

    # Tamamlanma oranları
    tamamlanma_orani = (
        (durum_stats["tamamlandi"] / durum_stats["toplam"] * 100)
        if durum_stats["toplam"] > 0
        else 0
    )

    context = {
        "durum_stats": durum_stats,
        "oncelik_stats": oncelik_stats,
        "park_stats": park_stats,
        "personel_stats": personel_stats,
        "aylik_trend": aylik_trend,
        "tamamlanma_orani": round(tamamlanma_orani, 1),
        "gecen_hafta_gorev": tum_gorevler.filter(
            baslangic_tarihi__date__gte=gecen_hafta
        ).count(),
        "gecen_ay_gorev": tum_gorevler.filter(
            baslangic_tarihi__date__gte=gecen_ay
        ).count(),
    }

    return render(request, "istakip/gorev_rapor.html", context)
