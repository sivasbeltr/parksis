# parkbahce.urls

from django.urls import path

from . import istatistik_views, rapor_views, views

app_name = "parkbahce"

urlpatterns = [
    path("parklar/", views.park_list, name="park_list"),
    path("parklar/<uuid:park_uuid>/", views.park_detail, name="park_detail"),
    path("istatistikler/", istatistik_views.istatistik_index, name="istatistik_index"),
    path("raporlar/", rapor_views.rapor_index, name="rapor_index"),
]
