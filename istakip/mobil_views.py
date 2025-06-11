import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView

from parkbahce.models import Park

from .forms import MobilKontrolForm, MobilKontrolResimForm
from .models import Gorev, GorevAsama, GunlukKontrol, KontrolResim, Personel


class MobilSorunBildirView(LoginRequiredMixin, TemplateView):
    """
    Mobil saha personeli için sorun bildirimi sayfası
    """

    template_name = "istakip/mobil/sorun_bildir.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Kullanıcının personel kaydını al
        try:
            personel = Personel.objects.get(user=self.request.user)
            context["personel"] = personel
        except Personel.DoesNotExist:
            context["personel"] = None

        context["kontrol_form"] = MobilKontrolForm()
        context["resim_form"] = MobilKontrolResimForm()

        return context


@login_required
def mobil_konum_park_bul(request):
    """
    Verilen konum koordinatlarına göre park bulma API
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            lat = data.get("lat")
            lng = data.get("lng")

            # lat ve lng kontrolü
            if lat is None or lng is None:
                return JsonResponse(
                    {"success": False, "message": _("Eksik konum bilgisi.")}
                )

            lat = float(lat)
            lng = float(lng)

            # Nokta oluştur
            konum = Point(lng, lat, srid=4326)
            konum.transform(
                5256
            )  # Türkiye koordinat sistemine dönüştür            # En yakın parkı bul (500 metre yarıçapında)
            park = (
                Park.objects.filter(
                    geom__distance_lte=(konum, D(m=settings.DISTANCE_PRECISION))
                )
                .annotate(distance=Distance("geom", konum))  # Mesafe hesaplaması
                .order_by("distance")
                .first()
            )
            if park:
                # Park geometrisini WGS84 formatına dönüştür (frontend için)
                park_geom_wgs84 = park.geom.transform(4326, clone=True)

                # Debug: koordinatları logla
                print(f"Park: {park.ad}")
                print(f"Original SRID: {park.geom.srid}")
                print(f"Transformed extent: {park_geom_wgs84.extent}")

                # Park bilgilerini döndür
                return JsonResponse(
                    {
                        "success": True,
                        "park": {
                            "uuid": str(park.uuid),
                            "ad": park.ad,
                            "alan": park.alan,
                            "mahalle": park.mahalle.ad if park.mahalle else "",
                            "park_tipi": park.park_tipi.ad if park.park_tipi else "",
                            "bounds": (
                                park_geom_wgs84.extent if park_geom_wgs84 else None
                            ),
                            "geojson": (
                                park_geom_wgs84.geojson if park_geom_wgs84 else None
                            ),  # GeoJSON ekle
                            "distance": (
                                park.distance.m if hasattr(park, "distance") else None
                            ),  # Mesafeyi metre cinsinden ekle
                        },
                    }
                )
            else:
                return JsonResponse(
                    {"success": False, "message": _("Bu konumda park bulunamadı.")}
                )

        except (ValueError, json.JSONDecodeError) as e:
            return JsonResponse(
                {"success": False, "message": _("Geçersiz konum bilgisi.")}
            )

    return JsonResponse({"success": False, "message": _("Geçersiz istek.")})


@login_required
def mobil_sorun_kaydet(request):
    """
    Mobil sorun kaydı API
    """
    if request.method == "POST":
        # Personel kontrolü
        print("Gelen request.FILES:", request.FILES)
        try:
            personel = Personel.objects.get(user=request.user)
        except Personel.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": _("Personel kaydınız bulunamadı.")}
            )

        park_uuid = request.POST.get("park_uuid")
        durum = request.POST.get("durum")
        aciklama = request.POST.get("aciklama", "")
        lat = request.POST.get("lat")
        lng = request.POST.get("lng")

        try:
            park = Park.objects.get(uuid=park_uuid)

            # Konum oluştur
            konum = None
            if lat and lng:
                konum = Point(float(lng), float(lat), srid=4326)
                konum.transform(5256)

            # Günlük kontrol oluştur
            kontrol = GunlukKontrol.objects.create(
                park=park,
                personel=personel,
                durum=durum,
                aciklama=aciklama,
                geom=konum,
                kontrol_tipi="rutin",
            )

            # Eğer sorun varsa ve resimler yüklenecekse
            resim_sayisi = 0
            if durum in ["sorun_var", "acil"]:
                for i in range(1, 4):  # En fazla 3 resim
                    resim_field = f"resim_{i}"
                    if resim_field in request.FILES:
                        resim_file = request.FILES[resim_field]
                        aciklama_field = request.POST.get(f"resim_aciklama_{i}", "")

                        # Resim kaydı oluştur
                        KontrolResim.objects.create(
                            gunluk_kontrol=kontrol,
                            resim=resim_file,
                            aciklama=aciklama_field,
                        )
                        resim_sayisi += 1

            return JsonResponse(
                {
                    "success": True,
                    "message": _("Kontrol kaydı başarıyla oluşturuldu."),
                    "kontrol_id": str(kontrol.uuid),
                    "resim_sayisi": resim_sayisi,
                }
            )

        except Park.DoesNotExist:
            return JsonResponse({"success": False, "message": _("Park bulunamadı.")})
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": _("Bir hata oluştu: {}").format(str(e))}
            )

    return JsonResponse({"success": False, "message": _("Geçersiz istek.")})


class MobilKontrolListesiView(LoginRequiredMixin, ListView):
    """
    Personelin yaptığı kontrollerin listesi
    """

    model = GunlukKontrol
    template_name = "istakip/mobil/kontrol_listesi.html"
    context_object_name = "kontroller"
    paginate_by = 20

    def get_queryset(self):
        # Sadece giriş yapan personelin kontrollerini getir
        try:
            personel = Personel.objects.get(user=self.request.user)
            qs = GunlukKontrol.objects.filter(personel=personel)

            # Tarih filtreleme
            baslangic = self.request.GET.get("baslangic")
            bitis = self.request.GET.get("bitis")

            if baslangic:
                try:
                    baslangic_tarih = datetime.strptime(baslangic, "%Y-%m-%d")
                    qs = qs.filter(kontrol_tarihi__gte=baslangic_tarih)
                except ValueError:
                    pass

            if bitis:
                try:
                    bitis_tarih = datetime.strptime(bitis, "%Y-%m-%d")
                    qs = qs.filter(kontrol_tarihi__lte=bitis_tarih)
                except ValueError:
                    pass

            return (
                qs.select_related("park", "park__mahalle")
                .prefetch_related("resimler")
                .order_by("-kontrol_tarihi")
            )

        except Personel.DoesNotExist:
            return GunlukKontrol.objects.none()


class MobilSorunListesiView(LoginRequiredMixin, ListView):
    """
    Personelin bildirdiği sorunların listesi
    """

    model = GunlukKontrol
    template_name = "istakip/mobil/sorun_listesi.html"
    context_object_name = "sorunlar"
    paginate_by = 20

    def get_queryset(self):
        try:
            personel = Personel.objects.get(user=self.request.user)
            return (
                GunlukKontrol.objects.filter(
                    personel=personel, durum__in=["sorun_var", "acil"]
                )
                .select_related("park", "park__mahalle")
                .prefetch_related("resimler")
                .order_by("-kontrol_tarihi")
            )
        except Personel.DoesNotExist:
            return GunlukKontrol.objects.none()


class MobilAtananGorevlerView(LoginRequiredMixin, ListView):
    """
    Personele atanan görevlerin listesi
    """

    model = Gorev
    template_name = "istakip/mobil/atanan_gorevler.html"
    context_object_name = "gorevler"
    paginate_by = 20

    def get_queryset(self):
        try:
            personel = Personel.objects.get(user=self.request.user)
            return (
                Gorev.objects.filter(atamalar__personel=personel)
                .select_related("park", "gorev_tipi")
                .prefetch_related("atamalar")
                .order_by("-created_at")
            )
        except Personel.DoesNotExist:
            return Gorev.objects.none()


class MobilGunlukRaporView(LoginRequiredMixin, TemplateView):
    """
    Personelin günlük raporları
    """

    template_name = "istakip/mobil/gunluk_rapor.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            personel = Personel.objects.get(user=self.request.user)
            bugün = timezone.now().date()

            # Bugünkü kontroller
            bugun_kontroller = (
                GunlukKontrol.objects.filter(
                    personel=personel, kontrol_tarihi__date=bugün
                )
                .select_related("park")
                .prefetch_related("resimler")
            )

            # İstatistikler
            context.update(
                {
                    "personel": personel,
                    "bugun_kontroller": bugun_kontroller,
                    "bugun_toplam": bugun_kontroller.count(),
                    "bugun_sorun_var": bugun_kontroller.filter(
                        durum="sorun_var"
                    ).count(),
                    "bugun_acil": bugun_kontroller.filter(durum="acil").count(),
                    "bugun_sorun_yok": bugun_kontroller.filter(
                        durum="sorun_yok"
                    ).count(),
                }
            )

        except Personel.DoesNotExist:
            context["personel"] = None

        return context


class MobilSorumluParklarView(LoginRequiredMixin, ListView):
    """
    Personelin sorumlu olduğu parkların listesi ve günlük kontrol durumları
    """

    model = Park
    template_name = "istakip/mobil/sorumlu_parklar.html"
    context_object_name = "parklar"
    paginate_by = 20

    def get_queryset(self):
        try:
            personel = Personel.objects.get(user=self.request.user)
            # ParkPersonel through model üzerinden sorumlu olunan parkları getir
            return (
                Park.objects.filter(park_personeller__personel=personel)
                .select_related("mahalle", "mahalle__ilce", "park_tipi")
                .prefetch_related("gunluk_kontroller")
                .order_by("ad")
            )
        except Personel.DoesNotExist:
            return Park.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            personel = Personel.objects.get(user=self.request.user)
            context["personel"] = personel

            # Bugünün tarihini al
            bugun = timezone.now().date()

            # Her park için bugünkü kontrol durumunu hesapla
            parklar_with_status = []
            for park in context["parklar"]:
                # Bu parkta bugün yapılan kontroller
                bugun_kontroller = park.gunluk_kontroller.filter(
                    kontrol_tarihi__date=bugun, personel=personel
                )

                # Son kontrol tarihi
                son_kontrol = (
                    park.gunluk_kontroller.filter(personel=personel)
                    .order_by("-kontrol_tarihi")
                    .first()
                )

                park_info = {
                    "park": park,
                    "bugun_kontrolu_yapildi": bugun_kontroller.exists(),
                    "bugun_kontrol_sayisi": bugun_kontroller.count(),
                    "son_kontrol": son_kontrol,
                    "son_kontrol_tarihi": (
                        son_kontrol.kontrol_tarihi if son_kontrol else None
                    ),
                    "son_kontrol_durumu": (
                        son_kontrol.get_durum_display() if son_kontrol else None
                    ),
                }
                parklar_with_status.append(park_info)

            context["parklar_with_status"] = parklar_with_status
            context["bugun"] = bugun

        except Personel.DoesNotExist:
            context["personel"] = None
            context["parklar_with_status"] = []

        return context
