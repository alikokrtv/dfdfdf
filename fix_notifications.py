"""
Bu script, mevcut DÖF'ler için bildirim durumunu düzeltmek ve 
bildirim sisteminin çalışıp çalışmadığını test etmek için kullanılır.
"""

from flask import Flask, current_app
from app import app
from models import DOF, User, Notification, UserRole
from utils import create_notification

def fix_notifications():
    """Tüm kalite yöneticilerine doğrudan bildirim gönderir"""
    with app.app_context():
        # Kalite yöneticilerini bul
        quality_managers = User.query.filter_by(role='QUALITY_MANAGER', active=True).all()
        print(f"Toplam {len(quality_managers)} kalite yöneticisi bulundu")
        
        # Son 10 DÖF'ü al
        recent_dofs = DOF.query.order_by(DOF.id.desc()).limit(10).all()
        print(f"Son {len(recent_dofs)} DÖF işlenecek")
        
        # Her DÖF için kalite yöneticilerine bildirim gönder
        total_notifications = 0
        for dof in recent_dofs:
            creator = User.query.get(dof.created_by) if dof.created_by else None
            creator_name = creator.full_name if creator else "Bilinmeyen Kullanıcı"
            
            message = f"{creator_name} tarafından '{dof.title}' (#{dof.id}) başlıklı bir DÖF oluşturuldu"
            
            for qm in quality_managers:
                # DÖF'ü oluşturan kişi kalite yöneticisi ise ona bildirim gönderme
                if qm.id != dof.created_by:
                    try:
                        notification = create_notification(qm.id, message, dof.id)
                        if notification:
                            print(f"✓ DÖF #{dof.id} için bildirim gönderildi: {qm.full_name} (ID: {qm.id})")
                            total_notifications += 1
                        else:
                            print(f"✗ DÖF #{dof.id} için bildirim gönderilemedi: {qm.full_name}")
                    except Exception as e:
                        print(f"! Hata: {str(e)}")
        
        print(f"Toplam {total_notifications} bildirim gönderildi.")
        
        # Bildirimlerin veritabanında olup olmadığını kontrol et
        notifications = Notification.query.order_by(Notification.id.desc()).limit(10).all()
        print("\nSon 10 bildirim:")
        for notif in notifications:
            user = User.query.get(notif.user_id)
            user_name = user.full_name if user else "Bilinmeyen"
            print(f"ID: {notif.id}, Kullanıcı: {user_name}, Mesaj: {notif.message[:50]}...")

if __name__ == "__main__":
    fix_notifications()
