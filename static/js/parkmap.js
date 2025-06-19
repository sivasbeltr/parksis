// Park Harita JavaScript Modülü
// Sivas Belediyesi Park ve Bahçeler Müdürlüğü

// Choices.py'dan gelen renk tanımlamaları
const ISTAKIP_COLORS = {
    GOREV_DURUM: {
        "planlanmis": "#F59E0B",
        "devam_ediyor": "#F59E0B",
        "onaya_gonderildi": "#8B5CF6",
        "tamamlandi": "#10B981",
        "iptal": "#EF4444",
        "gecikmis": "#F97316"
    },
    GOREV_ONCELIK: {
        "dusuk": "#6B7280",
        "normal": "#3B82F6",
        "yuksek": "#F59E0B",
        "acil": "#EF4444"
    },
    KONTROL_DURUM: {
        "sorun_yok": "#10B981",
        "sorun_var": "#EF4444",
        "acil": "#DC2626",
        "gozden_gecirildi": "#F59E0B",
        "ise_donusturuldu": "#8B5CF6",
        "cozuldu": "#10B981"
    },
    GOREV_ASAMA_DURUM: {
        "beklemede": "#F59E0B",
        "baslamadi": "#6B7280",
        "devam_ediyor": "#3B82F6",
        "tamamlandi": "#10B981"
    }
};

// Harita ve katman değişkenleri
let map;
let layers = {};
let currentZoom = 10;
let istakipLayers = {};

// Sivas Merkez koordinatları (EPSG:4326)
const sivasCenter = [37.0167, 39.7500];

// Harita başlangıç zoom seviyesi
const initialZoom = 12;

// Varsayılan filtreler (tüm seçenekleri kapsayacak şekilde)
const defaultFilters = {
    gorevler: {
        durum: 'planlanmis,devam_ediyor,onaya_gonderildi,gecikmis,tamamlandi,iptal',
        oncelik: 'acil,yuksek,normal,dusuk',
        tarih: ''
    },
    kontroller: {
        durum: 'sorun_yok,sorun_var,acil,gozden_gecirildi,ise_donusturuldu,cozuldu',
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
        console.log('Varsayılan filtreler yükleniyor:', defaultFilters);
        await loadGorevler(defaultFilters.gorevler);
        await loadGunlukKontroller(defaultFilters.kontroller);

        // İstatistikleri güncelle
        updateFilterStats();
    } catch (error) {
        console.error('İstakip katmanları yüklenirken hata:', error);
    }
}

// Leaflet benzeri SVG marker (sorun bildirimleri için)
function leafletMarkerStyle(color = '#10B981') {
    return new ol.style.Style({
        image: new ol.style.Icon({
            src: `data:image/svg+xml;utf8,<svg width='32' height='48' viewBox='0 0 32 48' fill='none' xmlns='http://www.w3.org/2000/svg'><g filter='url(%23a)'><path d='M16 47c7-10 15-18 15-29A15 15 0 0 0 1 18c0 11 8 19 15 29Z' fill='${encodeURIComponent(color)}'/><circle cx='16' cy='18' r='6' fill='white'/></g><defs><filter id='a' x='0' y='0' width='32' height='48' filterUnits='userSpaceOnUse' color-interpolation-filters='sRGB'><feDropShadow dx='0' dy='2' stdDeviation='2' flood-color='%23000000' flood-opacity='0.3'/></filter></defs></svg>`,
            anchor: [0.5, 1],
            scale: 1
        })
    });
}

// Duruma göre renk döndüren yardımcı fonksiyonlar
function getGorevColor(durum) {
    return ISTAKIP_COLORS.GOREV_DURUM[durum] + '40'; // 40 = %25 opacity için hex
}

function getGorevMainColor(durum) {
    return ISTAKIP_COLORS.GOREV_DURUM[durum] || ISTAKIP_COLORS.GOREV_DURUM.planlanmis;
}

function getKontrolColor(durum) {
    return ISTAKIP_COLORS.KONTROL_DURUM[durum] + '40'; // 40 = %25 opacity için hex
}

function getKontrolMainColor(durum) {
    return ISTAKIP_COLORS.KONTROL_DURUM[durum] || ISTAKIP_COLORS.KONTROL_DURUM.sorun_yok;
}

// Yeni estetik görev marker
function gorevMarkerStyle(durum) {
    const color = getGorevMainColor(durum);
    return new ol.style.Style({
        image: new ol.style.Icon({
            src: `data:image/svg+xml;utf8,<svg width='40' height='40' viewBox='0 0 40 40' fill='none' xmlns='http://www.w3.org/2000/svg'><g filter='url(%23shadow)'><circle cx='20' cy='20' r='18' fill='white'/><circle cx='20' cy='20' r='14' fill='${encodeURIComponent(color)}'/><circle cx='20' cy='20' r='10' fill='white'/><circle cx='20' cy='20' r='6' fill='${encodeURIComponent(color)}'/></g><defs><filter id='shadow' x='0' y='0' width='40' height='40' filterUnits='userSpaceOnUse' color-interpolation-filters='sRGB'><feDropShadow dx='0' dy='2' stdDeviation='2' flood-color='%23000000' flood-opacity='0.3'/></filter></defs></svg>`,
            anchor: [0.5, 0.5],
            scale: 1
        })
    });
}

// Görevler katmanını yükle
async function loadGorevler(filters = {}) {
    try {
        if (istakipLayers.gorevler) {
            map.removeLayer(istakipLayers.gorevler);
            istakipLayers.gorevler = null;
        }
        const params = new URLSearchParams();
        if (filters.durum) params.append('durum', filters.durum);
        if (filters.oncelik) params.append('oncelik', filters.oncelik);
        if (filters.tarih) {
            const dateRange = getDateRange(filters.tarih);
            if (dateRange.start) params.append('tarih_baslangic', dateRange.start);
            if (dateRange.end) params.append('tarih_bitis', dateRange.end);
        }
        console.log('Görevler için URL:', `/api/v1/gorev-listesi/?${params.toString()}`);
        const response = await fetch(`/api/v1/gorev-listesi/?${params.toString()}`);
        const data = await response.json();
        const features = [];
        (data.features || []).forEach(f => {
            let geom = f.geometry;
            if (geom && (geom.type === 'Polygon' || geom.type === 'MultiPolygon')) {
                let coords = geom.type === 'Polygon' ? geom.coordinates[0] : geom.coordinates[0][0];
                let x = 0, y = 0;
                coords.forEach(c => { x += c[0]; y += c[1]; });
                x /= coords.length; y /= coords.length;
                const point = new ol.geom.Point(ol.proj.fromLonLat([x, y]));
                const feature = new ol.Feature({ geometry: point });
                Object.entries(f.properties).forEach(([k, v]) => feature.set(k, v));
                features.push(feature);
            } else if (geom && geom.type === 'Point') {
                const point = new ol.geom.Point(ol.proj.fromLonLat(geom.coordinates));
                const feature = new ol.Feature({ geometry: point });
                Object.entries(f.properties).forEach(([k, v]) => feature.set(k, v));
                features.push(feature);
            }
        });
        const vectorSource = new ol.source.Vector({ features });
        const gorevLayer = new ol.layer.Vector({
            source: vectorSource,
            style: function (feature) {
                return gorevMarkerStyle(feature.get('durum'));
            },
            zIndex: 20
        });
        istakipLayers.gorevler = gorevLayer;
        map.addLayer(gorevLayer);
        const isVisible = document.getElementById('gorevlerToggle').checked;
        gorevLayer.setVisible(isVisible);
        console.log(`${features.length} görev marker'ı yüklendi`, { filters });
    } catch (error) {
        console.error('Görevler yüklenirken hata:', error);
    }
}

// Sorun bildirimleri katmanını yükle
async function loadGunlukKontroller(filters = {}) {
    try {
        if (istakipLayers.gunlukKontroller) {
            map.removeLayer(istakipLayers.gunlukKontroller);
            istakipLayers.gunlukKontroller = null;
        }
        const params = new URLSearchParams();
        if (filters.durum) params.append('durum', filters.durum);
        if (filters.tarih) {
            const dateRange = getDateRange(filters.tarih);
            if (dateRange.start) params.append('tarih_baslangic', dateRange.start);
            if (dateRange.end) params.append('tarih_bitis', dateRange.end);
        }
        console.log('Kontroller için URL:', `/api/v1/kontrol-listesi/?${params.toString()}`);
        const response = await fetch(`/api/v1/kontrol-listesi/?${params.toString()}`);
        const data = await response.json();
        const features = (data.features || []).map(f => {
            if (f.geometry && f.geometry.type === 'Point') {
                const point = new ol.geom.Point(ol.proj.fromLonLat(f.geometry.coordinates));
                const feature = new ol.Feature({ geometry: point });
                Object.entries(f.properties).forEach(([k, v]) => feature.set(k, v));
                return feature;
            }
            return null;
        }).filter(Boolean);
        const vectorSource = new ol.source.Vector({ features });
        const kontrolLayer = new ol.layer.Vector({
            source: vectorSource,
            style: function (feature) {
                const durum = feature.get('durum');
                const color = getKontrolMainColor(durum);
                return leafletMarkerStyle(color);
            },
            zIndex: 30
        });
        istakipLayers.gunlukKontroller = kontrolLayer;
        map.addLayer(kontrolLayer);
        const isVisible = document.getElementById('kontrollerToggle').checked;
        kontrolLayer.setVisible(isVisible);
        console.log(`${features.length} sorun bildirimi marker'ı yüklendi`, { filters });
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
        if (layer === istakipLayers.gorevler) {
            showGorevPopup(feature, evt.coordinate);
            return;
        }
        if (layer === istakipLayers.gunlukKontroller) {
            showKontrolPopup(feature, evt.coordinate);
            return;
        }
        if (layer === layers.parklar) {
            const parkUuid = feature.get('uuid');
            if (parkUuid) {
                showParkDetails(parkUuid);
            }
        }
        if (layer === layers.mahalleler) {
            showMahalleDetails(feature);
        }
    }
}

// Görev popup'ını göster
function showGorevPopup(feature, coordinate) {
    const durum = feature.get('durum');
    const headerBg = getGorevMainColor(durum);
    const headerStyle = `background: linear-gradient(90deg, ${headerBg} 0%, #10B981 100%);`;
    const content = `
        <div class="bg-white rounded-xl shadow-2xl border border-gray-200 w-80 max-w-sm overflow-hidden">
            <div class="p-4 text-white" style="${headerStyle}">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <h3 class="text-lg font-bold truncate mb-1">${feature.get('baslik')}</h3>
                        <p class="opacity-90 text-sm">
                            <i class="fas fa-clipboard-list mr-1"></i>Görev Detayları
                        </p>
                    </div>
                    <button onclick="closeMapPopup()" class="ml-2 p-1 rounded-full hover:bg-white/20 transition-colors">
                        <i class="fas fa-times text-sm"></i>
                    </button>
                </div>
            </div>
            <div class="p-4 space-y-3">
                <div class="flex items-center justify-center">
                    <span class="px-3 py-1.5 text-sm font-semibold rounded-full ${getDurumBadgeClass(feature.get('durum'))}">
                        ${getDurumIcon(feature.get('durum'))} ${feature.get('durum_display')}
                    </span>
                </div>
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
    const durum = feature.get('durum');
    const headerBg = getKontrolMainColor(durum);
    const headerStyle = `background: linear-gradient(90deg, ${headerBg} 0%, #F59E0B 100%);`;
    const content = `
        <div class="bg-white rounded-xl shadow-2xl border border-gray-200 w-80 max-w-sm overflow-hidden">
            <div class="p-4 text-white" style="${headerStyle}">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <h3 class="text-lg font-bold mb-1">Sorun Bildirimi</h3>
                        <p class="opacity-90 text-sm">
                            <i class="fas fa-exclamation-triangle mr-1"></i>Kontrol Raporu
                        </p>
                    </div>
                    <button onclick="closeMapPopup()" class="ml-2 p-1 rounded-full hover:bg-white/20 transition-colors">
                        <i class="fas fa-times text-sm"></i>
                    </button>
                </div>
            </div>
            <div class="p-4 space-y-3">
                <div class="flex items-center justify-center">
                    <span class="px-3 py-1.5 text-sm font-semibold rounded-full ${getKontrolBadgeClass(feature.get('durum'))}">
                        ${getKontrolIcon(feature.get('durum'))} ${feature.get('durum_display')}
                    </span>
                </div>
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
                <div class="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <p class="text-xs text-amber-600 uppercase tracking-wide mb-1">Açıklama</p>
                    <p class="text-sm text-gray-800 leading-relaxed">${feature.get('aciklama').length > 120 ?
                feature.get('aciklama').substring(0, 120) + '...' :
                feature.get('aciklama')}</p>
                </div>
                ` : ''}
            </div>
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
    const existingPopup = document.getElementById('mapPopup');
    if (existingPopup) {
        existingPopup.remove();
    }
    const popup = document.createElement('div');
    popup.id = 'mapPopup';
    popup.innerHTML = content;
    popup.style.position = 'absolute';
    popup.style.zIndex = '1000';
    popup.style.pointerEvents = 'auto';
    const pixel = map.getPixelFromCoordinate(coordinate);
    popup.style.left = (pixel[0] + 10) + 'px';
    popup.style.top = (pixel[1] - 10) + 'px';
    document.getElementById('map').appendChild(popup);
    setTimeout(() => {
        if (document.getElementById('mapPopup')) {
            document.getElementById('mapPopup').remove();
        }
    }, 5000);
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
            return 'bg-yellow-100 text-yellow-800';
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
        const mahalleModal = document.getElementById('mahalleModal');
        mahalleModal.classList.add('hidden');
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
    console.log('DOM yüklendi, form değerleri ayarlanıyor...');
    setDefaultFormValues();
    initMap();
    const drawerToggle = document.getElementById('drawerToggle');
    const drawerClose = document.getElementById('drawerClose');
    if (drawerToggle) {
        drawerToggle.addEventListener('click', toggleDrawer);
    }
    if (drawerClose) {
        drawerClose.addEventListener('click', toggleDrawer);
    }
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
    const gorevDurumOptions = Array.from(document.getElementById('gorevDurum').selectedOptions).map(opt => opt.value);
    const gorevOncelikOptions = Array.from(document.getElementById('gorevOncelik').selectedOptions).map(opt => opt.value);
    const kontrolDurumOptions = Array.from(document.getElementById('kontrolDurum').selectedOptions).map(opt => opt.value);
    const gorevFilters = {
        durum: gorevDurumOptions.join(','),
        oncelik: gorevOncelikOptions.join(','),
        tarih: document.getElementById('gorevTarih').value
    };
    const kontrolFilters = {
        durum: kontrolDurumOptions.join(','),
        tarih: document.getElementById('kontrolTarih').value
    };
    console.log('Filtreleme işlemi başladı:', {
        gorev: gorevFilters,
        kontrol: kontrolFilters
    });
    const applyBtn = document.getElementById('applyFilters');
    const originalText = applyBtn.innerHTML;
    applyBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Yükleniyor...';
    applyBtn.disabled = true;
    try {
        if (document.getElementById('gorevlerToggle').checked) {
            console.log('Görevler filtreleniyor:', gorevFilters);
            await loadGorevler(gorevFilters);
        } else {
            if (istakipLayers.gorevler) {
                map.removeLayer(istakipLayers.gorevler);
                istakipLayers.gorevler = null;
            }
        }
        if (document.getElementById('kontrollerToggle').checked) {
            console.log('Kontroller filtreleniyor:', kontrolFilters);
            await loadGunlukKontroller(kontrolFilters);
        } else {
            if (istakipLayers.gunlukKontroller) {
                map.removeLayer(istakipLayers.gunlukKontroller);
                istakipLayers.gunlukKontroller = null;
            }
        }
        updateFilterStats();
        console.log('Filtreleme işlemi tamamlandı');
    } catch (error) {
        console.error('Filtreler uygulanırken hata:', error);
    } finally {
        applyBtn.innerHTML = originalText;
        applyBtn.disabled = false;
    }
}

// Filtreleri temizle
async function clearFilters() {
    const gorevDurum = document.getElementById('gorevDurum');
    const gorevOncelik = document.getElementById('gorevOncelik');
    const kontrolDurum = document.getElementById('kontrolDurum');
    Array.from(gorevDurum.options).forEach(option => {
        option.selected = true;
    });
    Array.from(gorevOncelik.options).forEach(option => {
        option.selected = true;
    });
    Array.from(kontrolDurum.options).forEach(option => {
        option.selected = true;
    });
    document.getElementById('gorevTarih').value = '';
    document.getElementById('kontrolTarih').value = '';
    console.log('Filtreler temizlendi, varsayılan filtreler uygulanıyor:', defaultFilters);
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
    console.log('İstatistikler güncellendi:', { gorevCount, kontrolCount });
}

// Toggle filter form
function toggleFilterForm() {
    const filterForm = document.getElementById('filterForm');
    const toggleBtn = document.getElementById('toggleFilters');
    const icon = toggleBtn.querySelector('i');
    if (filterForm.style.display === 'none' || filterForm.style.display === '') {
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

// Test fonksiyonu
function addTestMarkers() {
    console.log('🧪 Test marker\'ları ekleniyor...');
    const testCoordinates = [
        [37.0167, 39.7500],
        [37.0200, 39.7530],
        [37.0130, 39.7470]
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
        style: function (feature) {
            const durum = feature.get('durum');
            const color = getKontrolMainColor(durum);
            return new ol.style.Style({
                image: new ol.style.Circle({
                    radius: 12,
                    fill: new ol.style.Fill({
                        color: color
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#FFFFFF',
                        width: 3
                    })
                })
            });
        },
        zIndex: 200
    });
    map.addLayer(testLayer);
    console.log('✅ Test marker\'ları eklendi');
    map.getView().fit(testSource.getExtent(), {
        padding: [50, 50, 50, 50],
        maxZoom: 14,
        duration: 1000
    });
}

window.addTestMarkers = addTestMarkers;

// Form değerlerini varsayılan filtrelere ayarla
function setDefaultFormValues() {
    console.log('Form değerleri varsayılan değerlere ayarlanıyor...');
    const gorevDurum = document.getElementById('gorevDurum');
    if (gorevDurum) {
        Array.from(gorevDurum.options).forEach(option => {
            option.selected = true;
        });
    }
    const gorevOncelik = document.getElementById('gorevOncelik');
    if (gorevOncelik) {
        Array.from(gorevOncelik.options).forEach(option => {
            option.selected = true;
        });
    }
    const kontrolDurum = document.getElementById('kontrolDurum');
    if (kontrolDurum) {
        Array.from(kontrolDurum.options).forEach(option => {
            option.selected = true;
        });
    }
    console.log('Form değerleri ayarlandı');
}