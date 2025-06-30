"""
Bildirim sistemi için doğrudan erişim sağlayan yardımcı modül
Bu modül, DÖF işlemleri için kullanılacak bildirim fonksiyonlarını içerir
"""

import datetime
from flask import current_app
from app import db
from models import User, Notification, DOF, UserRole

def send_direct_notification(user_id, message, dof_id=None):
    """
    Kullanıcıya doğrudan bildirim oluşturur (veritabanına kaydeder)
    """
    try:
        # Kullanıcıyı kontrol et
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"Kullanıcı bulunamadı: ID {user_id}")
            return None
            
        # Bildirim oluştur
        notification = Notification(
            user_id=user_id,
            message=message,
            dof_id=dof_id,
            created_at=datetime.datetime.now(),
            is_read=False
        )
        
        # Veritabanına kaydet
        db.session.add(notification)
        db.session.commit()
        
        current_app.logger.info(f"Bildirim oluşturuldu: ID {notification.id}, Kullanıcı: {user.full_name}")
        return notification
        
    except Exception as e:
        current_app.logger.error(f"Bildirim oluşturma hatası: {str(e)}")
        if 'db' in locals():
            db.session.rollback()
        return None

def notify_quality_managers_for_dof(dof, action_type, actor):
    """
    Bir DÖF için tüm kalite yöneticilerine bildirim gönderir
    """
    if not isinstance(dof, DOF):
        current_app.logger.error("Geçersiz DÖF objesi")
        return False
        
    try:
        # Kalite yöneticilerini bul
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        current_app.logger.info(f"Toplam {len(quality_managers)} kalite yöneticisi bulundu")
        
        # Bildirim mesajını oluştur
        if isinstance(actor, User):
            actor_name = actor.full_name
        else:
            actor_name = "Sistem"
            
        if action_type == "create":
            message = f"{actor_name} tarafından '{dof.title}' (#{dof.id}) başlıklı yeni bir DÖF oluşturuldu"
        elif action_type == "update":
            message = f"{actor_name} tarafından '{dof.title}' (#{dof.id}) başlıklı DÖF güncellendi"
        elif action_type == "status_change":
            message = f"{actor_name} tarafından '{dof.title}' (#{dof.id}) başlıklı DÖF'ün durumu '{dof.status_name}' olarak değiştirildi"
        elif action_type == "assign":
            message = f"{actor_name} tarafından '{dof.title}' (#{dof.id}) başlıklı DÖF atandı"
        elif action_type == "comment":
            message = f"{actor_name} tarafından '{dof.title}' (#{dof.id}) başlıklı DÖF'e yorum eklendi"
        elif action_type == "resolve":
            message = f"{actor_name} tarafından '{dof.title}' (#{dof.id}) başlıklı DÖF çözüldü"
        elif action_type == "close":
            message = f"{actor_name} tarafından '{dof.title}' (#{dof.id}) başlıklı DÖF kapatıldı"
        else:
            message = f"{actor_name} tarafından '{dof.title}' (#{dof.id}) başlıklı DÖF üzerinde değişiklik yapıldı"
            
        # Her kalite yöneticisine bildirim gönder
        actor_id = getattr(actor, 'id', None)
        for qm in quality_managers:
            # Aktörün kendisine bildirim gönderme
            if qm.id != actor_id:
                notification = send_direct_notification(qm.id, message, dof.id)
                if notification:
                    current_app.logger.info(f"Kalite yöneticisine bildirim gönderildi: {qm.full_name}")
                else:
                    current_app.logger.error(f"Kalite yöneticisine bildirim gönderilemedi: {qm.full_name}")
        
        return True
        
    except Exception as e:
        current_app.logger.error(f"Kalite yöneticilerine bildirim gönderme hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return False
