from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from istakip.models import Gorev, GunlukKontrol, Personel


class PersonelSerializer(serializers.ModelSerializer):
    """Personel serializer for basic info"""

    class Meta:
        model = Personel
        fields = ["uuid", "ad", "pozisyon", "telefon"]


class GunlukKontrolGeoSerializer(serializers.ModelSerializer):
    """Günlük kontrol serializer with manual GeoJSON format"""

    personel_ad = serializers.SerializerMethodField()
    personel_pozisyon = serializers.SerializerMethodField()
    park_ad = serializers.SerializerMethodField()
    park_uuid = serializers.SerializerMethodField()
    mahalle_ad = serializers.SerializerMethodField()
    mahalle_uuid = serializers.SerializerMethodField()
    ilce_ad = serializers.SerializerMethodField()
    durum_display = serializers.CharField(source="get_durum_display", read_only=True)
    kontrol_tipi_display = serializers.CharField(
        source="get_kontrol_tipi_display", read_only=True
    )

    def get_personel_ad(self, obj):
        return obj.personel.ad if obj.personel else None

    def get_personel_pozisyon(self, obj):
        return obj.personel.pozisyon if obj.personel else None

    def get_park_ad(self, obj):
        return obj.park.ad if obj.park else None

    def get_park_uuid(self, obj):
        return str(obj.park.uuid) if obj.park else None

    def get_mahalle_ad(self, obj):
        return obj.park.mahalle.ad if obj.park and obj.park.mahalle else None

    def get_mahalle_uuid(self, obj):
        return str(obj.park.mahalle.uuid) if obj.park and obj.park.mahalle else None

    def get_ilce_ad(self, obj):
        return (
            obj.park.mahalle.ilce.ad
            if obj.park and obj.park.mahalle and obj.park.mahalle.ilce
            else None
        )

    def to_representation(self, instance):
        """Override to create GeoJSON format manually"""
        data = super().to_representation(instance)

        # Geometriyi al ve SRID 4326'ya dönüştür
        geometry = None
        if instance.geom:
            transformed_geom = instance.geom.transform(4326, clone=True)
            import json

            # GeoJSON formatına dönüştür
            geometry = json.loads(transformed_geom.geojson)

        # GeoJSON Feature formatını oluştur
        feature = {"type": "Feature", "geometry": geometry, "properties": data}

        return feature

    class Meta:
        model = GunlukKontrol
        fields = [
            "uuid",
            "kontrol_tarihi",
            "kontrol_tipi",
            "kontrol_tipi_display",
            "durum",
            "durum_display",
            "aciklama",
            "personel_ad",
            "personel_pozisyon",
            "park_ad",
            "park_uuid",
            "mahalle_ad",
            "mahalle_uuid",
            "ilce_ad",
            "created_at",
            "updated_at",
        ]


class GorevGeoSerializer(serializers.ModelSerializer):
    """Görev serializer with manual GeoJSON format"""

    park_ad = serializers.SerializerMethodField()
    park_uuid = serializers.SerializerMethodField()
    mahalle_ad = serializers.SerializerMethodField()
    mahalle_uuid = serializers.SerializerMethodField()
    ilce_ad = serializers.SerializerMethodField()
    gorev_tipi_ad = serializers.SerializerMethodField()
    durum_display = serializers.CharField(source="get_durum_display", read_only=True)
    oncelik_display = serializers.CharField(
        source="get_oncelik_display", read_only=True
    )
    tekrar_tipi_display = serializers.CharField(
        source="get_tekrar_tipi_display", read_only=True
    )
    olusturan_username = serializers.SerializerMethodField()
    atanan_personeller = serializers.SerializerMethodField()

    def get_park_ad(self, obj):
        """Park adını döndür"""
        return obj.park.ad if obj.park else None

    def get_park_uuid(self, obj):
        """Park UUID'sini döndür"""
        return str(obj.park.uuid) if obj.park else None

    def get_mahalle_ad(self, obj):
        """Mahalle adını döndür"""
        return obj.park.mahalle.ad if obj.park and obj.park.mahalle else None

    def get_mahalle_uuid(self, obj):
        """Mahalle UUID'sini döndür"""
        return str(obj.park.mahalle.uuid) if obj.park and obj.park.mahalle else None

    def get_ilce_ad(self, obj):
        """İlçe adını döndür"""
        return (
            obj.park.mahalle.ilce.ad
            if obj.park and obj.park.mahalle and obj.park.mahalle.ilce
            else None
        )

    def get_gorev_tipi_ad(self, obj):
        """Görev tipi adını döndür"""
        return obj.gorev_tipi.ad if obj.gorev_tipi else None

    def get_olusturan_username(self, obj):
        """Oluşturan kullanıcı adını döndür"""
        return obj.olusturan.username if obj.olusturan else None

    def get_atanan_personeller(self, obj):
        """Atanan personelleri döndür"""
        try:
            atamalar = obj.atamalar.select_related("personel").all()
            return [
                {
                    "uuid": str(atama.personel.uuid) if atama.personel else None,
                    "ad": atama.personel.ad if atama.personel else None,
                    "pozisyon": atama.personel.pozisyon if atama.personel else None,
                    "gorev_rolu": atama.gorev_rolu,
                    "atama_tarihi": atama.atama_tarihi,
                }
                for atama in atamalar
                if atama.personel is not None
            ]
        except Exception:
            return []

    def to_representation(self, instance):
        """Override to create GeoJSON format manually"""
        data = super().to_representation(instance)

        # Park geometrisini al ve SRID 4326'ya dönüştür
        geometry = None
        if instance.park and instance.park.geom:
            transformed_geom = instance.park.geom.transform(4326, clone=True)
            import json

            from django.contrib.gis.geos import GEOSGeometry

            # GeoJSON formatına dönüştür
            geometry = json.loads(transformed_geom.geojson)

        # GeoJSON Feature formatını oluştur
        feature = {"type": "Feature", "geometry": geometry, "properties": data}

        return feature

    class Meta:
        model = Gorev
        fields = [
            "uuid",
            "baslik",
            "aciklama",
            "baslangic_tarihi",
            "bitis_tarihi",
            "durum",
            "durum_display",
            "oncelik",
            "oncelik_display",
            "tekrar_tipi",
            "tekrar_tipi_display",
            "tamamlanma_tarihi",
            "park_ad",
            "park_uuid",
            "mahalle_ad",
            "mahalle_uuid",
            "ilce_ad",
            "gorev_tipi_ad",
            "olusturan_username",
            "atanan_personeller",
            "onay_tarihi",
            "created_at",
            "updated_at",
        ]
