import logging
from datetime import datetime

from django.contrib.gis.geos import Polygon
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.response import Response

from istakip.models import Gorev, GunlukKontrol, Personel

from .istakip_serializers import PersonelSerializer


class BaseGeoViewSet(viewsets.ReadOnlyModelViewSet):
    """Base class for geographic viewsets with bbox filtering"""

    def get_queryset(self):
        queryset = super().get_queryset()
        bbox = self.request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    bbox_polygon.srid = 4326
                    bbox_transformed = bbox_polygon.transform(5256, clone=True)
                    if hasattr(self.queryset.model, "geom"):
                        queryset = queryset.filter(geom__intersects=bbox_transformed)
                    else:
                        queryset = queryset.filter(
                            park__geom__intersects=bbox_transformed
                        )
            except (ValueError, IndexError):
                pass
        return queryset


class PersonelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Personel.objects.filter(aktif=True).order_by("ad")
    serializer_class = PersonelSerializer
    lookup_field = "uuid"
    pagination_class = None

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = [
            {
                "uuid": item["uuid"],
                "label": f"{item['ad']} ({item['pozisyon'] or 'Görev Tanımsız'})",
                "ad": item["ad"],
                "pozisyon": item["pozisyon"],
            }
            for item in serializer.data
        ]
        return Response(data)
