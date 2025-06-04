from rest_framework import viewsets

from ortak.models import Mahalle
from parkbahce.models import Park
from parkbahce.viewmodels import ViewParklarDonatilarHabitatlar

from .serializers import (
    MahalleDetailSerializer,
    MahalleSerializer,
    ViewParklarDonatilarHabitatlarSerializer,
)


class ViewParklarDonatilarViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Parklar Donatilar.
    Provides read-only access to park data with amenities.
    """

    queryset = ViewParklarDonatilarHabitatlar.objects.all()
    serializer_class = ViewParklarDonatilarHabitatlarSerializer
    pagination_class = None  # Disable pagination if not needed
    filterset_fields = ["ad"]  # Example filter field, adjust as necessary
    ordering_fields = ["ad", "uuid"]  # Allow ordering by these fields


class MahalleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Mahalle.
    Provides read-only access to neighborhood data.
    """

    queryset = Mahalle.objects.all()
    serializer_class = MahalleSerializer
    lookup_field = "uuid"  # Use UUID as the lookup field
    pagination_class = None  # Disable pagination if not needed
    filterset_fields = ["ad", "ilce"]  # Example filter fields, adjust as necessary
    ordering_fields = ["ad", "ilce"]  # Allow ordering by these fields

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MahalleDetailSerializer
        return MahalleSerializer
