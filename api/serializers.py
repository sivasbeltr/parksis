# geo serializer
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from ortak.models import Mahalle
from parkbahce.models import Park, ParkTip, SulamaKaynak, SulamaTip
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
        read_only_fields = fields


class SulamaKaynakSerializer(serializers.ModelSerializer):

    class Meta:
        model = SulamaKaynak
        fields = "__all__"
        read_only_fields = fields


class SulamaTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = SulamaTip
        fields = "__all__"
        read_only_fields = fields
