# bu dosyada viewset'ler tanımlanır ama veritabanında view fonksiyonları ile oluşturulan modeller kullanılır.

import json

from django.db import connection
from rest_framework.response import Response
from rest_framework.views import APIView


class ParkbahceListApiView(APIView):
    """
    API view to retrieve park data in GeoJSON format.
    Normalde park harita verileri çok yavaş geldiği için bunu kullanıyoruz.
    """

    def get(self, request, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("SELECT geojson FROM parkbahce.view_parkbahce_list_api")
            row = cursor.fetchone()
            if row:
                # Parse the geojson column if it's a string
                geojson_data = row[0]
                if isinstance(geojson_data, str):
                    geojson_data = json.loads(geojson_data)
                return Response(geojson_data)
            return Response({})
