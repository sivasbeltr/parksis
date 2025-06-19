// Park Detay Sayfası Ortak JS

// CSRF Token alma
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Bildirim gösterme fonksiyonu
function showNotification(message, type = 'info') {
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

// Personel Atama Dialog
function openPersonelAtamaDialog() {
    const dialog = document.getElementById('personel-atama-dialog');
    if (dialog) {
        dialog.showModal();
        initializePersonelSearch();
        initializePersonelCheckboxes();
    }
}

function closePersonelAtamaDialog() {
    const dialog = document.getElementById('personel-atama-dialog');
    if (dialog) {
        dialog.close();
        // Dialog kapandıktan sonra sorumlu sekmesini yeniden yükle
        reloadSorumluTab();
    }
}

// Sorumlu sekmesini yeniden yükle
async function reloadSorumluTab() {
    try {
        const currentTab = document.querySelector('.tab-button.active[data-tab="sorumlu"]');
        if (currentTab) {
            const url = currentTab.dataset.url;
            const response = await fetch(url, {
                headers: {
                    'HX-Request': 'true'
                }
            });

            if (response.ok) {
                const content = await response.text();
                const tabContent = document.getElementById('tab-content');
                if (tabContent) {
                    tabContent.innerHTML = content;
                }
            }
        }
    } catch (error) {
        console.error('Sorumlu sekmesi yeniden yüklenirken hata:', error);
    }
}

// Checkbox tabanlı personel atama/kaldırma
async function togglePersonelAssignment(personelUuid, parkUuid, isChecked, personelName) {
    try {
        const url = isChecked
            ? `/parkbahce/eslestir/${parkUuid}/ekle/${personelUuid}/`
            : `/parkbahce/eslestir/${parkUuid}/cikar/${personelUuid}/`;

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.success) {
            showNotification(result.message, 'success');

            // UI güncelleme
            updatePersonelDialogUI(personelUuid, isChecked, personelName);
            updatePersonelCounts();
        } else {
            showNotification(result.message, 'error');
            // Checkbox'ı geri al
            const checkbox = document.querySelector(`input[data-personel-uuid="${personelUuid}"]`);
            if (checkbox) checkbox.checked = !isChecked;
        }
    } catch (error) {
        showNotification('Personel işlemi sırasında bir hata oluştu.', 'error');
        // Checkbox'ı geri al
        const checkbox = document.querySelector(`input[data-personel-uuid="${personelUuid}"]`);
        if (checkbox) checkbox.checked = !isChecked;
    }
}

// Dialog içerisindeki UI güncelleme
function updatePersonelDialogUI(personelUuid, isAssigned, personelName) {
    const personelItem = document.getElementById(`dialog-personel-${personelUuid}`);
    const atanmisContainer = document.getElementById('dialog-atanmis-personeller');

    if (isAssigned) {
        // Personeli atanmış listesine ekle
        const atanmisPersonel = document.getElementById(`dialog-atanmis-${personelUuid}`);
        if (!atanmisPersonel) {
            const personelData = personelItem.querySelector('.personel-name').textContent;
            const personelPosition = personelItem.querySelector('p').textContent.split(' •')[0];
            const personelInitial = personelName.charAt(0).toUpperCase();

            const newAtanmisItem = document.createElement('div');
            newAtanmisItem.id = `dialog-atanmis-${personelUuid}`;
            newAtanmisItem.className = 'flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg animate-fade-in';
            newAtanmisItem.innerHTML = `
                <div class="flex items-center space-x-3">
                    <div class="w-8 h-8 bg-green-100 dark:bg-green-800 rounded-lg flex items-center justify-center">
                        <span class="text-green-600 dark:text-green-400 font-bold text-sm">${personelInitial}</span>
                    </div>
                    <div>
                        <h5 class="font-medium text-gray-900 dark:text-white">${personelName}</h5>
                        <p class="text-sm text-gray-500 dark:text-gray-400">${personelPosition}</p>
                    </div>
                </div>
                <button onclick="removePersonelFromParkDialog('${personelUuid}', '${personelItem.querySelector('input').dataset.parkUuid}')" 
                        class="px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 text-sm rounded-lg transition-colors">
                    <i class="fas fa-times mr-1"></i>
                    Kaldır
                </button>
            `;
            atanmisContainer.appendChild(newAtanmisItem);
        }

        // Ana listede personeli güncelle
        if (personelItem) {
            personelItem.className = 'personel-item flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg';
            const personelNameEl = personelItem.querySelector('.personel-name');
            personelNameEl.className = 'font-medium text-green-700 dark:text-green-300 personel-name';
            const descEl = personelItem.querySelector('p');
            descEl.className = 'text-sm text-green-600 dark:text-green-400';
            descEl.textContent = descEl.textContent.split(' •')[0] + ' • Atanmış';

            const checkboxContainer = personelItem.querySelector('label span:last-child');
            checkboxContainer.textContent = 'Atanmış';
            checkboxContainer.className = 'ml-2 text-sm text-green-700 dark:text-green-300';

            const checkboxBg = personelItem.querySelector('.checkbox-bg');
            checkboxBg.className = 'w-5 h-5 bg-green-500 border-2 border-green-500 rounded transition-all duration-200 checkbox-bg';

            const checkboxIcon = personelItem.querySelector('.checkbox-icon');
            checkboxIcon.className = 'absolute inset-0 flex items-center justify-center text-white opacity-100 transition-opacity duration-200 checkbox-icon';
        }
    } else {
        // Atanmış listeden kaldır
        const atanmisPersonel = document.getElementById(`dialog-atanmis-${personelUuid}`);
        if (atanmisPersonel) {
            atanmisPersonel.remove();
        }

        // Ana listede personeli güncelle
        if (personelItem) {
            personelItem.className = 'personel-item flex items-center justify-between p-3 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors';
            const personelNameEl = personelItem.querySelector('.personel-name');
            personelNameEl.className = 'font-medium text-gray-900 dark:text-white personel-name';
            const descEl = personelItem.querySelector('p');
            descEl.className = 'text-sm text-gray-500 dark:text-gray-400';
            descEl.textContent = descEl.textContent.split(' •')[0];

            const checkboxContainer = personelItem.querySelector('label span:last-child');
            checkboxContainer.textContent = 'Ata';
            checkboxContainer.className = 'ml-2 text-sm text-gray-700 dark:text-gray-300';

            const checkboxBg = personelItem.querySelector('.checkbox-bg');
            checkboxBg.className = 'w-5 h-5 bg-white border-2 border-gray-300 dark:border-gray-600 rounded transition-all duration-200 checkbox-bg';

            const checkboxIcon = personelItem.querySelector('.checkbox-icon');
            checkboxIcon.className = 'absolute inset-0 flex items-center justify-center text-white opacity-0 transition-opacity duration-200 checkbox-icon';
        }
    }
}

// Personel sayılarını güncelle
function updatePersonelCounts() {
    const atanmisCount = document.querySelectorAll('#dialog-atanmis-personeller > div').length;
    const countElement = document.getElementById('dialog-atanmis-count');
    if (countElement) {
        countElement.textContent = atanmisCount;
    }
}

// Tab içerisinden personel kaldırma
async function removePersonelFromParkTab(personelUuid, personelName) {
    if (!confirm(`${personelName} adlı personeli parktan kaldırmak istediğinizden emin misiniz?`)) {
        return;
    }

    try {
        const checkbox = document.querySelector(`input[data-personel-uuid="${personelUuid}"]`);
        const parkUuid = checkbox ? checkbox.dataset.parkUuid : null;

        if (!parkUuid) {
            showNotification('Park bilgisi bulunamadı.', 'error');
            return;
        }

        const url = `/parkbahce/eslestir/${parkUuid}/cikar/${personelUuid}/`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (result.success) {
            showNotification(result.message, 'success');

            // Tab içerisindeki elementi kaldır
            const tabItem = document.getElementById(`atanmis-item-${personelUuid}`);
            if (tabItem) {
                tabItem.remove();
            }

            // Sayıyı güncelle
            const countElement = document.getElementById('atanmis-personel-count');
            if (countElement) {
                const currentCount = parseInt(countElement.textContent) - 1;
                countElement.textContent = currentCount;

                // Eğer hiç personel kalmadıysa empty state göster
                if (currentCount === 0) {
                    const listContainer = document.getElementById('atanmis-personel-listesi').parentElement;
                    listContainer.innerHTML = `
                        <div id="empty-state" class="text-center py-8 bg-gray-50 dark:bg-gray-700 rounded-xl">
                            <div class="w-16 h-16 bg-gray-200 dark:bg-gray-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i class="fas fa-user-slash text-gray-400 dark:text-gray-500 text-2xl"></i>
                            </div>
                            <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Atanmış Personel Bulunamadı</h4>
                            <p class="text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">
                                Bu parka henüz hiç personel atanmamış. Yeni personel atamak için butona tıklayın.
                            </p>
                        </div>
                    `;
                }
            }
        } else {
            showNotification(result.message, 'error');
        }
    } catch (error) {
        showNotification('Personel kaldırma sırasında bir hata oluştu.', 'error');
    }
}

// Dialog içerisinden personel kaldırma
async function removePersonelFromParkDialog(personelUuid, parkUuid) {
    const checkbox = document.querySelector(`input[data-personel-uuid="${personelUuid}"]`);
    if (checkbox) {
        checkbox.checked = false;
        const personelName = checkbox.dataset.personelName;
        await togglePersonelAssignment(personelUuid, parkUuid, false, personelName);
    }
}

function initializePersonelSearch() {
    const searchInput = document.getElementById('personel-search');
    const personelItems = document.querySelectorAll('.personel-item');

    if (!searchInput) return;

    searchInput.addEventListener('input', function () {
        const searchTerm = this.value.toLowerCase();
        personelItems.forEach(item => {
            const personelName = item.querySelector('.personel-name').textContent.toLowerCase();
            item.style.display = personelName.includes(searchTerm) ? 'flex' : 'none';
        });
    });
}

function initializePersonelCheckboxes() {
    const checkboxes = document.querySelectorAll('.personel-checkbox');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function () {
            const personelUuid = this.dataset.personelUuid;
            const parkUuid = this.dataset.parkUuid;
            const personelName = this.dataset.personelName;
            togglePersonelAssignment(personelUuid, parkUuid, this.checked, personelName);
        });
    });
}