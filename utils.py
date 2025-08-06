import os
import secrets
import datetime
import threading
from flask import current_app, render_template
from werkzeug.utils import secure_filename
from flask_mail import Message
from app import mail, db
from models import SystemLog, Notification, User, DOFStatus, UserActivity

def save_file(file, upload_folder=None):
    """
    Dosyayı güvenli bir şekilde kaydet ve dosya yolunu döndür
    """
    if not upload_folder:
        upload_folder = current_app.config['UPLOAD_FOLDER']
    
    # Eğer klasör yoksa oluştur
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Güvenli dosya adı oluştur
    filename = secure_filename(file.filename)
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(filename)
    new_filename = random_hex + file_ext
    
    # Dosyayı kaydet
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)
    
    # Veritabanı için göreceli yolu döndür
    relative_path = os.path.join('uploads', new_filename)
    
    return {
        'filename': filename,
        'file_path': relative_path,
        'file_size': os.path.getsize(file_path),
        'file_type': file_ext[1:] if file_ext.startswith('.') else file_ext
    }

def allowed_file(filename):
    """
    Dosya uzantısının izin verilen uzantılar listesinde olup olmadığını kontrol et
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Thread Pool boyutu - aynı anda en fazla bu kadar e-posta gönderimi olabilir
EMAIL_THREAD_POOL_SIZE = 5
_email_thread_pool = None
_email_thread_pool_lock = threading.Lock()

def get_email_thread_pool():
    """
    Thread pool örneğini döndürür, yoksa oluşturur
    """
    global _email_thread_pool
    with _email_thread_pool_lock:
        if _email_thread_pool is None:
            from concurrent.futures import ThreadPoolExecutor
            _email_thread_pool = ThreadPoolExecutor(max_workers=EMAIL_THREAD_POOL_SIZE, thread_name_prefix="EmailSender")
    return _email_thread_pool

def send_email_async(subject, recipients, body_html, body_text=None, track_id=None):
    """
    E-posta gönderme fonksiyonu - Asenkron olarak thread pool üzerinden çalışır
    Flask uygulama bağlamını korur ve thread pool kullanarak daha iyi performans sağlar
    
    Args:
        subject: E-posta konusu
        recipients: Alıcı e-posta adresleri listesi
        body_html: HTML içerik
        body_text: Düz metin içerik (isteğe bağlı)
        track_id: E-posta takibi için ID (isteğe bağlı)
    
    Returns:
        bool: İşlemin başarıyla başlatılıp başlatılmadığı
    """
    from flask import current_app
    
    # E-posta durumunu takip etmek için veritabanına kaydet
    if track_id:
        try:
            from models import EmailTrack, db
            with current_app.app_context():
                email_track = EmailTrack(
                    id=track_id,
                    subject=subject,
                    recipients=",".join(recipients) if isinstance(recipients, list) else recipients,
                    status="queued",
                    created_at=datetime.datetime.now()
                )
                db.session.add(email_track)
                db.session.commit()
                current_app.logger.info(f"E-posta takibi oluşturuldu: {track_id}")
        except Exception as e:
            current_app.logger.error(f"E-posta takibi oluşturma hatası: {str(e)}")
    
    # Mevcut uygulama bağlamını al
    app = current_app._get_current_object()
    
    def send_with_app_context():
        with app.app_context():
            status = "failed"
            error_msg = None
            try:
                result = send_email(subject, recipients, body_html, body_text, track_email=False)  # Asenkron'da takip etme, zaten burada yapılıyor
                if result:
                    status = "sent"
                    app.logger.info(f"Asenkron e-posta gönderimi başarılı: {subject} - Alıcı sayısı: {len(recipients) if isinstance(recipients, list) else 1}")
                else:
                    app.logger.error(f"Asenkron e-posta gönderimi başarısız: E-posta gönderilemedi")
                    error_msg = "E-posta gönderimi başarısız"                    
            except Exception as e:
                error_msg = str(e)
                app.logger.error(f"Asenkron e-posta gönderimi başarısız: {error_msg}")
                import traceback
                app.logger.error(f"Hata detayları: {traceback.format_exc()}")
            
            # E-posta durumunu güncelle
            if track_id:
                try:
                    from models import EmailTrack, db
                    email_track = EmailTrack.query.get(track_id)
                    if email_track:
                        email_track.status = status
                        email_track.error = error_msg
                        email_track.completed_at = datetime.datetime.now()
                        db.session.commit()
                        app.logger.info(f"E-posta takibi güncellendi: {track_id} - Durum: {status}")
                except Exception as e:
                    app.logger.error(f"E-posta takibi güncelleme hatası: {str(e)}")
    
    # Thread pool'dan bir thread al ve çalıştır
    try:
        pool = get_email_thread_pool()
        pool.submit(send_with_app_context)
        return True
    except Exception as e:
        current_app.logger.error(f"Thread pool hatası: {str(e)}")
        # Yedek olarak normal thread kullan
        thread = threading.Thread(target=send_with_app_context, name=f"EmailSenderBackup-{subject[:10]}")
        thread.daemon = True
        thread.start()
        return True

def send_email(subject, recipients, body_html, body_text=None, max_retries=1, track_email=True):
    """
    E-posta gönderme fonksiyonu - Flask-Mail kullanarak gönderim
    SMTP hatalarını daha iyi yönetir
    Türkçe karakter sorunlarını çözer
    Yeniden deneme mekanizması eklenmiştir
    E-posta takip sistemi eklendi
    
    Args:
        subject: E-posta konusu
        recipients: Alıcı e-posta adresleri listesi
        body_html: HTML içerik
        body_text: Düz metin içerik (isteğe bağlı)
        max_retries: Başarısız olursa kaç kez yeniden denenecek (varsayılan: 1)
        track_email: E-posta takip edilsin mi (varsayılan: True)
    
    Returns:
        bool: Gönderim başarılı ise True, değilse False
    """
    from flask import current_app
    from app import mail
    from flask_mail import Message
    import smtplib
    import time
    import uuid
    
    # E-posta takip ID'si oluştur
    track_id = str(uuid.uuid4()) if track_email else None
    
    # Kimseye e-posta gönderilmiyorsa, boş liste döndür
    if not recipients or len(recipients) == 0:
        current_app.logger.warning("E-posta gönderimi iptal: Alıcı listesi boş")
        return False
    
    # Boş e-posta adresi içeren alıcıları temizle
    valid_recipients = [r.strip() for r in recipients if r and '@' in r]
    if not valid_recipients:
        current_app.logger.warning("E-posta gönderimi iptal: Geçerli alıcı yok")
        return False
    
    # E-posta takip kaydı oluştur
    if track_id:
        try:
            from models import EmailTrack, db
            email_track = EmailTrack(
                id=track_id,
                subject=subject,
                recipients=",".join(valid_recipients),
                status="queued",
                created_at=datetime.datetime.now()
            )
            db.session.add(email_track)
            db.session.commit()
            current_app.logger.info(f"E-posta takibi oluşturuldu: {track_id}")
        except Exception as e:
            current_app.logger.error(f"E-posta takibi oluşturma hatası: {str(e)}")
    
    # Deneme sayacı
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            # E-posta gönderimi başlangıç logları
            retry_log = f" (Deneme {retry_count+1}/{max_retries+1})" if retry_count > 0 else ""
            current_app.logger.info(f"E-posta gönderimi başlıyor{retry_log}: Konu: {subject}, Alıcılar: {valid_recipients}")
            
            # Flask-Mail Message nesnesi oluştur
            msg = Message(subject=subject, recipients=valid_recipients)
            
            # Göndereni ayarla (bu SMTP hatasını önleyebilir)
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')
            # Eğer sender yoksa, MAIL_USERNAME ile doldur
            if not sender:
                sender = current_app.config.get('MAIL_USERNAME')
            msg.sender = sender

            # E-posta ayarlarını kontrol et ve logla
            mail_server = current_app.config.get('MAIL_SERVER', 'N/A')
            mail_port = current_app.config.get('MAIL_PORT', 'N/A')
            mail_use_tls = current_app.config.get('MAIL_USE_TLS', False)
            mail_use_ssl = current_app.config.get('MAIL_USE_SSL', False)
            current_app.logger.debug(f"Mail ayarları: Server={mail_server}, Port={mail_port}, TLS={mail_use_tls}, SSL={mail_use_ssl}, Sender={sender}")
            
            # HTML içerik ekle
            if body_html:
                msg.html = body_html
            
            # Düz metin içerik ekle
            if body_text:
                msg.body = body_text
            elif body_html:
                # HTML'den düz metin oluştur (basit bir şekilde)
                import re
                msg.body = re.sub('<[^<]+?>', '', body_html)
            
            # E-posta gönderimini dene
            mail.send(msg)
            
            # Başarılı gönderim
            current_app.logger.info(f"E-posta gönderimi BAŞARILI{retry_log}: {subject} - Alıcılar: {valid_recipients}")
            
            # E-posta takip kaydını güncelle
            if track_id:
                try:
                    from models import EmailTrack, db
                    email_track = EmailTrack.query.get(track_id)
                    if email_track:
                        email_track.status = "sent"
                        email_track.completed_at = datetime.datetime.now()
                        db.session.commit()
                        current_app.logger.info(f"E-posta takibi güncellendi: {track_id} - Durum: sent")
                except Exception as e:
                    current_app.logger.error(f"E-posta takibi güncelleme hatası: {str(e)}")
            
            return True
            
        except smtplib.SMTPServerDisconnected as disconnect_error:
            # Bağlantı kopması durumunda
            current_app.logger.error(f"SMTP Bağlantı Hatası{retry_log}: {str(disconnect_error)}")
            if retry_count < max_retries:
                # Kısa bir süre bekle ve yeniden dene
                time.sleep(2)
                retry_count += 1
                continue
            else:
                # E-posta takip kaydını güncelle
                if track_id:
                    try:
                        from models import EmailTrack, db
                        email_track = EmailTrack.query.get(track_id)
                        if email_track:
                            email_track.status = "failed"
                            email_track.error = f"SMTP Bağlantı Hatası: {str(disconnect_error)}"
                            email_track.completed_at = datetime.datetime.now()
                            db.session.commit()
                    except Exception as e:
                        current_app.logger.error(f"E-posta takibi güncelleme hatası: {str(e)}")
                return False
                
        except smtplib.SMTPException as smtp_error:
            # SMTP özel hatalarını yakala
            current_app.logger.error(f"SMTP Hatası{retry_log}: {str(smtp_error)}")
            print(f"SMTP HATASI: {str(smtp_error)}")
            
            if retry_count < max_retries:
                # Biraz daha uzun bekle ve yeniden dene
                time.sleep(3)
                retry_count += 1
                continue
            else:
                # E-posta takip kaydını güncelle
                if track_id:
                    try:
                        from models import EmailTrack, db
                        email_track = EmailTrack.query.get(track_id)
                        if email_track:
                            email_track.status = "failed"
                            email_track.error = f"SMTP Hatası: {str(smtp_error)}"
                            email_track.completed_at = datetime.datetime.now()
                            db.session.commit()
                    except Exception as e:
                        current_app.logger.error(f"E-posta takibi güncelleme hatası: {str(e)}")
                return False
            
        except Exception as e:
            # Diğer tüm hatalar
            current_app.logger.error(f"E-posta gönderim hatası{retry_log}: {str(e)}")
            import traceback
            error_details = traceback.format_exc()
            current_app.logger.error(f"Hata detayları: {error_details}")
            
            print(f"E-POSTA HATASI: {str(e)}")
            
            if retry_count < max_retries:
                time.sleep(2)
                retry_count += 1
                continue
            else:
                # E-posta takip kaydını güncelle
                if track_id:
                    try:
                        from models import EmailTrack, db
                        email_track = EmailTrack.query.get(track_id)
                        if email_track:
                            email_track.status = "failed"
                            email_track.error = f"Genel Hata: {str(e)}"
                            email_track.completed_at = datetime.datetime.now()
                            db.session.commit()
                    except Exception as track_error:
                        current_app.logger.error(f"E-posta takibi güncelleme hatası: {str(track_error)}")
                return False
            
    # Tüm denemeler başarısız oldu
    # E-posta takip kaydını hata olarak güncelle
    if track_id:
        try:
            from models import EmailTrack, db
            email_track = EmailTrack.query.get(track_id)
            if email_track:
                email_track.status = "failed"
                email_track.error = "Tüm gönderim denemeleri başarısız oldu"
                email_track.completed_at = datetime.datetime.now()
                db.session.commit()
                current_app.logger.info(f"E-posta takibi güncellendi: {track_id} - Durum: failed")
        except Exception as e:
            current_app.logger.error(f"E-posta takibi güncelleme hatası: {str(e)}")
    
    return False
        
# Form işlemlerini optimize eden fonksiyon

def optimize_db_operations(func):
    """
    Dekoratör: Veritabanı işlemlerini optimize etmek için
    Bu dekoratör, fonksiyonları veritabanı işlemleri için optimize eder.
    
    Özellikler:
    - Veritabanı işlem hızını artırır
    - Hata durumunda otomatik rollback yapar
    - Performans istatistikleri tutar
    """
    from functools import wraps
    import time
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        from sqlalchemy.exc import SQLAlchemyError
        start_time = time.time()
        
        try:
            # Ana fonksiyonu çağır (veritabanı işlemleri içerir)
            result = func(*args, **kwargs)
            
            # İşlem tamamlandı - her şey yolunda gittiyse, veritabanı işlemini kaydet
            db.session.commit()
            
            # İşlem süresini ölç
            end_time = time.time()
            process_time = round((end_time - start_time) * 1000)  # ms cinsinden
            
            # Performans logu
            if process_time > 500:  # 500ms'den uzun süren işlemler için uyarı
                current_app.logger.warning(f"YAVAŞ İŞLEM: {func.__name__} fonksiyonu {process_time}ms sürdü")
            else:
                current_app.logger.debug(f"DB İŞLEM: {func.__name__} fonksiyonu {process_time}ms sürdü")
            
            return result
            
        except SQLAlchemyError as e:
            # Veritabanı hatası durumunda işlemi geri al
            db.session.rollback()
            current_app.logger.error(f"Veritabanı işlemi hatası: {func.__name__} - {str(e)}")
            
            # Kritik hata durumunda üst seviyeye bildir
            raise
    
    return wrapper


# Veritabanı toplu işlemlerini optimize eden yardımcı fonksiyon
def batch_db_operations(operations_func):
    """
    Veritabanı toplu işlemlerini tek seferde gerçekleştirmek için yardımcı fonksiyon
    
    Kullanım:
    @batch_db_operations
    def process_items(items):
        for item in items:
            # item işlemleri
            db.session.add(item)
        # commit otomatik yapılır
    """
    from functools import wraps
    import time
    
    @wraps(operations_func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            # Fonksiyonu çağır
            result = operations_func(*args, **kwargs)
            
            # Tek seferde commit yap
            db.session.commit()
            
            # İşlem süresi ölçümü
            end_time = time.time()
            process_time = round((end_time - start_time) * 1000)
            
            current_app.logger.info(f"TOPLU İŞLEM: {operations_func.__name__} - {process_time}ms sürdü")
            return result
            
        except Exception as e:
            # Hata durumunda geri al
            db.session.rollback()
            current_app.logger.error(f"Toplu işlem hatası: {operations_func.__name__} - {str(e)}")
            raise
    
    return wrapper

def log_activity(user_id, action, details=None, ip_address=None, user_agent=None):
    """
    Hem sistem logu hem de kullanıcı aktivitesi kaydet
    """
    try:
        # Kullanıcıyı bul (adını loglamak için)
        user = User.query.get(user_id)
        user_name = user.full_name if user else f"Kullanıcı ID: {user_id}"
        
        # Aktivite açıklamasını düzenle
        if action == "Giriş Yapıldı":
            formatted_details = f"{user_name} tarafından sisteme giriş yapıldı"
        elif action == "Çıkış Yapıldı":
            formatted_details = f"{user_name} tarafından sistemden çıkış yapıldı"
        elif action.startswith("DÖF") and details:
            formatted_details = f"{details}"
        else:
            formatted_details = details if details else f"{action} işlemi gerçekleştirildi"
        
        # Sistem log kaydı oluştur
        log = SystemLog(
            user_id=user_id,
            action=action,
            details=formatted_details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.datetime.now()
        )
        db.session.add(log)
        
        # Kullanıcı aktivitesi kaydı oluştur
        user_activity = UserActivity(
            user_id=user_id,
            activity_type=action,
            description=formatted_details,
            related_id=None if not details or (isinstance(details, str) and not details.isdigit()) else int(details),
            ip_address=ip_address,
            browser_info=user_agent,
            created_at=datetime.datetime.now()
        )
        db.session.add(user_activity)
        
        # İki kaydı da veritabanına yaz
        db.session.commit()
        
        # Log kaydını konsola yaz
        current_app.logger.info(f"Aktivite kaydedildi: {action} - Kullanıcı: {user_name} (ID: {user_id})")
        
        return log, user_activity
    except Exception as e:
        current_app.logger.error(f"Log kaydetme hatası: {str(e)}")
        db.session.rollback()
        return None, None


def create_notification(user_id, message, dof_id=None):
    """
    Kullanıcıya bildirim oluştur ve email gönder
    """
    from flask import current_app
    import logging
    
    # Debug için ayrıntılı log
    current_app.logger.debug(f"create_notification çağrıldı - User ID: {user_id}, Message: {message[:50] if message else 'Boş mesaj'}..., DOF ID: {dof_id}")
    
    try:
        # Kullanıcıyı kontrol et
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"Bildirim oluşturulamadı: Kullanıcı bulunamadı (ID: {user_id})")
            return None
        
        current_app.logger.info(f"Bildirim oluşturuluyor: {user.username} ({user.email}) için '{message[:50] if message else 'Boş mesaj'}...'")
        
        # Bildirim oluştur
        notification = Notification(
            user_id=user_id,
            message=message,
            dof_id=dof_id,
            created_at=datetime.datetime.now(),  # UTC zaman kullanarak tutarlılık sağla
            is_read=False
        )
        
        # Veritabanına kaydet
        try:
            db.session.add(notification)
            db.session.commit()
            current_app.logger.info(f"Bildirim başarıyla oluşturuldu. ID: {notification.id}")
        except Exception as db_error:
            current_app.logger.error(f"Bildirim veritabanına eklenirken hata: {str(db_error)}")
            db.session.rollback()
            raise  # Hatayı yukarı ilet
        
        # E-posta gönderim denemesi
        if not user.email:
            current_app.logger.warning(f"Kullanıcının email adresi bulunamadı (ID: {user_id})")
            return notification
            
        # E-posta göndermeye çalış
        try:
            current_app.logger.info(f"E-posta göndermeye çalışılıyor: {user.email}")
            
            # DÖF bilgisi varsa bağlantı oluştur
            dof_link = ""
            if dof_id:
                dof_link = f"<p>İlgili DÖF için <a href='{current_app.config.get('BASE_URL', '')}dof/detail/{dof_id}'>tıklayınız</a>.</p>"
            
            # Email metni hazırla
            subject = "DÖF Sistemi Bildirim"
            body_html = f"""
            <html>
                <body>
                    <h3>DÖF Sistemi Bildirim</h3>
                    <p>{message}</p>
                    {dof_link}
                    <p>Bu otomatik bir bildirimdir, lütfen yanıtlamayınız.</p>
                </body>
            </html>
            """
            body_text = f"DÖF Sistemi Bildirim\n\n{message}\n\nBu otomatik bir bildirimdir, lütfen yanıtlamayınız."
            
            # Email gönderme fonksiyonunu çağır
            recipients = [user.email]
            send_email_async(subject, recipients, body_html, body_text)
            current_app.logger.info(f"E-posta gönderim başlatıldı: {user.email}")
            
        except Exception as e:
            current_app.logger.error(f"E-posta gönderiminde hata: {str(e)}")
            # E-posta gönderim hatası olsa bile bildirim oluşturuldu, devam et
            
        return notification
    except Exception as e:
        current_app.logger.error(f"Bildirim oluşturma hatası: {str(e)}")
        db.session.rollback()
        return None

import time
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

# Rol kontrolü için dekoratör
def requires_role(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.role not in roles:
                flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def notify_for_dof(dof, action_type, actor_name):
    """
    DÖF ile ilgili bir işlem yapıldığında ilgili kişilere bildirim gönder
    action_type: create, update, assign, comment, status_change vb.
    
    Bu fonksiyon artık notification_helper modülünü kullanarak bildirim gönderir.
    """
    from flask import current_app
    import logging
    
    try:
        # Bildirim yardımcı modülünü içe aktar
        from notification_helper import notify_all_relevant_users
        
        current_app.logger.info(f"DÖF #{dof.id} için bildirim gönderiliyor - Eylem türü: {action_type}")
        
        # İşlemi yapan kişinin görüntü adını belirle
        if isinstance(actor_name, User):
            actor_display_name = actor_name.full_name
            actor = actor_name
        elif isinstance(actor_name, str):
            actor_display_name = actor_name
            actor = None
        else:
            # Eğer actor_name beklenmeyen bir tipte ise, mevcut kullanıcının adını kullan
            try:
                from flask_login import current_user
                if hasattr(current_user, 'full_name'):
                    actor_display_name = current_user.full_name
                    actor = current_user
                else:
                    actor_display_name = "Sistem"
                    actor = None
            except Exception:
                actor_display_name = "Sistem"
                actor = None
        
        # DÖF ID numarasını bildirimde kullan
        dof_id_text = f"(#{dof.id})"
        
        # Bildirim mesajını oluştur
        if action_type == "create":
            message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı yeni bir DÖF oluşturuldu"
        elif action_type == "update":
            # Güncellenen alanları al
            try:
                from flask import request
                additional_info = request.form.get('description', '') if hasattr(request, 'form') else ''
                
                if hasattr(dof, 'last_activity') and dof.last_activity and hasattr(dof.last_activity, 'description'):
                    additional_info = dof.last_activity.description
                    
                if additional_info and len(additional_info) > 5:
                    # Uzun açıklamaları kısalt
                    if len(additional_info) > 150:
                        additional_info = additional_info[:147] + "..."
                    message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF güncellendi: {additional_info}"
                else:
                    message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF güncellendi"
            except Exception as e:
                # Hata durumunda standart mesajı kullan
                message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF güncellendi"
        elif action_type == "status_change":
            # Hangi durumdan hangi duruma geçildiğini detaylı göster
            old_status = ""
            try:
                from flask import request
                old_status_data = request.form.get('old_status', '') if hasattr(request, 'form') else ''
                
                if old_status_data:
                    old_status = f"{old_status_data} -> "
            except Exception:
                pass
                
            # Kaynak departmanın DÖF değerlendirmesi sonucuna özel mesajlar
            if dof.status == 5:  # Çözüldü (RESOLVED)
                message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF ÇÖZÜLDÜ olarak işaretlendi. Çözüm kaynak departman tarafından ONAYLANDI."
            elif dof.status == 4:  # Çözümden Memnun Değilim (IN_PROGRESS)
                message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF'e YENİ ÇÖZÜM İSTENİYOR. Kaynak departman çözümden memnun kalmadı."
            else:
                message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF'ün durumu {old_status}'{dof.status_name}' olarak değiştirildi"
        elif action_type == "assign":
            # Kime atandığını bul
            assignee_name = "ilgili kişiye"
            if dof.assigned_to:
                try:
                    assigned_user = User.query.get(dof.assigned_to)
                    if assigned_user:
                        assignee_name = f"{assigned_user.full_name}'e"
                except Exception:
                    pass
            message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF {assignee_name} atandı"
        elif action_type == "comment":
            # Yorumun içeriğini göster
            comment_text = ""
            try:
                from flask import request
                comment_data = request.form.get('comment', '') if hasattr(request, 'form') else ''
                
                if comment_data and len(comment_data) > 5:
                    # Uzun yorumları kısalt
                    if len(comment_data) > 100:
                        comment_text = f": '{comment_data[:97]}...'"
                    else:
                        comment_text = f": '{comment_data}'"
            except Exception:
                pass
                
            message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF'e yeni bir yorum eklendi{comment_text}"
        else:
            message = f"{actor_display_name} tarafından '{dof.title}' {dof_id_text} başlıklı DÖF üzerinde bir değişiklik yapıldı"
        
        # Yeni bildirim yardımcı modülünü kullanarak bildirimleri gönder
        notification_count = notify_all_relevant_users(dof, action_type, actor, message)
        
        current_app.logger.info(f"DÖF #{dof.id} için {notification_count} bildirim gönderildi")
        return True
    
    except ImportError:
        # notification_helper modülü bulunamadıysa, eski yöntemle bildirim göndermeyi dene
        current_app.logger.error("notification_helper modülü bulunamadı! Eski bildirim sistemi kullanılıyor.")
        
        try:
            # Eski yöntem: Yerel olarak create_notification'u kullan
            if not hasattr(notify_for_dof, "_legacy_warning_shown"):
                current_app.logger.warning("UYARI: Eski bildirim sistemi kullanılıyor - bildirimler düzgün çalışmayabilir!")
                notify_for_dof._legacy_warning_shown = True
                
            # İlgili kullanıcıları bul
            creator = User.query.get(dof.created_by) if dof.created_by else None
            assignee = User.query.get(dof.assigned_to) if dof.assigned_to else None
            quality_managers = User.query.filter_by(role='QUALITY_MANAGER', active=True).all()
            
            # Kalite yöneticilerine mutlaka bildirim gönder
            for qm in quality_managers:
                if qm and qm.id != getattr(actor_name, 'id', None):
                    create_notification(qm.id, message, dof.id)
                    current_app.logger.info(f"Kalite yöneticisine bildirim gönderildi: {qm.email}")
            
            # Oluşturan ve atanan kişilere bildirim
            if creator and creator.id != getattr(actor_name, 'id', None):
                create_notification(creator.id, message, dof.id)
                
            if assignee and assignee.id != getattr(actor_name, 'id', None):
                create_notification(assignee.id, message, dof.id)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Bildirim hatası: {str(e)}")
            return False
    
    except Exception as e:
        current_app.logger.error(f"Bildirim gönderme hatası: {str(e)}")
        # Hatayı detaylı logla
        import traceback
        current_app.logger.error(traceback.format_exc())
        return False
    

def get_dof_status_counts(department_id=None, user_id=None, current_user=None):
    """
    DÖF'lerin durum bazında sayılarını kullanıcı yetkisine göre filtreli şekilde getir
    Eğer department_id belirtilirse, sadece o departmana ait DÖF'leri sayar
    Eğer user_id belirtilirse, sadece o kullanıcının oluşturduğu DÖF'leri sayar
    Eğer current_user belirtilirse, kullanıcının yetkisi dahilindeki DÖF'leri gösterir
    
    Args:
        department_id: Departman ID (isteğe bağlı)
        user_id: Kullanıcı ID (isteğe bağlı)
        current_user: Mevcut oturum kullanıcısı (yetki kontrollerini uygulamak için)
        
    Returns:
        DöF sayılarını içeren sözlük
    """
    from models import DOF, User, UserRole
    from sqlalchemy import func, or_
    from flask import current_app
    import sys
    
    # Başlangıç sorgusu
    base_query = db.session.query(DOF)
    
    # İlişkili DÖF'leri filtreleme
    # İlişkili DÖF'ler başlığında "[İlişkili #" prefix'i içerir
    related_dof_filter = ~DOF.title.like("[İlişkili #%")
    base_query = base_query.filter(related_dof_filter)
    current_app.logger.info("DÖF özet sayıları için ilişkili DÖF'ler filtrelendi")
    
    # Kullanıcı ve departman filtreleri
    if user_id:
        base_query = base_query.filter(DOF.created_by == user_id)
    elif department_id:
        # Departman kullanıcılarını bul
        dept_users = User.query.filter_by(department_id=department_id).all()
        dept_user_ids = [user.id for user in dept_users]
        
        # Departman filtresi uygula
        if dept_user_ids:
            base_query = base_query.filter(or_(
                DOF.department_id == department_id,
                DOF.created_by.in_(dept_user_ids)
            ))
        else:
            # Sadece departmana atanan DÖF'leri filtrele
            base_query = base_query.filter(DOF.department_id == department_id)
    
    # Eğer current_user belirtilmişse ve normal admin veya kalite yöneticisi değilse,
    # yönetilen departmanların DÖF'lerini göster
    if current_user:
        try:
            # Merkezi AuthService ile yetki kontrolü
            if hasattr(current_user, 'role') and current_user.role not in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
                # AuthService'i içe aktar
                try:
                    from auth_service import AuthService
                    
                    # Loglamayı aktif et
                    current_app.logger.info(f"DÖF özet sayıları için AuthService filtrelemesi uygulanıyor: {current_user.username}, rol={current_user.role}")
                    
                    # AuthService kullanarak yetkiye göre sorguyu filtrele
                    base_query = AuthService.filter_viewable_dofs(current_user, base_query)
                except ImportError:
                    current_app.logger.error("AuthService import edilemedi: " + str(sys.exc_info()[1]))
                except Exception as e:
                    current_app.logger.error(f"AuthService DÖF filtreleme hatası: {str(e)}")
        except Exception as e:
            current_app.logger.error(f"DÖF özet sayıları filtreleme hatası: {str(e)}")
    
    # Debug için hangi DÖF'lerin bulunduğunu kontrol et
    all_dofs = base_query.all()
    current_app.logger.info(f"DEBUG - Bulunan DÖF'ler: {[(dof.id, dof.title, dof.status) for dof in all_dofs]}")
    
    # Duruma göre gruplama için yeniden sorgu oluştur
    query = db.session.query(DOF.status, func.count(DOF.id)).select_from(base_query.subquery())
    
    # Duruma göre gruplama ve sonuç
    result = query.group_by(DOF.status).all()
    
    # Debug logging için durum sayılarını logla
    current_app.logger.info(f"DEBUG - Durum sayıları raw query sonucu: {result}")
    
    counts = {
        'draft': 0,
        'submitted': 0,
        'in_review': 0,
        'assigned': 0,
        'in_progress': 0,
        'resolved': 0,
        'closed': 0,
        'rejected': 0,
        'planning': 0,
        'implementation': 0,
        'completed': 0,
        'source_review': 0,
        'total': 0
    }
    
    total = 0
    for status, count in result:
        total += count
        current_app.logger.info(f"DEBUG - Durum {status} için sayı: {count}")
        if status == DOFStatus.DRAFT:
            counts['draft'] = count
        elif status == DOFStatus.SUBMITTED:
            counts['submitted'] = count
        elif status == DOFStatus.IN_REVIEW:
            counts['in_review'] = count
        elif status == DOFStatus.ASSIGNED:
            counts['assigned'] = count
        elif status == DOFStatus.IN_PROGRESS:
            counts['in_progress'] = count
        elif status == DOFStatus.RESOLVED:
            counts['resolved'] = count
        elif status == DOFStatus.CLOSED:
            counts['closed'] = count
        elif status == DOFStatus.REJECTED:
            counts['rejected'] = count
        elif status == DOFStatus.PLANNING:
            counts['planning'] = count
        elif status == DOFStatus.IMPLEMENTATION:
            counts['implementation'] = count
        elif status == DOFStatus.COMPLETED:
            counts['completed'] = count
        elif status == DOFStatus.SOURCE_REVIEW:
            counts['source_review'] = count
    
    counts['total'] = total
    
    # MANUEL SAYIM FIX: SQL GROUP BY sorunu için manuel sayım kullan
    from models import DOF
    all_dofs_manual = base_query.all()
    
    # Manuel sayım
    manual_counts = {}
    for dof in all_dofs_manual:
        if dof.status in manual_counts:
            manual_counts[dof.status] += 1
        else:
            manual_counts[dof.status] = 1
    
    # Manuel sayımdan counts'u yeniden oluştur
    counts = {
        'draft': 0,
        'submitted': 0,
        'in_review': 0,
        'assigned': 0,
        'in_progress': 0,
        'resolved': 0,
        'closed': 0,
        'rejected': 0,
        'planning': 0,
        'implementation': 0,
        'completed': 0,
        'source_review': 0,
        'total': 0
    }
    
    for status_enum, count in manual_counts.items():
        if status_enum == DOFStatus.DRAFT:
            counts['draft'] = count
        elif status_enum == DOFStatus.SUBMITTED:
            counts['submitted'] = count
        elif status_enum == DOFStatus.IN_REVIEW:
            counts['in_review'] = count
        elif status_enum == DOFStatus.ASSIGNED:
            counts['assigned'] = count
        elif status_enum == DOFStatus.IN_PROGRESS:
            counts['in_progress'] = count
        elif status_enum == DOFStatus.RESOLVED:
            counts['resolved'] = count
        elif status_enum == DOFStatus.CLOSED:
            counts['closed'] = count
        elif status_enum == DOFStatus.REJECTED:
            counts['rejected'] = count
        elif status_enum == DOFStatus.PLANNING:
            counts['planning'] = count
        elif status_enum == DOFStatus.IMPLEMENTATION:
            counts['implementation'] = count
        elif status_enum == DOFStatus.COMPLETED:
            counts['completed'] = count
        elif status_enum == DOFStatus.SOURCE_REVIEW:
            counts['source_review'] = count
    
    counts['total'] = len(all_dofs_manual)
    
    # Yeni dashboard için özel hesaplamalar ekle
    # Devam Eden: Aktif durumda olan DÖF'ler (taslak ve kapatılan hariç)
    counts['in_progress_total'] = (
        counts['submitted'] + counts['in_review'] + counts['assigned'] + 
        counts['in_progress'] + counts['planning'] + counts['implementation'] + 
        counts['completed'] + counts['source_review']
    )
    
    # Atanmayı Bekleyen: İncelemede olan DÖF'ler (2. aşama)
    counts['pending_approval'] = counts['in_review']
    
    # Kapatılan: Tamamlanan ve çözülmüş DÖF'ler
    counts['closed_total'] = counts['closed'] + counts['resolved']
    
    return counts

def get_department_stats():
    """
    Departman bazında DÖF istatistiklerini detaylı şekilde getir
    """
    from models import DOF, Department, DOFAction, User
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_, or_
    from app import db
    
    # Tüm departmanları al
    departments = Department.query.all()
    stats = []
    
    # Bugün ve son 30 gün için sorgularda kullanılacak tarihler
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    thirty_days_ago = today - timedelta(days=30)
    seven_days_ago = today - timedelta(days=7)
    
    for dept in departments:
        # DEPARTMANA ATANAN DÖF'ıER
        assigned_dofs = DOF.query.filter_by(department_id=dept.id).all()
        
        # Toplam atanan DÖF sayısı
        assigned_total = len(assigned_dofs)
        assigned_closed = len([d for d in assigned_dofs if d.status == DOFStatus.CLOSED])
        assigned_rejected = len([d for d in assigned_dofs if d.status == DOFStatus.REJECTED])
        assigned_active = assigned_total - assigned_closed - assigned_rejected
        
        # Atanan DÖF'lerin durum dağılımı
        assigned_draft = len([d for d in assigned_dofs if d.status == DOFStatus.DRAFT])
        assigned_submitted = len([d for d in assigned_dofs if d.status == DOFStatus.SUBMITTED])
        assigned_in_review = len([d for d in assigned_dofs if d.status == DOFStatus.IN_REVIEW])
        assigned_assigned = len([d for d in assigned_dofs if d.status == DOFStatus.ASSIGNED])
        assigned_in_progress = len([d for d in assigned_dofs if d.status == DOFStatus.IN_PROGRESS])
        assigned_resolved = len([d for d in assigned_dofs if d.status == DOFStatus.RESOLVED])
        assigned_planning = len([d for d in assigned_dofs if d.status == DOFStatus.PLANNING])
        assigned_implementation = len([d for d in assigned_dofs if d.status == DOFStatus.IMPLEMENTATION])
        assigned_completed = len([d for d in assigned_dofs if d.status == DOFStatus.COMPLETED])
        assigned_source_review = len([d for d in assigned_dofs if d.status == DOFStatus.SOURCE_REVIEW])
        
        # Son 30 günde atanan DÖF sayısı
        assigned_recent = len([d for d in assigned_dofs if d.created_at >= thirty_days_ago])
        
        # Öncelik alanı kaldırıldı
        assigned_high_priority = 0
        assigned_medium_priority = 0
        assigned_low_priority = 0
        
        # Termini geçmiş atanan DÖF'ler
        assigned_overdue = len([d for d in assigned_dofs if d.deadline and d.deadline < today and d.status not in [DOFStatus.CLOSED, DOFStatus.REJECTED]])
        
        # Son 7 gün içinde kapatılan atanan DÖF'ler
        assigned_recently_closed = len([d for d in assigned_dofs if d.status == DOFStatus.CLOSED and d.closed_at and d.closed_at >= seven_days_ago])
        
        # DEPARTMANIN AÇTIĞI DÖF'LER
        # Departman üyelerinin ID'lerini al
        dept_user_ids = [u.id for u in User.query.filter_by(department_id=dept.id).all()]
        
        # Departman üyeleri tarafından oluşturulan DÖF'leri al
        created_dofs = DOF.query.filter(DOF.created_by.in_(dept_user_ids)).all() if dept_user_ids else []
        
        # Toplam açılan DÖF sayısı
        created_total = len(created_dofs)
        created_closed = len([d for d in created_dofs if d.status == DOFStatus.CLOSED])
        created_rejected = len([d for d in created_dofs if d.status == DOFStatus.REJECTED])
        created_active = created_total - created_closed - created_rejected
        
        # Açılan DÖF'lerin durum dağılımı
        created_draft = len([d for d in created_dofs if d.status == DOFStatus.DRAFT])
        created_submitted = len([d for d in created_dofs if d.status == DOFStatus.SUBMITTED])
        created_in_review = len([d for d in created_dofs if d.status == DOFStatus.IN_REVIEW])
        created_assigned = len([d for d in created_dofs if d.status == DOFStatus.ASSIGNED])
        created_in_progress = len([d for d in created_dofs if d.status == DOFStatus.IN_PROGRESS])
        created_resolved = len([d for d in created_dofs if d.status == DOFStatus.RESOLVED])
        created_planning = len([d for d in created_dofs if d.status == DOFStatus.PLANNING])
        created_implementation = len([d for d in created_dofs if d.status == DOFStatus.IMPLEMENTATION])
        created_completed = len([d for d in created_dofs if d.status == DOFStatus.COMPLETED])
        created_source_review = len([d for d in created_dofs if d.status == DOFStatus.SOURCE_REVIEW])
        
        # Son 30 günde açılan DÖF sayısı
        created_recent = len([d for d in created_dofs if d.created_at >= thirty_days_ago])
        
        # Ortalama çözüm süresi hesaplama
        avg_resolution_time = 0
        if assigned_closed > 0:
            # Kapatılmış DÖF'lerin ID'lerini al
            closed_dof_ids = [d.id for d in assigned_dofs if d.status == DOFStatus.CLOSED]
            
            # Ortalama çözüm süresini hesapla
            resolution_time_result = db.session.query(
                func.avg(DOFAction.created_at - DOF.created_at)
            ).join(DOF, DOF.id == DOFAction.dof_id).filter(
                DOFAction.action_type == 2,        # Durum değişikliği
                DOFAction.new_status == 6,        # Kapatıldı
                DOF.id.in_(closed_dof_ids)
            ).scalar()
            
            # Gün cinsinden süreyi elde et
            if resolution_time_result is not None:
                try:
                    # timedelta nesnesi ise
                    avg_resolution_time = round(resolution_time_result.total_seconds() / (24 * 3600), 1)
                except AttributeError:
                    # Decimal/Float değeri ise
                    avg_resolution_time = round(float(resolution_time_result) / (24 * 3600), 1)
        
        # DÖF tipi dağılımı (düzeltici/önleyici)
        corrective_count = len([d for d in assigned_dofs if d.dof_type == 1])  # Düzeltici
        preventive_count = len([d for d in assigned_dofs if d.dof_type == 2])  # Önleyici
        
        # Tüm istatistikleri tek bir sozlükte birleştir
        stats.append({
            'department': dept.name,
            
            # Toplam istatistikler
            'total': assigned_total,
            'closed': assigned_closed,
            'active': assigned_active,
            'rejected': assigned_rejected,
            
            # Yüzdeler
            'closed_percent': round((assigned_closed / assigned_total * 100) if assigned_total > 0 else 0, 1),
            'active_percent': round((assigned_active / assigned_total * 100) if assigned_total > 0 else 0, 1),
            'rejected_percent': round((assigned_rejected / assigned_total * 100) if assigned_total > 0 else 0, 1),
            
            # Ortalama çözüm süresi
            'avg_resolution_time': avg_resolution_time,
            
            # Atanan DÖF istatistikleri
            'assigned_total': assigned_total,
            'assigned_active': assigned_active,
            'assigned_closed': assigned_closed,
            'assigned_rejected': assigned_rejected,
            'assigned_draft': assigned_draft,
            'assigned_submitted': assigned_submitted,
            'assigned_in_review': assigned_in_review,
            'assigned_assigned': assigned_assigned,
            'assigned_in_progress': assigned_in_progress,
            'assigned_resolved': assigned_resolved,
            'assigned_planning': assigned_planning,
            'assigned_implementation': assigned_implementation,
            'assigned_completed': assigned_completed,
            'assigned_source_review': assigned_source_review,
            'assigned_recent': assigned_recent,
            'assigned_high_priority': assigned_high_priority,
            'assigned_medium_priority': assigned_medium_priority,
            'assigned_low_priority': assigned_low_priority,
            'assigned_overdue': assigned_overdue,
            'assigned_recently_closed': assigned_recently_closed,
            
            # Açılan DÖF istatistikleri
            'created_total': created_total,
            'created_active': created_active,
            'created_closed': created_closed,
            'created_rejected': created_rejected,
            'created_draft': created_draft,
            'created_submitted': created_submitted,
            'created_in_review': created_in_review,
            'created_assigned': created_assigned,
            'created_in_progress': created_in_progress,
            'created_resolved': created_resolved,
            'created_planning': created_planning,
            'created_implementation': created_implementation,
            'created_completed': created_completed,
            'created_source_review': created_source_review,
            'created_recent': created_recent,
            
            # DÖF tipi istatistikleri
            'corrective_count': corrective_count,
            'preventive_count': preventive_count
        })
    
    # İstatistikleri toplam DÖF sayısına göre sırala (atanan + oluşturulan toplam, büyükten küçüğe)
    stats.sort(key=lambda x: (x['assigned_total'] + x['created_total']), reverse=True)
    
    return stats

def can_user_edit_dof(user, dof):
    """
    Kullanıcının DÖF'u düzenleyebilme yetkisi olup olmadığını kontrol et
    """
    from models import UserRole, DOFStatus
    from flask import current_app
    
    current_app.logger.info(f"Yetki kontrolü - Kullanıcı: {user.full_name} (Rol: {user.role}), DÖF: #{dof.id} (Durum: {dof.status})")
    
    # Admin her zaman düzenleyebilir
    if user.role == UserRole.ADMIN:
        current_app.logger.info("Admin yetkisi - Erişim verildi")
        return True
    
    # Kalite yöneticileri inceleme aşamasındaki, planlama aşamasındaki ve çözülmüş DÖF'leri değerlendirebilir
    if user.role == UserRole.QUALITY_MANAGER:
        # Çözüm aşamalarına erişim
        if dof.status in [DOFStatus.SUBMITTED, DOFStatus.IN_REVIEW, DOFStatus.PLANNING, DOFStatus.RESOLVED]:
            return True
        
        # Kalite yöneticileri departman değişikliği yapabilir (tüm durumlar için)
        # Departman değiştirme işlemi için özel yetki
        if dof.status in [DOFStatus.ASSIGNED, DOFStatus.IN_PROGRESS, DOFStatus.IMPLEMENTATION, DOFStatus.COMPLETED, DOFStatus.SOURCE_REVIEW]:
            return True
        
        # Kalite yöneticisi aynı zamanda kaynak departman yöneticisi ise tamamlanmış DÖF'leri inceleyebilir
        if dof.creator and dof.creator.department_id == user.department_id and dof.status == DOFStatus.COMPLETED:
            return True
            
        return False
    
    # Oluşturan kişi (tüm aşamalarda yorum ekleyebilir)
    if dof.created_by == user.id:
        current_app.logger.info("DÖF oluşturan kişi yetkisi - Erişim verildi")
        return True
    
    # Departman yöneticileri ve franchise departman yöneticileri kendi departmanına ait DÖF'lere her zaman erişebilir
    if (user.role == UserRole.DEPARTMENT_MANAGER or user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER) and dof.department_id == user.department_id:
        current_app.logger.info("Atanan departman yöneticisi yetkisi - Erişim verildi")
        return True
            
    # DÖF'u oluşturan kişi (tamamlanan DÖF'leri değerlendirebilir)
    if dof.created_by == user.id and dof.status == DOFStatus.COMPLETED:
        return True
        
    # Kaynak departman yöneticisi (tamamlanan DÖF'leri inceleyebilir veya kaynak değerlendirme yapabilir)
    if (user.role == UserRole.DEPARTMENT_MANAGER or user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER) and user.department_id is not None:
        # DÖF'u açan departman ise ve tamamlanmış durumda veya kaynak değerlendirme aşamasında
        # DÖF'u oluşturan kişinin departmanını kontrol ediyoruz
        if dof.creator and dof.creator.department_id == user.department_id:
            if dof.status in [10, 11]:  # 10: COMPLETED, 11: SOURCE_REVIEW
                return True
        
        # Veya DÖF'u oluşturan kişinin departmanı kaynak departman ise
        # Circular import'u önlemek için lazy import kullan
        try:
            from models import User
            creator = User.query.get(dof.created_by)
            if creator and creator.department_id == user.department_id:
                if dof.status in [10, 11]:  # 10: COMPLETED, 11: SOURCE_REVIEW
                    return True
        except ImportError:
            current_app.logger.error("User modeli import edilemedi")
            pass
    
    return False

def get_next_possible_statuses(current_status, user_role):
    """
    Mevcut duruma ve kullanıcı rolüne göre sonraki olası durumları getir
    """
    from models import DOFStatus, UserRole
    
    status_flow = {
        # Admin için - tüm işlemleri yapabilir
        (UserRole.ADMIN, DOFStatus.DRAFT): [DOFStatus.SUBMITTED],
        (UserRole.ADMIN, DOFStatus.SUBMITTED): [DOFStatus.IN_REVIEW, DOFStatus.REJECTED],
        (UserRole.ADMIN, DOFStatus.IN_REVIEW): [DOFStatus.ASSIGNED, DOFStatus.REJECTED],
        (UserRole.ADMIN, DOFStatus.ASSIGNED): [DOFStatus.PLANNING],
        (UserRole.ADMIN, DOFStatus.PLANNING): [DOFStatus.IMPLEMENTATION, DOFStatus.ASSIGNED],
        (UserRole.ADMIN, DOFStatus.IMPLEMENTATION): [DOFStatus.COMPLETED],
        (UserRole.ADMIN, DOFStatus.COMPLETED): [DOFStatus.SOURCE_REVIEW],
        (UserRole.ADMIN, DOFStatus.SOURCE_REVIEW): [DOFStatus.RESOLVED, DOFStatus.IN_PROGRESS],
        (UserRole.ADMIN, DOFStatus.IN_PROGRESS): [DOFStatus.PLANNING],
        (UserRole.ADMIN, DOFStatus.RESOLVED): [DOFStatus.CLOSED, DOFStatus.IN_PROGRESS],
        (UserRole.ADMIN, DOFStatus.CLOSED): [],
        (UserRole.ADMIN, DOFStatus.REJECTED): [],
        
        # Kalite Yöneticisi için - değerlendirme ve onaylama, iptal
        (UserRole.QUALITY_MANAGER, DOFStatus.DRAFT): [],  # Artık taslakları düzenleyemeyecek
        (UserRole.QUALITY_MANAGER, DOFStatus.SUBMITTED): [DOFStatus.IN_REVIEW, DOFStatus.REJECTED],
        (UserRole.QUALITY_MANAGER, DOFStatus.IN_REVIEW): [DOFStatus.ASSIGNED, DOFStatus.REJECTED],
        (UserRole.QUALITY_MANAGER, DOFStatus.PLANNING): [DOFStatus.IMPLEMENTATION, DOFStatus.ASSIGNED],
        (UserRole.QUALITY_MANAGER, DOFStatus.RESOLVED): [DOFStatus.CLOSED, DOFStatus.IN_PROGRESS],
        (UserRole.QUALITY_MANAGER, DOFStatus.CLOSED): [],
        (UserRole.QUALITY_MANAGER, DOFStatus.REJECTED): [],
        
        # Departman Yöneticisi için - yeni akış: plan oluştur, uygula, tamamla
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.DRAFT): [],  # Düzenleyemez
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.SUBMITTED): [],  # Değiştiremez
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.IN_REVIEW): [],  # Değiştiremez
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.ASSIGNED): [DOFStatus.PLANNING],  # Kök neden ve aksiyon planı ekler
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.PLANNING): [],  # Kalite onayı bekler
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.IMPLEMENTATION): [DOFStatus.COMPLETED],  # Tamamlandı olarak işaretler
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.COMPLETED): [5, 4],  # 5: Çözüldü, 4: Çözümden Memnun Değilim (Kaynak departman için)
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.SOURCE_REVIEW): [],  # Sadece kaynak departman onaylayabilir
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.IN_PROGRESS): [DOFStatus.PLANNING],  # Düzeltme sonrası tekrar aksiyon planı
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.RESOLVED): [],  # Kapatamaz
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.CLOSED): [],
        (UserRole.DEPARTMENT_MANAGER, DOFStatus.REJECTED): [],
        
        # Franchise Departman Yöneticisi için - departman yöneticisi ile aynı yetkiler
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.DRAFT): [],  # Düzenleyemez
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.SUBMITTED): [],  # Değiştiremez
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.IN_REVIEW): [],  # Değiştiremez
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.ASSIGNED): [DOFStatus.PLANNING],  # Kök neden ve aksiyon planı ekler
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.PLANNING): [],  # Kalite onayı bekler
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.IMPLEMENTATION): [DOFStatus.COMPLETED],  # Tamamlandı olarak işaretler
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.COMPLETED): [5, 4],  # 5: Çözüldü, 4: Çözümden Memnun Değilim (Kaynak departman için)
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.SOURCE_REVIEW): [],  # Sadece kaynak departman onaylayabilir
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.IN_PROGRESS): [DOFStatus.PLANNING],  # Düzeltme sonrası tekrar aksiyon planı
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.RESOLVED): [],  # Kapatamaz
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.CLOSED): [],
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, DOFStatus.REJECTED): [],
        
        # Sayısal durum kodları için ekstra destekler
        (UserRole.DEPARTMENT_MANAGER, 10): [5, 4],  # 10: COMPLETED (Aksiyonlar Tamamlandı), 5: RESOLVED (Çözüldü), 4: IN_PROGRESS (Çözümden Memnun Değilim)
        (UserRole.FRANCHISE_DEPARTMENT_MANAGER, 10): [5, 4],  # 10: COMPLETED (Aksiyonlar Tamamlandı), 5: RESOLVED (Çözüldü), 4: IN_PROGRESS (Çözümden Memnun Değilim)
        
        # Normal Kullanıcı için - sadece taslak oluşturup gönderebilir
        (UserRole.USER, DOFStatus.DRAFT): [DOFStatus.SUBMITTED],  # Sadece taslak gönderebilir
        (UserRole.USER, DOFStatus.SUBMITTED): [],  # Diğer durumları değiştiremez
        (UserRole.USER, DOFStatus.IN_REVIEW): [],
        (UserRole.USER, DOFStatus.ASSIGNED): [],
        (UserRole.USER, DOFStatus.PLANNING): [],
        (UserRole.USER, DOFStatus.IMPLEMENTATION): [],
        (UserRole.USER, DOFStatus.COMPLETED): [],
        (UserRole.USER, DOFStatus.SOURCE_REVIEW): [],
        (UserRole.USER, DOFStatus.IN_PROGRESS): [],
        (UserRole.USER, DOFStatus.RESOLVED): [],
        (UserRole.USER, DOFStatus.CLOSED): [],
        (UserRole.USER, DOFStatus.REJECTED): []
    }
    
    return status_flow.get((user_role, current_status), [])

def can_user_change_status(user, dof, new_status):
    """
    Kullanıcının DÖF durumunu değiştirme yetkisi olup olmadığını kontrol et
    """
    from models import UserRole, DOFStatus
    
    # Öncelikle rol bazlı kısıtlamaları kontrol et
    possible_statuses = get_next_possible_statuses(dof.status, user.role)
    
    # Eğer yeni durum olası durumlar listesinde yoksa, değişiklik yapılamaz
    if new_status not in possible_statuses:
        return False
    
    # Normal kullanıcılar sadece kendi oluşturdukları taslakları gönderebilir
    if user.role == UserRole.USER:
        if dof.created_by != user.id:
            return False
        if dof.status != DOFStatus.DRAFT or new_status != DOFStatus.SUBMITTED:
            return False
    
    # Departman yöneticileri ve franchise departman yöneticileri için özel kontroller
    if user.role == UserRole.DEPARTMENT_MANAGER or user.role == UserRole.FRANCHISE_DEPARTMENT_MANAGER:
        # Tamamlandı veya Kaynak İncelemesi durumunda kaynak departman için, DÖF'un oluşturan departman için özel izin
        if dof.status in [10, 11] and new_status in [5, 4]:  # 10: COMPLETED, 11: SOURCE_REVIEW, 5: RESOLVED, 4: IN_PROGRESS
            # DÖF'u açan departman mı kontrol et (DÖF'u oluşturan kişinin departmanı)
            if dof.creator and dof.creator.department_id == user.department_id:
                return True
            
            # DÖF'u oluşturan kişinin departmanı kaynak departman mı kontrol et
            from models import User
            creator = User.query.get(dof.created_by)
            if creator and creator.department_id == user.department_id:
                return True
                
            # DÖF'u doğrudan oluşturan kişi mi kontrol et
            if dof.created_by == user.id:
                return True
        
        # Diğer durumlar için sadece atanan departman yöneticileri değişiklik yapabilir
        elif dof.department_id != user.department_id:
            return False
        
    # Kalite yöneticileri için özel kontroller
    if user.role == UserRole.QUALITY_MANAGER:
        # Eğer kalite yöneticisi aynı zamanda kaynak departman yöneticisi ise, tamamlanmış DÖF'ler için onay verebilir
        if dof.status == DOFStatus.COMPLETED and dof.creator and dof.creator.department_id == user.department_id:
            if new_status in [DOFStatus.RESOLVED, DOFStatus.IN_PROGRESS]:  # Çözüldü veya Çözümden Memnun Değilim
                return True
        
        # İnceleme aşamasındaki DÖF'ler için Atanan ya da Red durumuna geçiş
        if dof.status == DOFStatus.IN_REVIEW:
            if new_status not in [DOFStatus.ASSIGNED, DOFStatus.REJECTED]:
                return False
                
        # Kalite yöneticileri DÖF kapatabilir
        if dof.status == DOFStatus.RESOLVED and new_status == DOFStatus.CLOSED:
            return True
    
    return True
