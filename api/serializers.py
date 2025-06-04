# geo serializer
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

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
    ParkTip,
    ParkYol,
    SporAlan,
    SulamaHat,
    SulamaKaynak,
    SulamaNokta,
    SulamaTip,
    YesilAlan,
)
from parkbahce.viewmodels import ViewParklarDonatilarHabitatlar


class BaseGeoFeatureModelSerializer(GeoFeatureModelSerializer):

    def to_representation(self, instance):
        # Geometriyi 4326 SRID'ye çevir
        if instance.geom and instance.geom.srid != 4326:
            instance.geom = instance.geom.transform(4326, clone=True)
        return super().to_representation(instance)


class ViewParklarDonatilarHabitatlarSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewParklarDonatilarHabitatlar
        fields = (
            "id",
            "uuid",
            "ad",
            "donatilar",
            "habitatlar",
        )
        read_only_fields = fields


class MahalleSerializer(BaseGeoFeatureModelSerializer):

    class Meta:
        model = Mahalle

        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "ad",
        )
        read_only_fields = fields


class MahalleDetailSerializer(BaseGeoFeatureModelSerializer):
    """
    Serializer for Mahalle detail view.
    Includes additional fields if needed.
    """

    class Meta:
        geo_field = "geom"
        model = Mahalle
        fields = "__all__"


class ParkTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkTip
        fields = "__all__"


class SulamaKaynakSerializer(serializers.ModelSerializer):

    class Meta:
        model = SulamaKaynak
        fields = "__all__"


class SulamaTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = SulamaTip
        fields = "__all__"


# Park Serializers
class ParkListSerializer(BaseGeoFeatureModelSerializer):
    """Park listesi için minimal serializer"""

    mahalle_ad = serializers.SerializerMethodField()
    ilce_ad = serializers.SerializerMethodField()
    park_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = Park
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "ad",
            "alan",
            "cevre",
            "mahalle_ad",
            "ilce_ad",
            "park_tipi_ad",
        )
        read_only_fields = fields

    def get_mahalle_ad(self, obj):
        return obj.mahalle.ad if obj.mahalle else None

    def get_ilce_ad(self, obj):
        return obj.mahalle.ilce.ad if obj.mahalle and obj.mahalle.ilce else None

    def get_park_tipi_ad(self, obj):
        return obj.park_tipi.ad if obj.park_tipi else None


class ParkDetailSerializer(BaseGeoFeatureModelSerializer):
    """Park detayı için tam serializer"""

    mahalle = MahalleSerializer(read_only=True)
    park_tipi = ParkTipSerializer(read_only=True)
    sulama_tipi = SulamaTipSerializer(read_only=True)
    sulama_kaynagi = SulamaKaynakSerializer(read_only=True)

    class Meta:
        model = Park
        geo_field = "geom"
        fields = "__all__"


# Park Alt Model Serializers
class HabitatListSerializer(BaseGeoFeatureModelSerializer):
    """Habitat listesi için minimal serializer"""

    habitat_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = Habitat
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "ad",
            "habitat_tipi_ad",
            "dikim_tarihi",
            "firma",
        )

    def get_habitat_tipi_ad(self, obj):
        return obj.habitat_tipi.ad if obj.habitat_tipi else None


class HabitatDetailSerializer(BaseGeoFeatureModelSerializer):
    """Habitat detayı için tam serializer"""

    class Meta:
        model = Habitat
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class ParkDonatiListSerializer(BaseGeoFeatureModelSerializer):
    """Park donatı listesi için minimal serializer"""

    donati_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = ParkDonati
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "donati_tipi_ad",
        )

    def get_donati_tipi_ad(self, obj):
        return obj.donati_tipi.ad if obj.donati_tipi else None


class ParkDonatiDetailSerializer(BaseGeoFeatureModelSerializer):
    """Park donatı detayı için tam serializer"""

    class Meta:
        model = ParkDonati
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class ParkOyunGrupListSerializer(BaseGeoFeatureModelSerializer):
    """Oyun grubu listesi için minimal serializer"""

    oyun_grup_tipi_ad = serializers.SerializerMethodField()
    oyun_grup_model_ad = serializers.SerializerMethodField()

    class Meta:
        model = ParkOyunGrup
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "ad",
            "sayi",
            "oyun_grup_tipi_ad",
            "oyun_grup_model_ad",
        )
        read_only_fields = fields

    def get_oyun_grup_tipi_ad(self, obj):
        return obj.oyun_grup_tipi.ad if obj.oyun_grup_tipi else None

    def get_oyun_grup_model_ad(self, obj):
        return obj.oyun_grup_model.ad if obj.oyun_grup_model else None


class ParkOyunGrupDetailSerializer(BaseGeoFeatureModelSerializer):
    """Oyun grubu detayı için tam serializer"""

    class Meta:
        model = ParkOyunGrup
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class SulamaNoktaListSerializer(BaseGeoFeatureModelSerializer):
    """Sulama noktası listesi için minimal serializer"""

    sulama_nokta_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = SulamaNokta
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "sulama_nokta_tipi_ad",
        )
        read_only_fields = fields

    def get_sulama_nokta_tipi_ad(self, obj):
        return obj.sulama_nokta_tipi.ad if obj.sulama_nokta_tipi else None


class SulamaNoktaDetailSerializer(BaseGeoFeatureModelSerializer):
    """Sulama noktası detayı için tam serializer"""

    class Meta:
        model = SulamaNokta
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class ElektrikNoktaListSerializer(BaseGeoFeatureModelSerializer):
    """Elektrik noktası listesi için minimal serializer"""

    elektrik_nokta_tipi_ad = serializers.SerializerMethodField()
    elektrik_baglanti_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = ElektrikNokta
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "sayi",
            "elektrik_nokta_tipi_ad",
            "elektrik_baglanti_tipi_ad",
        )
        read_only_fields = fields

    def get_elektrik_nokta_tipi_ad(self, obj):
        return obj.elektrik_nokta_tipi.ad if obj.elektrik_nokta_tipi else None

    def get_elektrik_baglanti_tipi_ad(self, obj):
        return obj.elektrik_baglanti_tipi.ad if obj.elektrik_baglanti_tipi else None


class ElektrikNoktaDetailSerializer(BaseGeoFeatureModelSerializer):
    """Elektrik noktası detayı için tam serializer"""

    class Meta:
        model = ElektrikNokta
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class YesilAlanListSerializer(BaseGeoFeatureModelSerializer):
    """Yeşil alan listesi için minimal serializer"""

    class Meta:
        model = YesilAlan
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "alan",
            "cevre",
        )
        read_only_fields = fields


class YesilAlanDetailSerializer(BaseGeoFeatureModelSerializer):
    """Yeşil alan detayı için tam serializer"""

    class Meta:
        model = YesilAlan
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class SporAlanListSerializer(BaseGeoFeatureModelSerializer):
    """Spor alanı listesi için minimal serializer"""

    spor_alan_tipi_ad = serializers.SerializerMethodField()
    spor_aleti_grup_ad = serializers.SerializerMethodField()

    class Meta:
        model = SporAlan
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "alan",
            "cevre",
            "spor_alan_tipi_ad",
            "spor_aleti_grup_ad",
        )
        read_only_fields = fields

    def get_spor_alan_tipi_ad(self, obj):
        return obj.spor_alan_tipi.ad if obj.spor_alan_tipi else None

    def get_spor_aleti_grup_ad(self, obj):
        return obj.spor_aleti_grup.ad if obj.spor_aleti_grup else None


class SporAlanDetailSerializer(BaseGeoFeatureModelSerializer):
    """Spor alanı detayı için tam serializer"""

    class Meta:
        model = SporAlan
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class ParkBinaListSerializer(BaseGeoFeatureModelSerializer):
    """Park bina listesi için minimal serializer"""

    bina_kullanim_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = ParkBina
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "ad",
            "alan",
            "cevre",
            "bina_kullanim_tipi_ad",
        )
        read_only_fields = fields

    def get_bina_kullanim_tipi_ad(self, obj):
        return obj.bina_kullanim_tipi.ad if obj.bina_kullanim_tipi else None


class ParkBinaDetailSerializer(BaseGeoFeatureModelSerializer):
    """Park bina detayı için tam serializer"""

    class Meta:
        model = ParkBina
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class ParkHavuzListSerializer(BaseGeoFeatureModelSerializer):
    """Park havuz listesi için minimal serializer"""

    class Meta:
        model = ParkHavuz
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "alan",
            "cevre",
        )
        read_only_fields = fields


class ParkHavuzDetailSerializer(BaseGeoFeatureModelSerializer):
    """Park havuz detayı için tam serializer"""

    class Meta:
        model = ParkHavuz
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class ParkYolListSerializer(BaseGeoFeatureModelSerializer):
    """Park yol listesi için minimal serializer"""

    class Meta:
        model = ParkYol
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "yol_tipi",
            "alan",
        )
        read_only_fields = fields


class ParkYolDetailSerializer(BaseGeoFeatureModelSerializer):
    """Park yol detayı için tam serializer"""

    class Meta:
        model = ParkYol
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class OyunAlanListSerializer(BaseGeoFeatureModelSerializer):
    """Oyun alanı listesi için minimal serializer"""

    oyun_alan_kaplama_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = OyunAlan
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "alan",
            "cevre",
            "oyun_alan_kaplama_tipi_ad",
        )
        read_only_fields = fields

    def get_oyun_alan_kaplama_tipi_ad(self, obj):
        return obj.oyun_alan_kaplama_tipi.ad if obj.oyun_alan_kaplama_tipi else None


class OyunAlanDetailSerializer(BaseGeoFeatureModelSerializer):
    """Oyun alanı detayı için tam serializer"""

    class Meta:
        model = OyunAlan
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class SulamaHatListSerializer(BaseGeoFeatureModelSerializer):
    """Sulama hattı listesi için minimal serializer"""

    sulama_boru_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = SulamaHat
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "boru_cap",
            "uzunluk",
            "sulama_boru_tipi_ad",
        )
        read_only_fields = fields

    def get_sulama_boru_tipi_ad(self, obj):
        return obj.sulama_boru_tipi.ad if obj.sulama_boru_tipi else None


class SulamaHatDetailSerializer(BaseGeoFeatureModelSerializer):
    """Sulama hattı detayı için tam serializer"""

    class Meta:
        model = SulamaHat
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class ElektrikHatListSerializer(BaseGeoFeatureModelSerializer):
    """Elektrik hattı listesi için minimal serializer"""

    elektrik_kablo_tipi_ad = serializers.SerializerMethodField()
    elektrik_hat_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = ElektrikHat
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "boru_cap",
            "gerilim",
            "uzunluk",
            "elektrik_kablo_tipi_ad",
            "elektrik_hat_tipi_ad",
        )
        read_only_fields = fields

    def get_elektrik_kablo_tipi_ad(self, obj):
        return obj.elektrik_kablo_tipi.ad if obj.elektrik_kablo_tipi else None

    def get_elektrik_hat_tipi_ad(self, obj):
        return obj.elektrik_hat_tipi.ad if obj.elektrik_hat_tipi else None


class ElektrikHatDetailSerializer(BaseGeoFeatureModelSerializer):
    """Elektrik hattı detayı için tam serializer"""

    class Meta:
        model = ElektrikHat
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class KanalHatListSerializer(BaseGeoFeatureModelSerializer):
    """Kanal hattı listesi için minimal serializer"""

    kanal_boru_tipi_ad = serializers.SerializerMethodField()

    class Meta:
        model = KanalHat
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "boru_cap",
            "uzunluk",
            "kanal_boru_tipi_ad",
        )
        read_only_fields = fields

    def get_kanal_boru_tipi_ad(self, obj):
        return obj.kanal_boru_tipi.ad if obj.kanal_boru_tipi else None


class KanalHatDetailSerializer(BaseGeoFeatureModelSerializer):
    """Kanal hattı detayı için tam serializer"""

    class Meta:
        model = KanalHat
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")


class ParkAboneListSerializer(BaseGeoFeatureModelSerializer):
    """Park abone listesi için minimal serializer"""

    class Meta:
        model = ParkAbone
        geo_field = "geom"
        fields = (
            "id",
            "uuid",
            "abone_tipi",
            "abone_no",
            "abone_tarihi",
        )
        read_only_fields = fields


class ParkAboneDetailSerializer(BaseGeoFeatureModelSerializer):
    """Park abone detayı için tam serializer"""

    class Meta:
        model = ParkAbone
        geo_field = "geom"
        exclude = ("created_at", "updated_at", "osm_id", "extra_data")
