from django.urls import include, path
from rest_framework import routers

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


urlpatterns = router.urls
