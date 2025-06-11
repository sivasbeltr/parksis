from django.urls import path

from . import htmx_views, kullanici_views, mobil_views, views

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
    ),  # Kullanıcı Yönetimi
    path("kullanicilar/", views.kullanici_list, name="kullanici_list"),
    path("kullanicilar/yeni/", views.kullanici_create, name="kullanici_create"),
    path(
        "kullanicilar/<uuid:personel_uuid>/",
        views.kullanici_detail,
        name="kullanici_detail",
    ),
    # HTMX Kullanıcı Sekmeler
    path(
        "kullanicilar/<uuid:personel_uuid>/bilgileri/",
        htmx_views.kullanici_bilgileri_htmx,
        name="kullanici_bilgileri_htmx",
    ),
    path(
        "kullanicilar/<uuid:personel_uuid>/parklar/",
        htmx_views.kullanici_parklar_htmx,
        name="kullanici_parklar_htmx",
    ),
    path(
        "kullanicilar/<uuid:personel_uuid>/kontroller/",
        htmx_views.kullanici_kontroller_htmx,
        name="kullanici_kontroller_htmx",
    ),
    path(
        "kullanicilar/<uuid:personel_uuid>/performans/",
        htmx_views.kullanici_performans_htmx,
        name="kullanici_performans_htmx",
    ),
    path(
        "kullanicilar/<uuid:personel_uuid>/gorevler/",
        htmx_views.kullanici_gorevler_htmx,
        name="kullanici_gorevler_htmx",
    ),
    path(
        "kullanicilar/<uuid:personel_uuid>/park-atama/",
        htmx_views.park_atama_htmx,
        name="park_atama_htmx",
    ),
    path(
        "park-atama/<uuid:atama_uuid>/delete/",
        htmx_views.park_atama_sil_htmx,
        name="park_atama_sil_htmx",
    ),
]
