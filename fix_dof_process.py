"""
Bu script, "Yeni DÖF açılsın" sürecini iyileştirmek ve kalite yöneticilerinin gereksiz kontrol
kutularını işaretlemek zorunda kalmasını engellemek için kullanılır.
"""

from app import app, db
from models import User, UserRole, Notification, DOF, DOFStatus
import datetime

# Kalite yöneticilerine manuel bildirim gönderme fonksiyonu
def notify_quality_managers(dof_id, message):
    with app.app_context():
        # Kalite yöneticilerini bul
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        print(f"Kalite yöneticisi sayısı: {len(quality_managers)}")
        
        # DÖF'ü kontrol et
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"DÖF bulunamadı: ID {dof_id}")
            return
            
        # Her kalite yöneticisine bildirim gönder
        for qm in quality_managers:
            # Bildirim oluştur
            notification = Notification(
                user_id=qm.id,
                message=message,
                dof_id=dof_id,
                created_at=datetime.datetime.now(),
                is_read=False
            )
            db.session.add(notification)
            print(f"Kalite yöneticisi {qm.username} için bildirim oluşturuldu")
        
        db.session.commit()
        print("Bildirimler veritabanına kaydedildi.")

# Script çalıştırıldığında bu blok çalışır
if __name__ == "__main__":
    # En son DÖF'ü bul ve tüm kalite yöneticilerine bildirim gönder
    with app.app_context():
        latest_dof = DOF.query.order_by(DOF.id.desc()).first()
        if latest_dof:
            print(f"En son DÖF: ID={latest_dof.id}, Başlık='{latest_dof.title}'")
            message = f"ACİL: '{latest_dof.title}' başlıklı DÖF için inceleme gerekiyor."
            notify_quality_managers(latest_dof.id, message)
        else:
            print("Hiç DÖF bulunamadı.")
