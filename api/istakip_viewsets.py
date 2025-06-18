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


class GunlukKontrolFilter(filters.FilterSet):
    """Günlük kontrol filtreleme sınıfı"""

    mahalle = filters.CharFilter(method="filter_mahalle")
    durum = filters.CharFilter(method="filter_durum")
    personel = filters.CharFilter(method="filter_personel")
    tarih_baslangic = filters.DateFilter(field_name="kontrol_tarihi", lookup_expr="gte")
    tarih_bitis = filters.DateFilter(field_name="kontrol_tarihi", lookup_expr="lte")

    def filter_mahalle(self, queryset, name, value):
        """Mahalle UUID'lerine göre filtreleme (virgülle ayrılmış)"""
        if value:
            mahalle_uuids = [uuid.strip() for uuid in value.split(",")]
            return queryset.filter(park__mahalle__uuid__in=mahalle_uuids)
        return queryset

    def filter_durum(self, queryset, name, value):
        """Durumlara göre filtreleme (virgülle ayrılmış)"""
        if value:
            durumlar = [durum.strip() for durum in value.split(",")]
            return queryset.filter(durum__in=durumlar)
        return queryset

    def filter_personel(self, queryset, name, value):
        """Personel UUID'lerine göre filtreleme (virgülle ayrılmış)"""
        if value:
            personel_uuids = [uuid.strip() for uuid in value.split(",")]
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
        """Mahalle UUID'lerine göre filtreleme (virgülle ayrılmış)"""
        if value:
            mahalle_uuids = [uuid.strip() for uuid in value.split(",")]
            return queryset.filter(park__mahalle__uuid__in=mahalle_uuids)
        return queryset

    def filter_durum(self, queryset, name, value):
        """Durumlara göre filtreleme (virgülle ayrılmış)"""
        if value:
            durumlar = [durum.strip() for durum in value.split(",")]
            return queryset.filter(durum__in=durumlar)
        return queryset

    def filter_personel(self, queryset, name, value):
        """Atanan personel UUID'lerine göre filtreleme (virgülle ayrılmış)"""
        if value:
            personel_uuids = [uuid.strip() for uuid in value.split(",")]
            return queryset.filter(
                atanan_personeller__uuid__in=personel_uuids
            ).distinct()
        return queryset

    def filter_oncelik(self, queryset, name, value):
        """Önceliklere göre filtreleme (virgülle ayrılmış)"""
        if value:
            oncelikler = [oncelik.strip() for oncelik in value.split(",")]
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

        # BBOX filtering
        bbox = self.request.query_params.get("bbox")
        if bbox:
            try:
                # Parse BBOX coordinates (minx, miny, maxx, maxy)
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    # Create a Polygon from BBOX in SRID 4326
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    bbox_polygon.srid = 4326  # Set SRID to 4326 (WGS84)                    # Transform BBOX to SRID 5256 to match database
                    bbox_transformed = bbox_polygon.transform(5256, clone=True)

                    # For models with point geometry (geom field)
                    if hasattr(self.queryset.model, "geom"):
                        queryset = queryset.filter(geom__intersects=bbox_transformed)
                    # For models using park geometry
                    else:
                        queryset = queryset.filter(
                            park__geom__intersects=bbox_transformed
                        )
            except (ValueError, IndexError):
                pass

        return queryset


class GunlukKontrolViewSet(BaseGeoViewSet):
    """
    ViewSet for Günlük Kontrol (Daily Checks).
    Returns GeoJSON format with filtering capabilities.
    """

    queryset = GunlukKontrol.objects.select_related(
        "personel", "park", "park__mahalle", "park__mahalle__ilce"
    ).filter(
        geom__isnull=False
    )  # Sadece konum bilgisi olanlar

    serializer_class = GunlukKontrolGeoSerializer
    filterset_class = GunlukKontrolFilter
    lookup_field = "uuid"
    ordering_fields = ["kontrol_tarihi", "durum"]
    ordering = ["-kontrol_tarihi"]

    def get_queryset(self):
        """Override to apply filters and bbox"""
        queryset = super().get_queryset()

        # Tarih aralığı filtresi (eğer sadece tek tarih verilirse)
        tarih = self.request.query_params.get("tarih")
        if tarih:
            try:
                tarih_obj = datetime.strptime(tarih, "%Y-%m-%d").date()
                queryset = queryset.filter(kontrol_tarihi__date=tarih_obj)
            except ValueError:
                pass

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to return proper GeoJSON FeatureCollection format"""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            features = serializer.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            features = serializer.data

        # GeoJSON FeatureCollection formatı oluştur
        geojson = {"type": "FeatureCollection", "features": features}

        if page is not None:
            return self.get_paginated_response(geojson)

        return Response(geojson)


class GorevViewSet(BaseGeoViewSet):
    """
    ViewSet for Görev (Tasks).
    Returns GeoJSON format with filtering capabilities.
    """

    queryset = Gorev.objects.select_related(
        "park", "park__mahalle", "park__mahalle__ilce", "gorev_tipi", "olusturan"
    ).prefetch_related("atamalar__personel")

    serializer_class = GorevGeoSerializer
    filterset_class = GorevFilter
    lookup_field = "uuid"
    ordering_fields = ["baslangic_tarihi", "bitis_tarihi", "oncelik", "durum"]
    ordering = ["-baslangic_tarihi"]

    def get_queryset(self):
        """Override to apply filters and bbox"""
        queryset = super().get_queryset()

        # Tek tarih filtresi (başlangıç tarihine göre)
        tarih = self.request.query_params.get("tarih")
        if tarih:
            try:
                tarih_obj = datetime.strptime(tarih, "%Y-%m-%d").date()
                queryset = queryset.filter(baslangic_tarihi__date=tarih_obj)
            except ValueError:
                pass

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to return proper GeoJSON FeatureCollection format"""
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            features = serializer.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            features = serializer.data

        # GeoJSON FeatureCollection formatı oluştur
        geojson = {"type": "FeatureCollection", "features": features}

        if page is not None:
            return self.get_paginated_response(geojson)

        return Response(geojson)


class PersonelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Personel (Personnel).
    Helper endpoint for getting personnel list for filters.
    """

    queryset = Personel.objects.filter(aktif=True).order_by("ad")
    serializer_class = PersonelSerializer
    lookup_field = "uuid"
    pagination_class = None  # Disable pagination for filter options

    def list(self, request, *args, **kwargs):
        """Override list to return simplified structure for frontend filters"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Format for frontend select options
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
