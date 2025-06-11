from django.urls import path

from . import mobil_views

app_name = "istakip"

urlpatterns = [
    # Mobil Sorun İletim Sistemi
    path(
        "sorun-ilet/",
        mobil_views.MobilSorunBildirView.as_view(),
        name="mobil_sorun_bildir",
    ),
    # API Endpoints
    path(
        "api/konum-park-bul/",
        mobil_views.mobil_konum_park_bul,
        name="mobil_konum_park_bul",
    ),
    path(
        "api/sorun-kaydet/", mobil_views.mobil_sorun_kaydet, name="mobil_sorun_kaydet"
    ),
    # Mobil Listeleme Sayfaları
    path(
        "mobil/kontroller/",
        mobil_views.MobilKontrolListesiView.as_view(),
        name="mobil_kontrol_listesi",
    ),
    path(
        "mobil/sorunlar/",
        mobil_views.MobilSorunListesiView.as_view(),
        name="mobil_sorun_listesi",
    ),
    path(
        "mobil/gorevlerim/",
        mobil_views.MobilAtananGorevlerView.as_view(),
        name="mobil_atanan_gorevler",
    ),
    path(
        "mobil/gunluk-rapor/",
        mobil_views.MobilGunlukRaporView.as_view(),
        name="mobil_gunluk_rapor",
    ),
    path(
        "mobil/sorumlu-parklar/",
        mobil_views.MobilSorumluParklarView.as_view(),
        name="mobil_sorumlu_parklar",
    ),
]
