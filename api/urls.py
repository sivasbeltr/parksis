from django.urls import include, path
from rest_framework import routers

from .viewsets import MahalleViewSet, ViewParklarDonatilarViewSet

router = routers.DefaultRouter()

router.register(
    r"parklar-detay",
    ViewParklarDonatilarViewSet,
    basename="view-parklar-donatilar-habitatlar",
)

router.register(
    r"mahalleler",
    MahalleViewSet,
    basename="mahalleler",
)


urlpatterns = router.urls
