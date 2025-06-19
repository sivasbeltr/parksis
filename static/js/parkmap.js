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
            style: function (feature) {
                const hasPersonel = feature.get('personel_durum'); // boolean field

                if (hasPersonel) {
                    // Personel atanmış parklar - yeşil
                    return new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#047857',
                            width: 2
                        }),
                        fill: new ol.style.Fill({
                            color: 'rgba(16, 185, 129, 0.3)'
                        })
                    });
                } else {
                    // Personel atanmamış parklar - kırmızı kenarlık
                    return new ol.style.Style({
                        stroke: new ol.style.Stroke({
                            color: '#DC2626',
                            width: 2,
                            lineDash: [5, 5] // kesikli çizgi
                        }),
                        fill: new ol.style.Fill({
                            color: 'rgba(16, 185, 129, 0.3)'
                        })
                    });
                }
            },
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
        if (mahalleModal) {
            mahalleModal.classList.add('hidden');
        }
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
            parkModal.dataset.parkUuid = uuid;
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

// Park alt katmanlarını yükle
function loadParkSubLayers(parkUuid) {
    // Park modal'ını kapat
    document.getElementById('parkModal').classList.add('hidden');

    // Park'a yakınlaştır
    zoomToPark(parkUuid);

    // Burada gelecekte park içi detay katmanları yüklenebilir
    // Örneğin: habitatlar, donatılar, sulama noktaları vb.
    console.log(`Park ${parkUuid} için detay katmanları yükleniyor...`);
}

// Mahalle parklarını göster
function showMahalleParks(mahalleUuid) {
    // Mahalle modal'ını kapat
    document.getElementById('mahalleModal').classList.add('hidden');

    // Mahalleye yakınlaştır
    zoomToMahalle(mahalleUuid);

    // Burada o mahalledeki parkları vurgulayabiliriz
    console.log(`Mahalle ${mahalleUuid} parkları vurgulanıyor...`);

    // İleride mahalle parkları için özel stil uygulayabiliriz
    const parkLayer = layers.parklar;
    if (parkLayer) {
        const features = parkLayer.getSource().getFeatures();
        features.forEach(feature => {
            // Sadece o mahalledeki parkları vurgula
            if (feature.get('mahalle_uuid') === mahalleUuid) {
                // Özel vurgulama stili eklenebilir
            }
        });
    }
}

// Modal Personel Yönetimi Fonksiyonları
function openModalPersonelYonetimi(parkUuid) {
    // Park detay modal'ının z-index'ini düşür
    const parkModal = document.getElementById('parkModal');
    if (parkModal) {
        parkModal.style.zIndex = '998';
    }

    // Personel yönetimi modal'ını oluştur
    createPersonelYonetimiModal(parkUuid);
}

function createPersonelYonetimiModal(parkUuid) {
    // Varolan modal'ı kaldır
    const existingModal = document.getElementById('personel-yonetimi-modal');
    if (existingModal) {
        existingModal.remove();
    }

    // Yeni modal oluştur
    const modal = document.createElement('div');
    modal.id = 'personel-yonetimi-modal';
    modal.className = 'fixed inset-0 z-[999] flex items-center justify-center p-4';
    modal.innerHTML = `
        <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" onclick="closeModalPersonelYonetimi()"></div>
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden relative">
            <!-- Header -->
            <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
                    <i class="fas fa-users-cog text-green-600 mr-2"></i>
                    Personel Yönetimi
                </h3>
                <button onclick="closeModalPersonelYonetimi()" 
                        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
                    <i class="fas fa-times text-xl"></i>
                </button>
            </div>
            
            <!-- Content Container -->
            <div id="modal-content-container" class="flex-1 overflow-hidden">
                <!-- Loading göstergesi -->
                <div id="modal-loading" class="flex items-center justify-center p-8">
                    <div class="text-center">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
                        <p class="text-gray-500 dark:text-gray-400">Personel listesi yükleniyor...</p>
                    </div>
                </div>
                
                <!-- Gerçek içerik -->
                <div id="modal-actual-content" class="p-6 space-y-6 h-full overflow-y-auto" style="display: none;">
                    <!-- İçerik buraya yüklenecek -->
                </div>
            </div>

            <!-- Footer -->
            <div class="flex justify-end p-4 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
                <button onclick="closeModalPersonelYonetimi()" 
                        class="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors">
                    <i class="fas fa-times mr-2"></i>
                    Kapat
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Personel verilerini yükle
    loadModalPersonelData(parkUuid);
}

async function loadModalPersonelData(parkUuid) {
    try {
        // Hem park personellerini hem de tüm personelleri al
        const [parkPersonelResponse, tumPersonelResponse] = await Promise.all([
            fetch(`/api/v1/parklar/${parkUuid}/personeller/`),
            fetch('/api/v1/personeller/')
        ]);

        if (!parkPersonelResponse.ok || !tumPersonelResponse.ok) {
            throw new Error('Veri yüklenirken hata oluştu');
        }

        const parkPersonelleri = await parkPersonelResponse.json();
        const tumPersoneller = await tumPersonelResponse.json();

        // Modal içeriğini güncelle
        updateModalPersonelContent(parkUuid, parkPersonelleri, tumPersoneller);
    } catch (error) {
        console.error('Personel verileri yüklenirken hata:', error);

        // Hata durumunda basit personel listesi göster
        showSimplePersonelList(parkUuid);
    }
}

function showSimplePersonelList(parkUuid) {
    const modal = document.getElementById('personel-yonetimi-modal');
    if (!modal) return;

    const content = modal.querySelector('.p-4');
    content.innerHTML = `
        <div class="space-y-4">
            <div class="text-center py-8">
                <i class="fas fa-exclamation-triangle text-yellow-500 text-3xl mb-2"></i>
                <p class="text-gray-600 dark:text-gray-400">
                    Personel listesi yüklenemedi. Lütfen sayfayı yenileyin.
                </p>
            </div>
            <div class="flex justify-center">
                <button onclick="closeModalPersonelYonetimi()" 
                        class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors">
                    Kapat
                </button>
            </div>
        </div>
    `;
}

function updateModalPersonelContent(parkUuid, parkPersonelleri, tumPersoneller) {
    const modal = document.getElementById('personel-yonetimi-modal');
    if (!modal) return;

    const content = modal.querySelector('.p-4');

    // Atanmış personel UUID'lerini toplama
    const atanmisUuidler = new Set(parkPersonelleri.map(p => p.personel_uuid || p.uuid));

    content.innerHTML = `
        <div class="space-y-6 max-h-[70vh] overflow-y-auto">
            <!-- Atanmış Personeller -->
            <div class="space-y-3">
                <h4 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center">
                    <i class="fas fa-check-circle text-green-600 mr-2"></i>
                    Atanmış Personeller (<span id="modal-atanmis-count">${parkPersonelleri.length}</span>)
                </h4>
                
                <div id="modal-atanmis-liste" class="space-y-2">
                    ${parkPersonelleri.map(personel => `
                        <div id="modal-atanmis-${personel.personel_uuid || personel.uuid}" 
                             class="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-green-100 dark:bg-green-800 rounded-lg flex items-center justify-center">
                                    <span class="text-green-600 dark:text-green-400 font-bold text-sm">
                                        ${(personel.personel_ad || personel.ad || 'U').charAt(0).toUpperCase()
        }</span>
                                </div>
                                <div>
                                    <h5 class="font-medium text-gray-900 dark:text-white">${personel.personel_ad || personel.ad || 'Bilinmiyor'}</h5>
                                    <p class="text-sm text-gray-500 dark:text-gray-400">${personel.personel_pozisyon || personel.pozisyon || 'Pozisyon belirtilmemiş'}</p>
                                </div>
                            </div>
                            <button onclick="removePersonelFromModalQuick('${personel.personel_uuid || personel.uuid}', '${parkUuid}', '${personel.personel_ad || personel.ad || 'Bilinmiyor'}')" 
                                    class="px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded-lg transition-colors">
                                <i class="fas fa-times mr-1"></i>
                                Kaldır
                            </button>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Tüm Personeller -->
            <div class="space-y-3">
                <h4 class="text-sm font-semibold text-gray-900 dark:text-white flex items-center">
                    <i class="fas fa-users text-blue-600 mr-2"></i>
                    Tüm Aktif Personeller
                </h4>
                
                <!-- Arama -->
                <div class="relative">
                    <input type="text" 
                           id="modal-personel-search" 
                           placeholder="Personel ara..." 
                           class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent text-sm">
                    <i class="fas fa-search absolute left-3 top-3 text-gray-400"></i>
                </div>
                
                <div id="modal-tum-personeller" class="space-y-2 max-h-64 overflow-y-auto">
                    ${tumPersoneller.map(personel => {
            const isAssigned = atanmisUuidler.has(personel.uuid);
            return `
                            <div class="modal-personel-item flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${isAssigned ? 'opacity-50' : ''}" 
                                 data-personel-name="${(personel.ad || '').toLowerCase()}">
                                <div class="flex items-center space-x-3">
                                    <div class="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                                        <span class="text-blue-600 dark:text-blue-400 font-bold text-sm">
                                            ${(personel.ad || 'U').charAt(0).toUpperCase()
                }</span>
                                    </div>
                                    <div>
                                        <h5 class="font-medium text-gray-900 dark:text-white">${personel.ad || 'Bilinmiyor'}</h5>
                                        <p class="text-sm text-gray-500 dark:text-gray-400">${personel.pozisyon || 'Pozisyon belirtilmemiş'}</p>
                                    </div>
                                </div>
                                <button onclick="addPersonelToModalQuick('${personel.uuid}', '${parkUuid}', '${personel.ad || 'Bilinmiyor'}', '${personel.pozisyon || ''}')" 
                                        class="px-3 py-1.5 ${isAssigned ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'bg-green-100 hover:bg-green-200 text-green-700'} text-sm rounded-lg transition-colors"
                                        ${isAssigned ? 'disabled' : ''}>
                                    <i class="fas fa-${isAssigned ? 'check' : 'plus'} mr-1"></i>
                                    ${isAssigned ? 'Atanmış' : 'Ata'}
                                </button>
                            </div>
                        `;
        }).join('')}
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700 mt-4">
            <button onclick="closeModalPersonelYonetimi()" 
                    class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors">
                <i class="fas fa-times mr-2"></i>
                Kapat
            </button>
        </div>
    `;

    // Arama fonksiyonunu initialize et
    initModalPersonelSearch();
}

function initModalPersonelSearch() {
    const searchInput = document.getElementById('modal-personel-search');
    const personelItems = document.querySelectorAll('.modal-personel-item');

    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        personelItems.forEach(item => {
            const personelName = item.querySelector('.modal-personel-name').textContent.toLowerCase();
            item.style.display = personelName.includes(searchTerm) ? 'flex' : 'none';
        });
    });
}

// Modal personel checkbox fonksiyonu
function initModalPersonelCheckboxes() {
    const checkboxes = document.querySelectorAll('.modal-personel-checkbox');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const personelUuid = this.dataset.personelUuid;
            const parkUuid = this.dataset.parkUuid;
            const personelName = this.dataset.personelName;
            const personelPosition = this.dataset.personelPosition;

            if (this.checked) {
                addPersonelToModalQuick(personelUuid, parkUuid, personelName, personelPosition);
            } else {
                removePersonelFromModalQuick(personelUuid, parkUuid, personelName);
            }
        });
    });
}

async function loadModalPersonelData(parkUuid) {
    try {
        // Park personellerini al
        const parkPersonelResponse = await fetch(`/api/v1/parklar/${parkUuid}/personeller/`);
        const parkPersonelleri = parkPersonelResponse.ok ? await parkPersonelResponse.json() : [];

        // Tüm personelleri al
        const tumPersonelResponse = await fetch('/api/v1/personeller/');
        const tumPersonelData = tumPersonelResponse.ok ? await tumPersonelResponse.json() : { results: [] };
        const tumPersoneller = tumPersonelData.results || tumPersonelData;

        // İçeriği render et
        renderModalPersonelContent(parkUuid, parkPersonelleri, tumPersoneller);

        // Loading gizle ve içeriği göster
        const loading = document.getElementById('modal-loading');
        const content = document.getElementById('modal-actual-content');
        if (loading) loading.style.display = 'none';
        if (content) content.style.display = 'block';

        // Arama ve checkbox event'lerini başlat
        initModalPersonelSearch();
        initModalPersonelCheckboxes();

    } catch (error) {
        console.error('Personel verileri yüklenirken hata:', error);
        const loading = document.getElementById('modal-loading');
        if (loading) {
            loading.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-red-500 text-2xl mb-2"></i>
                    <p class="text-red-600">Personel listesi yüklenirken hata oluştu.</p>
                </div>
            `;
        }
    }
}

function renderModalPersonelContent(parkUuid, parkPersonelleri, tumPersoneller) {
    const content = document.getElementById('modal-actual-content');
    if (!content) return;

    // Atanmış personel UUID'lerini al
    const atanmisPersonelUuids = parkPersonelleri.map(p => p.personel_uuid);

    content.innerHTML = `
        <!-- Atanmış Personeller -->
        <div class="space-y-4">
            <h4 class="text-md font-semibold text-gray-900 dark:text-white flex items-center">
                <i class="fas fa-check-circle text-green-600 mr-2"></i>
                Atanmış Personeller (<span id="modal-personel-count">${parkPersonelleri.length}</span>)
            </h4>
            
            <div id="modal-atanmis-personeller" class="space-y-2">
                ${parkPersonelleri.map(personel => `
                    <div id="modal-atanmis-${personel.personel_uuid}" class="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg animate-fade-in">
                        <div class="flex items-center space-x-3">
                            <div class="w-8 h-8 bg-green-100 dark:bg-green-800 rounded-lg flex items-center justify-center">
                                <span class="text-green-600 dark:text-green-400 font-bold text-sm">${personel.personel_ad.charAt(0).toUpperCase()}</span>
                            </div>
                            <div>
                                <h5 class="font-medium text-gray-900 dark:text-white">${personel.personel_ad}</h5>
                                <p class="text-sm text-gray-500 dark:text-gray-400">${personel.personel_pozisyon || 'Pozisyon belirtilmemiş'}</p>
                            </div>
                        </div>
                        <button onclick="removePersonelFromModalQuick('${personel.personel_uuid}', '${parkUuid}', '${personel.personel_ad}')" 
                                class="px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded-lg transition-colors">
                            <i class="fas fa-times mr-1"></i>
                            Kaldır
                        </button>
                    </div>
                `).join('')}
            </div>
        </div>

        <!-- Tüm Personeller -->
        <div class="space-y-4">
            <h4 class="text-md font-semibold text-gray-900 dark:text-white flex items-center">
                <i class="fas fa-users text-blue-600 mr-2"></i>
                Tüm Aktif Personeller
            </h4>
            
            <!-- Arama -->
            <div class="relative">
                <input type="text" 
                       id="modal-personel-search" 
                       placeholder="Personel ara..." 
                       class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent">
                <i class="fas fa-search absolute left-3 top-3 text-gray-400"></i>
            </div>
            
            <div id="modal-tum-personeller" class="space-y-2 max-h-80 overflow-y-auto">
                ${tumPersoneller.map(personel => {
        const isAssigned = atanmisPersonelUuids.includes(personel.uuid);
        const initial = personel.ad ? personel.ad.charAt(0).toUpperCase() : 'P';
        const position = personel.pozisyon || 'Pozisyon belirtilmemiş';

        return `
                        <div id="modal-personel-${personel.uuid}" class="modal-personel-item flex items-center justify-between p-3 ${isAssigned
                ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700'
                : 'border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
            } rounded-lg transition-colors">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 ${isAssigned
                ? 'bg-green-100 dark:bg-green-800'
                : 'bg-blue-100 dark:bg-blue-900/30'
            } rounded-lg flex items-center justify-center">
                                    <span class="${isAssigned
                ? 'text-green-600 dark:text-green-400'
                : 'text-blue-600 dark:text-blue-400'
            } font-bold text-sm">${initial}</span>
                                </div>
                                <div>
                                    <h5 class="font-medium ${isAssigned
                ? 'text-green-700 dark:text-green-300'
                : 'text-gray-900 dark:text-white'
            } modal-personel-name">${personel.ad}</h5>
                                    <p class="text-sm ${isAssigned
                ? 'text-green-600 dark:text-green-400'
                : 'text-gray-500 dark:text-gray-400'
            }">${position}${isAssigned ? ' • Atanmış' : ''}</p>
                                </div>
                            </div>
                            <label class="flex items-center cursor-pointer">
                                <input type="checkbox" 
                                       class="modal-personel-checkbox sr-only" 
                                       data-personel-uuid="${personel.uuid}"
                                       data-personel-name="${personel.ad}"
                                       data-personel-position="${position}"
                                       data-park-uuid="${parkUuid}"
                                       ${isAssigned ? 'checked' : ''}>
                                <div class="relative">
                                    <div class="w-5 h-5 ${isAssigned
                ? 'bg-green-500 border-2 border-green-500'
                : 'bg-white border-2 border-gray-300 dark:border-gray-600'
            } rounded transition-all duration-200 modal-checkbox-bg"></div>
                                    <div class="absolute inset-0 flex items-center justify-center text-white ${isAssigned ? 'opacity-100' : 'opacity-0'
            } transition-opacity duration-200 modal-checkbox-icon">
                                        <i class="fas fa-check text-xs"></i>
                                    </div>
                                </div>
                                <span class="ml-2 text-sm ${isAssigned
                ? 'text-green-700 dark:text-green-300'
                : 'text-gray-700 dark:text-gray-300'
            }">${isAssigned ? 'Atanmış' : 'Ata'}</span>
                            </label>
                        </div>
                    `;
    }).join('')}
            </div>
        </div>
    `;
}

// Modal'dan personel ekleme
async function addPersonelToModalQuick(personelUuid, parkUuid, personelAd, personelPozisyon) {
    try {
        const response = await fetch(`/parkbahce/eslestir/${parkUuid}/ekle/${personelUuid}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.success) {
            showMapNotification(result.message, 'success');
            updateModalPersonelUI(personelUuid, parkUuid, personelAd, personelPozisyon, true);
            updateModalPersonelCount(1);

            // Ana modal personel listesini güncelle
            await updateMainModalPersonelList(parkUuid);

            // Parklar katmanını yeniden yükle
            await reloadParksLayer();
        } else {
            showMapNotification(result.message, 'error');
            // Checkbox'ı geri al
            const checkbox = document.querySelector(`input[data-personel-uuid="${personelUuid}"]`);
            if (checkbox) checkbox.checked = false;
        }
    } catch (error) {
        showMapNotification('Personel ekleme sırasında bir hata oluştu.', 'error');
        // Checkbox'ı geri al
        const checkbox = document.querySelector(`input[data-personel-uuid="${personelUuid}"]`);
        if (checkbox) checkbox.checked = false;
    }
}

// Modal'dan personel kaldırma
async function removePersonelFromModalQuick(personelUuid, parkUuid, personelAd) {
    try {
        const response = await fetch(`/parkbahce/eslestir/${parkUuid}/cikar/${personelUuid}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.success) {
            showMapNotification(result.message, 'success');
            updateModalPersonelUI(personelUuid, parkUuid, personelAd, '', false);
            updateModalPersonelCount(-1);

            // Ana modal personel listesini güncelle
            await updateMainModalPersonelList(parkUuid);

            // Parklar katmanını yeniden yükle
            await reloadParksLayer();
        } else {
            showMapNotification(result.message, 'error');
            // Checkbox'ı geri al
            const checkbox = document.querySelector(`input[data-personel-uuid="${personelUuid}"]`);
            if (checkbox) checkbox.checked = true;
        }
    } catch (error) {
        showMapNotification('Personel kaldırma sırasında bir hata oluştu.', 'error');
        // Checkbox'ı geri al
        const checkbox = document.querySelector(`input[data-personel-uuid="${personelUuid}"]`);
        if (checkbox) checkbox.checked = true;
    }
}

function updateModalPersonelUI(personelUuid, parkUuid, personelAd, personelPozisyon, isAdding) {
    const personelItem = document.getElementById(`modal-personel-${personelUuid}`);
    const atanmisContainer = document.getElementById('modal-atanmis-personeller');

    if (isAdding) {
        // Atanmış listesine ekle
        const atanmisPersonel = document.getElementById(`modal-atanmis-${personelUuid}`);
        if (!atanmisPersonel && atanmisContainer) {
            const personelInitial = personelAd.charAt(0).toUpperCase();
            const newAtanmisItem = document.createElement('div');
            newAtanmisItem.id = `modal-atanmis-${personelUuid}`;
            newAtanmisItem.className = 'flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg animate-fade-in';
            newAtanmisItem.innerHTML = `
                <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 bg-green-100 dark:bg-green-800 rounded-lg flex items-center justify-center">
                        <span class="text-green-600 dark:text-green-400 font-bold text-sm">${personelInitial}</span>
                    </div>
                    <div>
                        <h5 class="font-medium text-gray-900 dark:text-white">${personelAd}</h5>
                        <p class="text-sm text-gray-500 dark:text-gray-400">${personelPozisyon || 'Pozisyon belirtilmemiş'}</p>
                    </div>
                </div>
                <button onclick="removePersonelFromModalQuick('${personelUuid}', '${parkUuid}', '${personelAd}')" 
                        class="px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded-lg transition-colors">
                    <i class="fas fa-times mr-1"></i>
                    Kaldır
                </button>
            `;
            atanmisContainer.appendChild(newAtanmisItem);
        }

        // Ana listede güncelle
        if (personelItem) {
            updatePersonelItemVisuals(personelItem, true);
        }
    } else {
        // Atanmış listeden kaldır
        const atanmisPersonel = document.getElementById(`modal-atanmis-${personelUuid}`);
        if (atanmisPersonel) {
            atanmisPersonel.remove();
        }

        // Ana listede güncelle
        if (personelItem) {
            updatePersonelItemVisuals(personelItem, false);
        }
    }
}

function updatePersonelItemVisuals(personelItem, isAssigned) {
    const nameEl = personelItem.querySelector('.modal-personel-name');
    const descEl = personelItem.querySelector('p');
    const checkboxBg = personelItem.querySelector('.modal-checkbox-bg');
    const checkboxIcon = personelItem.querySelector('.modal-checkbox-icon');
    const checkboxLabel = personelItem.querySelector('label span:last-child');
    const avatarDiv = personelItem.querySelector('.w-8');

    if (isAssigned) {
        personelItem.className = 'modal-personel-item flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg transition-colors';
        nameEl.className = 'font-medium text-green-700 dark:text-green-300 modal-personel-name';
        descEl.className = 'text-sm text-green-600 dark:text-green-400';
        descEl.textContent = descEl.textContent.split(' •')[0] + ' • Atanmış';
        checkboxBg.className = 'w-5 h-5 bg-green-500 border-2 border-green-500 rounded transition-all duration-200 modal-checkbox-bg';
        checkboxIcon.className = 'absolute inset-0 flex items-center justify-center text-white opacity-100 transition-opacity duration-200 modal-checkbox-icon';
        checkboxLabel.textContent = 'Atanmış';
        checkboxLabel.className = 'ml-2 text-sm text-green-700 dark:text-green-300';
        avatarDiv.className = 'w-8 h-8 bg-green-100 dark:bg-green-800 rounded-lg flex items-center justify-center';
        avatarDiv.querySelector('span').className = 'text-green-600 dark:text-green-400 font-bold text-sm';
    } else {
        personelItem.className = 'modal-personel-item flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors';
        nameEl.className = 'font-medium text-gray-900 dark:text-white modal-personel-name';
        descEl.className = 'text-sm text-gray-500 dark:text-gray-400';
        descEl.textContent = descEl.textContent.split(' •')[0];
        checkboxBg.className = 'w-5 h-5 bg-white border-2 border-gray-300 dark:border-gray-600 rounded transition-all duration-200 modal-checkbox-bg';
        checkboxIcon.className = 'absolute inset-0 flex items-center justify-center text-white opacity-0 transition-opacity duration-200 modal-checkbox-icon';
        checkboxLabel.textContent = 'Ata';
        checkboxLabel.className = 'ml-2 text-sm text-gray-700 dark:text-gray-300';
        avatarDiv.className = 'w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center';
        avatarDiv.querySelector('span').className = 'text-blue-600 dark:text-blue-400 font-bold text-sm';
    }
}

function updateModalPersonelCount(change) {
    const countElement = document.getElementById('modal-atanmis-count');
    if (countElement) {
        const currentCount = parseInt(countElement.textContent) + change;
        countElement.textContent = Math.max(0, currentCount);
    }
}

function closeModalPersonelYonetimi() {
    const modal = document.getElementById('personel-yonetimi-modal');
    if (modal) {
        modal.remove();
    }
}

// Harita için CSRF token alma
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) return token.value;

    // Cookie'den CSRF token'ı al
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

// Harita için bildirim gösterme
function showMapNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full ${type === 'success' ? 'bg-green-600 text-white' :
        type === 'error' ? 'bg-red-600 text-white' :
            'bg-blue-600 text-white'
        }`;
    notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    document.body.appendChild(notification);
    setTimeout(() => { notification.classList.remove('translate-x-full'); }, 100);
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => { if (notification.parentElement) notification.remove(); }, 300);
    }, 5000);
}

// Modal'dan hızlı personel kaldırma
async function removePersonelFromModal(personelUuid, parkUuid, personelAd) {
    if (!confirm(`${personelAd} adlı personeli parktan kaldırmak istediğinizden emin misiniz?`)) {
        return;
    }

    try {
        const response = await fetch(`/parkbahce/eslestir/${parkUuid}/cikar/${personelUuid}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.success) {
            showMapNotification(result.message, 'success');

            // Ana modal personel listesini güncelle
            await updateMainModalPersonelList(parkUuid);

            // Parklar katmanını yeniden yükle
            await reloadParksLayer();
        } else {
            showMapNotification(result.message, 'error');
        }
    } catch (error) {
        showMapNotification('Personel kaldırma sırasında bir hata oluştu.', 'error');
    }
}

// Global fonksiyonları window objesine ekle
window.removePersonelFromModal = removePersonelFromModal;
window.showMapNotification = showMapNotification;
window.getCsrfToken = getCsrfToken;
window.openModalPersonelYonetimi = openModalPersonelYonetimi;
window.closeModalPersonelYonetimi = closeModalPersonelYonetimi;
window.removePersonelFromModalQuick = removePersonelFromModalQuick;
window.updateMainModalPersonelList = updateMainModalPersonelList;
window.addPersonelToModalQuick = addPersonelToModalQuick;
window.reloadParksLayer = reloadParksLayer;

// Personel yönetimi modal'ını açma
function openModalPersonelYonetimi(parkUuid) {
    if (!parkUuid) {
        showMapNotification('Park UUID bulunamadı.', 'error');
        return;
    }
    createPersonelYonetimiModal(parkUuid);
}

// Parklar katmanını yeniden yükle
async function reloadParksLayer() {
    try {
        console.log('Parklar katmanı yeniden yükleniyor...');

        // Mevcut parklar katmanını haritadan kaldır
        if (layers.parklar) {
            map.removeLayer(layers.parklar);
            layers.parklar = null;
        }

        // Parklar katmanını yeniden yükle
        await loadParklar();

        console.log('Parklar katmanı başarıyla yeniden yüklendi');
    } catch (error) {
        console.error('Parklar katmanı yeniden yüklenirken hata:', error);
        showMapNotification('Parklar katmanı güncellenirken bir hata oluştu.', 'error');
    }
}

// Ana modal'daki personel listesini güncelle
async function updateMainModalPersonelList(parkUuid) {
    try {
        const response = await fetch(`/api/v1/parklar/${parkUuid}/personeller/`, {
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            const personelData = await response.json();

            // Ana modal'daki personel elemanlarını al
            const modalPersonelCount = document.getElementById('modal-personel-count');
            const modalPersonelEmpty = document.getElementById('modal-personel-empty');
            let modalPersonelContainer = document.getElementById('modal-personel-listesi');
            let modalPersonelSection = document.getElementById('modal-personel-section');

            if (modalPersonelCount) {
                modalPersonelCount.textContent = personelData.length;
            }

            if (personelData.length > 0) {
                // Eğer personel section yoksa oluştur
                if (!modalPersonelSection) {
                    modalPersonelSection = document.createElement('div');
                    modalPersonelSection.id = 'modal-personel-section';
                    modalPersonelSection.className = 'bg-green-50 border border-green-200 rounded-lg p-3';
                    modalPersonelSection.innerHTML = `
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-sm font-semibold text-green-800 flex items-center">
                                <i class="fas fa-user-check text-green-600 mr-2"></i>
                                Atanmış Personeller (<span id="modal-personel-count">${personelData.length}</span>)
                            </h3>
                            <button onclick="openModalPersonelYonetimi('${parkUuid}')" 
                                    class="text-xs bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded-md transition-colors">
                                <i class="fas fa-cog mr-1"></i>Yönet
                            </button>
                        </div>
                        <div id="modal-personel-listesi" class="space-y-2">
                            <!-- Personel listesi buraya eklenecek -->
                        </div>
                    `;

                    // Empty state'in yanına ekle
                    if (modalPersonelEmpty) {
                        modalPersonelEmpty.parentNode.insertBefore(modalPersonelSection, modalPersonelEmpty);
                    }

                    modalPersonelContainer = document.getElementById('modal-personel-listesi');
                }

                // Personel listesini oluştur
                if (modalPersonelContainer) {
                    modalPersonelContainer.innerHTML = '';
                    personelData.forEach(personel => {
                        const personelDiv = document.createElement('div');
                        personelDiv.id = `modal-personel-item-${personel.personel_uuid}`;
                        personelDiv.className = 'flex items-center space-x-3 py-1 px-2 rounded-lg hover:bg-green-100 transition-colors group';

                        personelDiv.innerHTML = `
                            <div class="w-8 h-8 bg-green-200 rounded-full flex items-center justify-center shadow-sm">
                                <span class="text-green-700 font-bold text-base">
                                    ${personel.personel_ad.charAt(0).toUpperCase()}
                                </span>
                            </div>
                            <div class="flex-1 min-w-0">
                                <a href="/istakip/kullanici_detail/${personel.personel_uuid}/" 
                                   class="font-semibold text-green-900 transition-colors group-hover:text-green-700 focus:outline-none"
                                   style="text-decoration: none;">
                                    ${personel.personel_ad}
                                </a>
                                ${personel.personel_pozisyon ? `<span class="text-green-600 text-xs ml-1">(${personel.personel_pozisyon})</span>` : ''}
                            </div>
                            <div class="flex items-center space-x-2">
                                <span class="text-xs text-green-500 whitespace-nowrap">${personel.atama_tarihi}</span>
                                <button onclick="removePersonelFromModal('${personel.personel_uuid}', '${parkUuid}', '${personel.personel_ad}')" 
                                        class="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700 transition-all duration-200 p-1 rounded">
                                    <i class="fas fa-times text-xs"></i>
                                </button>
                            </div>
                        `;

                        modalPersonelContainer.appendChild(personelDiv);
                    });
                }

                // Personel section'ı göster, empty state'i gizle
                if (modalPersonelSection) modalPersonelSection.style.display = 'block';
                if (modalPersonelEmpty) modalPersonelEmpty.style.display = 'none';

            } else {
                // Personel yok - empty state göster, section gizle
                if (modalPersonelSection) modalPersonelSection.style.display = 'none';
                if (modalPersonelEmpty) modalPersonelEmpty.style.display = 'block';
            }

            console.log(`Ana modal personel listesi güncellendi: ${personelData.length} personel`);
        }
    } catch (error) {
        console.error('Ana modal personel listesi güncellenirken hata:', error);
    }
}