from app import app, db
from models import User, UserRole, Notification, DOF
import datetime

with app.app_context():
    # Kalite yöneticisi kontrolü
    quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER).all()
    print(f"Kalite yöneticisi sayısı: {len(quality_managers)}")
    
    # En son DÖF'ü bul
    latest_dof = DOF.query.order_by(DOF.id.desc()).first()
    if latest_dof:
        print(f"En son DÖF: ID={latest_dof.id}, Başlık='{latest_dof.title}'")
        
        # Test bildirimi oluştur
        for qm in quality_managers:
            notification = Notification(
                user_id=qm.id,
                message=f"TEST BİLDİRİMİ: '{latest_dof.title}' başlıklı DÖF için acil inceleme gerekiyor.",
                dof_id=latest_dof.id,
                created_at=datetime.datetime.now(),
                is_read=False
            )
            db.session.add(notification)
            print(f"Kalite yöneticisi {qm.username} için bildirim oluşturuldu")
        
        db.session.commit()
        print("Test bildirimleri veritabanına kaydedildi.")
    else:
        print("Hiç DÖF bulunamadı.")
