import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

# Import all extensions from extensions module to avoid circular imports
from extensions import db, login_manager, mail, socketio, csrf, scheduler, migrate

# Loglama ayarları
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

# Enhanced database connection with password fallback logic
if not os.environ.get('DATABASE_URL') and 'mysql+pymysql://' in Config.SQLALCHEMY_DATABASE_URI:
    from sqlalchemy import create_engine, text
    
    # Extract connection components
    original_uri = Config.SQLALCHEMY_DATABASE_URI
    logger.info(f"Testing database connection: {original_uri.replace(':255223', ':***').replace(':255223Rtv', ':***')}")
    
    # Password priority: 255223Rtv first, then 255223
    passwords_to_try = ['255223Rtv', '255223']
    connection_successful = False
    
    for password in passwords_to_try:
        # Create URI with current password
        if '255223Rtv' in original_uri:
            test_uri = original_uri.replace('255223Rtv', password)
        elif '255223' in original_uri:
            test_uri = original_uri.replace('255223', password)
        else:
            test_uri = original_uri
            
        try:
            logger.info(f"Trying database connection with password: {password}")
            eng = create_engine(test_uri, connect_args={"connect_timeout": 10})
            
            with eng.connect() as c:
                result = c.execute(text('SELECT 1'))
                if result.fetchone()[0] == 1:
                    logger.info(f"✅ Database connection successful with password: {password}")
                    Config.SQLALCHEMY_DATABASE_URI = test_uri
                    connection_successful = True
                    break
                    
        except Exception as e:
            logger.warning(f"❌ Database connection failed with password {password}: {str(e)}")
            continue
    
    if not connection_successful:
        logger.error("❌ All database connection attempts failed! Using original configuration.")
        logger.error("Please check database server status and credentials.")

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

# Veritabanını kontrol et
with app.app_context():
    try:
        # PING veritabanını kontrol eder ve bağlantıyı tazelemeye yardımcı olur
        engine = db.get_engine()
        with engine.connect() as conn:
            conn.execute(db.text('SELECT 1'))
                
        logger.info("Veritabanı bağlantısı başarıyla kontrol edildi.")
        db.create_all()
        logger.info("Tüm veritabanı tabloları başarıyla oluşturuldu.")
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

# Rotaları lazy import ile kaydet
def register_blueprints():
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

# Kullanıcı yükleyiciyi tanımla (routes'tan sonra)
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Jinja2 için global değişkenler (routes'tan sonra)
@app.context_processor
def inject_models():
    from models import Notification
    return {
        "Notification": Notification
    }

# Blueprint'leri kaydet
register_blueprints()

# E-posta ayarlarını veritabanından yükle (routes'tan sonra)
try:
    load_email_settings()
    logger.info("✅ E-posta ayarları başarıyla yüklendi")
except Exception as e:
    logger.error(f"E-posta ayarları yüklenirken hata oluştu: {str(e)}")

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
from flask import redirect, url_for, jsonify

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

@app.route('/health')
def health_check():
    """Sistem sağlık kontrolü"""
    try:
        # Veritabanı bağlantısını test et
        from extensions import db
        from sqlalchemy import text
        
        with db.engine.connect() as connection:
            result = connection.execute(text('SELECT 1 as health_check'))
            db_status = "OK" if result.fetchone()[0] == 1 else "FAILED"
            
        return jsonify({
            "status": "OK",
            "database": db_status,
            "message": "DOF Management System is running"
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "ERROR",
            "database": "FAILED",
            "error": str(e),
            "message": "DOF Management System has issues"
        }), 500

# Global error handlers
@app.errorhandler(500)
def internal_server_error(error):
    """Internal Server Error handler"""
    import traceback
    error_traceback = traceback.format_exc()
    logger.error(f"Internal Server Error: {str(error)}")
    logger.error(f"Traceback: {error_traceback}")
    
    if app.debug:
        return f"<h1>Internal Server Error</h1><pre>{error_traceback}</pre>", 500
    else:
        return jsonify({
            "error": "Internal Server Error",
            "message": "Bir sistem hatası oluştu. Lütfen sistem yöneticisi ile iletişime geçin."
        }), 500

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    import traceback
    error_traceback = traceback.format_exc()
    logger.error(f"Unhandled exception: {str(e)}")
    logger.error(f"Traceback: {error_traceback}")
    
    if app.debug:
        return f"<h1>Unhandled Exception</h1><pre>{error_traceback}</pre>", 500
    else:
        return jsonify({
            "error": "System Error",
            "message": "Beklenmeyen bir hata oluştu."
        }), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
