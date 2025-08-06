# DOF Yönetim Sistemi (Düzeltici ve Önleyici Faaliyet)

## 📋 Proje Hakkında

DOF (Düzeltici ve Önleyici Faaliyet) Yönetim Sistemi, organizasyonlarda kalite yönetimi süreçlerini dijitalleştirmek için geliştirilmiş kapsamlı bir web uygulamasıdır. Sistem, ISO 9001 standartlarına uygun olarak düzeltici ve önleyici faaliyetlerin takibini, yönetimini ve raporlanmasını sağlar.

## 🚀 Temel Özellikler

### 📊 Dashboard ve İzleme
- **Gerçek Zamanlı Durum Takibi**: DOF sayıları ve durumlarının anlık görünümü
- **Departman Bazlı İstatistikler**: Her departmanın DOF performansı
- **Grafik ve Raporlar**: Trend analizi ve detaylı raporlama
- **Hızlı Erişim Widget'ları**: Önemli metriklere kolay erişim

### 🔄 DOF Yaşam Döngüsü Yönetimi

#### 1. DOF Oluşturma
- **Detaylı Form Yapısı**: Kapsamlı bilgi girişi
- **Dosya Ekleme**: Kanıt ve destek dokümanları
- **Otomatik Kod Ataması**: Sistem tarafından benzersiz kod üretimi
- **Kaynak Belirleme**: İç/dış müşteri, tedarikçi vb.

#### 2. Kaynak Analizi ve Onay
- **Departman Yöneticisi Onayı**: İlk değerlendirme süreci
- **Kök Neden Analizi**: Sorunun temel nedenlerinin belirlenmesi
- **Risk Değerlendirmesi**: Etki ve olasılık analizi
- **Revizyon Talebi**: Eksik bilgiler için geri bildirim

#### 3. Aksiyon Planı Geliştirme
- **Çok Adımlı Plan Oluşturma**: Detaylı aksiyon planları
- **Sorumlu Atama**: Her adım için sorumlu kişi belirleme
- **Zaman Çizelgesi**: Başlangıç ve bitiş tarihleri
- **Öncelik Seviyeleri**: Düşük, orta, yüksek öncelik

#### 4. Uygulama ve Takip
- **Modal Tabanlı Tamamlama**: Detaylı tamamlama süreci
- **Kanıt Dosyası Yükleme**: PDF, resim, Office dokümanları
- **İlerleme Takibi**: Her adımın durumu ve ilerlemesi
- **Otomatik Bildirimler**: E-posta ve sistem bildirimleri

#### 5. Kalite Kontrolü ve Kapatma
- **Kalite Departmanı Onayı**: Son kontrol süreci
- **Etkinlik Değerlendirmesi**: Uygulanan aksiyonların değerlendirilmesi
- **Dokümantasyon**: Tüm sürecin kayıt altına alınması

### 👥 Kullanıcı Rolleri ve Yetkileri

#### 🔧 Sistem Yöneticisi (Admin)
- Tüm sistem ayarları ve konfigürasyonlar
- Kullanıcı ve departman yönetimi
- E-posta ayarları ve bildirim konfigürasyonu
- Sistem logları ve izleme

#### 👨‍💼 Kalite Yöneticisi (Quality Manager)
- Tüm DOF'lara erişim ve yönetim
- Kalite kontrol ve onay süreçleri
- Raporlama ve analiz
- Sistem geneli istatistikler

#### 📋 Departman Yöneticisi (Department Manager)
- Departman DOF'larını yönetme
- Kaynak analizi ve onay
- Aksiyon planı değerlendirme
- Departman raporları

#### 👤 Standart Kullanıcı (User)
- DOF oluşturma ve güncelleme
- Atanan aksiyonları tamamlama
- Kendi DOF'larını izleme
- Bildirim alma

#### 🎯 Franchise Yöneticisi (Franchise Manager)
- Franchise lokasyonları DOF'larını yönetme
- Bölgesel raporlama
- Çoklu lokasyon koordinasyonu

### 📧 Bildirim ve E-posta Sistemi

#### Otomatik E-posta Bildirimleri
- **DOF Oluşturma**: Yeni DOF bildirimi
- **Durum Değişiklikleri**: Her aşama değişiminde bildirim
- **Gecikme Uyarıları**: Süre aşımı öncesi hatırlatmalar
- **Günlük Raporlar**: Departman bazlı günlük özetler
- **Haftalık Özetler**: Haftalık performans raporları

#### Bildirim Türleri
- **Sistem İçi Bildirimler**: Gerçek zamanlı popup'lar
- **E-posta Bildirimleri**: Detaylı e-posta mesajları
- **Dashboard Uyarıları**: Kritik durumlar için özel uyarılar

### 📈 Raporlama ve Analiz

#### Dashboard Metrikleri
- **Toplam DOF Sayısı**: Sistem geneli DOF istatistikleri
- **Durum Dağılımları**: Açık, kapalı, beklemede DOF'lar
- **Departman Performansı**: Her departmanın başarı oranları
- **Trend Analizleri**: Zaman bazlı performans grafikleri

#### Detaylı Raporlar
- **DOF Listesi**: Filtrelenebilir ve dışa aktarılabilir
- **Performans Raporları**: Departman ve kullanıcı bazlı
- **Zaman Analizi**: Ortalama çözüm süreleri
- **Etkinlik Raporları**: Tamamlanan aksiyonların etkinliği

### 🔍 Arama ve Filtreleme

#### Gelişmiş Arama
- **Metin Tabanlı Arama**: Başlık, açıklama, yorumlarda arama
- **Tarih Aralığı**: Belirli dönemler için filtreleme
- **Durum Filtreleri**: Spesifik durumlar için filtreleme
- **Departman Filtreleri**: Departman bazlı görüntüleme

#### Hızlı Filtreler
- **Benim DOF'larım**: Kullanıcının oluşturduğu DOF'lar
- **Bekleyen Onaylar**: Onay bekleyen DOF'lar
- **Geciken DOF'lar**: Süre aşımına uğrayan DOF'lar
- **Bu Ay Oluşturulan**: Güncel dönem DOF'ları

## 🛠️ Teknik Altyapı

### Backend Teknolojileri
- **Python Flask 2.3+**: Micro web framework
- **SQLAlchemy 2.0+**: ORM ve veritabanı abstraction layer
- **Flask-SQLAlchemy**: Flask-SQLAlchemy extension
- **Flask-Login**: Kullanıcı oturum yönetimi
- **Werkzeug**: WSGI toolkit ve güvenlik utilities
- **SQLite/MySQL**: İlişkisel veritabanı desteği
- **Gunicorn**: Production WSGI HTTP Server
- **APScheduler**: Background job scheduler
- **Jinja2**: Template engine
- **WTForms**: Form validation ve rendering
- **Bcrypt**: Password hashing

### Frontend Teknolojileri
- **HTML5/CSS3**: Semantic markup ve modern styling
- **Bootstrap 5.3**: Responsive CSS framework
- **JavaScript ES6+**: Modern JavaScript features
- **jQuery 3.6+**: DOM manipulation ve AJAX
- **Font Awesome 6**: Vektör ikon kütüphanesi
- **Chart.js 4.0+**: Canvas-based charting
- **Bootstrap Icons**: Additional icon set
- **Popper.js**: Tooltip ve popover positioning

### Dosya Yönetimi ve Depolama
- **Güvenli Dosya Yükleme**: MIME type validation
- **Dosya Boyutu Kontrolü**: Configurable limits (16MB default)
- **Format Desteği**: PDF, JPG, JPEG, PNG, DOCX, XLSX, TXT
- **Dosya Hash Kontrolü**: SHA-256 checksums
- **Unique Filename Generation**: UUID-based naming
- **Path Traversal Protection**: Secure file path handling
- **Virus Scanning Ready**: Integration points for antivirus
- **Compression Support**: Automatic image optimization

### E-posta ve İletişim Sistemi
- **SMTP Protocol**: RFC 5321 compliant
- **TLS/SSL Encryption**: Secure email transmission
- **HTML/Plain Text**: Multi-part email support
- **Email Templates**: Jinja2-based templating
- **Bulk Email**: Queue-based mass mailing
- **Email Tracking**: Delivery status monitoring
- **Bounce Handling**: Failed delivery management
- **Rate Limiting**: Anti-spam protection
- **Email Validation**: RFC 5322 validation

### Güvenlik Altyapısı
- **CSRF Protection**: Cross-Site Request Forgery prevention
- **XSS Protection**: Input sanitization ve output encoding
- **SQL Injection Prevention**: Parameterized queries
- **Session Security**: Secure cookie configuration
- **Password Policy**: Complexity requirements
- **Rate Limiting**: Brute force protection
- **Input Validation**: Server-side validation
- **Content Security Policy**: CSP headers
- **HTTPS Enforcement**: SSL/TLS redirection

### Performans ve Optimizasyon
- **Database Connection Pooling**: SQLAlchemy connection pool
- **Query Optimization**: Indexed queries ve lazy loading
- **Caching Strategy**: Redis-ready caching layer
- **Static File Serving**: Efficient asset delivery
- **Gzip Compression**: Response compression
- **Database Indexing**: Optimized database indices
- **Pagination**: Memory-efficient data loading
- **Background Processing**: Async task processing

### İzleme ve Logging
- **Application Logging**: Structured logging with levels
- **Error Tracking**: Exception handling ve reporting
- **Performance Monitoring**: Response time tracking
- **Audit Trails**: User action logging
- **System Health Checks**: Automated monitoring
- **Log Rotation**: Automatic log file management
- **Metrics Collection**: Custom metrics gathering
- **Debug Tools**: Development debugging utilities

## 🏗️ Sistem Mimarisi

### Mimari Desenler
- **MVC (Model-View-Controller)**: Katmanlı mimari
- **Repository Pattern**: Veri erişim katmanı abstraction
- **Service Layer Pattern**: İş mantığı encapsulation
- **Factory Pattern**: Object creation abstraction
- **Observer Pattern**: Event-driven notifications
- **Strategy Pattern**: Configurable business rules
- **Dependency Injection**: Loose coupling

### Mikroservis Hazırlığı
- **Modular Design**: Service-oriented architecture
- **API-First Approach**: RESTful service design
- **Database per Service**: Isolated data stores
- **Event-Driven Communication**: Async messaging ready
- **Circuit Breaker**: Fault tolerance patterns
- **Health Check Endpoints**: Service monitoring
- **Configuration Management**: External config support

### Caching Stratejisi
- **Application-Level Caching**: In-memory cache
- **Database Query Caching**: SQLAlchemy query cache
- **Session Caching**: User session optimization
- **Static Asset Caching**: Browser cache headers
- **Redis Integration**: Distributed caching ready
- **Cache Invalidation**: Smart cache refresh

## 📁 Proje Yapısı

```
dfdfdf/
├── app.py                 # Ana Flask uygulaması ve factory
├── wsgi.py               # WSGI entry point
├── config.py             # Environment-based configuration
├── models.py             # SQLAlchemy ORM modelleri
├── auth_service.py       # Authentication ve authorization
├── notification_system.py # Event-driven notification system
├── mail_service.py       # SMTP email service
├── utils.py              # Shared utility functions
├── export_utils.py       # Data export ve reporting
├── stats_utils.py        # Statistics ve analytics
├── forms.py              # WTForms form definitions
├── routes/               # Blueprint-based routing
│   ├── __init__.py      # Route registry
│   ├── dof.py           # DOF lifecycle management
│   ├── admin.py         # Administrative functions
│   ├── auth.py          # Authentication routes
│   ├── api.py           # REST API endpoints
│   ├── notifications.py # Notification management
│   └── activity.py      # Activity logging
├── templates/            # Jinja2 template hierarchy
│   ├── layout.html      # Base template with blocks
│   ├── dashboard.html   # Dashboard with widgets
│   ├── dof/             # DOF-specific templates
│   │   ├── create.html  # DOF creation form
│   │   ├── detail.html  # DOF detail view
│   │   ├── list.html    # DOF listing with filters
│   │   └── partials/    # Reusable template components
│   ├── admin/           # Administrative templates
│   ├── email/           # Email template library
│   └── notifications/   # Notification templates
├── static/              # Frontend assets
│   ├── css/            # Stylesheet hierarchy
│   │   ├── custom.css  # Application-specific styles
│   │   └── process-bar.css # Component styles
│   ├── js/             # JavaScript modules
│   │   ├── main.js     # Core application logic
│   │   └── forms.js    # Form validation ve UX
│   └── uploads/        # User-uploaded files
├── migrations/          # Database schema evolution
│   ├── add_email_track.py
│   ├── add_group_manager_role.py
│   └── add_user_department_mapping.py
├── scripts/             # Automation ve maintenance
├── tests/               # Test suite (unit, integration)
├── docs/                # Technical documentation
├── requirements.txt     # Python dependencies with versions
├── requirements-dev.txt # Development dependencies
├── pyproject.toml      # Python project configuration
├── Dockerfile          # Container configuration
├── docker-compose.yml  # Multi-container setup
├── gunicorn_config.py  # Production server config
└── .env.example        # Environment variables template
```

## 🗃️ Database Design Patterns

### Entity Relationship Model
```
Users ||--o{ DOFs : creates
Users ||--o{ Departments : manages
Departments ||--o{ DOFs : assigned_to
DOFs ||--o{ WorkflowSteps : contains
DOFs ||--o{ ActionItems : has
DOFs ||--o{ Comments : has
DOFs ||--o{ Attachments : has
ActionItems ||--o{ ActionAttachments : has
Users ||--o{ Notifications : receives
```

### İndeksleme Stratejisi
```sql
-- Performance critical indices
CREATE INDEX idx_dofs_status ON dofs(status);
CREATE INDEX idx_dofs_assigned_dept ON dofs(assigned_department_id);
CREATE INDEX idx_dofs_creator ON dofs(creator_id);
CREATE INDEX idx_dofs_created_at ON dofs(created_at);
CREATE INDEX idx_workflow_dof_step ON workflow_steps(dof_id, step_type);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read);
CREATE INDEX idx_action_items_responsible ON action_items(responsible_user_id);
CREATE INDEX idx_comments_dof_created ON comments(dof_id, created_at);

-- Composite indices for complex queries
CREATE INDEX idx_dofs_status_dept_created ON dofs(status, assigned_department_id, created_at);
CREATE INDEX idx_workflow_status_assigned ON workflow_steps(status, assigned_user_id);
```

### Database Constraints
```sql
-- Referential integrity
ALTER TABLE dofs ADD CONSTRAINT fk_dofs_creator 
    FOREIGN KEY (creator_id) REFERENCES users(id);
ALTER TABLE dofs ADD CONSTRAINT fk_dofs_department 
    FOREIGN KEY (assigned_department_id) REFERENCES departments(id);

-- Business rule constraints
ALTER TABLE dofs ADD CONSTRAINT chk_dofs_status 
    CHECK (status IN ('draft', 'pending_source_review', 'source_approved', 
                     'pending_action_plan', 'action_plan_approved', 
                     'implementation', 'implementation_completed', 
                     'quality_review', 'closed'));
ALTER TABLE dofs ADD CONSTRAINT chk_dofs_priority 
    CHECK (priority IN ('low', 'medium', 'high'));

-- Data validation
ALTER TABLE users ADD CONSTRAINT chk_users_email 
    CHECK (email LIKE '%@%.%');
ALTER TABLE action_attachments ADD CONSTRAINT chk_file_size 
    CHECK (file_size > 0 AND file_size <= 16777216); -- 16MB
```

## 🚀 Deployment ve DevOps

### Container Orchestration
```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=mysql://user:pass@db:3306/dof
    depends_on:
      - db
      - redis
    volumes:
      - ./static/uploads:/app/static/uploads
      - ./logs:/app/logs

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: dof
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  mysql_data:
  redis_data:
```

### Production Configuration
```python
# gunicorn_config.py
import multiprocessing

bind = "0.0.0.0:5000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 5
preload_app = True
capture_output = True
enable_stdio_inheritance = True

# Logging
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "dof_management_system"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
```

### Environment Configuration
```bash
# .env.production
FLASK_ENV=production
SECRET_KEY=your-very-secure-secret-key-here
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/dof_production

# Email Configuration
MAIL_SERVER=smtp.company.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=dof-system@company.com
MAIL_PASSWORD=secure-app-password

# File Upload
UPLOAD_FOLDER=/app/static/uploads
MAX_CONTENT_LENGTH=16777216

# Redis Cache
REDIS_URL=redis://localhost:6379/0

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
LOG_LEVEL=INFO

# Feature Flags
ENABLE_DAILY_REPORTS=true
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_FILE_UPLOAD=true
```

### Monitoring ve Health Checks
```python
# System health check endpoints
@app.route('/health')
def health_check():
    """Basic health check endpoint"""
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}

@app.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with dependencies"""
    checks = {
        'database': check_database_connection(),
        'redis': check_redis_connection(),
        'email': check_email_service(),
        'disk_space': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    status = 'healthy' if all(checks.values()) else 'unhealthy'
    return {'status': status, 'checks': checks}

@app.route('/metrics')
def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics_data = {
        'dof_total': get_total_dof_count(),
        'active_users': get_active_user_count(),
        'email_queue_size': get_email_queue_size(),
        'response_time_avg': get_average_response_time()
    }
    return render_template('metrics.txt', metrics=metrics_data)
```

### Backup ve Recovery
```bash
#!/bin/bash
# backup_script.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Database backup
mysqldump -h localhost -u backup_user -p dof_production > $BACKUP_DIR/dof_db_$DATE.sql

# Files backup
tar -czf $BACKUP_DIR/dof_files_$DATE.tar.gz /app/static/uploads

# Logs backup
tar -czf $BACKUP_DIR/dof_logs_$DATE.tar.gz /app/logs

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "dof_*" -mtime +30 -delete

# Upload to cloud storage
aws s3 cp $BACKUP_DIR/dof_db_$DATE.sql s3://company-backups/dof/
aws s3 cp $BACKUP_DIR/dof_files_$DATE.tar.gz s3://company-backups/dof/
```

### Performance Tuning
```python
# Database optimization settings
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'pool_timeout': 30,
    'max_overflow': 30,
    'echo': False,  # Set to True for SQL debugging
    'echo_pool': False,
    'connect_args': {
        'charset': 'utf8mb4',
        'connect_timeout': 60,
        'read_timeout': 30,
        'write_timeout': 30,
    }
}

# Redis configuration for caching
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'dof_cache:',
}

# Session configuration
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_KEY_PREFIX = 'dof_session:'
PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
```

## 🗄️ Veritabanı Şeması

### Temel Tablolar

#### Users (Kullanıcılar)
```sql
- id (Primary Key)
- username (Unique)
- email (Unique)
- password_hash
- role (admin, quality_manager, department_manager, user, franchise_manager)
- department_id (Foreign Key)
- is_active
- created_at
```

#### Departments (Departmanlar)
```sql
- id (Primary Key)
- name (Unique)
- code
- manager_id (Foreign Key -> Users)
- is_active
- created_at
```

#### DOFs (Düzeltici/Önleyici Faaliyetler)
```sql
- id (Primary Key)
- dof_code (Unique)
- title
- description
- source_type (internal_customer, external_customer, supplier, etc.)
- source_description
- creator_id (Foreign Key -> Users)
- assigned_department_id (Foreign Key -> Departments)
- status (draft, pending_source_review, source_approved, etc.)
- priority (low, medium, high)
- due_date
- created_at
- updated_at
```

#### WorkflowSteps (İş Akışı Adımları)
```sql
- id (Primary Key)
- dof_id (Foreign Key -> DOFs)
- step_type (source_review, action_plan, implementation, etc.)
- status (pending, in_progress, completed, rejected)
- assigned_user_id (Foreign Key -> Users)
- completed_at
- notes
```

#### ActionItems (Aksiyon Maddeleri)
```sql
- id (Primary Key)
- dof_id (Foreign Key -> DOFs)
- description
- responsible_user_id (Foreign Key -> Users)
- due_date
- status (pending, in_progress, completed)
- completion_notes
- completed_at
```

#### ActionAttachments (Aksiyon Ekleri)
```sql
- id (Primary Key)
- action_item_id (Foreign Key -> ActionItems)
- filename
- original_filename
- file_size
- file_type
- uploaded_by (Foreign Key -> Users)
- uploaded_at
```

#### Comments (Yorumlar)
```sql
- id (Primary Key)
- dof_id (Foreign Key -> DOFs)
- user_id (Foreign Key -> Users)
- comment_text
- created_at
```

#### Notifications (Bildirimler)
```sql
- id (Primary Key)
- user_id (Foreign Key -> Users)
- dof_id (Foreign Key -> DOFs)
- type (dof_created, status_changed, due_soon, etc.)
- title
- message
- is_read
- created_at
```

## 🚦 DOF Durum Akışı

```
1. Taslak (Draft)
   ↓
2. Kaynak İncelemesi Bekliyor (Pending Source Review)
   ↓
3. Kaynak Onaylandı (Source Approved) / Plan Revizyonu Talep Edildi (Plan Revision Requested)
   ↓
4. Aksiyon Planı Bekleniyor (Pending Action Plan)
   ↓
5. Aksiyon Planı Onaylandı (Action Plan Approved) / Plan Revizyonu Talep Edildi
   ↓
6. Uygulama (Implementation)
   ↓
7. Uygulama Tamamlandı (Implementation Completed)
   ↓
8. Kalite İncelemesi (Quality Review)
   ↓
9. Kapalı (Closed) / Revizyon Gerekli (Revision Required)
```

## 📋 Kurulum ve Çalıştırma

### Gereksinimler
- Python 3.8+
- SQLite (veya MySQL)
- SMTP E-posta Sunucusu

### Adım Adım Kurulum

1. **Projeyi klonlayın**
```bash
git clone <repository-url>
cd dof-management-system
```

2. **Sanal ortam oluşturun**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

3. **Bağımlılıkları yükleyin**
```bash
pip install -r requirements.txt
```

4. **Veritabanını oluşturun**
```bash
python models.py
```

5. **Yönetici kullanıcısı oluşturun**
```bash
python create_admin.py
```

6. **Departmanları ayarlayın**
```bash
python setup_departments.py
```

7. **E-posta ayarlarını yapılandırın**
```bash
python setup_email_settings.py
```

8. **Uygulamayı çalıştırın**
```bash
python app.py
```

### Konfigürasyon

#### config.py
```python
# Temel ayarlar
SECRET_KEY = 'your-secret-key'
DATABASE_URL = 'sqlite:///dof.db'

# E-posta ayarları
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'

# Dosya yükleme ayarları
UPLOAD_FOLDER = 'static/uploads'
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'xlsx'}
```

### Üretim Ortamı

#### Gunicorn ile çalıştırma
```bash
gunicorn -c gunicorn_config.py wsgi:app
```

#### Docker ile çalıştırma
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-c", "gunicorn_config.py", "wsgi:app"]
```

## 🔧 Geliştirme Araçları

### Test Scriptleri
- `create_test_dof.py`: Test DOF'u oluşturma
- `test_email.py`: E-posta sistemi testi
- `test_notifications.py`: Bildirim sistemi testi
- `debug_logs.py`: Sistem loglarını inceleme

### Bakım Scriptleri
- `clear_dofs.py`: DOF'ları temizleme (güvenli)
- `fix_department_assignments.py`: Departman atamalarını düzeltme
- `sync_departments.py`: Departman senkronizasyonu
- `system_health_check.py`: Sistem sağlık kontrolü

### Migration Scriptleri
- `migrate_to_mysql.py`: MySQL'e geçiş
- `add_dof_code_column.py`: DOF kod sütunu ekleme
- `create_email_track_table.py`: E-posta izleme tablosu

## 📊 İzleme ve Loglama

### Log Türleri
- **Uygulama Logları**: Genel sistem işlemleri
- **E-posta Logları**: E-posta gönderim durumu
- **Hata Logları**: Sistem hataları ve istisnalar
- **Kullanıcı Aktivite Logları**: Kullanıcı işlemleri

### İzleme Metrikleri
- DOF oluşturma oranları
- Ortalama çözüm süreleri
- Departman performansları
- E-posta gönderim başarı oranları
- Sistem yanıt süreleri

## 🔐 Güvenlik

### Kimlik Doğrulama
- Güvenli parola hash'leme (Werkzeug)
- Oturum yönetimi (Flask-Session)
- CSRF koruması
- Rate limiting

### Dosya Güvenliği
- Dosya türü doğrulaması
- Dosya boyutu sınırlaması
- Güvenli dosya isimlendirme
- Zararlı dosya kontrolü

### Veri Güvenliği
- SQL injection koruması (SQLAlchemy ORM)
- XSS koruması (Jinja2 auto-escaping)
- Secure headers
- Input validation

## 🔄 API Dokumentasyonu

### REST API Endpoints

#### Authentication
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "jwt-token-here",
  "user": {
    "id": 1,
    "username": "user@example.com",
    "role": "department_manager",
    "department": "IT"
  }
}
```

#### DOF Management APIs

##### GET /api/dofs
```http
GET /api/dofs?page=1&per_page=10&status=open&department=IT
Authorization: Bearer jwt-token

Response:
{
  "dofs": [
    {
      "id": 1,
      "dof_code": "DOF-2024-001",
      "title": "Server Performance Issue",
      "status": "implementation",
      "priority": "high",
      "creator": {
        "id": 2,
        "username": "john.doe@company.com"
      },
      "assigned_department": {
        "id": 1,
        "name": "IT Department"
      },
      "created_at": "2024-01-15T10:30:00Z",
      "due_date": "2024-02-15T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 25,
    "pages": 3
  }
}
```

##### POST /api/dofs
```http
POST /api/dofs
Content-Type: application/json
Authorization: Bearer jwt-token

{
  "title": "New Quality Issue",
  "description": "Detailed description of the issue",
  "source_type": "internal_customer",
  "source_description": "Customer complaint details",
  "assigned_department_id": 2,
  "priority": "medium",
  "due_date": "2024-03-01T00:00:00Z"
}

Response:
{
  "id": 26,
  "dof_code": "DOF-2024-026",
  "status": "draft",
  "created_at": "2024-01-20T14:15:00Z",
  ...
}
```

##### GET /api/dofs/{id}
```http
GET /api/dofs/1
Authorization: Bearer jwt-token

Response:
{
  "id": 1,
  "dof_code": "DOF-2024-001",
  "title": "Server Performance Issue",
  "description": "Detailed description...",
  "status": "implementation",
  "workflow_steps": [
    {
      "id": 1,
      "step_type": "source_review",
      "status": "completed",
      "assigned_user": {
        "id": 3,
        "username": "manager@company.com"
      },
      "completed_at": "2024-01-16T09:00:00Z",
      "notes": "Source analysis completed"
    }
  ],
  "action_items": [
    {
      "id": 1,
      "description": "Upgrade server hardware",
      "responsible_user": {
        "id": 4,
        "username": "tech@company.com"
      },
      "status": "in_progress",
      "due_date": "2024-02-01T00:00:00Z"
    }
  ],
  "comments": [
    {
      "id": 1,
      "user": {
        "id": 2,
        "username": "john.doe@company.com"
      },
      "comment_text": "Issue identified and documented",
      "created_at": "2024-01-15T11:00:00Z"
    }
  ],
  "attachments": [
    {
      "id": 1,
      "filename": "error_log.txt",
      "file_size": 2048,
      "uploaded_by": {
        "id": 2,
        "username": "john.doe@company.com"
      },
      "uploaded_at": "2024-01-15T10:45:00Z"
    }
  ]
}
```

##### PUT /api/dofs/{id}
```http
PUT /api/dofs/1
Content-Type: application/json
Authorization: Bearer jwt-token

{
  "title": "Updated title",
  "priority": "high",
  "due_date": "2024-02-28T00:00:00Z"
}

Response:
{
  "id": 1,
  "updated_at": "2024-01-20T15:30:00Z",
  ...
}
```

##### POST /api/dofs/{id}/actions
```http
POST /api/dofs/1/actions
Content-Type: application/json
Authorization: Bearer jwt-token

{
  "description": "Implement monitoring system",
  "responsible_user_id": 5,
  "due_date": "2024-02-10T00:00:00Z"
}

Response:
{
  "id": 15,
  "description": "Implement monitoring system",
  "status": "pending",
  "created_at": "2024-01-20T16:00:00Z"
}
```

##### POST /api/dofs/{id}/comments
```http
POST /api/dofs/1/comments
Content-Type: application/json
Authorization: Bearer jwt-token

{
  "comment_text": "Progress update: 50% completed"
}

Response:
{
  "id": 25,
  "comment_text": "Progress update: 50% completed",
  "created_at": "2024-01-20T16:30:00Z"
}
```

#### Workflow Management APIs

##### POST /api/dofs/{id}/workflow/approve
```http
POST /api/dofs/1/workflow/approve
Content-Type: application/json
Authorization: Bearer jwt-token

{
  "step_type": "source_review",
  "notes": "Source analysis approved"
}

Response:
{
  "workflow_step": {
    "id": 10,
    "status": "completed",
    "completed_at": "2024-01-20T17:00:00Z"
  },
  "dof_status": "source_approved"
}
```

##### POST /api/dofs/{id}/workflow/reject
```http
POST /api/dofs/1/workflow/reject
Content-Type: application/json
Authorization: Bearer jwt-token

{
  "step_type": "action_plan",
  "notes": "Action plan needs more detail"
}

Response:
{
  "workflow_step": {
    "id": 11,
    "status": "rejected",
    "completed_at": "2024-01-20T17:15:00Z"
  },
  "dof_status": "plan_revision_requested"
}
```

#### File Upload APIs

##### POST /api/dofs/{id}/attachments
```http
POST /api/dofs/1/attachments
Content-Type: multipart/form-data
Authorization: Bearer jwt-token

files: [file1.pdf, file2.jpg]

Response:
{
  "uploaded_files": [
    {
      "id": 20,
      "filename": "evidence_file_abc123.pdf",
      "original_filename": "file1.pdf",
      "file_size": 1024576,
      "file_type": "application/pdf"
    },
    {
      "id": 21,
      "filename": "evidence_image_def456.jpg",
      "original_filename": "file2.jpg",
      "file_size": 512288,
      "file_type": "image/jpeg"
    }
  ]
}
```

#### Statistics APIs

##### GET /api/stats/dashboard
```http
GET /api/stats/dashboard
Authorization: Bearer jwt-token

Response:
{
  "total_dofs": 125,
  "status_counts": {
    "draft": 5,
    "pending_source_review": 8,
    "source_approved": 3,
    "pending_action_plan": 6,
    "action_plan_approved": 4,
    "implementation": 12,
    "implementation_completed": 7,
    "quality_review": 5,
    "closed": 75
  },
  "priority_distribution": {
    "low": 45,
    "medium": 55,
    "high": 25
  },
  "department_stats": [
    {
      "department": "IT",
      "total": 35,
      "open": 8,
      "closed": 27
    },
    {
      "department": "Quality",
      "total": 28,
      "open": 5,
      "closed": 23
    }
  ],
  "recent_activity": [
    {
      "dof_id": 1,
      "dof_code": "DOF-2024-001",
      "action": "status_changed",
      "new_status": "implementation",
      "timestamp": "2024-01-20T16:45:00Z"
    }
  ]
}
```

##### GET /api/stats/department/{id}
```http
GET /api/stats/department/1?period=30days
Authorization: Bearer jwt-token

Response:
{
  "department": {
    "id": 1,
    "name": "IT Department"
  },
  "period": "30days",
  "metrics": {
    "total_dofs": 35,
    "created_this_period": 8,
    "closed_this_period": 6,
    "average_resolution_time": 12.5,
    "overdue_count": 2
  },
  "trend_data": [
    {
      "date": "2024-01-01",
      "created": 2,
      "closed": 1
    },
    {
      "date": "2024-01-02",
      "created": 1,
      "closed": 2
    }
  ]
}
```

#### Error Responses
```http
HTTP/1.1 400 Bad Request
{
  "error": "validation_error",
  "message": "Validation failed",
  "details": {
    "title": ["This field is required"],
    "due_date": ["Invalid date format"]
  }
}

HTTP/1.1 401 Unauthorized
{
  "error": "authentication_required",
  "message": "Valid authentication token required"
}

HTTP/1.1 403 Forbidden
{
  "error": "insufficient_permissions",
  "message": "You don't have permission to access this resource"
}

HTTP/1.1 404 Not Found
{
  "error": "resource_not_found",
  "message": "DOF with id 999 not found"
}

HTTP/1.1 500 Internal Server Error
{
  "error": "internal_server_error",
  "message": "An unexpected error occurred",
  "request_id": "req_abc123def456"
}
```

## 🧪 Test Stratejileri

### Unit Testing
```python
# tests/test_models.py
import pytest
from app import create_app, db
from models import User, DOF, Department

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_dof_creation(app):
    """Test DOF model creation and validation"""
    with app.app_context():
        user = User(username='test@example.com', email='test@example.com')
        dept = Department(name='Test Dept', code='TEST')
        db.session.add_all([user, dept])
        db.session.commit()
        
        dof = DOF(
            title='Test DOF',
            description='Test description',
            creator_id=user.id,
            assigned_department_id=dept.id
        )
        db.session.add(dof)
        db.session.commit()
        
        assert dof.id is not None
        assert dof.dof_code.startswith('DOF-')
        assert dof.status == 'draft'

def test_workflow_progression(app):
    """Test DOF workflow state transitions"""
    with app.app_context():
        # Setup test data
        dof = create_test_dof()
        
        # Test valid state transitions
        assert dof.can_transition_to('pending_source_review')
        dof.status = 'pending_source_review'
        assert dof.status == 'pending_source_review'
        
        # Test invalid state transitions
        assert not dof.can_transition_to('closed')
```

### Integration Testing
```python
# tests/test_api.py
def test_dof_api_crud(client, auth_headers):
    """Test complete DOF CRUD operations via API"""
    
    # Create DOF
    dof_data = {
        'title': 'API Test DOF',
        'description': 'Created via API test',
        'source_type': 'internal_customer',
        'assigned_department_id': 1,
        'priority': 'medium'
    }
    
    response = client.post('/api/dofs', 
                          json=dof_data, 
                          headers=auth_headers)
    assert response.status_code == 201
    dof_id = response.json['id']
    
    # Read DOF
    response = client.get(f'/api/dofs/{dof_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['title'] == 'API Test DOF'
    
    # Update DOF
    update_data = {'priority': 'high'}
    response = client.put(f'/api/dofs/{dof_id}', 
                         json=update_data, 
                         headers=auth_headers)
    assert response.status_code == 200
    assert response.json['priority'] == 'high'
    
    # Delete DOF (if implemented)
    response = client.delete(f'/api/dofs/{dof_id}', headers=auth_headers)
    assert response.status_code == 204

def test_workflow_api(client, auth_headers):
    """Test workflow operations via API"""
    dof_id = create_test_dof_via_api(client, auth_headers)
    
    # Approve source review
    response = client.post(f'/api/dofs/{dof_id}/workflow/approve',
                          json={
                              'step_type': 'source_review',
                              'notes': 'Approved by test'
                          },
                          headers=auth_headers)
    assert response.status_code == 200
    assert response.json['dof_status'] == 'source_approved'
```

### End-to-End Testing
```python
# tests/test_e2e.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestDOFWorkflow:
    
    def setup_method(self):
        self.driver = webdriver.Chrome()
        self.driver.implicitly_wait(10)
    
    def teardown_method(self):
        self.driver.quit()
    
    def test_complete_dof_workflow(self):
        """Test complete DOF workflow from creation to closure"""
        
        # Login
        self.login_as_user('test@example.com', 'password')
        
        # Create DOF
        self.create_dof({
            'title': 'E2E Test DOF',
            'description': 'Created by E2E test',
            'source_type': 'external_customer'
        })
        
        # Verify DOF appears in list
        dof_list = self.driver.find_element(By.CLASS_NAME, 'dof-list')
        assert 'E2E Test DOF' in dof_list.text
        
        # Navigate to DOF detail
        dof_link = self.driver.find_element(By.LINK_TEXT, 'E2E Test DOF')
        dof_link.click()
        
        # Verify workflow status
        status_element = self.driver.find_element(By.CLASS_NAME, 'dof-status')
        assert status_element.text == 'Taslak'
        
        # Submit for review
        submit_btn = self.driver.find_element(By.ID, 'submit-for-review')
        submit_btn.click()
        
        # Verify status change
        WebDriverWait(self.driver, 10).until(
            EC.text_to_be_present_in_element(
                (By.CLASS_NAME, 'dof-status'), 
                'Kaynak İncelemesi Bekliyor'
            )
        )
    
    def login_as_user(self, username, password):
        self.driver.get('http://localhost:5000/login')
        
        username_field = self.driver.find_element(By.NAME, 'username')
        password_field = self.driver.find_element(By.NAME, 'password')
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        login_btn = self.driver.find_element(By.TYPE, 'submit')
        login_btn.click()
```

### Performance Testing
```python
# tests/test_performance.py
import time
import concurrent.futures
from locust import HttpUser, task, between

class DOFSystemUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post('/api/auth/login', json={
            'username': 'test@example.com',
            'password': 'password123'
        })
        self.token = response.json()['access_token']
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    @task(3)
    def view_dashboard(self):
        """Most frequent operation"""
        self.client.get('/dashboard', headers=self.headers)
    
    @task(2)
    def list_dofs(self):
        """Second most frequent operation"""
        self.client.get('/api/dofs', headers=self.headers)
    
    @task(1)
    def view_dof_detail(self):
        """Less frequent but important operation"""
        self.client.get('/api/dofs/1', headers=self.headers)
    
    @task(1)
    def create_dof(self):
        """Least frequent but resource intensive"""
        dof_data = {
            'title': f'Load Test DOF {time.time()}',
            'description': 'Created during load testing',
            'source_type': 'internal_customer',
            'assigned_department_id': 1
        }
        self.client.post('/api/dofs', json=dof_data, headers=self.headers)

def test_database_performance():
    """Test database query performance"""
    from models import DOF
    
    start_time = time.time()
    
    # Test large dataset query
    dofs = DOF.query.filter(DOF.status.in_(['open', 'in_progress'])).limit(1000).all()
    
    query_time = time.time() - start_time
    
    # Assert reasonable performance (adjust threshold as needed)
    assert query_time < 1.0, f"Query took {query_time} seconds, should be under 1 second"
    assert len(dofs) <= 1000

def test_concurrent_dof_creation():
    """Test system behavior under concurrent DOF creation"""
    
    def create_dof():
        # Simulate DOF creation
        return requests.post('http://localhost:5000/api/dofs', 
                           json={'title': 'Concurrent Test DOF'},
                           headers={'Authorization': 'Bearer token'})
    
    # Test with 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_dof) for _ in range(10)]
        results = [future.result() for future in futures]
    
    # All requests should succeed
    assert all(result.status_code == 201 for result in results)
```

### Security Testing
```python
# tests/test_security.py
def test_sql_injection_protection(client):
    """Test protection against SQL injection attacks"""
    
    malicious_input = "'; DROP TABLE dofs; --"
    
    response = client.post('/api/dofs', json={
        'title': malicious_input,
        'description': 'Test'
    })
    
    # Should not cause internal server error
    assert response.status_code != 500
    
    # Database should still be intact
    response = client.get('/api/dofs')
    assert response.status_code == 200

def test_xss_protection(client):
    """Test protection against XSS attacks"""
    
    xss_payload = '<script>alert("XSS")</script>'
    
    response = client.post('/api/dofs', json={
        'title': xss_payload,
        'description': 'Test'
    })
    
    if response.status_code == 201:
        dof_id = response.json['id']
        
        # Get DOF detail page
        response = client.get(f'/dof/{dof_id}')
        
        # Script tags should be escaped
        assert '<script>' not in response.text
        assert '&lt;script&gt;' in response.text or xss_payload not in response.text

def test_authentication_required(client):
    """Test that protected endpoints require authentication"""
    
    protected_endpoints = [
        '/api/dofs',
        '/api/stats/dashboard',
        '/admin/users',
        '/dof/create'
    ]
    
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 302]  # Unauthorized or redirect to login

def test_authorization_enforcement(client, auth_headers):
    """Test that users can only access authorized resources"""
    
    # Regular user trying to access admin endpoint
    response = client.get('/api/admin/users', headers=auth_headers['user'])
    assert response.status_code == 403
    
    # Department manager trying to access other department's DOFs
    response = client.get('/api/dofs?department=other_dept', headers=auth_headers['dept_manager'])
    # Should filter results based on user's department access
    assert response.status_code == 200
```

## 🎯 Continuous Integration/Continuous Deployment

### GitHub Actions Workflow
```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: dof_test
        ports:
          - 3306:3306
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: --health-cmd="redis-cli ping" --health-interval=10s --health-timeout=5s --health-retries=3
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run linting
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        black --check .
        isort --check-only .
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ -v --cov=. --cov-report=xml
      env:
        DATABASE_URL: mysql+pymysql://root:root@localhost:3306/dof_test
        REDIS_URL: redis://localhost:6379/0
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
      env:
        DATABASE_URL: mysql+pymysql://root:root@localhost:3306/dof_test
        REDIS_URL: redis://localhost:6379/0
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
    
    - name: Security scan
      run: |
        bandit -r . -f json -o security-report.json
        safety check --json --output safety-report.json
    
    - name: Build Docker image
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      run: |
        docker build -t dof-management:${{ github.sha }} .
        docker tag dof-management:${{ github.sha }} dof-management:latest
    
    - name: Deploy to staging
      if: github.event_name == 'push' && github.ref == 'refs/heads/develop'
      run: |
        # Deploy to staging environment
        echo "Deploying to staging..."
    
    - name: Deploy to production
      if: github.event_name == 'push' && github.ref == 'refs/heads/main'
      run: |
        # Deploy to production environment
        echo "Deploying to production..."
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3
        
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
        
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.4
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
```

## 📊 Monitoring ve Observability

### Application Metrics
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
import time

# Define metrics
dof_creation_counter = Counter('dof_created_total', 'Total DOFs created')
dof_status_gauge = Gauge('dof_status_count', 'Current DOF count by status', ['status'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration', ['endpoint', 'method'])
active_users_gauge = Gauge('active_users_total', 'Number of active users')

def track_api_performance(endpoint_name):
    """Decorator to track API endpoint performance"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                api_request_duration.labels(endpoint=endpoint_name, method='success').observe(time.time() - start_time)
                return result
            except Exception as e:
                api_request_duration.labels(endpoint=endpoint_name, method='error').observe(time.time() - start_time)
                raise
        return wrapper
    return decorator

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': 'text/plain; charset=utf-8'}

def update_dof_metrics():
    """Update DOF-related metrics"""
    from models import DOF
    
    status_counts = db.session.query(DOF.status, db.func.count(DOF.id)).group_by(DOF.status).all()
    
    for status, count in status_counts:
        dof_status_gauge.labels(status=status).set(count)
```

### Logging Configuration
```python
# logging_config.py
import logging
import logging.handlers
from logging.config import dictConfig

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        },
        'detailed': {
            'format': '[%(asctime)s] %(levelname)s %(name)s %(funcName)s():%(lineno)d %(message)s',
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s", "user_id": "%(user_id)s"}',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'detailed',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': 'logs/error.log',
            'maxBytes': 10485760,
            'backupCount': 5
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'WARNING',
            'formatter': 'json',
            'filename': 'logs/security.log',
            'maxBytes': 10485760,
            'backupCount': 10
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'dof': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False
        }
    }
}

def setup_logging():
    """Initialize logging configuration"""
    dictConfig(LOGGING_CONFIG)
    
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)
```

## 🔄 Data Migration ve Versioning

### Migration Framework
```python
# migrations/migration_base.py
from abc import ABC, abstractmethod
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class Migration(ABC):
    """Base class for database migrations"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    @property
    @abstractmethod
    def version(self):
        """Migration version number"""
        pass
    
    @property
    @abstractmethod
    def description(self):
        """Migration description"""
        pass
    
    @abstractmethod
    def up(self):
        """Apply migration"""
        pass
    
    @abstractmethod
    def down(self):
        """Rollback migration"""
        pass
    
    def execute_sql(self, sql):
        """Execute raw SQL safely"""
        try:
            self.db.execute(text(sql))
            self.db.commit()
            logger.info(f"Executed SQL: {sql[:100]}...")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to execute SQL: {e}")
            raise

# migrations/v2_0_add_evidence_files.py
class AddEvidenceFilesMigration(Migration):
    
    @property
    def version(self):
        return "2.0.0"
    
    @property
    def description(self):
        return "Add evidence file support for DOF completion"
    
    def up(self):
        """Add ActionAttachments table and related columns"""
        
        # Create ActionAttachments table
        self.execute_sql("""
            CREATE TABLE action_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_item_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_size INTEGER NOT NULL,
                file_type VARCHAR(100),
                uploaded_by INTEGER NOT NULL,
                uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (action_item_id) REFERENCES action_items (id),
                FOREIGN KEY (uploaded_by) REFERENCES users (id)
            )
        """)
        
        # Add completion_details column to action_items
        self.execute_sql("""
            ALTER TABLE action_items 
            ADD COLUMN completion_details TEXT
        """)
        
        # Create indices for performance
        self.execute_sql("""
            CREATE INDEX idx_action_attachments_action_item 
            ON action_attachments(action_item_id)
        """)
        
        logger.info("Successfully added evidence files support")
    
    def down(self):
        """Rollback changes"""
        self.execute_sql("DROP INDEX IF EXISTS idx_action_attachments_action_item")
        self.execute_sql("DROP TABLE IF EXISTS action_attachments")
        
        # Note: Cannot easily remove column in SQLite
        logger.warning("Cannot remove completion_details column in SQLite")
        
        logger.info("Rolled back evidence files migration")
```

## 🌍 Internationalization (i18n)

### Multi-language Support
```python
# babel.cfg
[python: **.py]
[jinja2: **/templates/**.html]

# translations/tr/LC_MESSAGES/messages.po
msgid "DOF Management System"
msgstr "DOF Yönetim Sistemi"

msgid "Create New DOF"
msgstr "Yeni DOF Oluştur"

msgid "Source Review"
msgstr "Kaynak İncelemesi"

msgid "Action Plan"
msgstr "Aksiyon Planı"

msgid "Implementation"
msgstr "Uygulama"

msgid "Quality Review"
msgstr "Kalite İncelemesi"

msgid "Closed"
msgstr "Kapalı"

# translations/en/LC_MESSAGES/messages.po
msgid "DOF Management System"
msgstr "DOF Management System"

msgid "Create New DOF"
msgstr "Create New DOF"

# i18n.py
from flask_babel import Babel, gettext, ngettext
from flask import request, session

babel = Babel()

@babel.localeselector
def get_locale():
    # 1. URL parameter
    if request.args.get('lang'):
        session['language'] = request.args.get('lang')
    
    # 2. User preference
    if 'language' in session:
        return session['language']
    
    # 3. Browser preference
    return request.accept_languages.best_match(['tr', 'en']) or 'en'

def init_babel(app):
    babel.init_app(app)
    
    # Add template global functions
    app.jinja_env.globals['_'] = gettext
    app.jinja_env.globals['ngettext'] = ngettext
```

def test_xss_protection(client):
    """Test protection against XSS attacks"""
    
    xss_payload = '<script>alert("XSS")</script>'
    
    response = client.post('/api/dofs', json={
        'title': xss_payload,
        'description': 'Test'
    })
    
    if response.status_code == 201:
        dof_id = response.json['id']
        
        # Get DOF detail page
        response = client.get(f'/dof/{dof_id}')
        
        # Script tags should be escaped
        assert '<script>' not in response.text
        assert '&lt;script&gt;' in response.text or xss_payload not in response.text

def test_authentication_required(client):
    """Test that protected endpoints require authentication"""
    
    protected_endpoints = [
        '/api/dofs',
        '/api/stats/dashboard',
        '/admin/users',
        '/dof/create'
    ]
    
    for endpoint in protected_endpoints:
        response = client.get(endpoint)
        assert response.status_code in [401, 302]  # Unauthorized or redirect to login

def test_authorization_enforcement(client, auth_headers):
    """Test that users can only access authorized resources"""
    
    # Regular user trying to access admin endpoint
    response = client.get('/api/admin/users', headers=auth_headers['user'])
    assert response.status_code == 403
    
    # Department manager trying to access other department's DOFs
    response = client.get('/api/dofs?department=other_dept', headers=auth_headers['dept_manager'])
    # Should filter results based on user's department access
    assert response.status_code == 200
```

## 🆘 Sorun Giderme

### Yaygın Sorunlar

#### E-posta Gönderimi Çalışmıyor
1. SMTP ayarlarını kontrol edin
2. E-posta sunucusu bağlantısını test edin
3. Uygulama parolasının doğru olduğundan emin olun

#### Dosya Yükleme Hatası
1. UPLOAD_FOLDER'ın yazılabilir olduğunu kontrol edin
2. Dosya boyutu sınırlarını kontrol edin
3. Dosya türünün desteklendiğinden emin olun

#### Veritabanı Bağlantı Hatası
1. Veritabanı dosyasının var olduğunu kontrol edin
2. Veritabanı yolunun doğru olduğunu kontrol edin
3. Gerekli tablolarının oluşturulduğunu kontrol edin

### Debug Modunda Çalıştırma
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

### Log Seviyelerini Ayarlama
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Katkıda Bulunma

### Geliştirme Süreci
1. Projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

### Kod Standartları
- PEP 8 Python kod standardını takip edin
- Fonksiyonlar için docstring kullanın
- Anlamlı commit mesajları yazın
- Test yazarak kodunuzu test edin

## 📞 Destek ve İletişim

### Teknik Destek
- **E-posta**: alikokrtv@gmail.com
- **Dokümantasyon**:
- **Bug Raporları**: GitHub Issues

### Özellik Talepleri
- GitHub Issues üzerinden özellik talebi oluşturun
- Detaylı açıklama ve kullanım senaryosu ekleyin
- Mümkünse mockup veya diagram ekleyin

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## 🔄 Güncellemeler ve Sürüm Notları

### v2.0.0 (Güncel)
- **Yeni**: Modal tabanlı tamamlama süreci
- **Yeni**: Kanıt dosyası yükleme sistemi
- **İyileştirme**: Geliştirilmiş workflow görüntüleme
- **İyileştirme**: Daha iyi hata yönetimi
- **Düzeltme**: Dashboard durum sayıları sorunu

### v1.5.0
- **Yeni**: Franchise yöneticisi rolü
- **Yeni**: Günlük e-posta raporları
- **İyileştirme**: Performans optimizasyonları
- **Düzeltme**: E-posta bildirim sorunları

### v1.0.0
- İlk stabil sürüm
- Temel DOF yönetimi özellikleri
- Kullanıcı rolleri ve yetkileri
- E-posta bildirim sistemi

---

**Not**: Bu sistem sürekli geliştirilmekte olup, yeni özellikler ve iyileştirmeler düzenli olarak eklenmektedir.