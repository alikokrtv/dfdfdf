"""
Bildirim sistemi yardımcı fonksiyonları
Bu modül, bildirimler göndermek için kullanılan fonksiyonları içerir
"""
import datetime
import threading
from flask import current_app
from flask_mail import Message
from extensions import db, mail
from models import User, Notification

def send_direct_email(email, subject, body_html, body_text=None):
    """E-posta gönderme fonksiyonu - utils.py içindeki send_email fonksiyonunu kullanır"""
    try:
        current_app.logger.info(f"Bildirim e-postası gönderiliyor: Konu: {subject}, Alıcı: {email}")
        
        # utils.py içindeki düzeltilmiş send_email fonksiyonunu kullan
        from utils import send_email
        
        # Alıcı adresini liste formatına çevir
        recipients = [email] if isinstance(email, str) else email
        
        # E-posta gönder
        result = send_email(subject, recipients, body_html, body_text)
        
        # Başarılı log
        current_app.logger.info(f"E-posta başarıyla gönderildi: {email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Bildirim e-posta gönderme hatası: {str(e)}")
        return False

def send_email_async(email, subject, body_html, body_text=None):
    """E-posta gönderme işlemini arka planda asenkron olarak yapar"""
    try:
        current_app.logger.info(f"Asenkron e-posta gönderimi başlatılıyor: {subject}")
        # utils.py içindeki send_email_async fonksiyonunu doğrudan kullan
        from utils import send_email_async as utils_send_email_async
        
        # Alıcı adresini liste formatına çevir
        recipients = [email] if isinstance(email, str) else email
        
        # Asenkron gönderim
        utils_send_email_async(subject, recipients, body_html, body_text)
        return True
    except Exception as e:
        current_app.logger.error(f"Asenkron e-posta gönderme hatası: {str(e)}")
        return False

def create_user_notification(user_id, message, dof_id=None, send_email=True):
    """Kullanıcıya bildirim oluşturur ve isteğe bağlı olarak email gönderir
    
    Args:
        user_id: Kullanıcı ID
        message: Bildirim mesajı
        dof_id: İlgili DÖF ID (isteğe bağlı)
        send_email: True ise e-posta gönderir, False ise sadece uygulama bildirimi oluşturur
    """
    current_app.logger.info(f"Bildirim oluşturuluyor: User ID: {user_id}, DOF ID: {dof_id}")
    
    try:
        # Kullanıcıyı kontrol et
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"Bildirim oluşturulamadı: Kullanıcı bulunamadı (ID: {user_id})")
            return None
        
        # Bildirim oluştur ve kaydet
        notification = Notification(
            user_id=user_id,
            message=message,
            dof_id=dof_id,
            created_at=datetime.datetime.now(),
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        current_app.logger.info(f"Bildirim veritabanına kaydedildi: ID: {notification.id}")
        
        # E-posta göndermeyi dene (sadece send_email=True ise)
        if user.email and send_email:
            try:
                current_app.logger.info(f"Bildirim e-postası gönderiliyor: {user.email}")
                
                # DÖF bağlantısı için daha modern URL oluşturma
                try:
                    from utils.email_helpers import get_app_url
                    dof_url = get_app_url(f"dof/detail/{dof_id}") if dof_id else ""
                except Exception:
                    dof_url = f"{current_app.config.get('BASE_URL', '')}dof/detail/{dof_id}" if dof_id else ""
                
                # Modern ve güzel e-posta şablonu
                subject = "DÖF Sistemi Bildirim"
                body_html = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                        .header {{ background-color: #f8f8f8; padding: 10px; border-bottom: 1px solid #ddd; }}
                        .footer {{ background-color: #f8f8f8; padding: 10px; border-top: 1px solid #ddd; margin-top: 20px; font-size: 12px; color: #777; }}
                        .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>DÖF Sistemi Bildirim</h2>
                        </div>
                        
                        <p>Sayın Yetkili,</p>
                        
                        <p>{message}</p>
                        
                        {f'<p><a href="{dof_url}" class="button">DÖF Detaylarını Görüntüle</a></p>' if dof_id else ''}
                        
                        <div class="footer">
                            <p>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                body_text = f"DÖF Sistemi Bildirim\n\n{message}\n\nBu otomatik bir bildirimdir, lütfen yanıtlamayınız."
                
                # Doğrudan gönder (asenkron yerine) - daha güvenilir
                current_app.logger.info(f"DÖF bildirimi için e-posta gönderiliyor: {user.email}")
                from utils import send_email
                result = send_email(subject, [user.email], body_html, body_text)
                current_app.logger.info(f"E-posta gönderim sonucu: {result}")
                
            except Exception as e:
                current_app.logger.error(f"E-posta gönderiminde hata: {str(e)}")
                # E-posta hatası bildirimin oluşmasını engellememeli
        elif not user.email:
            current_app.logger.warning(f"Kullanıcının e-posta adresi yok: {user_id}")
        elif not send_email:
            current_app.logger.info(f"E-posta gönderimi devre dışı bırakıldı: {user_id}")
        
        return notification
    
    except Exception as e:
        current_app.logger.error(f"Bildirim oluşturma hatası: {str(e)}")
        db.session.rollback()
        return None

def notify_all_relevant_users(dof, action_type, actor, message, send_email=True):
    """Bir DÖF ile ilgili tüm ilgili kullanıcılara bildirim gönderir
    
    Args:
        dof: DÖF nesnesi
        action_type: İşlem tipi (create, review, resolve, vb.)
        actor: İşlemi yapan kullanıcı nesnesi
        message: Gönderilecek bildirim mesajı
        send_email: True ise e-posta bildirimini de gönderir, False ise sadece uygulama bildirimi gönderir
    """
    current_app.logger.info(f"DÖF #{dof.id} için bildirim gönderme başlatıldı. Eylem: {action_type}")
    
    try:
        # İlgili kullanıcıları bul
        notify_users = []
        
        # Oluşturan
        if dof.created_by and (actor is None or dof.created_by != getattr(actor, 'id', None)):
            creator = User.query.get(dof.created_by)
            if creator and creator not in notify_users:
                notify_users.append(creator)
                current_app.logger.info(f"Oluşturucu bildirimi: {creator.email}")
        
        # Atanan 
        if dof.assigned_to and (actor is None or dof.assigned_to != getattr(actor, 'id', None)):
            assignee = User.query.get(dof.assigned_to)
            if assignee and assignee not in notify_users:
                notify_users.append(assignee)
                current_app.logger.info(f"Atanan bildirimi: {assignee.email}")
        
        # Departman yöneticisi
        if dof.department_id:
            # ENUM KULLAN - String değil
            from models import UserRole
            
            # Doğru tipte değer kullan
            dept_managers = User.query.filter_by(
                department_id=dof.department_id, 
                active=True
            ).filter(User.role.in_([UserRole.DEPARTMENT_MANAGER, UserRole.FRANCHISE_DEPARTMENT_MANAGER])).all()
            
            for manager in dept_managers:
                if manager and manager not in notify_users and (actor is None or manager.id != getattr(actor, 'id', None)):
                    notify_users.append(manager)
                    current_app.logger.info(f"Departman yöneticisi bildirimi: {manager.email}")
        
        # Kalite yöneticileri (en kritik grup - tüm olayları görebilmeli)
        from models import UserRole
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        
        if quality_managers:
            current_app.logger.info(f"{len(quality_managers)} kalite yöneticisi bulundu")
            for qm in quality_managers:
                if qm and qm not in notify_users and (actor is None or qm.id != getattr(actor, 'id', None)):
                    notify_users.append(qm)
                    current_app.logger.info(f"Kalite yöneticisi bildirimi: {qm.email}")
        else:
            current_app.logger.warning("Kalite yöneticisi bulunamadı!")
        
        # Bildirimleri gönder (e-posta parametresini kullanarak)
        notification_count = 0
        for user in notify_users:
            # send_email parametresini geçir
            notification = create_user_notification(user.id, message, dof.id, send_email=send_email)
            if notification:
                notification_count += 1
                
        current_app.logger.info(f"DÖF #{dof.id} için {notification_count} bildirim gönderildi")
        return notification_count
    
    except Exception as e:
        current_app.logger.error(f"Bildirim gönderme hatası: {str(e)}")
        return 0
