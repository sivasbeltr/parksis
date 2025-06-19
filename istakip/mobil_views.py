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

from .forms import MobilKontrolForm
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
                )  # Aşamayı başlat
            if asama.durum == "tamamlandi":
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Bu aşama zaten tamamlanmış.",
                    }
                )
            asama.durum = "devam_ediyor"
            asama.baslangic_tarihi = timezone.now()
            asama.save()

            # Ana görevi de devam ediyor yap (eğer planlanmış ise)
            if asama.gorev.durum == "planlanmis":
                asama.gorev.durum = "devam_ediyor"
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

            # Aşamayı tamamla
            asama.durum = "tamamlandi"
            asama.tamamlanma_tarihi = timezone.now()  # Tamamlama resmi varsa kaydet
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
            gorev.tamamlanma_tarihi = timezone.now()
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
            gorev.onaylayan = request.user
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
