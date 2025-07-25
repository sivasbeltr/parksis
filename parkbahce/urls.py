# parkbahce.urls

from django.urls import path

from . import abone_views, htmx_views, istatistik_views, rapor_views, views

app_name = "parkbahce"

urlpatterns = [
    path("parklar/", views.park_list, name="park_list"),
    path("parklar/<uuid:park_uuid>/", views.park_detail, name="park_detail"),
    path("mahalleler/", views.mahalle_list, name="mahalle_list"),
    path("mahalle/<uuid:mahalle_uuid>/", views.mahalle_detail, name="mahalle_detail"),
    path("donatilar/", views.donatilar_list, name="donatilar_list"),
    path("habitatlar/", views.habitatlar_list, name="habitatlar_list"),
    path(
        "park-donati-habitat-listesi/",
        views.park_donati_habitat_list,
        name="park_donati_habitat_list",
    ),
    path("park-harita/", views.park_harita, name="park_harita"),
    path("istatistikler/", istatistik_views.istatistik_index, name="istatistik_index"),
    path("raporlar/", rapor_views.rapor_index, name="rapor_index"),
    # Altyapı yönetimi
    path("altyapi/sulama-sistemi/", views.sulama_sistemi, name="sulama_sistemi"),
    path(
        "altyapi/elektrik-altyapisi/",
        views.elektrik_altyapisi,
        name="elektrik_altyapisi",
    ),
    path("altyapi/kanal-hatlari/", views.kanal_hatlari, name="kanal_hatlari"),
    path("altyapi/yol-agi/", views.yol_agi, name="yol_agi"),
    path(
        "altyapi/abonelik-takibi/", abone_views.abonelik_takibi, name="abonelik_takibi"
    ),  # Abone yönetimi
    path("abone/ekle/", abone_views.abone_ekle, name="abone_ekle"),
    path(
        "abone/ekle/<uuid:park_uuid>/", abone_views.abone_ekle, name="abone_ekle_park"
    ),
    path("abone/<uuid:abone_uuid>/", abone_views.abone_detail, name="abone_detail"),
    path(
        "abone/<uuid:abone_uuid>/duzenle/",
        abone_views.abone_duzenle,
        name="abone_duzenle",
    ),
    path("abone/<uuid:abone_uuid>/sil/", abone_views.abone_sil, name="abone_sil"),
    path(
        "abone/<uuid:abone_uuid>/endeks-ekle/",
        abone_views.endeks_ekle,
        name="endeks_ekle",
    ),
    # Park ve Mahalle detay HTMX endpoints
    path(
        "htmx/park-detail/<uuid:park_uuid>/",
        htmx_views.park_detail_htmx,
        name="park_detail_htmx",
    ),
    path(
        "htmx/mahalle-detail/<uuid:mahalle_uuid>/",
        htmx_views.mahalle_detail_htmx,
        name="mahalle_detail_htmx",
    ),  # Park Detay Sekmeleri HTMX
    path(
        "htmx/park-tabs/<uuid:park_uuid>/habitatlar/",
        htmx_views.park_habitatlar_tab_htmx,
        name="park_habitatlar_tab_htmx",
    ),
    path(
        "htmx/park-tabs/<uuid:park_uuid>/donatilar/",
        htmx_views.park_donatilar_tab_htmx,
        name="park_donatilar_tab_htmx",
    ),
    path(
        "htmx/park-tabs/<uuid:park_uuid>/oyun-gruplari/",
        htmx_views.park_oyun_gruplari_tab_htmx,
        name="park_oyun_gruplari_tab_htmx",
    ),
    path(
        "htmx/park-tabs/<uuid:park_uuid>/aboneler/",
        htmx_views.park_aboneler_tab_htmx,
        name="park_aboneler_tab_htmx",
    ),
    path(
        "htmx/park-tabs/<uuid:park_uuid>/altyapi/",
        htmx_views.park_altyapi_tab_htmx,
        name="park_altyapi_tab_htmx",
    ),
    path(
        "htmx/park-tabs/<uuid:park_uuid>/alanlar/",
        htmx_views.park_alanlar_tab_htmx,
        name="park_alanlar_tab_htmx",
    ),
    path(
        "htmx/park-tabs/<uuid:park_uuid>/istatistikler/",
        htmx_views.park_istatistikler_tab_htmx,
        name="park_istatistikler_tab_htmx",
    ),
    path(
        "htmx/park-tabs/<uuid:park_uuid>/sorumlu/",
        htmx_views.park_sorumlu_tab_htmx,
        name="park_sorumlu_tab_htmx",
    ),
    path(
        "htmx/park-tabs/<uuid:park_uuid>/sorun-gecmisi/",
        htmx_views.park_sorun_gecmisi_tab_htmx,
        name="park_sorun_gecmisi_tab_htmx",
    ),
    # HTMX endpoints
    path("htmx/recent-parks/", htmx_views.recent_parks_htmx, name="recent_parks_htmx"),
    path(
        "htmx/quick-actions/", htmx_views.quick_actions_htmx, name="quick_actions_htmx"
    ),
    path(
        "htmx/park-types-distribution/",
        htmx_views.park_types_distribution_htmx,
        name="park_types_distribution_htmx",
    ),
    path(
        "htmx/neighborhood-distribution/",
        htmx_views.neighborhood_distribution_htmx,
        name="neighborhood_distribution_htmx",
    ),
    path(
        "htmx/infrastructure-status/",
        htmx_views.infrastructure_status_htmx,
        name="infrastructure_status_htmx",
    ),  # Park-Kullanıcı Eşleştirme API'leri
    path(
        "eslestir/<uuid:park_uuid>/ekle/<uuid:kullanici_uuid>/",
        views.kullanici_park_ekle,
        name="kullanici_park_ekle",
    ),
    path(
        "eslestir/<uuid:park_uuid>/cikar/<uuid:kullanici_uuid>/",
        views.kullanici_park_cikar,
        name="kullanici_park_cikar",
    ),
    path(
        "eslestir/<uuid:park_uuid>/kontrol/<uuid:kullanici_uuid>/",
        views.kullanici_park_kontrol,
        name="kullanici_park_kontrol",
    ),
    # İstakip detay endpoints
    path(
        "htmx/gorev-detail/<uuid:gorev_uuid>/",
        htmx_views.gorev_detail_htmx,
        name="gorev_detail_htmx",
    ),
    path(
        "htmx/kontrol-detail/<uuid:kontrol_uuid>/",
        htmx_views.kontrol_detail_htmx,
        name="kontrol_detail_htmx",
    ),
]
