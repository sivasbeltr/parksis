from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path

from parkbahce import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    path("parkbahce/", include("parkbahce.urls")),
    path("istakip/", include("istakip.urls")),
    path("api/v1/", include("api.urls")),
]

# Media files serving during development
if settings.DEBUG and not getattr(settings, "USE_MINIO", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
