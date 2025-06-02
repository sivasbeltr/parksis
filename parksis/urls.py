from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from parkbahce import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    path("parkbahce/", include("parkbahce.urls")),
]
