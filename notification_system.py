"""
Yeni Merkezi Bildirim Sistemi
Bu modül, sistemdeki tüm bildirim işlemlerini tek bir merkezi noktadan yönetir.
"""
import datetime
import threading
from flask import current_app, g, request
from app import db
from models import User, Notification, UserRole, DOF, Department

def send_notification(user_id, message, dof_id=None, send_email=True):
    """
    Tek bir kullanıcıya bildirim ve opsiyonel olarak e-posta gönderir.
    
    Args:
        user_id: Kullanıcı ID
        message: Bildirim mesajı
        dof_id: İlgili DÖF ID (opsiyonel)
        send_email: E-posta göndermek için True (varsayılan)
    
    Returns:
        Oluşturulan bildirim nesnesi veya None (hata durumunda)
    """
    try:
        # 1. Kullanıcıyı kontrol et
        user = User.query.get(user_id)
        if not user:
            current_app.logger.error(f"Bildirim oluşturulamadı: Kullanıcı bulunamadı (ID: {user_id})")
            return None
        
        # 2. Uygulama içi bildirim oluştur
        notification = Notification(
            user_id=user_id,
            message=message,
            dof_id=dof_id,
            created_at=datetime.datetime.now(),
            is_read=False
        )
        
        # 3. Bildirim veritabanına kaydedilir
        db.session.add(notification)
        db.session.commit()
        current_app.logger.info(f"Bildirim veritabanına kaydedildi: ID: {notification.id}, Kullanıcı: {user.full_name}")
        
        # 4. E-posta göndermek isteğe bağlı
        if user.email and send_email:
            send_email_to_user(user, message, dof_id)
            
        return notification
    
    except Exception as e:
        current_app.logger.error(f"Bildirim oluşturma hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        return None

def send_email_to_user(user, message, dof_id=None):
    """
    Kullanıcıya e-posta gönderir.
    """
    try:
        if not user.email:
            current_app.logger.warning(f"E-posta gönderilemiyor: Kullanıcının e-posta adresi yok (ID: {user.id})")
            return False
        
        # E-posta içeriği hazırla
        dof = DOF.query.get(dof_id) if dof_id else None
        subject = f"DÖF Sistemi Bildirim: {dof.title if dof else ''}"
        
        # URL oluştur
        base_url = None
        try:
            if hasattr(request, 'host_url'):
                base_url = request.host_url.rstrip('/')
            else:
                base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
        except:
            base_url = 'http://localhost:5000'
            
        dof_url = f"{base_url}/dof/{dof_id}" if dof_id else ""
        
        # HTML içeriği
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .header {{ background-color: #f8f8f8; padding: 10px; border-bottom: 1px solid #ddd; }}
                .footer {{ background-color: #f8f8f8; padding: 10px; border-top: 1px solid #ddd; margin-top: 20px; font-size: 12px; color: #777; }}
                .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; }}
                .highlight {{ color: #007bff; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>DÖF Sistemi Bildirim</h2>
                </div>
                
                <p>Sayın {user.full_name},</p>
                
                <p>{message}</p>
                
                {f'<p><a href="{dof_url}" class="button">DÖF Detaylarını Görüntüle</a></p>' if dof_id else ''}
                
                <div class="footer">
                    <p>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Düz metin içeriği
        text_content = f"DÖF Sistemi Bildirim\n\nSayın {user.full_name},\n\n{message}\n\n{dof_url if dof_id else ''}\n\nBu otomatik bir bildirimdir, lütfen yanıtlamayınız."
        
        # E-posta gönder
        from utils import send_email
        send_email(subject, [user.email], html_content, text_content)
        current_app.logger.info(f"E-posta gönderildi: Alıcı: {user.email}")
        return True
        
    except Exception as e:
        current_app.logger.error(f"E-posta gönderme hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return False

def notify_for_dof_event(dof_id, event_type, actor_id=None, custom_message=None):
    """
    DÖF ile ilgili bir olayda tüm ilgili kullanıcılara bildirim gönderir.
    
    Args:
        dof_id: DÖF ID
        event_type: Olay tipi 
            - create: DÖF oluşturma
            - update: DÖF güncelleme
            - assign: Departman atama
            - review: İnceleme
            - plan: Çözüm planı oluşturma
            - approve_plan: Çözüm planı onayı
            - complete: Tamamlama bildirimi
            - source_review: Kaynak değerlendirme
            - resolve: Çözüm
            - reject: Red
            - close: Kapatma
        actor_id: İşlemi yapan kullanıcı ID (opsiyonel)
        custom_message: Özel mesaj (opsiyonel)
    
    Returns:
        Gönderilen bildirim sayısı
    """
    try:
        # DÖF'ü al
        dof = DOF.query.get(dof_id)
        if not dof:
            current_app.logger.error(f"Bildirim gönderilemedi: DÖF bulunamadı (ID: {dof_id})")
            return 0
        
        # İşlemi yapan kullanıcıyı al
        actor = User.query.get(actor_id) if actor_id else None
        actor_name = actor.full_name if actor else "Sistem"
        
        # Varsayılan mesaj
        if not custom_message:
            if event_type == "create":
                message = f"{actor_name} tarafından yeni DÖF oluşturuldu: {dof.title} (#{dof.id})"
            elif event_type == "update":
                message = f"{actor_name} tarafından DÖF güncellendi: {dof.title} (#{dof.id})"
            elif event_type == "assign":
                dept = Department.query.get(dof.department_id) if dof.department_id else None
                dept_name = dept.name if dept else "Belirtilmemiş"
                message = f"DÖF #{dof.id} - '{dof.title}' {dept_name} departmanına atandı."
            elif event_type == "review":
                message = f"{actor_name} tarafından DÖF incelendi: {dof.title} (#{dof.id})"
            elif event_type == "plan":
                message = f"DÖF #{dof.id} - '{dof.title}' için çözüm planı oluşturuldu."
            elif event_type == "approve_plan":
                message = f"DÖF #{dof.id} - '{dof.title}' için çözüm planı onaylandı."
            elif event_type == "complete":
                message = f"DÖF #{dof.id} - '{dof.title}' için aksiyonlar tamamlandı."
            elif event_type == "source_review":
                message = f"DÖF #{dof.id} - '{dof.title}' kaynak departman incelemesine gönderildi."
            elif event_type == "resolve":
                message = f"DÖF #{dof.id} - '{dof.title}' çözüldü."
            elif event_type == "reject":
                message = f"DÖF #{dof.id} - '{dof.title}' reddedildi."
            elif event_type == "close":
                message = f"DÖF #{dof.id} - '{dof.title}' kapatıldı."
            else:
                message = f"DÖF #{dof.id} - '{dof.title}' ile ilgili bir işlem gerçekleşti."
        else:
            message = custom_message
        
        # İlgili kullanıcıları topla
        notify_users = []
        
        # 1. DÖF oluşturan
        if dof.created_by and (not actor_id or dof.created_by != actor_id):
            creator = User.query.get(dof.created_by)
            if creator and creator.active and creator not in notify_users:
                notify_users.append(creator)
                current_app.logger.info(f"DÖF oluşturan bildirim listesine eklendi: {creator.full_name}")
        
        # 2. DÖF atanan kişi
        if dof.assigned_to and (not actor_id or dof.assigned_to != actor_id):
            assignee = User.query.get(dof.assigned_to)
            if assignee and assignee.active and assignee not in notify_users:
                notify_users.append(assignee)
                current_app.logger.info(f"DÖF atanan kişi bildirim listesine eklendi: {assignee.full_name}")
        
        # 3. Departman yöneticileri
        if dof.department_id:
            dept_managers = User.query.filter_by(
                department_id=dof.department_id,
                role=UserRole.DEPARTMENT_MANAGER,
                active=True
            ).all()
            
            for manager in dept_managers:
                if manager and (not actor_id or manager.id != actor_id) and manager not in notify_users:
                    notify_users.append(manager)
                    current_app.logger.info(f"Departman yöneticisi bildirim listesine eklendi: {manager.full_name}")
        
        # 4. Kalite yöneticileri
        quality_managers = User.query.filter_by(
            role=UserRole.QUALITY_MANAGER,
            active=True
        ).all()
        
        for qm in quality_managers:
            if qm and (not actor_id or qm.id != actor_id) and qm not in notify_users:
                notify_users.append(qm)
                current_app.logger.info(f"Kalite yöneticisi bildirim listesine eklendi: {qm.full_name}")
        
        # 5. Direktörler - altındaki bölge müdürlerinin yönettiği departmanların DOF'leri için bildirim
        if dof.department_id:
            # Bu departmanı yöneten bölge müdürlerini bul
            from models import UserDepartmentMapping, DirectorManagerMapping
            
            dept_mappings = UserDepartmentMapping.query.filter_by(department_id=dof.department_id).all()
            for mapping in dept_mappings:
                group_manager = mapping.user
                if group_manager and group_manager.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
                    # Bu çoklu departman yöneticisini yöneten direktörleri bul
                    director_mappings = DirectorManagerMapping.query.filter_by(manager_id=group_manager.id).all()
                    for dir_mapping in director_mappings:
                        director = dir_mapping.director
                        if director and director.role == UserRole.DIRECTOR and director.active:
                            if (not actor_id or director.id != actor_id) and director not in notify_users:
                                notify_users.append(director)
                                current_app.logger.info(f"Direktör bildirim listesine eklendi: {director.full_name}")
        
        # Bildirimleri gönder
        notification_count = 0
        for user in notify_users:
            notification = send_notification(user.id, message, dof.id, send_email=True)
            if notification:
                notification_count += 1
        
        current_app.logger.info(f"DÖF #{dof.id} için toplam {notification_count} bildirim gönderildi. Olay: {event_type}")
        return notification_count
        
    except Exception as e:
        current_app.logger.error(f"DÖF bildirim hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return 0

def notify_department_assignment(dof_id, department_id, actor_id=None):
    """
    DÖF departman ataması için özel bildirim gönderme.
    Bu işlem özel olarak ele alınır çünkü departman yöneticilerine 
    bildirim gönderilmesi kritik önem taşır.
    """
    try:
        # DÖF'ü al
        dof = DOF.query.get(dof_id)
        if not dof:
            current_app.logger.error(f"Departman atama bildirimi gönderilemedi: DÖF bulunamadı (ID: {dof_id})")
            return 0
        
        # Departmanı al
        department = Department.query.get(department_id)
        if not department:
            current_app.logger.error(f"Departman atama bildirimi gönderilemedi: Departman bulunamadı (ID: {department_id})")
            return 0
        
        # İşlemi yapan kullanıcıyı al
        actor = User.query.get(actor_id) if actor_id else None
        actor_name = actor.full_name if actor else "Sistem"
        
        # Özel mesaj oluştur
        message = f"DÖF #{dof.id} - '{dof.title}' {department.name} departmanına atandı."
        
        # Standart bildirim fonksiyonunu çağır
        notification_count = notify_for_dof_event(dof_id, "assign", actor_id, message)
        
        current_app.logger.info(f"Departman atama bildirimi tamamlandı. DÖF #{dof.id} -> {department.name}, {notification_count} bildirim")
        return notification_count
        
    except Exception as e:
        current_app.logger.error(f"Departman atama bildirim hatası: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return 0
