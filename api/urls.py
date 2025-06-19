from django.urls import include, path
from rest_framework import routers

from .istakip_viewsets import (
    GorevDevamEdiyorViewSet,
    GorevGecikmisTViewSet,
    GorevIptalViewSet,
    GorevOnayaGonderildiViewSet,
    GorevPlanlanmisViewSet,
    GorevTamamlandiViewSet,
    GunlukKontrolAcilViewSet,
    GunlukKontrolCozulduViewSet,
    GunlukKontrolGozdenGecirildiViewSet,
    GunlukKontrolIseDonusturulduViewSet,
    GunlukKontrolSorunVarViewSet,
    GunlukKontrolSorunYokViewSet,
    PersonelViewSet,
)
from .view_viewsets import ParkbahceListApiView
from .viewsets import (
    ElektrikHatViewSet,
    ElektrikNoktaViewSet,
    HabitatViewSet,
    KanalHatViewSet,
    MahalleViewSet,
    OyunAlanViewSet,
    ParkAboneViewSet,
    ParkBinaViewSet,
    ParkDonatiViewSet,
    ParkHavuzViewSet,
    ParkOyunGrupViewSet,
    ParkViewSet,
    ParkYolViewSet,
    SporAlanViewSet,
    SulamaHatViewSet,
    SulamaNoktaViewSet,
    ViewParklarDonatilarViewSet,
    YesilAlanViewSet,
)

router = routers.DefaultRouter()

# Ana ViewSets
router.register(
    r"parklar",
    ParkViewSet,
    basename="parklar",
)

router.register(
    r"mahalleler",
    MahalleViewSet,
    basename="mahalleler",
)

router.register(
    r"parklar-detay",
    ViewParklarDonatilarViewSet,
    basename="view-parklar-donatilar-habitatlar",
)

router.register(
    r"personeller",
    PersonelViewSet,
    basename="personeller",
)

# İş Takip - Görev Durumları
router.register(
    r"gorevler/planlanmis",
    GorevPlanlanmisViewSet,
    basename="gorevler-planlanmis",
)

router.register(
    r"gorevler/devam-ediyor",
    GorevDevamEdiyorViewSet,
    basename="gorevler-devam-ediyor",
)

router.register(
    r"gorevler/onaya-gonderildi",
    GorevOnayaGonderildiViewSet,
    basename="gorevler-onaya-gonderildi",
)

router.register(
    r"gorevler/tamamlandi",
    GorevTamamlandiViewSet,
    basename="gorevler-tamamlandi",
)

router.register(
    r"gorevler/iptal",
    GorevIptalViewSet,
    basename="gorevler-iptal",
)

router.register(
    r"gorevler/gecikmis",
    GorevGecikmisTViewSet,
    basename="gorevler-gecikmis",
)

# İş Takip - Günlük Kontrol Durumları
router.register(
    r"gunluk-kontrol/sorun-yok",
    GunlukKontrolSorunYokViewSet,
    basename="gunluk-kontrol-sorun-yok",
)

router.register(
    r"gunluk-kontrol/sorun-var",
    GunlukKontrolSorunVarViewSet,
    basename="gunluk-kontrol-sorun-var",
)

router.register(
    r"gunluk-kontrol/acil",
    GunlukKontrolAcilViewSet,
    basename="gunluk-kontrol-acil",
)

router.register(
    r"gunluk-kontrol/gozden-gecirildi",
    GunlukKontrolGozdenGecirildiViewSet,
    basename="gunluk-kontrol-gozden-gecirildi",
)

router.register(
    r"gunluk-kontrol/ise-donusturuldu",
    GunlukKontrolIseDonusturulduViewSet,
    basename="gunluk-kontrol-ise-donusturuldu",
)

router.register(
    r"gunluk-kontrol/cozuldu",
    GunlukKontrolCozulduViewSet,
    basename="gunluk-kontrol-cozuldu",
)

# Nokta Geometrili Modeller
router.register(
    r"habitatlar",
    HabitatViewSet,
    basename="habitatlar",
)

router.register(
    r"park-donatilar",
    ParkDonatiViewSet,
    basename="park-donatilar",
)

router.register(
    r"oyun-gruplari",
    ParkOyunGrupViewSet,
    basename="oyun-gruplari",
)

router.register(
    r"sulama-noktalari",
    SulamaNoktaViewSet,
    basename="sulama-noktalari",
)

router.register(
    r"elektrik-noktalari",
    ElektrikNoktaViewSet,
    basename="elektrik-noktalari",
)

router.register(
    r"park-aboneler",
    ParkAboneViewSet,
    basename="park-aboneler",
)

# Alan Geometrili Modeller
router.register(
    r"yesil-alanlar",
    YesilAlanViewSet,
    basename="yesil-alanlar",
)

router.register(
    r"spor-alanlar",
    SporAlanViewSet,
    basename="spor-alanlar",
)

router.register(
    r"park-binalar",
    ParkBinaViewSet,
    basename="park-binalar",
)

router.register(
    r"park-havuzlar",
    ParkHavuzViewSet,
    basename="park-havuzlar",
)

router.register(
    r"park-yollar",
    ParkYolViewSet,
    basename="park-yollar",
)

router.register(
    r"oyun-alanlar",
    OyunAlanViewSet,
    basename="oyun-alanlar",
)

# Çizgi Geometrili Modeller
router.register(
    r"sulama-hatlari",
    SulamaHatViewSet,
    basename="sulama-hatlari",
)

router.register(
    r"elektrik-hatlari",
    ElektrikHatViewSet,
    basename="elektrik-hatlari",
)

router.register(
    r"kanal-hatlari",
    KanalHatViewSet,
    basename="kanal-hatlari",
)


urlpatterns = [
    path("", include(router.urls)),
    path(
        "parkbahce-list-api/",
        ParkbahceListApiView.as_view(),
        name="parkbahce_list_api",
    ),
]
