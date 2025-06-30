import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler

# Loglama ayarları
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Veritabanı ve uygulama yapılandırması
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Mail yapılandırmasını sağlam bir şekilde yapılandır
mail = Mail()

socketio = SocketIO()
csrf = CSRFProtect()
scheduler = BackgroundScheduler()
migrate = Migrate()

# Flask uygulamasını oluştur
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dof-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Özel Jinja2 filtreleri ekleme
@app.template_filter('nl2br')
def nl2br_filter(text):
    if text:
        return text.replace('\n', '<br>')
    return ''

# Tarih formatı için filtre
@app.template_filter('format_datetime')
def format_datetime(value):
    """Veritabanından gelen tarih değerini yerel saat dilimine çevirir ve formatlar"""
    if value is None:
        return ""
    from datetime import datetime
    # UTC olarak saklandığı için direk göster, saat dilimi dönüşümü yapma
    return value.strftime('%d.%m.%Y %H:%M')

@app.template_filter('get_status_name')
def get_status_name(status_code):
    """DÖF durum kodunu açıklamasına çevirir"""
    status_names = {
        0: "Taslak",
        1: "Gönderildi",
        2: "İncelemede",
        3: "Atandı",
        4: "Devam Ediyor",
        5: "Çözüldü",
        6: "Kapatıldı",
        7: "Reddedildi",
        8: "Aksiyon Planı İncelemede",
        9: "Aksiyon Planı Uygulama Aşamasında",
        10: "Aksiyonlar Tamamlandı",
        11: "Kaynak Değerlendirmesinde"
    }
    return status_names.get(status_code, "Bilinmiyor")

# Uygulama yapılandırmasını yükle
from config import Config
app.config.from_object(Config)

# Eklentileri başlat
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Bu sayfayı görüntülemek için lütfen giriş yapın.'

# E-posta ayarlarını başlangıçta yükle
mail.init_app(app)

# Veritabanındaki e-posta ayarlarını yükleme fonksiyonu
def load_email_settings():
    try:
        from models import EmailSettings
        settings = EmailSettings.query.first()
        if settings:
            # E-posta ayarlarını uygula
            app.config['MAIL_SERVER'] = settings.smtp_host
            app.config['MAIL_PORT'] = settings.smtp_port
            app.config['MAIL_USE_TLS'] = settings.smtp_use_tls
            app.config['MAIL_USE_SSL'] = settings.smtp_use_ssl
            app.config['MAIL_USERNAME'] = settings.smtp_user
            app.config['MAIL_PASSWORD'] = settings.smtp_pass
            app.config['MAIL_DEFAULT_SENDER'] = settings.default_sender
            
            # Mail servisini yeniden başlat
            mail.init_app(app)
            
            logger.info(f"E-posta ayarları veritabanından yüklendi: {settings.smtp_host}:{settings.smtp_port}")
    except Exception as e:
        logger.error(f"E-posta ayarları yüklenirken hata oluştu: {str(e)}")
        # Varsayılan ayarları kullanmaya devam et

csrf.init_app(app)
socketio.init_app(app)

# Modelleri yükle
with app.app_context():
    try:
        import models
        # PING veritabanını kontrol eder ve bağlantıyı tazelemeye yardımcı olur
        engine = db.get_engine()
        if hasattr(engine, 'execute'):
            engine.execute('SELECT 1')
        else:
            with engine.connect() as conn:
                conn.execute('SELECT 1')
                
        logger.info("Veritabanı bağlantısı başarıyla kontrol edildi.")
        db.create_all()
        logger.info("Tüm veritabanı tabloları başarıyla oluşturuldu.")
        
        # E-posta ayarlarını veritabanından yükle
        load_email_settings()
    except Exception as e:
        logger.error(f"Veritabanı tabloları oluşturulurken hata: {str(e)}")
        
        # DirectorManagerMapping modelini manuel olarak oluşturmak için SQL kodunu göster
        table_create_sql = """
        CREATE TABLE director_manager_mapping (
            id INT AUTO_INCREMENT PRIMARY KEY,
            director_id INT NOT NULL,
            manager_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_director_manager (director_id, manager_id),
            CONSTRAINT fk_director_user FOREIGN KEY (director_id) REFERENCES users (id),
            CONSTRAINT fk_manager_user FOREIGN KEY (manager_id) REFERENCES users (id)
        );
        """
        
        logger.info("DirectorManagerMapping modelini manuel olarak oluşturmak için SQL kodu:")
        logger.info(table_create_sql)

# Kullanıcı yükleyiciyi tanımla
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Jinja2 için global değişkenler
@app.context_processor
def inject_models():
    from models import Notification
    return {
        "Notification": Notification
    }

# Rotaları kaydet
from routes.auth import auth_bp
from routes.dof import dof_bp
from routes.admin import admin_bp
from routes.api import api_bp
from routes.feedback import feedback_bp
from routes.setup import setup_bp
from routes.activity import activity_bp
from routes.notifications import notifications_bp
from routes.thank_you import thank_you_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dof_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(setup_bp)
app.register_blueprint(activity_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(thank_you_bp, url_prefix='/thank-you')

# E-posta zamanlayıcısını başlat
try:
    from daily_email_scheduler import init_scheduler
    email_scheduler = init_scheduler()
    if email_scheduler:
        logger.info("✅ Günlük e-posta raporu zamanlayıcısı başlatıldı")
    else:
        logger.warning("⚠️ Günlük e-posta raporu zamanlayıcısı başlatılamadı")
except Exception as e:
    logger.error(f"❌ E-posta zamanlayıcısı başlatma hatası: {str(e)}")

# Zamanlanmış görevleri başlat
scheduler.start()

# Uygulama başlatıldığında departman-kullanıcı eşleştirmelerini kontrol et
with app.app_context():
    try:
        from sync_departments import sync_user_departments, sync_dof_departments
        
        # Kullanıcı departmanlarını senkronize et
        user_results = sync_user_departments()
        logger.info(f"Departman-Kullanıcı eşleştirmesi: {user_results['total_users']} kullanıcıdan {len(user_results['fixed_users'])} tanesi düzeltildi.")
        
        # DÖF departmanlarını senkronize et
        dof_results = sync_dof_departments()
        logger.info(f"Departman-DÖF eşleştirmesi: {dof_results['total_dofs']} DÖF'ten {len(dof_results['fixed_dofs'])} tanesi düzeltildi.")
        
        if user_results['fixed_users'] or dof_results['fixed_dofs']:
            logger.info(f"Toplam {len(user_results['fixed_users'])} kullanıcı ve {len(dof_results['fixed_dofs'])} DÖF için departman eşleştirmesi yapıldı.")
    except Exception as e:
        logger.error(f"Departman-kullanıcı eşleştirmesi sırasında hata: {str(e)}")


# Ana rotayı tanımla
from flask import redirect, url_for

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
