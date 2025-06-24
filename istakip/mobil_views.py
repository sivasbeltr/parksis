import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView

from parkbahce.forms import MobilEndeksForm
from parkbahce.models import AboneEndeks, Park, ParkAbone

from .forms import MobilKontrolForm
from .models import (
    Gorev,
    GorevAsama,
    GorevTamamlamaResim,
    GunlukKontrol,
    KontrolResim,
    Personel,
)


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

        return context

    def post(self, request, *args, **kwargs):
        """
        Form post işlemi - sorun bildirimi
        """
        print("Gelen Dosyalar:", request.FILES)
        try:
            personel = Personel.objects.get(user=request.user)
        except Personel.DoesNotExist:
            messages.error(request, _("Personel kaydınız bulunamadı."))
            return redirect("istakip:mobil_sorun_bildir")

        # Form verilerini al
        park_uuid = request.POST.get("park_uuid")
        durum = request.POST.get("durum")
        aciklama = request.POST.get("aciklama", "")
        lat = request.POST.get("lat")
        lng = request.POST.get("lng")

        if not park_uuid or not durum:
            messages.error(request, _("Gerekli alanlar eksik."))
            return redirect("istakip:mobil_sorun_bildir")

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

                        try:
                            # Resim kaydı oluştur
                            KontrolResim.objects.create(
                                gunluk_kontrol=kontrol,
                                resim=resim_file,
                                aciklama=aciklama_field,
                            )
                            resim_sayisi += 1
                        except ValueError as e:
                            # 3 resim sınırı aşılırsa
                            if resim_sayisi >= 3:
                                break

            # Başarılı sayfaya yönlendir
            return redirect(
                "istakip:mobil_kontrol_gonderildi", kontrol_uuid=kontrol.uuid
            )

        except Park.DoesNotExist:
            messages.error(request, _("Park bulunamadı."))
            return redirect("istakip:mobil_sorun_bildir")
        except Exception as e:
            messages.error(request, _("Bir hata oluştu: {}").format(str(e)))
            return redirect("istakip:mobil_sorun_bildir")


class MobilKontrolGonderildiView(LoginRequiredMixin, TemplateView):
    """
    Kontrol başarıyla gönderildi sayfası
    """

    template_name = "istakip/mobil/kontrol_gonderildi.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        kontrol_uuid = kwargs.get("kontrol_uuid")
        try:
            kontrol = get_object_or_404(
                GunlukKontrol.objects.select_related(
                    "park",
                    "park__mahalle",
                    "park__mahalle__ilce",
                    "park__park_tipi",
                    "park__sulama_tipi",
                    "personel",
                ).prefetch_related("resimler"),
                uuid=kontrol_uuid,
                personel__user=self.request.user,
            )
            context["kontrol"] = kontrol

            # İstatistik verilerini hesapla
            personel = kontrol.personel
            bugün = timezone.now().date()
            hafta_başı = bugün - timedelta(days=bugün.weekday())
            ay_başı = bugün.replace(day=1)

            # Bugünkü kontroller
            bugun_kontroller = GunlukKontrol.objects.filter(
                personel=personel, kontrol_tarihi__date=bugün
            )

            # Bu haftaki kontroller
            hafta_kontroller = GunlukKontrol.objects.filter(
                personel=personel, kontrol_tarihi__date__gte=hafta_başı
            )

            # Bu ayki kontroller
            ay_kontroller = GunlukKontrol.objects.filter(
                personel=personel, kontrol_tarihi__date__gte=ay_başı
            )

            # Oranları hesapla
            toplam_ay = ay_kontroller.count()
            sorunsuz_ay = ay_kontroller.filter(durum="sorun_yok").count()
            sorunlu_ay = ay_kontroller.filter(durum__in=["sorun_var", "acil"]).count()

            sorunsuz_oran = round(
                (sorunsuz_ay / toplam_ay * 100) if toplam_ay > 0 else 0
            )
            sorunlu_oran = round((sorunlu_ay / toplam_ay * 100) if toplam_ay > 0 else 0)

            context["stats"] = {
                "bugun_kontrol": bugun_kontroller.count(),
                "hafta_kontrol": hafta_kontroller.count(),
                "ay_kontrol": toplam_ay,
                "sorunsuz_oran": sorunsuz_oran,
                "sorunlu_oran": sorunlu_oran,
            }

        except GunlukKontrol.DoesNotExist:
            context["kontrol"] = None
            context["stats"] = {
                "bugun_kontrol": 0,
                "hafta_kontrol": 0,
                "ay_kontrol": 0,
                "sorunsuz_oran": 0,
                "sorunlu_oran": 0,
            }

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
            qs = (
                Gorev.objects.filter(atamalar__personel=personel)
                .select_related("park", "park__mahalle", "gorev_tipi")
                .prefetch_related("atamalar__personel", "asamalar")
                .order_by("-created_at")
            )

            # Filtreleme
            durum = self.request.GET.get("durum")
            oncelik = self.request.GET.get("oncelik")
            baslangic = self.request.GET.get("baslangic")
            bitis = self.request.GET.get("bitis")

            # Varsayılan olarak tamamlanmamış görevler
            if not durum:
                durum = "aktif"

            if durum == "aktif":
                qs = qs.exclude(durum__in=["tamamlandi", "iptal"])
            elif durum != "":
                qs = qs.filter(durum=durum)

            if oncelik:
                qs = qs.filter(oncelik=oncelik)

            if baslangic:
                try:
                    baslangic_tarih = datetime.strptime(baslangic, "%Y-%m-%d")
                    qs = qs.filter(created_at__gte=baslangic_tarih)
                except ValueError:
                    pass

            if bitis:
                try:
                    bitis_tarih = datetime.strptime(bitis, "%Y-%m-%d")
                    qs = qs.filter(created_at__lte=bitis_tarih)
                except ValueError:
                    pass

            return qs
        except Personel.DoesNotExist:
            return Gorev.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Her görev için tamamlanan aşama sayısını hesapla
        for gorev in context["gorevler"]:
            tamamlanan_sayisi = gorev.asamalar.filter(durum="tamamlandi").count()
            gorev.tamamlanan_asama_sayisi = tamamlanan_sayisi

        return context


class MobilAtananGorevDetailView(LoginRequiredMixin, TemplateView):
    """
    Atanan görev detay sayfası - aşamalar ve timeline ile
    """

    template_name = "istakip/mobil/atanan_gorev_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            personel = Personel.objects.get(user=self.request.user)
            gorev_uuid = kwargs.get("gorev_uuid")

            gorev = get_object_or_404(
                Gorev.objects.filter(atamalar__personel=personel)
                .select_related("park", "park__mahalle", "gorev_tipi")
                .prefetch_related(
                    "atamalar__personel", "asamalar", "tamamlama_resimleri"
                ),
                uuid=gorev_uuid,
            )

            # Aşamaları sıralı getir
            asamalar = gorev.asamalar.all().order_by("created_at")

            context.update(
                {
                    "gorev": gorev,
                    "asamalar": asamalar,
                    "personel": personel,
                }
            )

        except Personel.DoesNotExist:
            context["gorev"] = None
            context["asamalar"] = []

        return context


@login_required
def mobil_asama_ekle(request):
    """
    Mobil görev aşaması ekleme
    """
    if request.method == "POST":
        try:
            personel = Personel.objects.get(user=request.user)
            gorev_uuid = request.POST.get("gorev_uuid")

            # Görevin bu personele atanmış olduğunu kontrol et
            gorev = get_object_or_404(
                Gorev.objects.filter(atamalar__personel=personel), uuid=gorev_uuid
            )

            # Görev tamamlanmış veya iptal edilmişse aşama eklenemez
            if gorev.durum in ["tamamlandi", "iptal"]:
                return JsonResponse(
                    {"success": False, "message": "Bu görev için aşama eklenemez."}
                )

            ad = request.POST.get("ad")
            aciklama = request.POST.get("aciklama", "")
            resim = request.FILES.get("resim")

            if not ad:
                return JsonResponse(
                    {"success": False, "message": "Aşama adı zorunludur."}
                )

            # Aşama oluştur
            asama = GorevAsama.objects.create(
                gorev=gorev,
                ad=ad,
                aciklama=aciklama,
                durum="baslamadi",
                sorumlu=personel,
            )

            # Resim varsa kaydet
            if resim:
                asama.resim = resim
                asama.save()

            return JsonResponse(
                {"success": True, "message": "Aşama başarıyla eklendi."}
            )

        except Personel.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Personel kaydınız bulunamadı."}
            )
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Hata: {str(e)}"})

    return JsonResponse({"success": False, "message": "Geçersiz istek."})


@login_required
def mobil_asama_baslat(request, asama_uuid):
    """
    Mobil görev aşamasını başlatma
    """
    if request.method == "POST":
        try:
            personel = Personel.objects.get(user=request.user)

            # Aşamayı bul ve kontrol et
            asama = get_object_or_404(
                GorevAsama.objects.filter(
                    gorev__atamalar__personel=personel
                ).select_related("gorev"),
                uuid=asama_uuid,
            )

            if asama.durum == "devam_ediyor":
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bu aşama zaten başlatılmış ve devam ediyor.",
                    }
                )
            if asama.durum == "tamamlandi":
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bu aşama zaten tamamlanmış.",
                    }
                )

            # Aşamayı başlat ve tarihleri mantıklı şekilde ayarla
            asama.durum = "devam_ediyor"
            asama.baslangic_tarihi = timezone.now()
            # Tamamlanma tarihini sıfırla (geri alınmış olabilir)
            asama.tamamlanma_tarihi = None
            asama.save()

            # Ana görevi de devam ediyor yap (eğer planlanmış ise)
            if asama.gorev.durum == "planlanmis":
                asama.gorev.durum = "devam_ediyor"
                # Görev tarihleri de sıfırla
                asama.gorev.tamamlanma_tarihi = None
                asama.gorev.onay_tarihi = None
                asama.gorev.save()

                # Eğer bağlı bir sorun bildirimi varsa onun da durumunu güncelle
                if asama.gorev.gunluk_kontrol:
                    asama.gorev.gunluk_kontrol.durum = "ise_donusturuldu"
                    asama.gorev.gunluk_kontrol.save()

            return JsonResponse({"success": True, "message": "Aşama başlatıldı."})

        except Personel.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Personel kaydınız bulunamadı."}
            )
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Hata: {str(e)}"})

    return JsonResponse({"success": False, "message": "Geçersiz istek."})


@login_required
def mobil_asama_tamamla(request, asama_uuid):
    """
    Mobil görev aşamasını tamamlama - resim ve açıklama ile
    """
    if request.method == "POST":
        try:
            personel = Personel.objects.get(user=request.user)

            # Aşamayı bul ve kontrol et
            asama = get_object_or_404(
                GorevAsama.objects.filter(
                    gorev__atamalar__personel=personel
                ).select_related("gorev"),
                uuid=asama_uuid,
            )

            if asama.durum != "devam_ediyor":
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bu aşama tamamlanabilir durumda değil.",
                    }
                )

            # Tamamlama mesajını al
            tamamlama_mesaji = request.POST.get("tamamlama_mesaji", "")

            # Eğer tamamlama mesajı varsa, mevcut açıklamaya ekle
            if tamamlama_mesaji:
                if asama.aciklama:
                    asama.aciklama += f"\n\nTamamlama Mesajı: {tamamlama_mesaji}"
                else:
                    asama.aciklama = f"Tamamlama Mesajı: {tamamlama_mesaji}"

            # Aşamayı tamamla ve tarihleri set et
            asama.durum = "tamamlandi"
            asama.tamamlanma_tarihi = timezone.now()
            # Başlangıç tarihi yoksa set et
            if not asama.baslangic_tarihi:
                asama.baslangic_tarihi = timezone.now()

            # Tamamlama resmi varsa kaydet
            if "tamamlama_resmi" in request.FILES:
                asama.resim = request.FILES["tamamlama_resmi"]

            asama.save()

            return JsonResponse({"success": True, "message": "Aşama tamamlandı."})

        except Personel.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Personel kaydınız bulunamadı."}
            )
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Hata: {str(e)}"})

    return JsonResponse({"success": False, "message": "Geçersiz istek."})


@login_required
def mobil_gorev_tamamla(request, gorev_uuid):
    """
    Mobil görev onaya gönderme
    """
    if request.method == "POST":
        try:
            personel = Personel.objects.get(user=request.user)

            # Görevi bul ve kontrol et
            gorev = get_object_or_404(
                Gorev.objects.filter(atamalar__personel=personel), uuid=gorev_uuid
            )

            if gorev.durum in ["tamamlandi", "iptal", "onaya_gonderildi"]:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bu görev zaten tamamlanmış, iptal edilmiş veya onaya gönderilmiş.",
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

            # Görevi onaya gönder
            gorev.durum = "onaya_gonderildi"
            # Onaya gönderildiğinde tamamlanma tarihi geçici olarak set edilir
            gorev.tamamlanma_tarihi = timezone.now()
            # Onay tarihi henüz sıfırlanır
            gorev.onay_tarihi = None
            gorev.save()

            # Eğer bağlı bir sorun bildirimi varsa onun da durumunu güncelle
            if gorev.gunluk_kontrol:
                gorev.gunluk_kontrol.durum = "gozden_gecirildi"
                gorev.gunluk_kontrol.save()

            return JsonResponse({"success": True, "message": "Görev onaya gönderildi."})

        except Personel.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Personel kaydınız bulunamadı."}
            )
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Hata: {str(e)}"})

    return JsonResponse({"success": False, "message": "Geçersiz istek."})


@login_required
def mobil_gorev_onayla(request, gorev_uuid):
    """
    Mobil görevi onaylama (yönetici için)
    """
    if request.method == "POST":
        try:
            # Sadece yöneticiler onaylayabilir
            if (
                not request.user.is_staff
                and not request.user.groups.filter(
                    name__in=["Yönetici", "Park Uzmanı"]
                ).exists()
            ):
                return JsonResponse(
                    {"success": False, "message": "Bu işlem için yetkiniz bulunmuyor."}
                )

            # Görevi bul ve kontrol et
            gorev = get_object_or_404(Gorev, uuid=gorev_uuid)

            if gorev.durum != "onaya_gonderildi":
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bu görev onaylanabilir durumda değil.",
                    }
                )

            # Görevi onayla ve tamamlandı olarak işaretle
            gorev.durum = "tamamlandi"
            # Tamamlanma tarihi zaten onaya gönderilirken set edildi
            # Onay tarihi şimdi set edilir
            gorev.onay_tarihi = timezone.now()
            gorev.save()

            # Eğer bağlı bir sorun bildirimi varsa onun da durumunu güncelle
            if gorev.gunluk_kontrol:
                gorev.gunluk_kontrol.durum = "cozuldu"
                gorev.gunluk_kontrol.save()

            return JsonResponse(
                {"success": True, "message": "Görev başarıyla onaylandı ve tamamlandı."}
            )

        except Exception as e:
            return JsonResponse({"success": False, "message": f"Hata: {str(e)}"})

    return JsonResponse({"success": False, "message": "Geçersiz istek."})


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

            # Toplam park sayısı
            toplam_park_sayisi = context["parklar"].count()

            # Her park için bugünkü kontrol durumunu hesapla
            parklar_with_status = []
            bugun_kontrol_sayisi = 0
            bekleyen_sayisi = 0

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

                bugun_kontrolu_yapildi = bugun_kontroller.exists()

                # İstatistikler için sayaçları artır
                if bugun_kontrolu_yapildi:
                    bugun_kontrol_sayisi += 1
                else:
                    bekleyen_sayisi += 1

                park_info = {
                    "park": park,
                    "bugun_kontrolu_yapildi": bugun_kontrolu_yapildi,
                    "bugun_kontrol_sayisi": bugun_kontroller.count(),
                    "son_kontrol": son_kontrol,
                    "son_kontrol_tarihi": (
                        son_kontrol.kontrol_tarihi if son_kontrol else None
                    ),
                    "son_kontrol_durumu": (
                        son_kontrol.get_durum_display() if son_kontrol else None
                    ),
                    "kontrol_bekleyen": (
                        not bugun_kontrolu_yapildi
                        and (
                            not son_kontrol or son_kontrol.kontrol_tarihi.date() < bugun
                        )
                    ),
                }
                parklar_with_status.append(park_info)

            context.update(
                {
                    "parklar_with_status": parklar_with_status,
                    "bugun": bugun,
                    "toplam_park_sayisi": toplam_park_sayisi,
                    "bugun_kontrol_sayisi": bugun_kontrol_sayisi,
                    "bekleyen_sayisi": bekleyen_sayisi,
                }
            )

        except Personel.DoesNotExist:
            context["personel"] = None
            context["parklar_with_status"] = []
            context["toplam_park_sayisi"] = 0
            context["bugun_kontrol_sayisi"] = 0
            context["bekleyen_sayisi"] = 0

        return context


class MobilPerformansIstatistikView(LoginRequiredMixin, TemplateView):
    """
    Personelin detaylı performans istatistikleri
    """

    template_name = "istakip/mobil/performans_istatistik.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            personel = Personel.objects.get(user=self.request.user)

            # Tarih hesaplamaları
            bugun = timezone.now().date()
            hafta_basi = bugun - timedelta(days=bugun.weekday())
            hafta_sonu = hafta_basi + timedelta(days=6)
            ay_basi = bugun.replace(day=1)

            # Bugünkü kontroller
            bugun_kontroller = GunlukKontrol.objects.filter(
                personel=personel, kontrol_tarihi__date=bugun
            )

            # Haftalık kontroller
            hafta_kontroller = GunlukKontrol.objects.filter(
                personel=personel,
                kontrol_tarihi__date__gte=hafta_basi,
                kontrol_tarihi__date__lte=hafta_sonu,
            )

            # Aylık kontroller
            ay_kontroller = GunlukKontrol.objects.filter(
                personel=personel, kontrol_tarihi__date__gte=ay_basi
            )

            # Bugünkü istatistikler
            bugun_kontrol = bugun_kontroller.count()
            bugun_sorunsuz = bugun_kontroller.filter(durum="sorun_yok").count()
            bugun_sorun_var = bugun_kontroller.filter(durum="sorun_var").count()
            bugun_acil = bugun_kontroller.filter(durum="acil").count()

            # Haftalık istatistikler
            hafta_kontrol = hafta_kontroller.count()
            hafta_sorunsuz = hafta_kontroller.filter(durum="sorun_yok").count()
            hafta_sorunsuz_oran = round(
                (hafta_sorunsuz / hafta_kontrol * 100) if hafta_kontrol > 0 else 0
            )
            hafta_ortalama = hafta_kontrol / 7

            # Aylık istatistikler
            ay_kontrol = ay_kontroller.count()
            ay_sorunsuz = ay_kontroller.filter(durum="sorun_yok").count()
            sorunsuz_oran = round(
                (ay_sorunsuz / ay_kontrol * 100) if ay_kontrol > 0 else 0
            )

            # Sorumlu park sayısı
            sorumlu_park_sayisi = Park.objects.filter(
                park_personeller__personel=personel
            ).count()

            # Toplam resim sayısı (bu ay)
            toplam_resim = KontrolResim.objects.filter(
                gunluk_kontrol__personel=personel,
                gunluk_kontrol__kontrol_tarihi__date__gte=ay_basi,
            ).count()

            # Son 7 günlük trend
            gunluk_trend = []
            max_kontrol = 0

            for i in range(7):
                gun = bugun - timedelta(days=6 - i)
                gun_kontrol = GunlukKontrol.objects.filter(
                    personel=personel, kontrol_tarihi__date=gun
                ).count()

                if gun_kontrol > max_kontrol:
                    max_kontrol = gun_kontrol

                gunluk_trend.append(
                    {
                        "gun": gun,
                        "sayi": gun_kontrol,
                        "yuzde": 0,
                    }  # Bu daha sonra hesaplanacak
                )

            # Yüzdeleri hesapla
            for gun_data in gunluk_trend:
                if max_kontrol > 0:
                    gun_data["yuzde"] = round((gun_data["sayi"] / max_kontrol) * 100)

            # En aktif günü bul
            gun_isimleri = [
                "Pazartesi",
                "Salı",
                "Çarşamba",
                "Perşembe",
                "Cuma",
                "Cumartesi",
                "Pazar",
            ]
            en_aktif_gun_data = max(gunluk_trend, key=lambda x: x["sayi"])
            en_aktif_gun = gun_isimleri[en_aktif_gun_data["gun"].weekday()]

            context.update(
                {
                    "personel": personel,
                    "hafta_baslangic": hafta_basi,
                    "hafta_bitis": hafta_sonu,
                    "ay_baslangic": ay_basi,
                    "stats": {
                        "bugun_kontrol": bugun_kontrol,
                        "bugun_sorunsuz": bugun_sorunsuz,
                        "bugun_sorun_var": bugun_sorun_var,
                        "bugun_acil": bugun_acil,
                        "hafta_kontrol": hafta_kontrol,
                        "hafta_sorunsuz_oran": hafta_sorunsuz_oran,
                        "hafta_ortalama": hafta_ortalama,
                        "ay_kontrol": ay_kontrol,
                        "sorunsuz_oran": sorunsuz_oran,
                        "sorumlu_park_sayisi": sorumlu_park_sayisi,
                        "ortalama_sure": 15,  # Sabit değer, gerçek hesaplama için zaman bilgisi gerekli
                        "en_aktif_gun": en_aktif_gun,
                        "toplam_resim": toplam_resim,
                        "gunluk_trend": gunluk_trend,
                    },
                }
            )

        except Personel.DoesNotExist:
            context["personel"] = None
            context["stats"] = {}

        return context


class MobilGorevOnayaGonderView(LoginRequiredMixin, TemplateView):
    """
    Mobil görev tamamlama ve onaya gönderme sayfası - resim yükleme ile
    """

    template_name = "istakip/mobil/gorev_onaya_gonder.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            personel = Personel.objects.get(user=self.request.user)
            gorev_uuid = kwargs.get("gorev_uuid")

            gorev = get_object_or_404(
                Gorev.objects.filter(atamalar__personel=personel)
                .select_related("park", "park__mahalle", "gorev_tipi")
                .prefetch_related(
                    "atamalar__personel", "asamalar", "tamamlama_resimleri"
                ),
                uuid=gorev_uuid,
            )

            # Görev durumu kontrolü
            if gorev.durum in ["tamamlandi", "iptal", "onaya_gonderildi"]:
                messages.warning(
                    self.request, "Bu görev için tamamlama işlemi yapılamaz."
                )
                return redirect(
                    "istakip:mobil_atanan_gorev_detail", gorev_uuid=gorev.uuid
                )

            # Aşama istatistikleri
            asamalar = gorev.asamalar.all()
            asama_stats = {
                "toplam": asamalar.count(),
                "tamamlanan": asamalar.filter(durum="tamamlandi").count(),
            }

            # İlerleme yüzdesi
            ilerleme = 0
            if asama_stats["toplam"] > 0:
                ilerleme = int(
                    (asama_stats["tamamlanan"] / asama_stats["toplam"]) * 100
                )

            context.update(
                {
                    "gorev": gorev,
                    "asama_stats": asama_stats,
                    "ilerleme": ilerleme,
                    "personel": personel,
                }
            )

        except Personel.DoesNotExist:
            context["gorev"] = None

        return context

    def post(self, request, *args, **kwargs):
        """
        Görev tamamlama formu işleme
        """
        try:
            personel = Personel.objects.get(user=request.user)
            gorev_uuid = kwargs.get("gorev_uuid")

            gorev = get_object_or_404(
                Gorev.objects.filter(atamalar__personel=personel), uuid=gorev_uuid
            )

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
                    "redirect_url": "{% url 'istakip:mobil_atanan_gorevler' %}",
                }
            )

        except Personel.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Personel kaydınız bulunamadı."}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Bir hata oluştu: {str(e)}"}
            )


class MobilAboneListesiView(LoginRequiredMixin, ListView):
    """
    Mobil abone listesi - endeks girişi için
    """

    model = ParkAbone
    template_name = "istakip/mobil/abone_listesi.html"
    context_object_name = "aboneler"
    paginate_by = 20

    def get_queryset(self):
        try:
            personel = Personel.objects.get(user=self.request.user)
            # Sadece personelin sorumlu olduğu parklardaki aboneleri getir
            qs = (
                ParkAbone.objects.filter(park__park_personeller__personel=personel)
                .select_related("park", "park__mahalle")
                .prefetch_related("endeksler")
                .order_by("park__ad", "abone_tipi", "abone_no")
            )

            # Filtreleme
            search_query = self.request.GET.get("search", "").strip()
            abone_tipi_filter = self.request.GET.get("abone_tipi", "")
            park_filter = self.request.GET.get("park", "")

            if search_query:
                qs = qs.filter(
                    Q(park__ad__icontains=search_query)
                    | Q(abone_no__icontains=search_query)
                )

            if abone_tipi_filter:
                qs = qs.filter(abone_tipi=abone_tipi_filter)

            if park_filter:
                qs = qs.filter(park__uuid=park_filter)

            return qs

        except Personel.DoesNotExist:
            return ParkAbone.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            personel = Personel.objects.get(user=self.request.user)

            # Filtreleme için seçenekler
            sorumlu_parklar = Park.objects.filter(
                park_personeller__personel=personel
            ).order_by("ad")

            # Her abone için son endeks bilgisi
            for abone in context["aboneler"]:
                son_endeks = abone.endeksler.order_by("-endeks_degeri").first()
                abone.son_endeks = son_endeks
                abone.son_endeks_tarihi = (
                    son_endeks.endeks_tarihi if son_endeks else None
                )

                # Bugün endeks girildi mi?
                bugun = timezone.now().date()
                abone.bugun_endeks_var = abone.endeksler.filter(
                    endeks_tarihi=bugun
                ).exists()

            context.update(
                {
                    "personel": personel,
                    "sorumlu_parklar": sorumlu_parklar,
                    "search_query": self.request.GET.get("search", ""),
                    "abone_tipi_filter": self.request.GET.get("abone_tipi", ""),
                    "park_filter": self.request.GET.get("park", ""),
                }
            )

        except Personel.DoesNotExist:
            context["personel"] = None

        return context


class MobilEndeksEkleView(LoginRequiredMixin, TemplateView):
    """
    Mobil endeks ekleme sayfası
    """

    template_name = "istakip/mobil/endeks_ekle.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            personel = Personel.objects.get(user=self.request.user)
            abone_uuid = kwargs.get("abone_uuid")

            # Aboneyi getir ve yetkiyi kontrol et
            abone = get_object_or_404(
                ParkAbone.objects.filter(park__park_personeller__personel=personel)
                .select_related("park", "park__mahalle")
                .prefetch_related("endeksler"),
                uuid=abone_uuid,
            )

            # Son 5 endeks kaydı
            son_endeksler = abone.endeksler.order_by("-endeks_degeri")[:5]

            # Son endeks değeri (en büyük endeks değeri)
            son_endeks = abone.endeksler.order_by("-endeks_degeri").first()

            # Form
            form = MobilEndeksForm(park_abone=abone)

            context.update(
                {
                    "abone": abone,
                    "personel": personel,
                    "form": form,
                    "son_endeksler": son_endeksler,
                    "son_endeks": son_endeks,
                }
            )

        except Personel.DoesNotExist:
            context["abone"] = None

        return context

    def post(self, request, *args, **kwargs):
        """
        Endeks kaydetme işlemi
        """
        try:
            personel = Personel.objects.get(user=request.user)
            abone_uuid = kwargs.get("abone_uuid")

            # Aboneyi getir ve yetkiyi kontrol et
            abone = get_object_or_404(
                ParkAbone.objects.filter(park__park_personeller__personel=personel),
                uuid=abone_uuid,
            )

            form = MobilEndeksForm(request.POST, park_abone=abone)

            if form.is_valid():
                endeks = form.save(commit=False)
                endeks.park_abone = abone
                endeks.save()

                messages.success(
                    request,
                    f"✅ {abone.get_abone_tipi_display()} abonesi ({abone.abone_no}) için "
                    f"endeks değeri {endeks.endeks_degeri} başarıyla kaydedildi.",
                )
                return redirect("istakip:mobil_abone_listesi")
            else:
                # Form hatalarını mesaj olarak da göster (mobil için ekstra)
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"❌ {error}")

                # Context'i yeniden hazırla ve aynı sayfayı render et
                context = self.get_context_data(**kwargs)
                context["form"] = form  # Hatalı formu tekrar gönder
                return render(request, self.template_name, context)

        except Personel.DoesNotExist:
            messages.error(request, "❌ Personel kaydınız bulunamadı.")
            return redirect("istakip:mobil_abone_listesi")
        except Exception as e:
            messages.error(request, f"❌ Beklenmeyen bir hata oluştu: {str(e)}")
            return redirect("istakip:mobil_abone_listesi")


class MobilEndeksGecmisiView(LoginRequiredMixin, ListView):
    """
    Mobil endeks geçmişi listesi
    """

    model = AboneEndeks
    template_name = "istakip/mobil/endeks_gecmisi.html"
    context_object_name = "endeksler"
    paginate_by = 30

    def get_queryset(self):
        try:
            personel = Personel.objects.get(user=self.request.user)

            # Sadece personelin sorumlu olduğu parklardaki endeksleri getir
            qs = (
                AboneEndeks.objects.filter(
                    park_abone__park__park_personeller__personel=personel
                )
                .select_related(
                    "park_abone", "park_abone__park", "park_abone__park__mahalle"
                )
                .order_by("-endeks_tarihi", "-created_at")
            )

            # Filtreleme
            tarih_baslangic = self.request.GET.get("tarih_baslangic")
            tarih_bitis = self.request.GET.get("tarih_bitis")
            abone_tipi_filter = self.request.GET.get("abone_tipi", "")

            if tarih_baslangic:
                try:
                    baslangic_tarih = datetime.strptime(
                        tarih_baslangic, "%Y-%m-%d"
                    ).date()
                    qs = qs.filter(endeks_tarihi__gte=baslangic_tarih)
                except ValueError:
                    pass

            if tarih_bitis:
                try:
                    bitis_tarih = datetime.strptime(tarih_bitis, "%Y-%m-%d").date()
                    qs = qs.filter(endeks_tarihi__lte=bitis_tarih)
                except ValueError:
                    pass

            if abone_tipi_filter:
                qs = qs.filter(park_abone__abone_tipi=abone_tipi_filter)

            return qs

        except Personel.DoesNotExist:
            return AboneEndeks.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            personel = Personel.objects.get(user=self.request.user)

            # İstatistikler
            bugun = timezone.now().date()
            bugunku_endeksler = AboneEndeks.objects.filter(
                park_abone__park__park_personeller__personel=personel,
                endeks_tarihi=bugun,
            ).count()

            context.update(
                {
                    "personel": personel,
                    "bugunku_endeksler": bugunku_endeksler,
                    "tarih_baslangic": self.request.GET.get("tarih_baslangic", ""),
                    "tarih_bitis": self.request.GET.get("tarih_bitis", ""),
                    "abone_tipi_filter": self.request.GET.get("abone_tipi", ""),
                }
            )

        except Personel.DoesNotExist:
            context["personel"] = None

        return context


@login_required
def mobil_endeks_kaydet(request):
    """
    AJAX endeks kaydetme API
    """
    if request.method == "POST":
        try:
            personel = Personel.objects.get(user=request.user)

            abone_uuid = request.POST.get("abone_uuid")
            endeks_tarihi = request.POST.get("endeks_tarihi")
            endeks_degeri = request.POST.get("endeks_degeri")

            # Aboneyi getir ve yetkiyi kontrol et
            abone = get_object_or_404(
                ParkAbone.objects.filter(park__park_personeller__personel=personel),
                uuid=abone_uuid,
            )

            # Basit validasyon
            if not endeks_tarihi or not endeks_degeri:
                return JsonResponse(
                    {"success": False, "message": "Tüm alanlar zorunludur."}
                )

            try:
                endeks_tarihi = datetime.strptime(endeks_tarihi, "%Y-%m-%d").date()
                endeks_degeri = float(endeks_degeri)
            except (ValueError, TypeError):
                return JsonResponse(
                    {"success": False, "message": "Geçersiz tarih veya endeks değeri."}
                )

            # Aynı tarihte endeks var mı kontrol et
            if AboneEndeks.objects.filter(
                park_abone=abone, endeks_tarihi=endeks_tarihi
            ).exists():
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bu tarihte zaten bir endeks kaydı bulunmaktadır.",
                    }
                )

            # Son endeks kontrolü (en büyük endeks değeri)
            son_endeks = abone.endeksler.order_by("-endeks_degeri").first()
            if son_endeks and endeks_degeri < son_endeks.endeks_degeri:
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Endeks değeri son kayıtlı değerden ({son_endeks.endeks_degeri}) küçük olamaz.",
                    }
                )
            elif not son_endeks and endeks_degeri < (abone.ilk_endeks or 0):
                return JsonResponse(
                    {
                        "success": False,
                        "message": f"Endeks değeri ilk endeks değerinden ({abone.ilk_endeks or 0}) küçük olamaz.",
                    }
                )

            # Endeks kaydını oluştur
            endeks = AboneEndeks.objects.create(
                park_abone=abone,
                endeks_tarihi=endeks_tarihi,
                endeks_degeri=endeks_degeri,
            )

            # Flash mesaj ekle
            messages.success(
                request,
                f"✅ {abone.get_abone_tipi_display()} abonesi ({abone.abone_no}) için "
                f"endeks değeri {endeks.endeks_degeri} başarıyla kaydedildi.",
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Endeks başarıyla kaydedildi.",
                    "data": {
                        "endeks_degeri": endeks.endeks_degeri,
                        "endeks_tarihi": endeks.endeks_tarihi.strftime("%d.%m.%Y"),
                        "abone_tipi": abone.get_abone_tipi_display(),
                        "abone_no": abone.abone_no,
                    },
                }
            )

        except Personel.DoesNotExist:
            return JsonResponse(
                {"success": False, "message": "Personel kaydınız bulunamadı."}
            )
        except Exception as e:
            return JsonResponse(
                {"success": False, "message": f"Bir hata oluştu: {str(e)}"}
            )
