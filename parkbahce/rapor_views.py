from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from auth.decorators import roles_required


@roles_required("admin", "mudur", "ofis")
def rapor_index(request):
    """
    Raporlar ana sayfası - kategorize edilmiş rapor indeksi
    """

    # Rapor kategorileri ve içerikleri
    rapor_kategorileri = {
        "park_raporlari": {
            "baslik": "Park Raporları",
            "aciklama": "Park yönetimi ve analiz raporları",
            "icon": "fas fa-seedling",
            "renk": "green",
            "raporlar": [
                {
                    "ad": "Genel Park Raporu",
                    "aciklama": "Tüm parkların genel durumu ve istatistikleri",
                    "icon": "fas fa-chart-pie",
                    "url": "#",
                },
                {
                    "ad": "Park Envanter Raporu",
                    "aciklama": "Parkların detaylı envanter listesi ve özellikleri",
                    "icon": "fas fa-list-alt",
                    "url": "#",
                },
                {
                    "ad": "Park Tipi Analizi",
                    "aciklama": "Park tiplerinin dağılımı ve karşılaştırmalı analiz",
                    "icon": "fas fa-chart-bar",
                    "url": "#",
                },
                {
                    "ad": "Alan Kullanım Raporu",
                    "aciklama": "Park alanlarının kullanım oranları ve etkinlik analizi",
                    "icon": "fas fa-chart-area",
                    "url": "#",
                },
            ],
        },
        "altyapi_raporlari": {
            "baslik": "Altyapı Raporları",
            "aciklama": "Sulama, elektrik ve diğer altyapı sistemleri",
            "icon": "fas fa-cog",
            "renk": "blue",
            "raporlar": [
                {
                    "ad": "Sulama Sistemi Raporu",
                    "aciklama": "Sulama sistemlerinin durumu ve performans analizi",
                    "icon": "fas fa-tint",
                    "url": "#",
                },
                {
                    "ad": "Elektrik Altyapı Raporu",
                    "aciklama": "Elektrik sistemleri ve aydınlatma altyapısı durumu",
                    "icon": "fas fa-bolt",
                    "url": "#",
                },
                {
                    "ad": "Abonelik Durumu Raporu",
                    "aciklama": "Su, elektrik ve doğalgaz aboneliklerinin detayları",
                    "icon": "fas fa-file-invoice",
                    "url": "#",
                },
                {
                    "ad": "Altyapı Maliyet Analizi",
                    "aciklama": "Altyapı sistemlerinin maliyet ve verimlilik analizi",
                    "icon": "fas fa-calculator",
                    "url": "#",
                },
            ],
        },
        "bakim_raporlari": {
            "baslik": "Bakım Raporları",
            "aciklama": "Bakım işlemleri ve performans takibi",
            "icon": "fas fa-tools",
            "renk": "orange",
            "raporlar": [
                {
                    "ad": "Bakım Performans Raporu",
                    "aciklama": "Bakım işlemlerinin performansı ve tamamlanma oranları",
                    "icon": "fas fa-chart-line",
                    "url": "#",
                },
                {
                    "ad": "Periyodik Bakım Raporu",
                    "aciklama": "Planlı bakım işlemlerinin takibi ve planlaması",
                    "icon": "fas fa-calendar-check",
                    "url": "#",
                },
                {
                    "ad": "Sorun Takip Raporu",
                    "aciklama": "Bildirilen sorunların çözüm süreçleri ve analizi",
                    "icon": "fas fa-exclamation-triangle",
                    "url": "#",
                },
            ],
        },
        "cografi_raporlar": {
            "baslik": "Coğrafi Raporlar",
            "aciklama": "Mahalle ve bölge bazında analiz raporları",
            "icon": "fas fa-map-marked-alt",
            "renk": "purple",
            "raporlar": [
                {
                    "ad": "Mahalle Bazında Park Dağılımı",
                    "aciklama": "Mahalleler bazında park sayısı ve alan dağılımı",
                    "icon": "fas fa-map-pin",
                    "url": "#",
                },
                {
                    "ad": "Coğrafi Yoğunluk Analizi",
                    "aciklama": "Park yoğunluğu ve erişilebilirlik harita analizi",
                    "icon": "fas fa-heatmap",
                    "url": "#",
                },
                {
                    "ad": "Nüfus Bazında Park Oranı",
                    "aciklama": "Mahalle nüfusuna göre park alanı yeterlilik analizi",
                    "icon": "fas fa-users",
                    "url": "#",
                },
            ],
        },
        "malzeme_raporlari": {
            "baslik": "Malzeme & Donatı",
            "aciklama": "Park donatıları ve malzeme yönetimi",
            "icon": "fas fa-chess-board",
            "renk": "teal",
            "raporlar": [
                {
                    "ad": "Donatı Envanter Raporu",
                    "aciklama": "Park donatılarının envanter listesi ve durumu",
                    "icon": "fas fa-chair",
                    "url": "#",
                },
                {
                    "ad": "Habitat ve Bitki Raporu",
                    "aciklama": "Park içi bitki örtüsü ve habitat analizi",
                    "icon": "fas fa-leaf",
                    "url": "#",
                },
                {
                    "ad": "Donatı Yaşam Döngüsü",
                    "aciklama": "Park donatılarının yaşam döngüsü ve yenileme planı",
                    "icon": "fas fa-recycle",
                    "url": "#",
                },
            ],
        },
        "finansal_raporlar": {
            "baslik": "Finansal Raporlar",
            "aciklama": "Maliyet analizi ve bütçe raporları",
            "icon": "fas fa-coins",
            "renk": "amber",
            "raporlar": [
                {
                    "ad": "Maliyet Analiz Raporu",
                    "aciklama": "Park işletme maliyetleri ve bütçe analizi",
                    "icon": "fas fa-chart-pie",
                    "url": "#",
                },
                {
                    "ad": "Yatırım Getiri Analizi",
                    "aciklama": "Park yatırımlarının sosyal ve ekonomik getiri analizi",
                    "icon": "fas fa-trending-up",
                    "url": "#",
                },
            ],
        },
    }

    context = {
        "rapor_kategorileri": rapor_kategorileri,
    }

    return render(request, "rapor/index.html", context)
