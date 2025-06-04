from django.contrib.gis.geos import Polygon
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ortak.models import Mahalle
from parkbahce.models import (
    ElektrikHat,
    ElektrikNokta,
    Habitat,
    KanalHat,
    OyunAlan,
    Park,
    ParkAbone,
    ParkBina,
    ParkDonati,
    ParkHavuz,
    ParkOyunGrup,
    ParkYol,
    SporAlan,
    SulamaHat,
    SulamaNokta,
    YesilAlan,
)
from parkbahce.viewmodels import ViewParklarDonatilarHabitatlar

from .serializers import (  # Park serializers; Alt model serializers
    ElektrikHatDetailSerializer,
    ElektrikHatListSerializer,
    ElektrikNoktaDetailSerializer,
    ElektrikNoktaListSerializer,
    HabitatDetailSerializer,
    HabitatListSerializer,
    KanalHatDetailSerializer,
    KanalHatListSerializer,
    MahalleDetailSerializer,
    MahalleSerializer,
    OyunAlanDetailSerializer,
    OyunAlanListSerializer,
    ParkAboneDetailSerializer,
    ParkAboneListSerializer,
    ParkBinaDetailSerializer,
    ParkBinaListSerializer,
    ParkDetailSerializer,
    ParkDonatiDetailSerializer,
    ParkDonatiListSerializer,
    ParkHavuzDetailSerializer,
    ParkHavuzListSerializer,
    ParkListSerializer,
    ParkOyunGrupDetailSerializer,
    ParkOyunGrupListSerializer,
    ParkYolDetailSerializer,
    ParkYolListSerializer,
    SporAlanDetailSerializer,
    SporAlanListSerializer,
    SulamaHatDetailSerializer,
    SulamaHatListSerializer,
    SulamaNoktaDetailSerializer,
    SulamaNoktaListSerializer,
    ViewParklarDonatilarHabitatlarSerializer,
    YesilAlanDetailSerializer,
    YesilAlanListSerializer,
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


class ParkFilter(filters.FilterSet):
    """Park filtreleme sınıfı"""

    mahalle = filters.CharFilter(field_name="mahalle__ad", lookup_expr="icontains")
    ilce = filters.CharFilter(field_name="mahalle__ilce__ad", lookup_expr="icontains")
    park_tipi = filters.CharFilter(field_name="park_tipi__ad", lookup_expr="icontains")
    min_alan = filters.NumberFilter(field_name="alan", lookup_expr="gte")
    max_alan = filters.NumberFilter(field_name="alan", lookup_expr="lte")

    class Meta:
        model = Park
        fields = ["mahalle", "ilce", "park_tipi", "min_alan", "max_alan"]


class BaseGeoViewSet(viewsets.ReadOnlyModelViewSet):
    """Base class for geographic viewsets with bbox filtering"""

    def get_queryset(self):
        queryset = super().get_queryset()

        # BBOX filtering
        bbox = self.request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    queryset = queryset.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        # Zoom level filtering for detail level
        zoom = self.request.query_params.get("zoom")
        if zoom:
            try:
                zoom_level = int(zoom)
                if zoom_level < 14:  # Lower zoom levels, less detail
                    # Potentially limit the number of features
                    queryset = queryset[:1000]
            except ValueError:
                pass

        return queryset


class ParkViewSet(BaseGeoViewSet):
    """
    ViewSet for Park.
    Provides read-only access to park data.
    """

    queryset = Park.objects.select_related(
        "mahalle", "park_tipi", "sulama_tipi", "sulama_kaynagi"
    ).all()
    lookup_field = "uuid"
    filterset_class = ParkFilter
    ordering_fields = ["ad", "alan", "created_at"]
    ordering = ["ad"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ParkDetailSerializer
        return ParkListSerializer

    @action(detail=True, methods=["get"])
    def habitatlar(self, request, uuid=None):
        """Parka ait habitatları döndürür"""
        park = self.get_object()
        habitatlar = park.habitatlar.all()

        # BBOX filtering for habitats
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    habitatlar = habitatlar.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = HabitatListSerializer(
            habitatlar, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def donatilar(self, request, uuid=None):
        """Parka ait donatıları döndürür"""
        park = self.get_object()
        donatilar = park.donatilar.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    donatilar = donatilar.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = ParkDonatiListSerializer(
            donatilar, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def oyun_gruplari(self, request, uuid=None):
        """Parka ait oyun gruplarını döndürür"""
        park = self.get_object()
        oyun_gruplari = park.oyun_gruplari.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    oyun_gruplari = oyun_gruplari.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = ParkOyunGrupListSerializer(
            oyun_gruplari, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def sulama_noktalari(self, request, uuid=None):
        """Parka ait sulama noktalarını döndürür"""
        park = self.get_object()
        sulama_noktalari = park.sulama_noktalari.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    sulama_noktalari = sulama_noktalari.filter(
                        geom__intersects=bbox_polygon
                    )
            except (ValueError, IndexError):
                pass

        serializer = SulamaNoktaListSerializer(
            sulama_noktalari, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def elektrik_noktalari(self, request, uuid=None):
        """Parka ait elektrik noktalarını döndürür"""
        park = self.get_object()
        elektrik_noktalari = park.elektrik_noktalar.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    elektrik_noktalari = elektrik_noktalari.filter(
                        geom__intersects=bbox_polygon
                    )
            except (ValueError, IndexError):
                pass

        serializer = ElektrikNoktaListSerializer(
            elektrik_noktalari, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def yesil_alanlar(self, request, uuid=None):
        """Parka ait yeşil alanları döndürür"""
        park = self.get_object()
        yesil_alanlar = park.yesil_alanlar.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    yesil_alanlar = yesil_alanlar.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = YesilAlanListSerializer(
            yesil_alanlar, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def spor_alanlar(self, request, uuid=None):
        """Parka ait spor alanlarını döndürür"""
        park = self.get_object()
        spor_alanlar = park.spor_alanlar.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    spor_alanlar = spor_alanlar.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = SporAlanListSerializer(
            spor_alanlar, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def binalar(self, request, uuid=None):
        """Parka ait binaları döndürür"""
        park = self.get_object()
        binalar = park.binalar.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    binalar = binalar.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = ParkBinaListSerializer(
            binalar, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def havuzlar(self, request, uuid=None):
        """Parka ait havuzları döndürür"""
        park = self.get_object()
        havuzlar = park.havuzlar.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    havuzlar = havuzlar.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = ParkHavuzListSerializer(
            havuzlar, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def yollar(self, request, uuid=None):
        """Parka ait yolları döndürür"""
        park = self.get_object()
        yollar = park.yollar.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    yollar = yollar.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = ParkYolListSerializer(
            yollar, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def oyun_alanlar(self, request, uuid=None):
        """Parka ait oyun alanlarını döndürür"""
        park = self.get_object()
        oyun_alanlar = park.oyun_alanlar.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    oyun_alanlar = oyun_alanlar.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = OyunAlanListSerializer(
            oyun_alanlar, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def sulama_hatlari(self, request, uuid=None):
        """Parka ait sulama hatlarını döndürür"""
        park = self.get_object()
        sulama_hatlari = park.sulama_hatlari.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    sulama_hatlari = sulama_hatlari.filter(
                        geom__intersects=bbox_polygon
                    )
            except (ValueError, IndexError):
                pass

        serializer = SulamaHatListSerializer(
            sulama_hatlari, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def elektrik_hatlari(self, request, uuid=None):
        """Parka ait elektrik hatlarını döndürür"""
        park = self.get_object()
        elektrik_hatlari = park.elektrik_hatlari.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    elektrik_hatlari = elektrik_hatlari.filter(
                        geom__intersects=bbox_polygon
                    )
            except (ValueError, IndexError):
                pass

        serializer = ElektrikHatListSerializer(
            elektrik_hatlari, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def kanal_hatlari(self, request, uuid=None):
        """Parka ait kanal hatlarını döndürür"""
        park = self.get_object()
        kanal_hatlari = park.kanal_hatlari.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    kanal_hatlari = kanal_hatlari.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = KanalHatListSerializer(
            kanal_hatlari, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def aboneler(self, request, uuid=None):
        """Parka ait aboneleri döndürür"""
        park = self.get_object()
        aboneler = park.aboneler.all()

        # BBOX filtering
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                bbox_coords = [float(coord) for coord in bbox.split(",")]
                if len(bbox_coords) == 4:
                    bbox_polygon = Polygon.from_bbox(bbox_coords)
                    aboneler = aboneler.filter(geom__intersects=bbox_polygon)
            except (ValueError, IndexError):
                pass

        serializer = ParkAboneListSerializer(
            aboneler, many=True, context={"request": request}
        )
        return Response(serializer.data)


# Individual ViewSets for each model
class HabitatViewSet(BaseGeoViewSet):
    """ViewSet for Habitat"""

    queryset = Habitat.objects.select_related("park", "habitat_tipi").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "habitat_tipi__ad"]
    ordering_fields = ["ad", "dikim_tarihi"]
    ordering = ["ad"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return HabitatDetailSerializer
        return HabitatListSerializer


class ParkDonatiViewSet(BaseGeoViewSet):
    """ViewSet for ParkDonati"""

    queryset = ParkDonati.objects.select_related("park", "donati_tipi").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "donati_tipi__ad"]
    ordering = ["id"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ParkDonatiDetailSerializer
        return ParkDonatiListSerializer


class ParkOyunGrupViewSet(BaseGeoViewSet):
    """ViewSet for ParkOyunGrup"""

    queryset = ParkOyunGrup.objects.select_related(
        "park", "oyun_grup_tipi", "oyun_grup_model"
    ).all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "oyun_grup_tipi__ad", "oyun_grup_model__ad"]
    ordering_fields = ["ad", "sayi"]
    ordering = ["ad"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ParkOyunGrupDetailSerializer
        return ParkOyunGrupListSerializer


class SulamaNoktaViewSet(BaseGeoViewSet):
    """ViewSet for SulamaNokta"""

    queryset = SulamaNokta.objects.select_related("park", "sulama_nokta_tipi").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "sulama_nokta_tipi__ad"]
    ordering = ["id"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SulamaNoktaDetailSerializer
        return SulamaNoktaListSerializer


class ElektrikNoktaViewSet(BaseGeoViewSet):
    """ViewSet for ElektrikNokta"""

    queryset = ElektrikNokta.objects.select_related("park").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid"]
    ordering = ["id"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ElektrikNoktaDetailSerializer
        return ElektrikNoktaListSerializer


class YesilAlanViewSet(BaseGeoViewSet):
    """ViewSet for YesilAlan"""

    queryset = YesilAlan.objects.select_related("park").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid"]
    ordering_fields = ["alan"]
    ordering = ["-alan"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return YesilAlanDetailSerializer
        return YesilAlanListSerializer


class SporAlanViewSet(BaseGeoViewSet):
    """ViewSet for SporAlan"""

    queryset = SporAlan.objects.select_related(
        "park", "spor_alan_tipi", "spor_aleti_grup"
    ).all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "spor_alan_tipi__ad", "spor_aleti_grup__ad"]
    ordering_fields = ["alan"]
    ordering = ["-alan"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SporAlanDetailSerializer
        return SporAlanListSerializer


class ParkBinaViewSet(BaseGeoViewSet):
    """ViewSet for ParkBina"""

    queryset = ParkBina.objects.select_related("park", "bina_kullanim_tipi").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "bina_kullanim_tipi__ad"]
    ordering_fields = ["ad", "alan"]
    ordering = ["ad"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ParkBinaDetailSerializer
        return ParkBinaListSerializer


class ParkHavuzViewSet(BaseGeoViewSet):
    """ViewSet for ParkHavuz"""

    queryset = ParkHavuz.objects.select_related("park").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid"]
    ordering_fields = ["alan"]
    ordering = ["-alan"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ParkHavuzDetailSerializer
        return ParkHavuzListSerializer


class ParkYolViewSet(BaseGeoViewSet):
    """ViewSet for ParkYol"""

    queryset = ParkYol.objects.select_related("park").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "yol_tipi"]
    ordering_fields = ["alan"]
    ordering = ["-alan"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ParkYolDetailSerializer
        return ParkYolListSerializer


class OyunAlanViewSet(BaseGeoViewSet):
    """ViewSet for OyunAlan"""

    queryset = OyunAlan.objects.select_related("park", "oyun_alan_kaplama_tipi").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "oyun_alan_kaplama_tipi__ad"]
    ordering_fields = ["alan"]
    ordering = ["-alan"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OyunAlanDetailSerializer
        return OyunAlanListSerializer


class SulamaHatViewSet(BaseGeoViewSet):
    """ViewSet for SulamaHat"""

    queryset = SulamaHat.objects.select_related("park", "sulama_boru_tipi").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "sulama_boru_tipi__ad"]
    ordering_fields = ["uzunluk", "boru_cap"]
    ordering = ["-uzunluk"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SulamaHatDetailSerializer
        return SulamaHatListSerializer


class ElektrikHatViewSet(BaseGeoViewSet):
    """ViewSet for ElektrikHat"""

    queryset = ElektrikHat.objects.select_related(
        "park", "elektrik_kablo_tipi", "elektrik_hat_tipi"
    ).all()
    lookup_field = "uuid"
    filterset_fields = [
        "park__uuid",
        "elektrik_kablo_tipi__ad",
        "elektrik_hat_tipi__ad",
    ]
    ordering_fields = ["uzunluk", "gerilim"]
    ordering = ["-uzunluk"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ElektrikHatDetailSerializer
        return ElektrikHatListSerializer


class KanalHatViewSet(BaseGeoViewSet):
    """ViewSet for KanalHat"""

    queryset = KanalHat.objects.select_related("park", "kanal_boru_tipi").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "kanal_boru_tipi__ad"]
    ordering_fields = ["uzunluk", "boru_cap"]
    ordering = ["-uzunluk"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return KanalHatDetailSerializer
        return KanalHatListSerializer


class ParkAboneViewSet(BaseGeoViewSet):
    """ViewSet for ParkAbone"""

    queryset = ParkAbone.objects.select_related("park").all()
    lookup_field = "uuid"
    filterset_fields = ["park__uuid", "abone_tipi"]
    ordering_fields = ["abone_tarihi", "abone_no"]
    ordering = ["-abone_tarihi"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ParkAboneDetailSerializer
        return ParkAboneListSerializer
