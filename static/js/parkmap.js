// Park Harita JavaScript Modülü
// Sivas Belediyesi Park ve Bahçeler Müdürlüğü

// Harita ve katman değişkenleri
let map;
let layers = {};
let currentZoom = 10;
let istakipLayers = {}; // İstakip katmanları için değişken

// Sivas Merkez koordinatları (EPSG:4326)
const sivasCenter = [37.0167, 39.7500];

// Harita başlangıç zoom seviyesi
const initialZoom = 12;

// Varsayılan filtreler
const defaultFilters = {
    gorevler: {
        durum: 'planlanmis,devam_ediyor,onaya_gonderildi,gecikmis', // Tamamlanmamış görevler
        oncelik: '',
        tarih: ''
    },
    kontroller: {
        durum: 'sorun_var,acil', // Çözülmemiş sorunlar
        tarih: ''
    }
};

// Harita başlatma
function initMap() {
    // Base layer (OpenStreetMap)
    const baseLayer = new ol.layer.Tile({
        source: new ol.source.OSM()
    });

    // Harita oluşturma
    map = new ol.Map({
        target: 'map',
        layers: [baseLayer],
        view: new ol.View({
            center: ol.proj.fromLonLat(sivasCenter),
            zoom: initialZoom
        })
    });

    // Zoom değişim olayını dinle
    map.getView().on('change:resolution', function () {
        currentZoom = map.getView().getZoom();
        updateZoomDisplay();
    });

    // Harita tıklama olayı
    map.on('singleclick', handleMapClick);

    // Temel katmanları yükle
    loadMahalleler();
    loadParklar();
    // İstakip katmanlarını yükle
    loadIstakipLayers();

    updateZoomDisplay();
}

// Zoom seviyesi göstergesi güncelle
function updateZoomDisplay() {
    document.getElementById('zoomLevel').textContent = Math.round(currentZoom);
}

// Mahalleler katmanını yükle
async function loadMahalleler() {
    try {
        const response = await fetch('/api/v1/mahalleler/');
        const data = await response.json();

        const vectorSource = new ol.source.Vector({
            features: new ol.format.GeoJSON().readFeatures(data, {
                featureProjection: 'EPSG:3857'
            })
        });

        const mahalleLayer = new ol.layer.Vector({
            source: vectorSource,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: '#6B7280',
                    width: 3,
                    lineDash: [5, 5]
                }),
                fill: new ol.style.Fill({
                    color: 'rgba(0, 0, 0, 0)'
                }),
                text: new ol.style.Text({
                    font: '12px Arial',
                    fill: new ol.style.Fill({
                        color: '#374151'
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#FFFFFF',
                        width: 2
                    })
                })
            }),
            zIndex: 1
        });

        // Mahalle isimlerini göster
        mahalleLayer.getSource().getFeatures().forEach(feature => {
            const style = mahalleLayer.getStyle().clone();
            style.getText().setText(feature.get('ad'));
            feature.setStyle(style);
        });

        layers.mahalleler = mahalleLayer;
        map.addLayer(mahalleLayer);
    } catch (error) {
        console.error('Mahalleler yüklenirken hata:', error);
    }
}

// Parklar katmanını yükle
async function loadParklar() {
    try {
        const response = await fetch('/api/v1/parkbahce-list-api/');
        const data = await response.json();

        const vectorSource = new ol.source.Vector({
            features: new ol.format.GeoJSON().readFeatures(data, {
                featureProjection: 'EPSG:3857'
            })
        });

        const parkLayer = new ol.layer.Vector({
            source: vectorSource,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: '#047857',
                    width: 2
                }),
                fill: new ol.style.Fill({
                    color: 'rgba(16, 185, 129, 0.3)'
                })
            }),
            zIndex: 2
        });

        layers.parklar = parkLayer;
        map.addLayer(parkLayer);
    } catch (error) {
        console.error('Parklar yüklenirken hata:', error);
    }
}

// İstakip katmanlarını yükle
async function loadIstakipLayers() {
    try {
        // Varsayılan filtrelerle görevleri ve kontrolleri yükle
        await loadGorevler(defaultFilters.gorevler);
        await loadGunlukKontroller(defaultFilters.kontroller);

        // İstatistikleri güncelle
        updateFilterStats();
    } catch (error) {
        console.error('İstakip katmanları yüklenirken hata:', error);
    }
}

// Görevler katmanını yükle
async function loadGorevler(filters = {}) {
    try {
        // Mevcut katmanı temizle
        if (istakipLayers.gorevler) {
            map.removeLayer(istakipLayers.gorevler);
        }

        // API URL'sini oluştur
        const params = new URLSearchParams();
        if (filters.durum) params.append('durum', filters.durum);
        if (filters.oncelik) params.append('oncelik', filters.oncelik);
        if (filters.tarih) {
            const dateRange = getDateRange(filters.tarih);
            if (dateRange.start) params.append('tarih_baslangic', dateRange.start);
            if (dateRange.end) params.append('tarih_bitis', dateRange.end);
        }

        const response = await fetch(`/api/v1/gorev-listesi/?${params.toString()}`);
        const data = await response.json();

        const vectorSource = new ol.source.Vector({
            features: new ol.format.GeoJSON().readFeatures(data, {
                featureProjection: 'EPSG:3857'
            })
        });

        const gorevLayer = new ol.layer.Vector({
            source: vectorSource,
            style: function (feature) {
                const durum = feature.get('durum');
                const oncelik = feature.get('oncelik');

                // Duruma göre ana renk
                let fillColor = '#3B82F6'; // varsayılan mavi
                let strokeColor = '#1E40AF';

                switch (durum) {
                    case 'planlanmis':
                        fillColor = '#6B7280'; // gri
                        strokeColor = '#374151';
                        break;
                    case 'devam_ediyor':
                        fillColor = '#F59E0B'; // amber
                        strokeColor = '#D97706';
                        break;
                    case 'onaya_gonderildi':
                        fillColor = '#8B5CF6'; // purple
                        strokeColor = '#7C3AED';
                        break;
                    case 'tamamlandi':
                        fillColor = '#10B981'; // green
                        strokeColor = '#059669';
                        break;
                    case 'iptal':
                        fillColor = '#EF4444'; // red
                        strokeColor = '#DC2626';
                        break;
                    case 'gecikmis':
                        fillColor = '#F97316'; // orange
                        strokeColor = '#EA580C';
                        break;
                }

                // Önceliğe göre stroke kalınlığı
                let strokeWidth = 2;
                if (oncelik === 'acil') {
                    strokeWidth = 4;
                    strokeColor = '#DC2626'; // kırmızı
                } else if (oncelik === 'yuksek') {
                    strokeWidth = 3;
                }

                return new ol.style.Style({
                    fill: new ol.style.Fill({
                        color: fillColor + '80' // %50 şeffaflık
                    }),
                    stroke: new ol.style.Stroke({
                        color: strokeColor,
                        width: strokeWidth
                    })
                });
            },
            zIndex: 10
        });

        istakipLayers.gorevler = gorevLayer;
        map.addLayer(gorevLayer);

        // Görünürlük durumunu checkbox'a göre ayarla
        const isVisible = document.getElementById('gorevlerToggle').checked;
        gorevLayer.setVisible(isVisible);

        console.log(`${data.features.length} görev yüklendi`);
    } catch (error) {
        console.error('Görevler yüklenirken hata:', error);
    }
}

// Günlük kontroller katmanını yükle
async function loadGunlukKontroller(filters = {}) {
    try {
        // Mevcut katmanı temizle
        if (istakipLayers.gunlukKontroller) {
            map.removeLayer(istakipLayers.gunlukKontroller);
        }

        // API URL'sini oluştur
        const params = new URLSearchParams();
        if (filters.durum) params.append('durum', filters.durum);
        if (filters.tarih) {
            const dateRange = getDateRange(filters.tarih);
            if (dateRange.start) params.append('tarih_baslangic', dateRange.start);
            if (dateRange.end) params.append('tarih_bitis', dateRange.end);
        } const response = await fetch(`/api/v1/kontrol-listesi/?${params.toString()}`);
        const data = await response.json();
        console.log('Günlük kontroller verisi:', data);

        // Veri kontrolü
        if (!data || !data.features || data.features.length === 0) {
            console.warn('Kontrol verisi bulunamadı veya boş');
            updateFilterStats();
            return;
        }

        console.log('Toplam kontrol features:', data.features.length);

        // Her feature'ı detaylı olarak logla
        data.features.forEach((feature, index) => {
            console.log(`Feature ${index + 1}:`, {
                type: feature.type,
                geometry: feature.geometry,
                coordinates: feature.geometry?.coordinates,
                properties: feature.properties,
                durum: feature.properties?.durum
            });
        });
        const vectorSource = new ol.source.Vector({
            features: new ol.format.GeoJSON().readFeatures(data, {
                featureProjection: 'EPSG:3857'
            })
        });

        console.log('🔄 Vector source oluşturuldu, feature sayısı:', vectorSource.getFeatures().length);

        // Features kontrolü
        vectorSource.getFeatures().forEach((feature, index) => {
            console.log(`📍 Feature ${index + 1}:`, {
                uuid: feature.get('uuid'),
                durum: feature.get('durum'),
                geometry: feature.getGeometry().getType(),
                coordinates: feature.getGeometry().getCoordinates()
            });
        });

        const kontrolLayer = new ol.layer.Vector({
            source: vectorSource,
            style: function (feature) {
                const durum = feature.get('durum');
                let color = '#10B981'; // varsayılan yeşil
                let iconUrl = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMzYiIHZpZXdCb3g9IjAgMCAyNCAzNiIgZmlsbD0ibm9uZSIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDM2QzEyIDM2IDI0IDI0IDI0IDEyQzI0IDUuMzcyNTggMTguNjI3NCAwIDEyIDBDNS4zNzI1OCAwIDAgNS4zNzI1OCAwIDEyQzAgMjQgMTIgMzYgMTIgMzYiIGZpbGw9IiMxMEI5ODEiLz4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOCIgZmlsbD0id2hpdGUiLz4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iNCIgZmlsbD0iIzEwQjk4MSIvPgo8L3N2Zz4K';

                switch (durum) {
                    case 'sorun_var':
                        color = '#EF4444';
                        iconUrl = `data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMzYiIHZpZXdCb3g9IjAgMCAyNCAzNiIgZmlsbD0ibm9uZSIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDM2QzEyIDM2IDI0IDI0IDI0IDEyQzI0IDUuMzcyNTggMTguNjI3NCAwIDEyIDBDNS4zNzI1OCAwIDAgNS4zNzI1OCAwIDEyQzAgMjQgMTIgMzYgMTIgMzYiIGZpbGw9IiNFRjQ0NDQiLz4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOCIgZmlsbD0id2hpdGUiLz4KPHRleHQgeD0iMTIiIHk9IjE2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjEwIiBmb250LWZhbWlseT0iRm9udEF3ZXNvbWUiIGZpbGw9IiNFRjQ0NDQiPiE8L3RleHQ+Cjwvc3ZnPgo=`;
                        break;
                    case 'acil':
                        color = '#DC2626';
                        iconUrl = `data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzAiIGhlaWdodD0iNDQiIHZpZXdCb3g9IjAgMCAzMCA0NCIgZmlsbD0ibm9uZSIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTE1IDQ0QzE1IDQ0IDMwIDMwIDMwIDE1QzMwIDYuNzE1NzMgMjMuMjg0MyAwIDE1IDBDNi43MTU3MyAwIDAgNi43MTU3MyAwIDE1QzAgMzAgMTUgNDQgMTUgNDQiIGZpbGw9IiNEQzI2MjYiLz4KPGNpcmNsZSBjeD0iMTUiIGN5PSIxNSIgcj0iMTAiIGZpbGw9IndoaXRlIi8+Cjx0ZXh0IHg9IjE1IiB5PSIyMCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSIxNCIgZm9udC1mYW1pbHk9IkZvbnRBd2Vzb21lIiBmaWxsPSIjREMyNjI2Ij7wn5qoPC90ZXh0Pgo8L3N2Zz4K`;
                        break;
                    case 'gozden_gecirildi':
                        color = '#F59E0B';
                        iconUrl = `data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMzYiIHZpZXdCb3g9IjAgMCAyNCAzNiIgZmlsbD0ibm9uZSIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDM2QzEyIDM2IDI0IDI0IDI0IDEyQzI0IDUuMzcyNTggMTguNjI3NCAwIDEyIDBDNS4zNzI1OCAwIDAgNS4zNzI1OCAwIDEyQzAgMjQgMTIgMzYgMTIgMzYiIGZpbGw9IiNGNTlFMEIiLz4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOCIgZmlsbD0id2hpdGUiLz4KPHRleHQgeD0iMTIiIHk9IjE2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjgiIGZvbnQtZmFtaWx5PSJGb250QXdlc29tZSIgZmlsbD0iI0Y1OUUwQiI+8J+QgTwvdGV4dD4KPC9zdmc+Cg==`;
                        break;
                    case 'sorun_yok':
                        color = '#10B981';
                        iconUrl = `data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMzYiIHZpZXdCb3g9IjAgMCAyNCAzNiIgZmlsbD0ibm9uZSIgeG1zbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDM2QzEyIDM2IDI0IDI0IDI0IDEyQzI0IDUuMzcyNTggMTguNjI3NCAwIDEyIDBDNS4zNzI1OCAwIDAgNS4zNzI1OCAwIDEyQzAgMjQgMTIgMzYgMTIgMzYiIGZpbGw9IiMxMEI5ODEiLz4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOCIgZmlsbD0id2hpdGUiLz4KPHRleHQgeD0iMTIiIHk9IjE2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjgiIGZvbnQtZmFtaWx5PSJGb250QXdlc29tZSIgZmlsbD0iIzEwQjk4MSI+4pyTPC90ZXh0Pgo8L3N2Zz4K`;
                        break;
                }

                return new ol.style.Style({
                    image: new ol.style.Icon({
                        src: iconUrl,
                        scale: 1,
                        anchor: [0.5, 1],
                        anchorXUnits: 'fraction',
                        anchorYUnits: 'fraction'
                    })
                });
            },
            zIndex: 15
        });

        istakipLayers.gunlukKontroller = kontrolLayer;
        map.addLayer(kontrolLayer);

        // Görünürlük durumunu checkbox'a göre ayarla
        const isVisible = document.getElementById('kontrollerToggle').checked;
        kontrolLayer.setVisible(isVisible);

        console.log(`${data.features.length} kontrol yüklendi`);
    } catch (error) {
        console.error('Günlük kontroller yüklenirken hata:', error);
    }
}

// Harita tıklama işleyici
function handleMapClick(evt) {
    const features = map.getFeaturesAtPixel(evt.pixel);

    if (features.length > 0) {
        const feature = features[0];
        const layer = map.getLayers().getArray().find(l =>
            l.getSource && l.getSource().getFeatures &&
            l.getSource().getFeatures().includes(feature)
        );

        // Görev tıklandıysa popup göster
        if (layer === istakipLayers.gorevler) {
            showGorevPopup(feature, evt.coordinate);
            return;
        }

        // Kontrol tıklandıysa popup göster
        if (layer === istakipLayers.gunlukKontroller) {
            showKontrolPopup(feature, evt.coordinate);
            return;
        }

        // Park tıklandıysa modal aç
        if (layer === layers.parklar) {
            const parkUuid = feature.get('uuid');
            if (parkUuid) {
                showParkDetails(parkUuid);
            }
        }

        // Mahalle tıklandıysa modal aç
        if (layer === layers.mahalleler) {
            showMahalleDetails(feature);
        }
    }
}

// Görev popup'ını göster
function showGorevPopup(feature, coordinate) {
    const content = `
        <div class="bg-white rounded-xl shadow-2xl border border-gray-200 w-80 max-w-sm overflow-hidden">
            <!-- Header -->
            <div class="p-4 bg-gradient-to-r from-emerald-500 to-green-600 text-white">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <h3 class="text-lg font-bold truncate mb-1">${feature.get('baslik')}</h3>
                        <p class="text-emerald-100 text-sm opacity-90">
                            <i class="fas fa-clipboard-list mr-1"></i>Görev Detayları
                        </p>
                    </div>
                    <button onclick="closeMapPopup()" class="ml-2 p-1 rounded-full hover:bg-white/20 transition-colors">
                        <i class="fas fa-times text-sm"></i>
                    </button>
                </div>
            </div>
            
            <!-- Content -->
            <div class="p-4 space-y-3">
                <!-- Durum Badge -->
                <div class="flex items-center justify-center">
                    <span class="px-3 py-1.5 text-sm font-semibold rounded-full ${getDurumBadgeClass(feature.get('durum'))}">
                        ${getDurumIcon(feature.get('durum'))} ${feature.get('durum_display')}
                    </span>
                </div>
                
                <!-- Bilgiler Grid -->
                <div class="space-y-2">
                    <div class="flex items-center p-2 bg-gray-50 rounded-lg">
                        <div class="w-8 h-8 bg-park-green-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-map-marker-alt text-park-green-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-gray-500 uppercase tracking-wide">Park</p>
                            <p class="text-sm font-medium text-gray-900 truncate">${feature.get('park_ad')}</p>
                        </div>
                    </div>
                    
                    ${feature.get('gorev_tipi_ad') ? `
                    <div class="flex items-center p-2 bg-gray-50 rounded-lg">
                        <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-tag text-purple-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-gray-500 uppercase tracking-wide">Kategori</p>
                            <p class="text-sm font-medium text-gray-900 truncate">${feature.get('gorev_tipi_ad')}</p>
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="flex items-center p-2 bg-gray-50 rounded-lg">
                        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-calendar text-blue-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-gray-500 uppercase tracking-wide">Başlangıç</p>
                            <p class="text-sm font-medium text-gray-900">${new Date(feature.get('baslangic_tarihi')).toLocaleDateString('tr-TR', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    })}</p>
                        </div>
                    </div>
                    
                    ${feature.get('oncelik') !== 'normal' ? `
                    <div class="flex items-center p-2 bg-orange-50 border border-orange-200 rounded-lg">
                        <div class="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-exclamation-triangle text-orange-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-orange-500 uppercase tracking-wide">Öncelik</p>
                            <p class="text-sm font-bold text-orange-700">${feature.get('oncelik_display')}</p>
                        </div>
                    </div>
                    ` : ''}
                    
                    ${feature.get('atanan_personeller') && feature.get('atanan_personeller').length > 0 ? `
                    <div class="flex items-center p-2 bg-indigo-50 border border-indigo-200 rounded-lg">
                        <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-users text-indigo-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-indigo-500 uppercase tracking-wide">Atanan</p>
                            <p class="text-sm font-medium text-indigo-700 truncate">
                                ${feature.get('atanan_personeller').map(p => p.ad).slice(0, 2).join(', ')}
                                ${feature.get('atanan_personeller').length > 2 ? ` +${feature.get('atanan_personeller').length - 2}` : ''}
                            </p>
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Footer -->
            <div class="p-4 bg-gray-50 border-t border-gray-200 flex gap-2">
                <a href="/istakip/gorevler/${feature.get('uuid')}/" 
                   class="flex-1 inline-flex items-center justify-center px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-sm hover:shadow-md">
                    <i class="fas fa-eye mr-2"></i>Detayları Gör
                </a>
                <button onclick="closeMapPopup()" 
                        class="px-3 py-2.5 text-gray-600 hover:text-gray-800 border border-gray-300 hover:border-gray-400 rounded-lg transition-colors">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;

    showMapPopup(content, coordinate);
}

// Kontrol popup'ını göster
function showKontrolPopup(feature, coordinate) {
    const content = `
        <div class="bg-white rounded-xl shadow-2xl border border-gray-200 w-80 max-w-sm overflow-hidden">
            <!-- Header -->
            <div class="p-4 bg-gradient-to-r from-red-500 to-orange-600 text-white">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <h3 class="text-lg font-bold mb-1">Sorun Bildirimi</h3>
                        <p class="text-red-100 text-sm opacity-90">
                            <i class="fas fa-exclamation-triangle mr-1"></i>Kontrol Raporu
                        </p>
                    </div>
                    <button onclick="closeMapPopup()" class="ml-2 p-1 rounded-full hover:bg-white/20 transition-colors">
                        <i class="fas fa-times text-sm"></i>
                    </button>
                </div>
            </div>
            
            <!-- Content -->
            <div class="p-4 space-y-3">
                <!-- Durum Badge -->
                <div class="flex items-center justify-center">
                    <span class="px-3 py-1.5 text-sm font-semibold rounded-full ${getKontrolBadgeClass(feature.get('durum'))}">
                        ${getKontrolIcon(feature.get('durum'))} ${feature.get('durum_display')}
                    </span>
                </div>
                
                <!-- Bilgiler Grid -->
                <div class="space-y-2">
                    <div class="flex items-center p-2 bg-gray-50 rounded-lg">
                        <div class="w-8 h-8 bg-park-green-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-map-marker-alt text-park-green-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-gray-500 uppercase tracking-wide">Lokasyon</p>
                            <p class="text-sm font-medium text-gray-900 truncate">${feature.get('park_ad')}</p>
                        </div>
                    </div>
                    
                    <div class="flex items-center p-2 bg-gray-50 rounded-lg">
                        <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-user text-blue-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-gray-500 uppercase tracking-wide">Bildiren</p>
                            <p class="text-sm font-medium text-gray-900 truncate">${feature.get('personel_ad')}</p>
                        </div>
                    </div>
                    
                    <div class="flex items-center p-2 bg-gray-50 rounded-lg">
                        <div class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-clock text-purple-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-gray-500 uppercase tracking-wide">Tarih</p>
                            <p class="text-sm font-medium text-gray-900">${new Date(feature.get('kontrol_tarihi')).toLocaleDateString('tr-TR', {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit'
    })}</p>
                        </div>
                    </div>
                    
                    <div class="flex items-center p-2 bg-gray-50 rounded-lg">
                        <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center mr-3">
                            <i class="fas fa-list text-indigo-600 text-sm"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-xs text-gray-500 uppercase tracking-wide">Tip</p>
                            <p class="text-sm font-medium text-gray-900 truncate">${feature.get('kontrol_tipi_display')}</p>
                        </div>
                    </div>
                </div>
                
                ${feature.get('aciklama') ? `
                <!-- Açıklama -->
                <div class="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <p class="text-xs text-amber-600 uppercase tracking-wide mb-1">Açıklama</p>
                    <p class="text-sm text-gray-800 leading-relaxed">${feature.get('aciklama').length > 120 ?
                feature.get('aciklama').substring(0, 120) + '...' :
                feature.get('aciklama')}</p>
                </div>
                ` : ''}
            </div>
            
            <!-- Footer -->
            <div class="p-4 bg-gray-50 border-t border-gray-200 flex gap-2">
                <a href="/istakip/sorun/${feature.get('uuid')}/detay/" 
                   class="flex-1 inline-flex items-center justify-center px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-all duration-200 shadow-sm hover:shadow-md">
                    <i class="fas fa-eye mr-2"></i>Detayları Gör
                </a>
                <button onclick="closeMapPopup()" 
                        class="px-3 py-2.5 text-gray-600 hover:text-gray-800 border border-gray-300 hover:border-gray-400 rounded-lg transition-colors">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;

    showMapPopup(content, coordinate);
}

// Popup göster
function showMapPopup(content, coordinate) {
    // Mevcut popup'ı kaldır
    const existingPopup = document.getElementById('mapPopup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Yeni popup oluştur
    const popup = document.createElement('div');
    popup.id = 'mapPopup';
    popup.innerHTML = content;
    popup.style.position = 'absolute';
    popup.style.zIndex = '1000';
    popup.style.pointerEvents = 'auto';

    // Koordinatları pixel pozisyonuna çevir
    const pixel = map.getPixelFromCoordinate(coordinate);
    popup.style.left = (pixel[0] + 10) + 'px';
    popup.style.top = (pixel[1] - 10) + 'px';

    // Popup'ı haritaya ekle
    document.getElementById('map').appendChild(popup);

    // 5 saniye sonra otomatik kapat
    setTimeout(() => {
        if (document.getElementById('mapPopup')) {
            document.getElementById('mapPopup').remove();
        }
    }, 5000);

    // Tıklama ile kapat
    popup.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    map.once('click', () => {
        if (document.getElementById('mapPopup')) {
            document.getElementById('mapPopup').remove();
        }
    });
}

// Badge class fonksiyonları
function getDurumBadgeClass(durum) {
    switch (durum) {
        case 'planlanmis':
            return 'bg-gray-100 text-gray-800';
        case 'devam_ediyor':
            return 'bg-amber-100 text-amber-800';
        case 'onaya_gonderildi':
            return 'bg-purple-100 text-purple-800';
        case 'tamamlandi':
            return 'bg-green-100 text-green-800';
        case 'iptal':
            return 'bg-red-100 text-red-800';
        case 'gecikmis':
            return 'bg-orange-100 text-orange-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

function getKontrolBadgeClass(durum) {
    switch (durum) {
        case 'sorun_var':
            return 'bg-red-100 text-red-800';
        case 'acil':
            return 'bg-red-200 text-red-900';
        case 'gozden_gecirildi':
            return 'bg-orange-100 text-orange-800';
        case 'ise_donusturuldu':
            return 'bg-purple-100 text-purple-800';
        case 'sorun_yok':
            return 'bg-green-100 text-green-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

function getDurumIcon(durum) {
    switch (durum) {
        case 'planlanmis':
            return '<i class="fas fa-clock"></i>';
        case 'devam_ediyor':
            return '<i class="fas fa-play"></i>';
        case 'onaya_gonderildi':
            return '<i class="fas fa-hourglass-half"></i>';
        case 'tamamlandi':
            return '<i class="fas fa-check"></i>';
        case 'iptal':
            return '<i class="fas fa-times"></i>';
        case 'gecikmis':
            return '<i class="fas fa-exclamation-triangle"></i>';
        default:
            return '<i class="fas fa-question"></i>';
    }
}

function getKontrolIcon(durum) {
    switch (durum) {
        case 'sorun_var':
            return '<i class="fas fa-exclamation-triangle"></i>';
        case 'acil':
            return '<i class="fas fa-fire"></i>';
        case 'gozden_gecirildi':
            return '<i class="fas fa-eye"></i>';
        case 'ise_donusturuldu':
            return '<i class="fas fa-cogs"></i>';
        case 'sorun_yok':
            return '<i class="fas fa-check"></i>';
        default:
            return '<i class="fas fa-question"></i>';
    }
}

// Popup kapatma fonksiyonu
function closeMapPopup() {
    const popup = document.getElementById('mapPopup');
    if (popup) {
        popup.remove();
    }
}

// Park detaylarını göster
async function showParkDetails(uuid) {
    try {
        // Önce mahalle modal'ını kapat
        const mahalleModal = document.getElementById('mahalleModal');
        mahalleModal.classList.add('hidden');

        // CSS transition'ının tamamlanması için bekle
        await new Promise(resolve => setTimeout(resolve, 350));

        const response = await fetch(`/parkbahce/htmx/park-detail/${uuid}/`, {
            headers: {
                'HX-Request': 'true'
            }
        });

        if (response.ok) {
            const content = await response.text();
            document.getElementById('parkModalTitle').textContent = 'Park Detayları';
            document.getElementById('parkModalContent').innerHTML = content;

            // Park modal'ını aç
            const parkModal = document.getElementById('parkModal');
            parkModal.style.zIndex = '999';
            parkModal.classList.remove('hidden');
        } else {
            console.error('Park detayları yüklenemedi');
        }
    } catch (error) {
        console.error('Park detayları yüklenirken hata:', error);
    }
}

// Mahalle detaylarını göster
async function showMahalleDetails(feature) {
    try {
        const mahalleUuid = feature.get('uuid');
        if (!mahalleUuid) {
            console.error('Mahalle UUID bulunamadı');
            return;
        }

        const response = await fetch(`/parkbahce/htmx/mahalle-detail/${mahalleUuid}/`, {
            headers: {
                'HX-Request': 'true'
            }
        });

        if (response.ok) {
            const content = await response.text();
            document.getElementById('mahalleModalTitle').textContent = 'Mahalle Detayları';
            document.getElementById('mahalleModalContent').innerHTML = content;
            document.getElementById('mahalleModal').classList.remove('hidden');
        } else {
            console.error('Mahalle detayları yüklenemedi:', response.status);
        }
    } catch (error) {
        console.error('Mahalle detayları yüklenirken hata:', error);
    }
}

// Park'a yakınlaş
function zoomToPark(parkUuid) {
    const parkLayer = layers.parklar;
    if (parkLayer) {
        const features = parkLayer.getSource().getFeatures();
        const parkFeature = features.find(f => f.get('uuid') === parkUuid);
        if (parkFeature) {
            const extent = parkFeature.getGeometry().getExtent();
            map.getView().fit(extent, {
                padding: [50, 50, 50, 50],
                maxZoom: 18,
                duration: 1000
            });
        }
    }
    document.getElementById('parkModal').classList.add('hidden');
}

// Mahalle'ye yakınlaş
function zoomToMahalle(mahalleUuid) {
    const mahalleLayer = layers.mahalleler;
    if (mahalleLayer) {
        const features = mahalleLayer.getSource().getFeatures();
        const mahalleFeature = features.find(f => f.get('uuid') === mahalleUuid);
        if (mahalleFeature) {
            const extent = mahalleFeature.getGeometry().getExtent();
            map.getView().fit(extent, {
                padding: [50, 50, 50, 50],
                maxZoom: 16,
                duration: 1000
            });
        }
    }
    document.getElementById('mahalleModal').classList.add('hidden');
}

// Drawer işlevleri
function toggleDrawer() {
    const drawer = document.getElementById('layerDrawer');
    drawer.classList.toggle('open');
}

// Event listener'lar
document.addEventListener('DOMContentLoaded', function () {
    initMap();

    // Drawer toggle
    const drawerToggle = document.getElementById('drawerToggle');
    const drawerClose = document.getElementById('drawerClose');

    if (drawerToggle) {
        drawerToggle.addEventListener('click', toggleDrawer);
    }
    if (drawerClose) {
        drawerClose.addEventListener('click', toggleDrawer);
    }

    // Modal kapatma
    const parkModalClose = document.getElementById('parkModalClose');
    const parkModalOverlay = document.getElementById('parkModalOverlay');
    const mahalleModalClose = document.getElementById('mahalleModalClose');
    const mahalleModalOverlay = document.getElementById('mahalleModalOverlay');

    if (parkModalClose) {
        parkModalClose.addEventListener('click', () => {
            document.getElementById('parkModal').classList.add('hidden');
        });
    }
    if (parkModalOverlay) {
        parkModalOverlay.addEventListener('click', () => {
            document.getElementById('parkModal').classList.add('hidden');
        });
    }

    if (mahalleModalClose) {
        mahalleModalClose.addEventListener('click', () => {
            document.getElementById('mahalleModal').classList.add('hidden');
        });
    }
    if (mahalleModalOverlay) {
        mahalleModalOverlay.addEventListener('click', () => {
            document.getElementById('mahalleModal').classList.add('hidden');
        });
    }

    // Katman checkbox'ları - sadece temel katmanlar için
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        if (checkbox.id === 'mahalleler-toggle' || checkbox.id === 'parklar-toggle') {
            checkbox.addEventListener('change', function () {
                const layerName = this.id.replace('-toggle', '');
                const layer = layers[layerName];

                if (layer) {
                    layer.setVisible(this.checked);
                }
            });
        }
    });

    // İstakip katman toggle'ları
    const gorevlerToggle = document.getElementById('gorevlerToggle');
    const kontrollerToggle = document.getElementById('kontrollerToggle');

    if (gorevlerToggle) {
        gorevlerToggle.addEventListener('change', function () {
            toggleIstakipLayer('gorevler', this.checked);
        });
    }

    if (kontrollerToggle) {
        kontrollerToggle.addEventListener('change', function () {
            toggleIstakipLayer('kontroller', this.checked);
        });
    }

    // Filter butonları
    const applyFiltersBtn = document.getElementById('applyFilters');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const toggleFiltersBtn = document.getElementById('toggleFilters');

    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', applyFilters);
    }

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearFilters);
    }

    if (toggleFiltersBtn) {
        toggleFiltersBtn.addEventListener('click', toggleFilterForm);
    }
});

// Tarih aralığını hesapla
function getDateRange(period) {
    const today = new Date();
    let start = null;
    let end = null;

    switch (period) {
        case 'bugun':
            start = today.toISOString().split('T')[0];
            end = start;
            break;
        case 'bu_hafta':
            const weekStart = new Date(today);
            weekStart.setDate(today.getDate() - today.getDay());
            start = weekStart.toISOString().split('T')[0];

            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekStart.getDate() + 6);
            end = weekEnd.toISOString().split('T')[0];
            break;
        case 'bu_ay':
            start = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
            end = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];
            break;
    }

    return { start, end };
}

// Filtreleri uygula
async function applyFilters() {
    const gorevFilters = {
        durum: document.getElementById('gorevDurum').value,
        oncelik: document.getElementById('gorevOncelik').value,
        tarih: document.getElementById('gorevTarih').value
    };

    const kontrolFilters = {
        durum: document.getElementById('kontrolDurum').value,
        tarih: document.getElementById('kontrolTarih').value
    };

    // Yükleme göstergesi
    const applyBtn = document.getElementById('applyFilters');
    const originalText = applyBtn.innerHTML;
    applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Yükleniyor...';
    applyBtn.disabled = true;

    try {
        // Katmanları güncelle
        if (document.getElementById('gorevlerToggle').checked) {
            await loadGorevler(gorevFilters);
        }

        if (document.getElementById('kontrollerToggle').checked) {
            await loadGunlukKontroller(kontrolFilters);
        }

        // İstatistikleri güncelle
        updateFilterStats();

    } catch (error) {
        console.error('Filtreler uygulanırken hata:', error);
    } finally {
        // Yükleme göstergesini kaldır
        applyBtn.innerHTML = originalText;
        applyBtn.disabled = false;
    }
}

// Filtreleri temizle
async function clearFilters() {
    // Form alanlarını temizle
    document.getElementById('gorevDurum').value = '';
    document.getElementById('gorevOncelik').value = '';
    document.getElementById('gorevTarih').value = '';
    document.getElementById('kontrolDurum').value = '';
    document.getElementById('kontrolTarih').value = '';

    // Varsayılan filtreleri uygula
    await loadGorevler(defaultFilters.gorevler);
    await loadGunlukKontroller(defaultFilters.kontroller);

    updateFilterStats();
}

// İstatistikleri güncelle
function updateFilterStats() {
    const gorevCount = istakipLayers.gorevler ?
        istakipLayers.gorevler.getSource().getFeatures().length : 0;
    const kontrolCount = istakipLayers.gunlukKontroller ?
        istakipLayers.gunlukKontroller.getSource().getFeatures().length : 0;

    document.getElementById('gorevCount').textContent = gorevCount;
    document.getElementById('kontrolCount').textContent = kontrolCount;
}

// Toggle filter form
function toggleFilterForm() {
    const filterForm = document.getElementById('filterForm');
    const toggleBtn = document.getElementById('toggleFilters');
    const icon = toggleBtn.querySelector('i');

    if (filterForm.style.display === 'none') {
        filterForm.style.display = 'block';
        icon.className = 'fas fa-chevron-up text-sm';
    } else {
        filterForm.style.display = 'none';
        icon.className = 'fas fa-chevron-down text-sm';
    }
}

// Katman görünürlüğünü değiştir
function toggleIstakipLayer(layerType, isVisible) {
    if (layerType === 'gorevler' && istakipLayers.gorevler) {
        istakipLayers.gorevler.setVisible(isVisible);
    } else if (layerType === 'kontroller' && istakipLayers.gunlukKontroller) {
        istakipLayers.gunlukKontroller.setVisible(isVisible);
    }
}

// Test fonksiyonu - Manual marker ekleme
function addTestMarkers() {
    console.log('🧪 Test marker\'ları ekleniyor...');

    // Test koordinatları (Sivas merkez)
    const testCoordinates = [
        [37.0167, 39.7500], // Sivas merkez
        [37.0200, 39.7530], // Biraz doğuda
        [37.0130, 39.7470]  // Biraz batıda
    ];

    const testFeatures = testCoordinates.map((coord, index) => {
        const feature = new ol.Feature({
            geometry: new ol.geom.Point(ol.proj.fromLonLat(coord))
        });
        feature.set('uuid', `test-${index}`);
        feature.set('durum', 'sorun_var');
        feature.set('park_ad', `Test Park ${index + 1}`);
        return feature;
    });

    const testSource = new ol.source.Vector({
        features: testFeatures
    });

    const testLayer = new ol.layer.Vector({
        source: testSource,
        style: new ol.style.Style({
            image: new ol.style.Circle({
                radius: 12,
                fill: new ol.style.Fill({
                    color: '#FF0000'
                }),
                stroke: new ol.style.Stroke({
                    color: '#FFFFFF',
                    width: 3
                })
            })
        }),
        zIndex: 200
    });

    map.addLayer(testLayer);
    console.log('✅ Test marker\'ları eklendi');

    // Test marker'larına zoom yap
    map.getView().fit(testSource.getExtent(), {
        padding: [50, 50, 50, 50],
        maxZoom: 14,
        duration: 1000
    });
}

// Global test fonksiyonu
window.addTestMarkers = addTestMarkers;