// DÖF Yönetim Sistemi - Form Fonksiyonları

document.addEventListener('DOMContentLoaded', function() {
    // Kök Neden Analizi sayfası için
    initRootCauseForm();
    // Yükleme ekranı için
    initLoaderOverlay();
    // Form optimizasyonu
    optimizeForms();
    // DÖF işlemlerinde yükleme ekranı gösterme
    setupDofActionLinks();
    // Form ön belleğe alma
    setupFormCaching();
    // Sel2 optimize et (performans için)
    optimizeSelect2();
    // Form girişlerini hızlandır
    accelerateFormInputs();
});

// Kök Neden Analizi formu
function initRootCauseForm() {
    // resolve.html sayfasında olup olmadığını kontrol et
    if (document.querySelector('form') && document.getElementById('root_cause1')) {
        console.log("Kök Neden Analizi formu bulundu, aktivasyonu başlatılıyor");
        
        // Formu ve butonları bul
        const form = document.querySelector('form');
        const submitBtn = document.querySelector('button[type="submit"][name="complete"]');
        const saveBtn = document.querySelector('button[type="submit"]');

        if (form) {
            // Form gönderilmeden önce kontrol
            form.addEventListener('submit', function(e) {
                // Zorunlu alanlar dolduruldu mu kontrolü
                const root_cause1 = document.getElementById('root_cause1');
                const root_cause2 = document.getElementById('root_cause2');
                const root_cause3 = document.getElementById('root_cause3');
                const action_plan = document.getElementById('action_plan');
                const deadline = document.getElementById('deadline');

                const errors = [];
                
                if (!root_cause1 || !root_cause1.value.trim()) {
                    errors.push('1. Kök Neden alanı zorunludur.');
                }
                if (!root_cause2 || !root_cause2.value.trim()) {
                    errors.push('2. Kök Neden alanı zorunludur.');
                }
                if (!root_cause3 || !root_cause3.value.trim()) {
                    errors.push('3. Kök Neden alanı zorunludur.');
                }
                if (!action_plan || !action_plan.value.trim()) {
                    errors.push('Aksiyon Planı alanı zorunludur.');
                }
                if (!deadline || !deadline.value) {
                    errors.push('Termin Tarihi alanı zorunludur.');
                }

                if (errors.length > 0) {
                    e.preventDefault();
                    showFormErrors(errors);
                }
            });
        }
    }
}

// Form hatalarını göster
function showFormErrors(errors) {
    // Mevcut hata mesajlarını temizle
    const existingAlerts = document.querySelectorAll('.alert-danger');
    existingAlerts.forEach(alert => alert.remove());
    
    // Yeni hata mesajını oluştur
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
    alertDiv.role = 'alert';
    
    let errorHtml = '<strong>Lütfen aşağıdaki hataları düzeltin:</strong><ul>';
    errors.forEach(error => {
        errorHtml += `<li>${error}</li>`;
    });
    errorHtml += '</ul>';
    
    alertDiv.innerHTML = errorHtml + 
        '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Kapat"></button>';
    
    // Formu bul ve başına hata mesajını ekle
    const form = document.querySelector('form');
    if (form) {
        form.prepend(alertDiv);
        
        // Sayfayı hata mesajına kaydır
        alertDiv.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Yükleme ekranını gizle
    hideLoader();
}

// Yükleme ekranı işlemleri
function initLoaderOverlay() {
    const loaderOverlay = document.getElementById('loader-overlay');
    if (!loaderOverlay) return;
    
    // Sayfa yüklenildiğinde yükleme ekranını gizle
    hideLoader();
}

// Yükleme ekranını göster
function showLoader() {
    const loaderOverlay = document.getElementById('loader-overlay');
    if (loaderOverlay) {
        loaderOverlay.classList.add('show');
    }
}

// Yükleme ekranını gizle
function hideLoader() {
    const loaderOverlay = document.getElementById('loader-overlay');
    if (loaderOverlay) {
        loaderOverlay.classList.remove('show');
    }
}

// Form gönderimlerini optimize et
function optimizeForms() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        // Arama formları ve no-loader sınıfı içeren formlar hariç
        if (!form.classList.contains('search-form') && !form.classList.contains('no-loader')) {
            form.addEventListener('submit', function(e) {
                if (form.checkValidity()) {
                    showLoader();
                    
                    // Submit butonlarını devre dışı bırak
                    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
                    submitButtons.forEach(button => {
                        button.disabled = true;
                    });
                }
            });
        }
    });
    
    // Submit butonları için olay dinleyicileri ekle
    const submitButtons = document.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitButtons.forEach(button => {
        button.addEventListener('click', function() {
            const form = this.closest('form');
            if (form && !form.classList.contains('search-form') && !form.classList.contains('no-loader')) {
                // Double-click'i önlemek için butonu devre dışı bırak
                setTimeout(() => {
                    if (form.checkValidity()) {
                        this.disabled = true;
                        showLoader();
                    }
                }, 10);
            }
        });
    });
}

// DÖF işlemi bağlantıları için yükleme ekranı ayarla
function setupDofActionLinks() {
    // DÖF detay ve işlem sayfalarındaki butonlar
    const dofActionLinks = document.querySelectorAll('a.btn:not(.no-loader)');
    dofActionLinks.forEach(link => {
        // DÖF işlemi bağlantılarını kontrol et
        if (link.href.includes('/dof/') && 
            (link.href.includes('/review') || 
             link.href.includes('/resolve') || 
             link.href.includes('/close') || 
             link.href.includes('/detail') || 
             link.href.includes('/edit'))) {
            
            // Önceden yükleme işlemi (Pre-fetching)
            if (link.classList.contains('prefetch')) {
                const prefetchLink = document.createElement('link');
                prefetchLink.rel = 'prefetch';
                prefetchLink.href = link.href;
                document.head.appendChild(prefetchLink);
            }
            
            link.addEventListener('click', function(e) {
                // CTRL veya CMD tuşu ile tıklamayı kontrol et (yeni sekmede açma)
                if (!e.ctrlKey && !e.metaKey) {
                    showLoader();
                }
            });
        }
    });
}

// Form ön belleğe alma (sessionstorage) - formdaki verilerin kaybolanı önlemek için
function setupFormCaching() {
    const forms = document.querySelectorAll('form:not(.no-cache)');
    
    forms.forEach(form => {
        const formId = form.id || form.action;
        if (!formId) return;
        
        // Form alan girişlerini dinle ve depolama
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            // Şifre alanlarını ön belleğe alma
            if (input.type === 'password' || input.type === 'file') return;
            
            // İlk yükleme esnasında önbellekten verileri al
            if (sessionStorage.getItem(`${formId}_${input.name}`)) {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = sessionStorage.getItem(`${formId}_${input.name}`) === 'true';
                } else {
                    input.value = sessionStorage.getItem(`${formId}_${input.name}`);
                    // Select2 için güncelleme tetikle
                    if (input.classList.contains('select2-hidden-accessible')) {
                        $(input).trigger('change');
                    }
                }
            }
            
            // Değişiklikleri dinle ve ön belleğe al
            input.addEventListener('change', function() {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    sessionStorage.setItem(`${formId}_${input.name}`, input.checked);
                } else {
                    sessionStorage.setItem(`${formId}_${input.name}`, input.value);
                }
            });
            
            // Metin alanları için daha sık depolama
            if (input.tagName === 'TEXTAREA' || input.type === 'text') {
                input.addEventListener('input', function() {
                    sessionStorage.setItem(`${formId}_${input.name}`, input.value);
                });
            }
        });
        
        // Form gönderildiğinde ön belleği temizle
        form.addEventListener('submit', function() {
            if (!form.classList.contains('keep-cache')) {
                clearFormCache(formId);
            }
        });
    });
}

// Form ön belleğini temizle
function clearFormCache(formId) {
    const keysToRemove = [];
    for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i);
        if (key.startsWith(`${formId}_`)) {
            keysToRemove.push(key);
        }
    }
    
    keysToRemove.forEach(key => sessionStorage.removeItem(key));
}

// Select2 performans optimizasyonu
function optimizeSelect2() {
    // Sayfada select2 varsa yükle
    if (document.querySelector('.select2')) {
        // Minimize DOM etkileşimlerini azaltmak için tek seferde uygula
        $('.select2').each(function(){
            const select = $(this);
            const minItems = select.data('min-items') || 15;
            
            select.select2({
                theme: 'bootstrap4',
                language: 'tr',
                width: '100%',
                minimumResultsForSearch: minItems, // az seçenekli listelerde arama özelliğini kapat
                delay: 250, // arama için gecikme süresi
                dropdownCssClass: 'select2-dropdown-optimize',
                placeholder: select.data('placeholder') || null
            });
        });
    }
}

// Form girişlerini hızlandır
function accelerateFormInputs() {
    const textareas = document.querySelectorAll('textarea:not(.no-resize)');
    
    // Textarea otomatik boyutlandırma
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Başlangıçta tetikle
        if (textarea.value) {
            textarea.dispatchEvent(new Event('input'));
        }
    });
    
    // Dosya yükleme iyileştirmesi
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Dosya boyutu kontrolü
            const maxSize = this.dataset.maxSize || 16 * 1024 * 1024; // varsayılan 16MB
            let totalSize = 0;
            
            for (let i = 0; i < this.files.length; i++) {
                totalSize += this.files[i].size;
            }
            
            // Boyut kontrollerini browser tarafında yap
            if (totalSize > maxSize) {
                alert(`Dosya boyutu çok büyük. En fazla ${Math.round(maxSize / (1024 * 1024))}MB olabilir.`);
                this.value = ''; // Dosya seçimini temizle
                return;
            }
        });
    });
}
