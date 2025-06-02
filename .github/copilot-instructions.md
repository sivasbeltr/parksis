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
> **Not:** Bu yönergeler, Copilot ve geliştirici ekip için rehber niteliğindedir. Tüm kod önerileri bu prensipler çerçevesinde geliştirilmelidir.
