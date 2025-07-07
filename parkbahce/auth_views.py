from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from istakip.models import Gorev, GunlukKontrol, Personel
from parkbahce.models import Park


def login_view(request):
    """Kullanıcı giriş sayfası"""
    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(
                        request,
                        f"Hoş geldiniz, {user.get_full_name() or user.username}!",
                    )

                    # Kullanıcı rolüne göre yönlendirme
                    user_groups = user.groups.values_list("name", flat=True)

                    # Eğer sadece saha personeli rolü varsa direkt sorun bildirme sayfasına yönlendir
                    if list(user_groups) == ["saha"]:
                        return redirect("istakip:mobil_sorun_bildir")

                    # Diğer durumlar için ana sayfaya yönlendir
                    next_url = request.GET.get("next", "index")
                    return redirect(next_url)
                else:
                    messages.error(request, "Hesabınız devre dışı bırakılmış.")
            else:
                messages.error(request, "Kullanıcı adı veya şifre hatalı.")
        else:
            messages.error(request, "Kullanıcı adı ve şifre alanları zorunludur.")

    return render(request, "auth/login.html")


def logout_view(request):
    """Kullanıcı çıkış işlemi"""
    user_name = (
        request.user.get_full_name() or request.user.username
        if request.user.is_authenticated
        else None
    )
    logout(request)

    if user_name:
        messages.success(
            request, f"Güvenli bir şekilde çıkış yaptınız. Görüşmek üzere {user_name}!"
        )

    return redirect("login")


@login_required
def profile_view(request):
    """Kullanıcı profil sayfası"""
    user = request.user

    # Kullanıcının personel kaydı varsa al
    try:
        personel = Personel.objects.get(user=user)
    except Personel.DoesNotExist:
        personel = None

    # Kullanıcının sorumlu olduğu parklar
    sorumlu_parklar = []
    if personel:
        sorumlu_parklar = (
            Park.objects.filter(park_personeller__personel=personel)
            .select_related("mahalle", "park_tipi")
            .distinct()
        )

    # Son 30 günlük veri için tarih
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Kullanıcının görevleri
    gorevler = []
    gunluk_kontroller = []

    # İstatistikler için varsayılan değerler
    stats = {
        "toplam_parklar": 0,
        "aktif_gorevler": 0,
        "tamamlanan_gorevler": 0,
        "son_kontrol_sayisi": 0,
    }

    if personel:
        # Görevler queryset
        gorevler_queryset = (
            Gorev.objects.filter(
                atanan_personeller=personel, created_at__gte=thirty_days_ago
            )
            .select_related("park", "gorev_tipi")
            .order_by("-created_at")
        )

        # İstatistikler için görev sayıları
        stats["aktif_gorevler"] = gorevler_queryset.filter(
            durum__in=["planlanmis", "basladi"]
        ).count()
        stats["tamamlanan_gorevler"] = gorevler_queryset.filter(
            durum="tamamlandi"
        ).count()

        # Görev listesi için ilk 10 kayıt
        gorevler = list(gorevler_queryset[:10])

        # Günlük kontroller queryset
        gunluk_kontroller_queryset = (
            GunlukKontrol.objects.filter(
                personel=personel, created_at__gte=thirty_days_ago
            )
            .select_related("park")
            .order_by("-kontrol_tarihi")
        )

        # Kontrol sayısı
        stats["son_kontrol_sayisi"] = gunluk_kontroller_queryset.count()

        # Kontrol listesi için ilk 10 kayıt
        gunluk_kontroller = list(gunluk_kontroller_queryset[:10])

        # Toplam park sayısı
        stats["toplam_parklar"] = sorumlu_parklar.count()

    # Kullanıcı grupları
    user_groups = user.groups.all()

    # Son aktiviteler (birleşik)
    aktiviteler = []

    # Görevleri ekle
    for gorev in gorevler[:5]:
        aktiviteler.append(
            {
                "tip": "gorev",
                "tarih": gorev.created_at,
                "baslik": gorev.baslik,
                "aciklama": f"{gorev.park.ad} - {gorev.get_durum_display()}",
                "icon": "fas fa-tasks",
                "color": (
                    "blue"
                    if gorev.durum == "basladi"
                    else "green" if gorev.durum == "tamamlandi" else "gray"
                ),
            }
        )

    # Kontrolleri ekle
    for kontrol in gunluk_kontroller[:5]:
        aktiviteler.append(
            {
                "tip": "kontrol",
                "tarih": kontrol.kontrol_tarihi,
                "baslik": f"{kontrol.park.ad} Kontrolü",
                "aciklama": f"{kontrol.get_durum_display()} - {kontrol.get_kontrol_tipi_display()}",
                "icon": "fas fa-clipboard-check",
                "color": (
                    "red"
                    if kontrol.durum == "sorun_var"
                    else "orange" if kontrol.durum == "acil" else "green"
                ),
            }
        )

    # Tarihe göre sırala
    aktiviteler.sort(key=lambda x: x["tarih"], reverse=True)
    aktiviteler = aktiviteler[:10]  # Son 10 aktivite

    context = {
        "user": user,
        "personel": personel,
        "sorumlu_parklar": sorumlu_parklar,
        "gorevler": gorevler,
        "gunluk_kontroller": gunluk_kontroller,
        "stats": stats,
        "user_groups": user_groups,
        "aktiviteler": aktiviteler,
    }

    return render(request, "auth/profile.html", context)


@login_required
def profile_settings_view(request):
    """Kullanıcı profil ayarları"""
    if request.method == "POST":
        user = request.user

        # Temel bilgileri güncelle
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.save()

        # Personel bilgilerini güncelle (varsa)
        try:
            personel = Personel.objects.get(user=user)
            telefon = request.POST.get("telefon", "").strip()
            pozisyon = request.POST.get("pozisyon", "").strip()

            personel.ad = f"{first_name} {last_name}".strip() or user.username
            personel.telefon = telefon
            personel.eposta = email
            personel.pozisyon = pozisyon
            personel.save()

        except Personel.DoesNotExist:
            pass

        messages.success(request, "Profil bilgileriniz başarıyla güncellendi.")
        return redirect("parkbahce:profile")

    return redirect("parkbahce:profile")
