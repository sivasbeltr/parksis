// Park İstakip Katmanları JavaScript Modülü
// İş Takip Katmanları Yönetimi - Sivas Belediyesi

// İstakip katman yöneticisi sınıfı
class IstakipLayerManager {
    constructor(map, colors) {
        this.map = map;
        this.colors = colors;
        this.istakipLayers = {};
        this.dateRange = {
            baslangic: null,
            bitis: null
        };
        this.initializeEventListeners();
        this.setDefaultDateRange();
        this.loadLayerCounts();
    }

    // Varsayılan tarih aralığını ayarla (son 1 ay)
    setDefaultDateRange() {
        const today = new Date();
        const oneMonthAgo = new Date();
        oneMonthAgo.setMonth(today.getMonth() - 1);

        this.dateRange.bitis = today.toISOString().split('T')[0];
        this.dateRange.baslangic = oneMonthAgo.toISOString().split('T')[0];

        // Form alanlarını güncelle
        document.getElementById('bitis-tarih').value = this.dateRange.bitis;
        document.getElementById('baslangic-tarih').value = this.dateRange.baslangic;
    }

    // Event listener'ları başlat
    initializeEventListeners() {
        // Tarih uygula butonu
        document.getElementById('tarih-uygula').addEventListener('click', () => {
            this.updateDateRange();
            this.refreshAllLayers();
            this.loadLayerCounts();
        });

        // Görev katman checkbox'ları
        const gorevTypes = ['planlanmis', 'devam-ediyor', 'onaya-gonderildi', 'tamamlandi', 'iptal', 'gecikmis'];
        gorevTypes.forEach(type => {
            const checkbox = document.getElementById(`gorev-${type}-toggle`);
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    this.toggleGorevLayer(type, checkbox.checked);
                });
            }
        });

        // Kontrol katman checkbox'ları
        const kontrolTypes = ['sorun-yok', 'sorun-var', 'acil', 'gozden-gecirildi', 'ise-donusturuldu', 'cozuldu'];
        kontrolTypes.forEach(type => {
            const checkbox = document.getElementById(`kontrol-${type}-toggle`);
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    this.toggleKontrolLayer(type, checkbox.checked);
                });
            }
        });
    }

    // Tarih aralığını güncelle
    updateDateRange() {
        const baslangicInput = document.getElementById('baslangic-tarih');
        const bitisInput = document.getElementById('bitis-tarih');

        this.dateRange.baslangic = baslangicInput.value;
        this.dateRange.bitis = bitisInput.value;

        console.log('Tarih aralığı güncellendi:', this.dateRange);
    }

    // Katman sayılarını yükle
    async loadLayerCounts() {
        try {
            const params = new URLSearchParams();
            if (this.dateRange.baslangic) {
                params.append('baslangic_tarih', this.dateRange.baslangic);
            }
            if (this.dateRange.bitis) {
                params.append('bitis_tarih', this.dateRange.bitis);
            }

            // Görev sayıları
            const gorevTypes = ['planlanmis', 'devam-ediyor', 'onaya-gonderildi', 'tamamlandi', 'iptal', 'gecikmis'];
            for (const type of gorevTypes) {
                try {
                    const response = await fetch(`/api/v1/gorevler/${type}/?${params.toString()}`);
                    if (response.ok) {
                        const data = await response.json();
                        const count = data.features ? data.features.length : 0;
                        const countElement = document.getElementById(`gorev-${type}-count`);
                        if (countElement) {
                            countElement.textContent = count;
                        }
                    }
                } catch (error) {
                    console.error(`Görev ${type} sayısı yüklenirken hata:`, error);
                }
            }

            // Kontrol sayıları
            const kontrolTypes = ['sorun-yok', 'sorun-var', 'acil', 'gozden-gecirildi', 'ise-donusturuldu', 'cozuldu'];
            for (const type of kontrolTypes) {
                try {
                    const response = await fetch(`/api/v1/gunluk-kontrol/${type}/?${params.toString()}`);
                    if (response.ok) {
                        const data = await response.json();
                        const count = data.features ? data.features.length : 0;
                        const countElement = document.getElementById(`kontrol-${type}-count`);
                        if (countElement) {
                            countElement.textContent = count;
                        }
                    }
                } catch (error) {
                    console.error(`Kontrol ${type} sayısı yüklenirken hata:`, error);
                }
            }
        } catch (error) {
            console.error('Katman sayıları yüklenirken genel hata:', error);
        }
    }

    // Tüm aktif katmanları yenile
    refreshAllLayers() {
        Object.keys(this.istakipLayers).forEach(layerKey => {
            if (this.istakipLayers[layerKey] && this.map.getLayers().getArray().includes(this.istakipLayers[layerKey])) {
                if (layerKey.startsWith('gorev-')) {
                    const type = layerKey.replace('gorev-', '');
                    this.loadGorevLayer(type);
                } else if (layerKey.startsWith('kontrol-')) {
                    const type = layerKey.replace('kontrol-', '');
                    this.loadKontrolLayer(type);
                }
            }
        });
    }

    // Görev katmanını aç/kapat
    toggleGorevLayer(type, isVisible) {
        const layerKey = `gorev-${type}`;

        if (isVisible) {
            this.loadGorevLayer(type);
        } else {
            this.removeLayer(layerKey);
        }
    }

    // Kontrol katmanını aç/kapat
    toggleKontrolLayer(type, isVisible) {
        const layerKey = `kontrol-${type}`;

        if (isVisible) {
            this.loadKontrolLayer(type);
        } else {
            this.removeLayer(layerKey);
        }
    }

    // Görev katmanını yükle
    async loadGorevLayer(type) {
        const layerKey = `gorev-${type}`;
        console.log(`${layerKey} katmanı yükleniyor...`);

        try {
            // Mevcut katmanı kaldır
            this.removeLayer(layerKey);

            // API'den veri çek
            const url = this.buildGorevApiUrl(type);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Katmanı oluştur
            const layer = this.createGorevLayer(data, type);

            // Katmanı haritaya ekle
            this.istakipLayers[layerKey] = layer;
            this.map.addLayer(layer);

            console.log(`${layerKey} katmanı başarıyla yüklendi. ${data.features ? data.features.length : 0} öğe.`);
        } catch (error) {
            console.error(`${layerKey} katmanı yüklenirken hata:`, error);
            this.showNotification(`${type} görevleri yüklenirken hata oluştu.`, 'error');
        }
    }

    // Kontrol katmanını yükle
    async loadKontrolLayer(type) {
        const layerKey = `kontrol-${type}`;
        console.log(`${layerKey} katmanı yükleniyor...`);

        try {
            // Mevcut katmanı kaldır
            this.removeLayer(layerKey);

            // API'den veri çek
            const url = this.buildKontrolApiUrl(type);
            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Katmanı oluştur
            const layer = this.createKontrolLayer(data, type);

            // Katmanı haritaya ekle
            this.istakipLayers[layerKey] = layer;
            this.map.addLayer(layer);

            console.log(`${layerKey} katmanı başarıyla yüklendi. ${data.features ? data.features.length : 0} öğe.`);
        } catch (error) {
            console.error(`${layerKey} katmanı yüklenirken hata:`, error);
            this.showNotification(`${type} kontrolleri yüklenirken hata oluştu.`, 'error');
        }
    }

    // Görev API URL'si oluştur
    buildGorevApiUrl(type) {
        const baseUrl = `/api/v1/gorevler/${type}/`;
        const params = new URLSearchParams();

        if (this.dateRange.baslangic) {
            params.append('baslangic_tarih', this.dateRange.baslangic);
        }
        if (this.dateRange.bitis) {
            params.append('bitis_tarih', this.dateRange.bitis);
        }

        // BBOX ekle (mevcut harita görünümü)
        const view = this.map.getView();
        const extent = view.calculateExtent(this.map.getSize());
        const bbox = ol.proj.transformExtent(extent, 'EPSG:3857', 'EPSG:4326');
        params.append('bbox', bbox.join(','));

        return `${baseUrl}?${params.toString()}`;
    }

    // Kontrol API URL'si oluştur
    buildKontrolApiUrl(type) {
        const baseUrl = `/api/v1/gunluk-kontrol/${type}/`;
        const params = new URLSearchParams();

        if (this.dateRange.baslangic) {
            params.append('baslangic_tarih', this.dateRange.baslangic);
        }
        if (this.dateRange.bitis) {
            params.append('bitis_tarih', this.dateRange.bitis);
        }

        // BBOX ekle (mevcut harita görünümü)
        const view = this.map.getView();
        const extent = view.calculateExtent(this.map.getSize());
        const bbox = ol.proj.transformExtent(extent, 'EPSG:3857', 'EPSG:4326');
        params.append('bbox', bbox.join(','));

        return `${baseUrl}?${params.toString()}`;
    }

    // Görev katmanı oluştur
    createGorevLayer(geojsonData, type) {
        const color = this.colors.GOREV_DURUM[type.replace('-', '_')] || '#10B981';

        const vectorSource = new ol.source.Vector({
            features: new ol.format.GeoJSON().readFeatures(geojsonData, {
                featureProjection: 'EPSG:3857'
            })
        });

        return new ol.layer.Vector({
            source: vectorSource,
            style: this.createGorevMarkerStyle(color),
            zIndex: 10,
            title: `gorev-${type}`
        });
    }

    // Kontrol katmanı oluştur
    createKontrolLayer(geojsonData, type) {
        const color = this.colors.KONTROL_DURUM[type.replace('-', '_')] || '#10B981';

        const vectorSource = new ol.source.Vector({
            features: new ol.format.GeoJSON().readFeatures(geojsonData, {
                featureProjection: 'EPSG:3857'
            })
        });

        return new ol.layer.Vector({
            source: vectorSource,
            style: this.createKontrolMarkerStyle(color),
            zIndex: 11,
            title: `kontrol-${type}`
        });
    }

    // Görev marker stili oluştur (kare şekil)
    createGorevMarkerStyle(color) {
        return new ol.style.Style({
            image: new ol.style.Icon({
                src: `data:image/svg+xml;utf8,<svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><rect x='2' y='2' width='20' height='20' rx='3' fill='${encodeURIComponent(color)}' stroke='white' stroke-width='2'/><path d='M8 12l2 2 4-4' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>`,
                anchor: [0.5, 0.5],
                scale: 1
            })
        });
    }

    // Kontrol marker stili oluştur (daire şekil)
    createKontrolMarkerStyle(color) {
        return new ol.style.Style({
            image: new ol.style.Icon({
                src: `data:image/svg+xml;utf8,<svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'><circle cx='12' cy='12' r='10' fill='${encodeURIComponent(color)}' stroke='white' stroke-width='2'/><path d='M9 12l2 2 4-4' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'/></svg>`,
                anchor: [0.5, 0.5],
                scale: 1
            })
        });
    }

    // Katmanı kaldır
    removeLayer(layerKey) {
        if (this.istakipLayers[layerKey]) {
            this.map.removeLayer(this.istakipLayers[layerKey]);
            delete this.istakipLayers[layerKey];
        }
    }

    // Bildirim göster
    showNotification(message, type = 'info') {
        // Ana parkmap.js'deki showMapNotification fonksiyonunu kullan
        if (typeof showMapNotification === 'function') {
            showMapNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    // Tüm istakip katmanlarını temizle
    clearAllLayers() {
        Object.keys(this.istakipLayers).forEach(layerKey => {
            this.removeLayer(layerKey);
        });
    }

    // Harita tıklama olayında istakip katmanlarını kontrol et
    handleMapClick(feature, layer) {
        // Katman başlığından tip belirle
        const layerTitle = layer.get('title');
        if (layerTitle && (layerTitle.startsWith('gorev-') || layerTitle.startsWith('kontrol-'))) {
            this.showIstakipFeatureDetails(feature, layerTitle);
            return true; // İşlendiğini belirt
        }
        return false; // İşlenmediğini belirt
    }    // İstakip özellik detaylarını göster
    showIstakipFeatureDetails(feature, layerKey) {
        const properties = feature.getProperties();

        if (layerKey.startsWith('gorev-')) {
            // Görev UUID'sini al ve showGorevDetails fonksiyonunu çağır
            const gorevUuid = properties.uuid;
            if (gorevUuid && typeof showGorevDetails === 'function') {
                showGorevDetails(gorevUuid);
            }
        } else if (layerKey.startsWith('kontrol-')) {
            // Kontrol UUID'sini al ve showKontrolDetails fonksiyonunu çağır
            const kontrolUuid = properties.uuid;
            if (kontrolUuid && typeof showKontrolDetails === 'function') {
                showKontrolDetails(kontrolUuid);
            }
        }
    }
}

// Global değişken olarak export et
window.IstakipLayerManager = IstakipLayerManager;