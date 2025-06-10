from django.urls import path

from . import views

app_name = "istakip"

urlpatterns = [
    # Mobil Sorun İletim Sistemi
    path(
        "sorun-ilet/", views.MobilSorunBildirView.as_view(), name="mobil_sorun_bildir"
    ),
    # API Endpoints
    path(
        "api/konum-park-bul/", views.mobil_konum_park_bul, name="mobil_konum_park_bul"
    ),
    path("api/sorun-kaydet/", views.mobil_sorun_kaydet, name="mobil_sorun_kaydet"),
    # Mobil Listeleme Sayfaları
    path(
        "mobil/kontroller/",
        views.MobilKontrolListesiView.as_view(),
        name="mobil_kontrol_listesi",
    ),
    path(
        "mobil/sorunlar/",
        views.MobilSorunListesiView.as_view(),
        name="mobil_sorun_listesi",
    ),
    path(
        "mobil/gorevlerim/",
        views.MobilAtananGorevlerView.as_view(),
        name="mobil_atanan_gorevler",
    ),
    path(
        "mobil/gunluk-rapor/",
        views.MobilGunlukRaporView.as_view(),
        name="mobil_gunluk_rapor",
    ),
    path(
        "mobil/sorumlu-parklar/",
        views.MobilSorumluParklarView.as_view(),
        name="mobil_sorumlu_parklar",
    ),
]
