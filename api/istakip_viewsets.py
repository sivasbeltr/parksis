import logging
from datetime import datetime, timedelta

from django.contrib.gis.geos import Polygon
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.response import Response

from istakip.choices import GorevDurumChoices, KontrolDurumChoices
from istakip.models import Gorev, GunlukKontrol, Personel

from .istakip_serializers import (
    GorevGeoSerializer,
    GunlukKontrolGeoSerializer,
    PersonelSerializer,
)


class BaseDateFilteredViewSet(viewsets.ReadOnlyModelViewSet):
    """Base class with date filtering capability"""

    def get_queryset(self):
        queryset = super().get_queryset()

        # Tarih aralığı filtresi
        baslangic_tarih = self.request.query_params.get("baslangic_tarih")
        bitis_tarih = self.request.query_params.get("bitis_tarih")

        # Eğer tarih aralığı belirtilmemişse son 1 ay
        if not baslangic_tarih or not bitis_tarih:
            bitis_tarih = timezone.now()
            baslangic_tarih = bitis_tarih - timedelta(days=30)
        else:
            try:
                baslangic_tarih = timezone.datetime.fromisoformat(
                    baslangic_tarih.replace("Z", "+00:00")
                )
                bitis_tarih = timezone.datetime.fromisoformat(
                    bitis_tarih.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                # Hatalı tarih formatı durumunda son 1 ay
                bitis_tarih = timezone.now()
                baslangic_tarih = bitis_tarih - timedelta(days=30)

        # Her zaman bitiş tarihine 1 gün ekle, başlangıç tarihinden 1 gün çıkart
        baslangic_tarih = baslangic_tarih - timedelta(days=1)
        bitis_tarih = bitis_tarih + timedelta(days=1)

        # Model'e göre uygun tarih alanını filtrele
        if hasattr(self.queryset.model, "baslangic_tarihi"):
            queryset = queryset.filter(
                baslangic_tarihi__gte=baslangic_tarih, baslangic_tarihi__lte=bitis_tarih
            )
        elif hasattr(self.queryset.model, "kontrol_tarihi"):
            queryset = queryset.filter(
                kontrol_tarihi__gte=baslangic_tarih, kontrol_tarihi__lte=bitis_tarih
            )

        return queryset


class GorevDurumViewSet(BaseDateFilteredViewSet):
    """Görevleri duruma göre listeleyen ViewSet"""

    queryset = Gorev.objects.select_related("park", "gorev_tipi").prefetch_related(
        "atanan_personeller"
    )
    serializer_class = GorevGeoSerializer
    lookup_field = "uuid"
    pagination_class = None

    def get_queryset(self):
        durum = getattr(self, "durum", None)
        queryset = self.queryset

        if durum:
            queryset = queryset.filter(durum=durum)

        # Parent'tan tarih filtresi uygula
        return (
            super().get_queryset().filter(pk__in=queryset.values_list("pk", flat=True))
        )


class GorevPlanlanmisViewSet(GorevDurumViewSet):
    durum = GorevDurumChoices.PLANLANMIS


class GorevDevamEdiyorViewSet(GorevDurumViewSet):
    durum = GorevDurumChoices.DEVAM_EDIYOR


class GorevOnayaGonderildiViewSet(GorevDurumViewSet):
    durum = GorevDurumChoices.ONAYA_GONDERILDI


class GorevTamamlandiViewSet(GorevDurumViewSet):
    durum = GorevDurumChoices.TAMAMLANDI


class GorevIptalViewSet(GorevDurumViewSet):
    durum = GorevDurumChoices.IPTAL


class GorevGecikmisTViewSet(GorevDurumViewSet):
    durum = GorevDurumChoices.GECIKMIS


class GunlukKontrolDurumViewSet(BaseDateFilteredViewSet):
    """Günlük kontrolleri duruma göre listeleyen ViewSet"""

    queryset = GunlukKontrol.objects.select_related(
        "park", "personel"
    ).prefetch_related("resimler")
    serializer_class = GunlukKontrolGeoSerializer
    lookup_field = "uuid"
    pagination_class = None

    def get_queryset(self):
        durum = getattr(self, "durum", None)
        queryset = self.queryset

        if durum:
            queryset = queryset.filter(durum=durum)

        # Parent'tan tarih filtresi uygula
        return (
            super().get_queryset().filter(pk__in=queryset.values_list("pk", flat=True))
        )


class GunlukKontrolSorunYokViewSet(GunlukKontrolDurumViewSet):
    durum = KontrolDurumChoices.SORUN_YOK


class GunlukKontrolSorunVarViewSet(GunlukKontrolDurumViewSet):
    durum = KontrolDurumChoices.SORUN_VAR


class GunlukKontrolAcilViewSet(GunlukKontrolDurumViewSet):
    durum = KontrolDurumChoices.ACIL


class GunlukKontrolGozdenGecirildiViewSet(GunlukKontrolDurumViewSet):
    durum = KontrolDurumChoices.GOZDEN_GECIRILDI


class GunlukKontrolIseDonusturulduViewSet(GunlukKontrolDurumViewSet):
    durum = KontrolDurumChoices.ISE_DONUSTURULDU


class GunlukKontrolCozulduViewSet(GunlukKontrolDurumViewSet):
    durum = KontrolDurumChoices.COZULDU


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
