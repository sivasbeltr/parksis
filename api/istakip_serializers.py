from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from istakip.models import Gorev, GunlukKontrol, Personel


class PersonelSerializer(serializers.ModelSerializer):
    """Personel serializer for basic info"""

    class Meta:
        model = Personel
        fields = ["uuid", "ad", "pozisyon", "telefon"]
