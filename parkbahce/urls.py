# parkbahce.urls

from django.contrib import admin
from django.urls import include, path

from .views import index, park_delete, park_detail, park_edit, park_list

app_name = "parkbahce"


urlpatterns = [
    path("", index),
    path("list", park_list, name="park_list"),
    path("detail/<uuid:uuid>", park_detail, name="park_detail"),
    path("edit/<uuid:uuid>", park_edit, name="park_edit"),
    path("delete/<uuid:uuid>", park_delete, name="park_delete"),
]
