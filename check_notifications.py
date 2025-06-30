"""
Bu script, kalite yöneticileri için olan bildirimleri kontrol eder.
"""

from app import app, db
from models import User, UserRole, Notification, DOF, DOFStatus
import datetime

def check_notifications():
    with app.app_context():
        # Kalite yöneticilerini bul
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        print(f"Sistemde {len(quality_managers)} kalite yöneticisi bulundu:")
        
        for qm in quality_managers:
            print(f"\n--- {qm.username} ({qm.full_name}) ---")
            print(f"Kullanıcı ID: {qm.id}")
            print(f"Email: {qm.email}")
            
            # Kullanıcının bildirimlerini kontrol et
            notifications = Notification.query.filter_by(user_id=qm.id).order_by(Notification.created_at.desc()).limit(10).all()
            print(f"Son 10 bildirim: {len(notifications)}")
            
            for i, notification in enumerate(notifications, 1):
                print(f"{i}. [{'Okunmadı' if not notification.is_read else 'Okundu'}] {notification.created_at.strftime('%d.%m.%Y %H:%M')}: {notification.message}")
            
            # Okunmamış bildirim sayısı
            unread_count = Notification.query.filter_by(user_id=qm.id, is_read=False).count()
            print(f"Okunmamış bildirim sayısı: {unread_count}")
        
        # En son bildirimler
        print("\n--- Son 5 bildirim ---")
        latest_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
        for notification in latest_notifications:
            user = User.query.get(notification.user_id)
            print(f"Kullanıcı: {user.username}, Mesaj: {notification.message}")

if __name__ == "__main__":
    check_notifications()
