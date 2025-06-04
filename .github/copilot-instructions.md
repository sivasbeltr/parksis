# Copilot Instructions

Bu proje, Sivas Belediyesi Park ve Bahçeler Müdürlüğü'ne ait bir park yönetim sistemidir. Aşağıdaki kurallara ve tasarım prensiplerine uyulmalıdır:

## 📊 Proje Genel Bilgiler
- **Teknoloji Stack:** Django + PostGIS + Tailwind CSS + Chart.js
- **Hedef Kullanıcılar:** Park ve Bahçeler Müdürlüğü çalışanları (birincil), Saha personeli (mobil), Vatandaşlar (gelecekte)
- **Admin Panel:** Sadece prototip amaçlı kullanılacak

## 🎨 Tasarım Prensipleri
- **Modern, estetik ve zarif arayüz:** Park sistemine uygun yeşil tonlar, doğa temalı görseller ve ikonlar
- **Mobile-first yaklaşım:** Öncelikle mobil cihazlar için optimize edilecek
- **Responsive tasarım:** Tüm cihaz boyutlarında mükemmel görünüm
- **Dark/Light modlar:** Kullanıcılar tema arasında geçiş yapabilecek
- **Sivas Belediyesi kurumsal kimliği:** Logo, renkler ve tipografi uyumlu

## 🖥️ Arayüz Yapısı
- **Sidebar:** Sol tarafta tree yapısında, açılabilir/kapanabilir, aranabilir menü
- **Navbar:** Üst kısımda kullanıcı bilgileri, tema değişimi, bildirimler
- **Ana İçerik:** Responsive grid sistemi ile organize edilmiş içerik alanı

## 💻 Teknik Gereksinimler

### Frontend
- **CSS Framework:** Sadece Tailwind CSS (CDN entegrasyonu)
- **Grafik Kütüphanesi:** Chart.js (istatistik ve analiz grafikleri için)
- **Harita Kütüphanesi:** OpenLayers + OpenStreetMap (harita işlemleri için)
- **Template Yapısı:** Django şablon sistemi
- **JavaScript:** Vanilla JS veya minimal kütüphaneler

### Backend & API
- **Framework:** Django + Django GIS
- **Veritabanı:** PostgreSQL + PostGIS
- **API:** REST API endpointleri `/api/v1/` prefixi ile
- **API Uygulaması:** `api/` dizininde organize edilecek

### Mobil Arayüz
- **Saha Personeli:** PWA (Progressive Web App) yaklaşımı
- **Özellikler:** Sorun bildirimi, fotoğraf yükleme, konum tabanlı işlemler
- **Offline Desteği:** Temel işlevsellik offline çalışabilir

## 📱 İş Akışı ve Takip Sistemi
- **İş Takip:** Her oluşturulan iş aşama aşama takip edilecek
- **Bildirim Sistemi:** Saha personelinden gelen sorun bildirimleri
- **Analitik:** Tüm işlemler analiz edilebilir olacak
- **Raporlama:** Detaylı raporlama ve gösterge paneli

## 🎯 Kullanıcı Rolleri
1. **Yönetici:** Tam yetki, tüm modüller
2. **Park Uzmanı:** Park yönetimi, raporlama
3. **Saha Personeli:** Sorun bildirimi, mobil arayüz
4. **Vatandaş:** (Gelecekte) Bildirim ve takip

## 🌿 Park Yönetimi Modülleri
- **Park Envanteri:** Parklar, donatılar, habitatlar
- **Bakım Takibi:** Periyodik bakım planları
- **Sorun Yönetimi:** Bildirim alma ve çözüm takibi
- **Sulama Sistemi:** Otomatik sulama kontrolü
- **Elektrik Altyapısı:** Aydınlatma ve elektrik yönetimi

## ⚡ Performans ve Optimizasyon
- **Cache:** Django cache framework kullanımı
- **Veritabanı:** PostgreSQL optimizasyonu ve indexleme
- **Static Files:** MinIO veya yerel storage
- **API:** Sayfalama ve filtreleme desteği

## 🎨 Renk Paleti ve Tema
- **Ana Renkler:** Yeşil tonları (#10B981, #059669, #047857)
- **Accent Renkler:** Sivas Belediyesi kurumsal mavi
- **Dark Mode:** Koyu yeşil ve gri tonları
- **Light Mode:** Açık yeşil ve beyaz tonları

## 📋 Kod Standartları
- **Python:** PEP 8 standartları
- **Django:** Best practices ve security guidelines
- **JavaScript:** ES6+ standartları
- **CSS:** Tailwind utility-first yaklaşımı
- **Template:** Django template best practices

## 🔐 Güvenlik
- **Authentication:** Django auth sistemi
- **Authorization:** Role-based access control
- **CSRF:** Django CSRF koruması
- **Input Validation:** Form ve API validasyonu
- **File Upload:** Güvenli dosya yükleme

## 📊 Analitik ve Raporlama
- **Dashboard:** Chart.js ile interaktif grafikler
- **KPI Takibi:** Park sayısı, bakım oranları, sorun çözüm süreleri
- **Coğrafi Analiz:** PostGIS ile konum bazlı analizler
- **Zaman Serisi:** Trend analizleri ve tahminleme

## 🗂️ Şablon Yapısı
- **Ana Şablon:** Tüm sayfalar için temel şablon `templates/layout.html` dosyası kullanılacaktır.
- **Sayfa Şablonları:** Her uygulama için `templates/app_name/view_name.html` yapısı kullanılacaktır. Sınıf tabanlı view isimleri snake_case'e dönüştürülerek dosya adı olarak kullanılacaktır (ör: ParkListView → park/list_view.html).
- **Partial Şablonlar:** Tekrar kullanılabilir parçalar `templates/partials/` dizininde tutulacaktır. Mesela sidebar var Navbar için `templates/partials/sidebar.html` ve `templates/partials/navbar.html` gibi.

## 📜 Ek Notlar
- **Dokümantasyon:** Proje dokümantasyonu `docs/` dizininde tutulacaktır.
- **Testler:** Django test frameworkü kullanılacak, unit ve integration testler yazılacaktır.
- **Versiyon Kontrolü:** Git kullanılarak proje sürümleri takip edilecek, her özellik için ayrı branch oluşturulacaktır.
- **Pull Request:** Her yeni özellik veya düzeltme için PR oluşturulacak, kod incelemesi yapılacaktır.
- **CBS srid 4326:** Coğrafi veriler için SRID 4326 kullanılacaktır. Biz Veritabanına 5256 ile kaydedip, frontend'de 4326 olarak göstereceğiz.

## 🌐 API Yapısı ve Endpointler

### 📊 Ana API Endpointleri

#### **🌳 Park ve Ana Modeller:**
```
GET /api/v1/parklar/                           # Park listesi
GET /api/v1/parklar/{uuid}/                    # Park detayı
GET /api/v1/mahalleler/                        # Mahalle listesi
GET /api/v1/parklar-detay/                     # Park detay görünümü
```

#### **📍 Park Alt Modelleri (Park UUID üzerinden):**
```
GET /api/v1/parklar/{uuid}/habitatlar/         # Parka ait habitatlar
GET /api/v1/parklar/{uuid}/donatilar/          # Parka ait donatılar
GET /api/v1/parklar/{uuid}/oyun_gruplari/      # Parka ait oyun grupları
GET /api/v1/parklar/{uuid}/sulama_noktalari/   # Parka ait sulama noktaları
GET /api/v1/parklar/{uuid}/elektrik_noktalari/ # Parka ait elektrik noktaları
GET /api/v1/parklar/{uuid}/yesil_alanlar/      # Parka ait yeşil alanlar
GET /api/v1/parklar/{uuid}/spor_alanlar/       # Parka ait spor alanları
GET /api/v1/parklar/{uuid}/binalar/            # Parka ait binalar
GET /api/v1/parklar/{uuid}/havuzlar/           # Parka ait havuzlar
GET /api/v1/parklar/{uuid}/yollar/             # Parka ait yollar
GET /api/v1/parklar/{uuid}/oyun_alanlar/       # Parka ait oyun alanları
GET /api/v1/parklar/{uuid}/sulama_hatlari/     # Parka ait sulama hatları
GET /api/v1/parklar/{uuid}/elektrik_hatlari/   # Parka ait elektrik hatları
GET /api/v1/parklar/{uuid}/kanal_hatlari/      # Parka ait kanal hatları
GET /api/v1/parklar/{uuid}/aboneler/           # Parka ait aboneler
```

#### **🔍 Bağımsız Model Endpointleri:**

**Nokta Geometrili Modeller:**
```
GET /api/v1/habitatlar/                        # Tüm habitatlar
GET /api/v1/habitatlar/{uuid}/                 # Habitat detayı
GET /api/v1/park-donatilar/                    # Tüm park donatıları
GET /api/v1/park-donatilar/{uuid}/             # Donatı detayı
GET /api/v1/oyun-gruplari/                     # Tüm oyun grupları
GET /api/v1/oyun-gruplari/{uuid}/              # Oyun grubu detayı
GET /api/v1/sulama-noktalari/                  # Tüm sulama noktaları
GET /api/v1/sulama-noktalari/{uuid}/           # Sulama noktası detayı
GET /api/v1/elektrik-noktalari/                # Tüm elektrik noktaları
GET /api/v1/elektrik-noktalari/{uuid}/         # Elektrik noktası detayı
GET /api/v1/park-aboneler/                     # Tüm park aboneleri
GET /api/v1/park-aboneler/{uuid}/              # Abone detayı
```

**Alan Geometrili Modeller:**
```
GET /api/v1/yesil-alanlar/                     # Tüm yeşil alanlar
GET /api/v1/yesil-alanlar/{uuid}/              # Yeşil alan detayı
GET /api/v1/spor-alanlar/                      # Tüm spor alanları
GET /api/v1/spor-alanlar/{uuid}/               # Spor alanı detayı
GET /api/v1/park-binalar/                      # Tüm park binaları
GET /api/v1/park-binalar/{uuid}/               # Bina detayı
GET /api/v1/park-havuzlar/                     # Tüm park havuzları
GET /api/v1/park-havuzlar/{uuid}/              # Havuz detayı
GET /api/v1/park-yollar/                       # Tüm park yolları
GET /api/v1/park-yollar/{uuid}/                # Yol detayı
GET /api/v1/oyun-alanlar/                      # Tüm oyun alanları
GET /api/v1/oyun-alanlar/{uuid}/               # Oyun alanı detayı
```

**Çizgi Geometrili Modeller:**
```
GET /api/v1/sulama-hatlari/                    # Tüm sulama hatları
GET /api/v1/sulama-hatlari/{uuid}/             # Sulama hattı detayı
GET /api/v1/elektrik-hatlari/                  # Tüm elektrik hatları
GET /api/v1/elektrik-hatlari/{uuid}/           # Elektrik hattı detayı
GET /api/v1/kanal-hatlari/                     # Tüm kanal hatları
GET /api/v1/kanal-hatlari/{uuid}/              # Kanal hattı detayı
```

### 🌐 Filtreleme Parametreleri
```
?bbox=min_lng,min_lat,max_lng,max_lat          # Coğrafi sınır filtresi
?zoom=14                                       # Zoom seviyesi kontrolü
?park__uuid={park_uuid}                        # Belirli parka ait veriler
?mahalle=merkez                                # Mahalle filtresi
?ilce=merkez                                   # İlçe filtresi
?park_tipi=mahalle                             # Park tipi filtresi
?min_alan=100&max_alan=5000                    # Alan aralığı filtresi
```

### 🎯 API Kullanım Örnekleri
```javascript
// Belirli bir parka ait habitatları getir
fetch('/api/v1/parklar/7cebfebd-16f3-40cf-a413-9361d13f6f6c/habitatlar/')

// BBOX ile filtrelenmiş donatıları getir
fetch('/api/v1/park-donatilar/?bbox=36.9,39.7,37.1,39.8')

// Zoom seviyesine göre sınırlı veri getir
fetch('/api/v1/yesil-alanlar/?zoom=13&bbox=36.9,39.7,37.1,39.8')
```

### 📋 API Serializer Yapısı
- **Liste Serializers:** Minimal alanlar (id, uuid, ad, alan, cevre vb.)
- **Detay Serializers:** Tüm alanlar (created_at, updated_at, osm_id, extra_data hariç)
- **GeoJSON Format:** SRID 4326 formatında coğrafi veri çıkışı
- **Performance Optimization:** BBOX ve zoom seviyesi ile filtreleme

### 🗺️ Harita Entegrasyonu
- **GeoJSON:** OpenLayers ile uyumlu veri formatı
- **Dynamic Loading:** Zoom seviyesi ve bbox'a göre veri yükleme
- **Layer Management:** Park ve alt modelleri için ayrı katmanlar
- **Interactive Features:** Tıklama ve hover özellikleri

> **Not:** Bu yönergeler, Copilot ve geliştirici ekip için rehber niteliğindedir. Tüm kod önerileri bu prensipler çerçevesinde geliştirilmelidir.


