// DÖF Yönetim Sistemi - Ana JavaScript Dosyası

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar aktif link
    setActiveSidebarLink();
    
    // Bildirimler modülü
    initNotifications();
    
    // DataTables entegrasyonu
    initDataTables();
    
    // Tarih seçicileri
    initDatePickers();
    
    // Select2 entegrasyonu
    initSelect2();
    
    // Form doğrulama
    initFormValidation();
    
    // Grafikler
    initCharts();
    
    // Tooltips
    initTooltips();
});

// Sidebar'daki aktif linki işaretle
function setActiveSidebarLink() {
    const currentUrl = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar .nav-link');
    
    sidebarLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentUrl || currentUrl.startsWith(href) && href !== '/') {
            link.classList.add('active');
        }
    });
}

// Bildirimler modülü
function initNotifications() {
    const notificationButton = document.getElementById('notification-button');
    const notificationList = document.getElementById('notification-list');
    const notificationBadge = document.getElementById('notification-badge');
    const notificationMarkAllRead = document.getElementById('notification-mark-all-read');
    
    if (!notificationButton || !notificationList) return; // Exit if notification elements don't exist
    
    // Bildirimleri yükle
    function loadNotifications() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(data => {
                if (!notificationList) return; // Exit if notification list doesn't exist
                
                notificationList.innerHTML = '';
                
                if (data.length === 0) {
                    notificationList.innerHTML = '<div class="dropdown-item text-center">Bildirim bulunmamaktadır</div>';
                    if (notificationBadge) {
                        notificationBadge.style.display = 'none';
                    }
                    return;
                }
                
                if (notificationBadge) {
                    notificationBadge.style.display = 'inline-block';
                    notificationBadge.textContent = data.length;
                }
                
                data.forEach(notification => {
                    const item = document.createElement('a');
                    item.className = 'dropdown-item notification-item unread';
                    item.href = notification.dof_id ? `/dof/${notification.dof_id}` : '#';
                    item.dataset.id = notification.id;
                    
                    item.innerHTML = `
                        <div class="d-flex align-items-center">
                            <div class="me-2">
                                <i class="fas fa-bell text-primary"></i>
                            </div>
                            <div class="flex-grow-1">
                                <div>${notification.message}</div>
                                <small class="text-muted notification-time">${notification.created_at}</small>
                            </div>
                        </div>
                    `;
                    
                    item.addEventListener('click', function(e) {
                        markNotificationRead(notification.id);
                    });
                    
                    notificationList.appendChild(item);
                });
            })
            .catch(error => console.error('Bildirimler yüklenirken hata oluştu:', error));
    }
    
    // Bildirimi okundu olarak işaretle
    function markNotificationRead(notificationId) {
        fetch('/api/notifications/mark-read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ notification_id: notificationId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Bildirim başarıyla işaretlendi, işlem yönlendirmeden dolayı gerekli olmayabilir
            }
        })
        .catch(error => console.error('Bildirim işaretlenirken hata oluştu:', error));
    }
    
    // Tüm bildirimleri okundu olarak işaretle
    if (notificationMarkAllRead) {
        notificationMarkAllRead.addEventListener('click', function(e) {
            e.preventDefault();
            
            fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadNotifications(); // Bildirimleri yeniden yükle
                    
                    // Başarı mesajı göster
                    showAlert('success', 'Tüm bildirimler okundu olarak işaretlendi');
                }
            })
            .catch(error => console.error('Bildirimler işaretlenirken hata oluştu:', error));
        });
    }
    
    // İlk yükleme
    loadNotifications();
    
    // Periyodik yenileme
    setInterval(loadNotifications, 60000); // Her 1 dakikada bir yenile
}

// DataTables entegrasyonu
function initDataTables() {
    // Tüm mevcut DataTables tablolarını temizle ve yok et
    $('.datatable, .datatable-responsive').each(function() {
        if ($.fn.DataTable.isDataTable(this)) {
            $(this).DataTable().destroy();
        }
    });

    // Boşta kalınta kalan DataTable objeleri için CSS sıfıflarını temizle
    $('.dataTable').removeClass('dataTable');
    
    // Şimdi tabloları yeniden başlat
    $('.datatable').DataTable({
        responsive: true,
        language: {
            url: '//cdn.datatables.net/plug-ins/1.10.25/i18n/Turkish.json'
        },
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Tümü"]],
        pageLength: 10
    });
    
    $('.datatable-responsive').DataTable({
        responsive: true,
        language: {
            url: '//cdn.datatables.net/plug-ins/1.10.25/i18n/Turkish.json'
        },
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Tümü"]],
        pageLength: 10
    });
}

// Tarih seçicileri
function initDatePickers() {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    if (dateInputs.length > 0) {
        dateInputs.forEach(input => {
            // Tarayıcı desteği varsa native kullan
            if (input._flatpickr) return;
            
            const today = new Date().toISOString().split('T')[0];
            if (!input.value) {
                input.value = today;
            }
        });
    }
}

// Select2 entegrasyonu
function initSelect2() {
    const select2Elements = document.querySelectorAll('.select2');
    
    if (select2Elements.length > 0 && typeof $.fn.select2 !== 'undefined') {
        select2Elements.forEach(select => {
            $(select).select2({
                theme: 'bootstrap4',
                language: 'tr',
                width: '100%'
            });
        });
    }
    
    // AJAX ile kullanıcı araması
    const userLookupElements = document.querySelectorAll('.user-lookup');
    
    if (userLookupElements.length > 0 && typeof $.fn.select2 !== 'undefined') {
        userLookupElements.forEach(select => {
            $(select).select2({
                theme: 'bootstrap4',
                language: 'tr',
                width: '100%',
                ajax: {
                    url: '/api/user-lookup',
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return {
                            q: params.term
                        };
                    },
                    processResults: function(data) {
                        return {
                            results: data
                        };
                    },
                    cache: true
                },
                minimumInputLength: 2,
                placeholder: 'Kullanıcı ara...'
            });
        });
    }
    
    // AJAX ile departman araması
    const departmentLookupElements = document.querySelectorAll('.department-lookup');
    
    if (departmentLookupElements.length > 0 && typeof $.fn.select2 !== 'undefined') {
        departmentLookupElements.forEach(select => {
            $(select).select2({
                theme: 'bootstrap4',
                language: 'tr',
                width: '100%',
                ajax: {
                    url: '/api/department-lookup',
                    dataType: 'json',
                    delay: 250,
                    data: function(params) {
                        return {
                            q: params.term
                        };
                    },
                    processResults: function(data) {
                        return {
                            results: data
                        };
                    },
                    cache: true
                },
                minimumInputLength: 2,
                placeholder: 'Departman ara...'
            });
        });
    }
}

// Form doğrulama
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// Grafikler
function initCharts() {
    // DÖF Durumları Pasta Grafiği
    const dofStatusChart = document.getElementById('dofStatusChart');
    if (dofStatusChart) {
        fetch('/api/chart-data/dof-status')
            .then(response => response.json())
            .then(data => {
                new Chart(dofStatusChart, {
                    type: 'pie',
                    data: data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right'
                            },
                            title: {
                                display: true,
                                text: 'DÖF Durumları'
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Grafik verisi yüklenirken hata oluştu:', error));
    }
    
    // Aylık DÖF Sayıları Çizgi Grafiği
    const monthlyDofsChart = document.getElementById('monthlyDofsChart');
    if (monthlyDofsChart) {
        fetch('/api/chart-data/monthly-dofs')
            .then(response => response.json())
            .then(data => {
                new Chart(monthlyDofsChart, {
                    type: 'line',
                    data: data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            title: {
                                display: true,
                                text: 'Aylık DÖF Sayıları'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Grafik verisi yüklenirken hata oluştu:', error));
    }
    
    // Departman İstatistikleri Bar Grafiği
    const departmentStatsChart = document.getElementById('departmentStatsChart');
    if (departmentStatsChart) {
        fetch('/api/chart-data/department-stats')
            .then(response => response.json())
            .then(data => {
                new Chart(departmentStatsChart, {
                    type: 'bar',
                    data: data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            },
                            title: {
                                display: true,
                                text: 'Departman DÖF Sayıları'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Grafik verisi yüklenirken hata oluştu:', error));
    }
}

// Tooltips
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// CSRF Token
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

// Uyarı mesajı göster
function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Kapat"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // 5 saniye sonra otomatik kapat
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => {
            alert.remove();
        }, 300);
    }, 5000);
}
