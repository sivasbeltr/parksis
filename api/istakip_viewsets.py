import logging
from datetime import datetime

from django.contrib.gis.geos import Polygon
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.response import Response

from istakip.models import Gorev, GunlukKontrol, Personel

from .istakip_serializers import (
    GorevGeoSerializer,
    GunlukKontrolGeoSerializer,
    PersonelSerializer,
)

# Logger tanımlama
logger = logging.getLogger(__name__)


class GunlukKontrolFilter(filters.FilterSet):
    """Günlük kontrol filtreleme sınıfı"""

    mahalle = filters.CharFilter(method="filter_mahalle")
    durum = filters.CharFilter(method="filter_durum")
    personel = filters.CharFilter(method="filter_personel")
    tarih_baslangic = filters.DateFilter(field_name="kontrol_tarihi", lookup_expr="gte")
    tarih_bitis = filters.DateFilter(field_name="kontrol_tarihi", lookup_expr="lte")

    def filter_mahalle(self, queryset, name, value):
        logger.debug(f"Filtreleme: mahalle={value}")
        if value:
            mahalle_uuids = [uuid.strip() for uuid in value.split(",") if uuid.strip()]
            return queryset.filter(park__mahalle__uuid__in=mahalle_uuids)
        return queryset

    def filter_durum(self, queryset, name, value):
        logger.debug(f"Filtreleme: durum={value}")
        if value:
            durumlar = [durum.strip() for durum in value.split(",") if durum.strip()]
            if durumlar:
                return queryset.filter(durum__in=durumlar)
        return queryset

    def filter_personel(self, queryset, name, value):
        logger.debug(f"Filtreleme: personel={value}")
        if value:
            personel_uuids = [uuid.strip() for uuid in value.split(",") if uuid.strip()]
            return queryset.filter(personel__uuid__in=personel_uuids)
        return queryset

    class Meta:
        model = GunlukKontrol
        fields = ["mahalle", "durum", "personel", "tarih_baslangic", "tarih_bitis"]


class GorevFilter(filters.FilterSet):
    """Görev filtreleme sınıfı"""

    mahalle = filters.CharFilter(method="filter_mahalle")
    durum = filters.CharFilter(method="filter_durum")
    personel = filters.CharFilter(method="filter_personel")
    oncelik = filters.CharFilter(method="filter_oncelik")
    tarih_baslangic = filters.DateFilter(
        field_name="baslangic_tarihi", lookup_expr="gte"
    )
    tarih_bitis = filters.DateFilter(field_name="bitis_tarihi", lookup_expr="lte")

    def filter_mahalle(self, queryset, name, value):
        logger.debug(f"Filtreleme: mahalle={value}")
        if value:
            mahalle_uuids = [uuid.strip() for uuid in value.split(",") if uuid.strip()]
            return queryset.filter(park__mahalle__uuid__in=mahalle_uuids)
        return queryset

    def filter_durum(self, queryset, name, value):
        logger.debug(f"Filtreleme: durum={value}")
        if value:
            durumlar = [durum.strip() for durum in value.split(",") if durum.strip()]
            if durumlar:
                return queryset.filter(durum__in=durumlar)
        return queryset

    def filter_personel(self, queryset, name, value):
        logger.debug(f"Filtreleme: personel={value}")
        if value:
            personel_uuids = [uuid.strip() for uuid in value.split(",") if uuid.strip()]
            return queryset.filter(
                atamalar__personel__uuid__in=personel_uuids
            ).distinct()
        return queryset

    def filter_oncelik(self, queryset, name, value):
        logger.debug(f"Filtreleme: oncelik={value}")
        if value:
            oncelikler = [
                oncelik.strip() for oncelik in value.split(",") if oncelik.strip()
            ]
            if oncelikler:
                return queryset.filter(oncelik__in=oncelikler)
        return queryset

    class Meta:
        model = Gorev
        fields = [
            "mahalle",
            "durum",
            "personel",
            "oncelik",
            "tarih_baslangic",
            "tarih_bitis",
        ]


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


class GunlukKontrolViewSet(BaseGeoViewSet):
    queryset = GunlukKontrol.objects.select_related(
        "personel", "park", "park__mahalle", "park__mahalle__ilce"
    ).filter(geom__isnull=False)
    serializer_class = GunlukKontrolGeoSerializer
    filterset_class = GunlukKontrolFilter
    lookup_field = "uuid"
    ordering_fields = ["kontrol_tarihi", "durum"]
    ordering = ["-kontrol_tarihi"]

    def get_queryset(self):
        queryset = super().get_queryset()
        tarih = self.request.query_params.get("tarih")
        if tarih:
            try:
                tarih_obj = datetime.strptime(tarih, "%Y-%m-%d").date()
                queryset = queryset.filter(kontrol_tarihi__date=tarih_obj)
            except ValueError:
                pass
        logger.debug(f"Kontrol sorgusu: {queryset.query}")
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            features = serializer.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            features = serializer.data
        geojson = {"type": "FeatureCollection", "features": features}
        logger.debug(f"Kontrol GeoJSON: {len(features)} özellik döndü")
        if page is not None:
            return self.get_paginated_response(geojson)
        return Response(geojson)


class GorevViewSet(BaseGeoViewSet):
    queryset = Gorev.objects.select_related(
        "park", "park__mahalle", "park__mahalle__ilce", "gorev_tipi", "olusturan"
    ).prefetch_related("atamalar__personel")
    serializer_class = GorevGeoSerializer
    filterset_class = GorevFilter
    lookup_field = "uuid"
    ordering_fields = ["baslangic_tarihi", "bitis_tarihi", "oncelik", "durum"]
    ordering = ["-baslangic_tarihi"]

    def get_queryset(self):
        queryset = super().get_queryset()
        tarih = self.request.query_params.get("tarih")
        if tarih:
            try:
                tarih_obj = datetime.strptime(tarih, "%Y-%m-%d").date()
                queryset = queryset.filter(baslangic_tarihi__date=tarih_obj)
            except ValueError:
                pass
        logger.debug(f"Görev sorgusu: {queryset.query}")
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            features = serializer.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            features = serializer.data
        geojson = {"type": "FeatureCollection", "features": features}
        logger.debug(f"Görev GeoJSON: {len(features)} özellik döndü")
        if page is not None:
            return self.get_paginated_response(geojson)
        return Response(geojson)


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
