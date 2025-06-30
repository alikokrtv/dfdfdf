import os
from datetime import timedelta

class Config:
    # Flask yapılandırması
    # Railway ortamı için DEBUG mod kapalı olmalı
    DEBUG = os.environ.get('FLASK_DEBUG', False)
    
    # Railway URL'sini kullan veya varsayılan localhost
    RAILWAY_URL = os.environ.get('RAILWAY_PUBLIC_URL', '')
    RAILWAY_STATIC_URL = os.environ.get('RAILWAY_STATIC_URL', '')
    
    if RAILWAY_URL:  # Railway ortamındaysa
        BASE_URL = f"https://{RAILWAY_URL}/"
        # Railway ortamında SERVER_NAME ayarını kullanma 
        # (bağlantı hatası önlemek için)
        SERVER_NAME = None 
    else:  # Yerel geliştirme ortamı
        BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000/')
        SERVER_NAME = os.environ.get('SERVER_NAME', None)  # Yerel ortamda da None olarak ayarlıyoruz
    
    # Veritabanı yapılandırması
    # Database URL için varsayılan değer ata
    
    # Railway Deployment için optimize edilmiş veritabanı ayarları
    # Railway otomatik olarak DATABASE_URL ortam değişkenini oluşturur
    
    # Varsayılan olarak Railway platformunun sağladığı DATABASE_URL kullanılır
    # Eğer bu değişken yoksa, belirtilen veritabanı bağlantı bilgileri kullanılır
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL and DATABASE_URL.startswith('mysql'):
        # Railway platformu tarafından sağlanan DATABASE_URL kullan
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif os.environ.get('RAILWAY_ENVIRONMENT') == 'production':
        # Railway ortamı için güvenli varsayılan bağlantı
        DB_USER = os.environ.get('MYSQLUSER', 'root')
        DB_PASSWORD = os.environ.get('MYSQLPASSWORD')
        DB_HOST = os.environ.get('MYSQLHOST', 'mysql.railway.internal')
        DB_PORT = os.environ.get('MYSQLPORT', '3306')
        DB_NAME = os.environ.get('MYSQLDATABASE', 'railway')
        
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # Yerel geliştirme ortamı için varsayılan bağlantı
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:255223Rtv@localhost/dof_db'
    
    # SQLite bağlantısı (yorum satırında)
    # # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dof.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Gelişmiş veritabanı bağlantı havuzu ayarları - Railway MySQL için optimize edildi
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,               # Maximum havuz boyutu
        "max_overflow": 20,           # Maximum overflow bağlantı sayısı
        "pool_recycle": 120,          # Bağlantıları 120 saniyede bir geri dönüştür (timeout'tan kaynaklı sorunları önlemek için)
        "pool_pre_ping": True,        # Her kullanımdan önce bağlantıyı test et
        "pool_timeout": 30,           # Havuzdan bağlantı beklerken timeout süresi
        "connect_args": {
            "connect_timeout": 60,    # MySQL bağlantı timeout'u (saniye)
            "read_timeout": 60        # MySQL okuma timeout'u (saniye)
        }
    }
    
    # Oturum yapılandırması
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Mail yapılandırması - Kurumsal e-posta için güncellenmiş ayarlar
    MAIL_SERVER = 'mail.kurumsaleposta.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'df@beraber.com.tr'
    MAIL_PASSWORD = '=z5-5MNKn=ip5P4@'
    MAIL_DEFAULT_SENDER = 'Plus Kitchen <df@pluskitchen.com.tr>'
    MAIL_MAX_EMAILS = 10  # Tek seferde gönderilecek maksimum e-posta sayısı
    MAIL_DEBUG = False     # Hata ayıklama modunu kapat
    MAIL_SUPPRESS_SEND = False  # Test modunda göndermeyi engelleme
    
    # Dosya yükleme yapılandırması
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx', 'xls', 'xlsx'}
