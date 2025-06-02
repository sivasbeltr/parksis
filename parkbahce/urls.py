# parkbahce.urls

from django.urls import path

from . import views

app_name = "parkbahce"

urlpatterns = [
    path("parklar/", views.park_list, name="park_list"),
    path("parklar/<uuid:park_uuid>/", views.park_detail, name="park_detail"),
]
