import json

from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from istakip.models import Gorev, GunlukKontrol, Personel


class PersonelSerializer(serializers.ModelSerializer):
    """Personel serializer for basic info"""

    class Meta:
        model = Personel
        fields = ["uuid", "ad", "pozisyon", "telefon"]


class GorevGeoSerializer(GeoFeatureModelSerializer):
    """Görev için GeoJSON serializer - marker konumu park merkezi olacak"""

    park_ad = serializers.SerializerMethodField()
    park_uuid = serializers.SerializerMethodField()
    durum_display = serializers.CharField(source="get_durum_display", read_only=True)
    oncelik_display = serializers.CharField(
        source="get_oncelik_display", read_only=True
    )
    gorev_tipi_ad = serializers.SerializerMethodField()
    atanan_personel_sayisi = serializers.SerializerMethodField()
    geom = serializers.SerializerMethodField()

    def get_park_ad(self, obj):
        return obj.park.ad if obj.park else None

    def get_park_uuid(self, obj):
        return str(obj.park.uuid) if obj.park else None

    def get_gorev_tipi_ad(self, obj):
        return obj.gorev_tipi.ad if obj.gorev_tipi else None

    def get_geom(self, obj):
        """Parkın merkez noktasını (centroid) GeoJSON Point olarak döndür"""
        if obj.park and obj.park.geom:
            geom = obj.park.geom
            centroid = geom.centroid
            if centroid.srid != 4326:
                centroid = centroid.transform(4326, clone=True)
            # GeoJSON string -> dict
            if hasattr(centroid, "geojson"):
                return json.loads(centroid.geojson)
        return None

    class Meta:
        model = Gorev
        geo_field = "geom"
        fields = [
            "uuid",
            "baslik",
            "aciklama",
            "durum",
            "durum_display",
            "oncelik",
            "oncelik_display",
            "baslangic_tarihi",
            "bitis_tarihi",
            "tamamlanma_tarihi",
            "park_ad",
            "park_uuid",
            "gorev_tipi_ad",
            "atanan_personel_sayisi",
            "geom",
        ]

    def get_atanan_personel_sayisi(self, obj):
        return obj.atanan_personeller.count()


class GunlukKontrolGeoSerializer(GeoFeatureModelSerializer):
    """Günlük Kontrol için GeoJSON serializer"""

    park_ad = serializers.CharField(source="park.ad", read_only=True)
    park_uuid = serializers.CharField(source="park.uuid", read_only=True)
    personel_ad = serializers.CharField(source="personel.ad", read_only=True)
    personel_uuid = serializers.CharField(source="personel.uuid", read_only=True)
    durum_display = serializers.CharField(source="get_durum_display", read_only=True)
    kontrol_tipi_display = serializers.CharField(
        source="get_kontrol_tipi_display", read_only=True
    )
    resim_sayisi = serializers.SerializerMethodField()

    def to_representation(self, instance):
        # Geometriyi 4326 SRID'ye çevir
        if instance.geom and instance.geom.srid != 4326:
            instance.geom = instance.geom.transform(4326, clone=True)
        return super().to_representation(instance)

    class Meta:
        model = GunlukKontrol
        geo_field = "geom"
        fields = [
            "uuid",
            "kontrol_tarihi",
            "durum",
            "durum_display",
            "kontrol_tipi",
            "kontrol_tipi_display",
            "aciklama",
            "park_ad",
            "park_uuid",
            "personel_ad",
            "personel_uuid",
            "resim_sayisi",
        ]

    def get_resim_sayisi(self, obj):
        return obj.resimler.count()
