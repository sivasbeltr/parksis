from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from parkbahce import auth_views, views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin/", admin.site.urls),
    path("parkbahce/", include("parkbahce.urls")),
    path("istakip/", include("istakip.urls")),
    path("api/v1/", include("api.urls")),
    path("hesap/giris/", auth_views.login_view, name="login"),
    path("hesap/cikis/", auth_views.logout_view, name="logout"),
    path("hesap/profil/", auth_views.profile_view, name="profile"),
    path("hesap/ayarlar/", auth_views.profile_settings_view, name="profile_settings"),
]

# Media files serving during development
if settings.DEBUG and not getattr(settings, "USE_MINIO", False):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
