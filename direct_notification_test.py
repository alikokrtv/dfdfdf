"""
Doğrudan bildirim testi - Form doldurmadan kalite yöneticilerine bildirim gitmesini test eder
"""

from app import app, db
from models import User, UserRole, Notification, DOF, DOFStatus
from direct_notification import notify_quality_managers_for_dof
import datetime

def test_direct_notifications():
    with app.app_context():
        # En son DÖF'ü bul
        latest_dof = DOF.query.order_by(DOF.id.desc()).first()
        if not latest_dof:
            print("Hiç DÖF bulunamadı!")
            return
            
        print(f"Test edilen DÖF: #{latest_dof.id} - {latest_dof.title}")
        
        # Önce mevcut tüm bildirimler için bilgi yazdır
        print("\nMevcut bildirimler:")
        notifications = Notification.query.filter_by(dof_id=latest_dof.id).all()
        if notifications:
            for notification in notifications:
                user = User.query.get(notification.user_id)
                print(f"  - Kullanıcı: {user.username} ({user.role_name}), Mesaj: {notification.message[:50]}...")
        else:
            print("  Bu DÖF için henüz bildirim yok.")
            
        # Kalite yöneticilerini bul
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        print(f"\n{len(quality_managers)} kalite yöneticisi bulundu:")
        for qm in quality_managers:
            print(f"  - {qm.username} ({qm.full_name}), Email: {qm.email}")
            
        # Doğrudan bildirim gönderme
        print("\nDoğrudan bildirim gönderme yöntemini test ediyoruz...")
        
        # Yöntem 1: notify_quality_managers_for_dof kullanarak
        admin_user = User.query.filter_by(role=UserRole.ADMIN).first()
        result = notify_quality_managers_for_dof(latest_dof, "create", admin_user)
        
        if result:
            print("✅ direct_notification.notify_quality_managers_for_dof başarıyla çalıştı")
        else:
            print("❌ direct_notification.notify_quality_managers_for_dof çalışırken hata oluştu")
            
        # Yöntem 2: Doğrudan bildirim oluşturma
        print("\nDoğrudan bildirim oluşturma yöntemi test ediliyor...")
        success_count = 0
        
        for qm in quality_managers:
            try:
                notification = Notification(
                    user_id=qm.id,
                    dof_id=latest_dof.id,
                    message=f"TEST: #{latest_dof.id} - '{latest_dof.title}' başlıklı DÖF için doğrudan bildirim testi.",
                    created_at=datetime.datetime.now(),
                    is_read=False
                )
                db.session.add(notification)
                success_count += 1
            except Exception as e:
                print(f"Hata: {str(e)}")
        
        if success_count > 0:
            db.session.commit()
            print(f"✅ {success_count} doğrudan bildirim başarıyla oluşturuldu")
        else:
            print("❌ Doğrudan bildirim oluşturulamadı")
            
        # Sonuç bildirimleri kontrol et
        print("\nBildirim kontrolü:")
        notifications = Notification.query.filter_by(dof_id=latest_dof.id).all()
        if notifications:
            for notification in notifications:
                user = User.query.get(notification.user_id)
                print(f"  - Kullanıcı: {user.username} ({user.role_name}), Mesaj: {notification.message[:50]}...")
        else:
            print("  Hala bildirim yok!")
            
        print("\nDÖF yönetimi sayfasını ziyaret ederek bildirimleri kontrol edin.")
        print("URL: http://localhost:5000/notifications")

if __name__ == "__main__":
    test_direct_notifications()
