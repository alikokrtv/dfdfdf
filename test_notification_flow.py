"""
Test DÖF Oluşturma ve Bildirim Testi
Kanyon'dan Emaar departmanına bir test DÖF oluşturur ve bildirimlerin kalite yöneticilerine ulaşıp ulaşmadığını kontrol eder.
"""

from app import app, db
from models import User, Department, DOF, DOFStatus, UserRole, Notification, DOFAction
from datetime import datetime

def create_test_dof():
    with app.app_context():
        # Kanyon departmanını bul
        kanyon_dept = Department.query.filter_by(name="Kanyon").first()
        if not kanyon_dept:
            print("Kanyon departmanı bulunamadı!")
            return
            
        # Emaar departmanını bul
        emaar_dept = Department.query.filter_by(name="Emaar").first()
        if not emaar_dept:
            print("Emaar departmanı bulunamadı!")
            return
            
        # Kanyon kullanıcısını bul (ilk departman yöneticisini al)
        kanyon_user = User.query.filter_by(department_id=kanyon_dept.id).first()
        if not kanyon_user:
            print("Kanyon departmanında kullanıcı bulunamadı!")
            return
        
        print(f"Kanyon kullanıcısı: {kanyon_user.username} ({kanyon_user.full_name})")
        
        # Test DÖF oluştur
        test_dof = DOF(
            title="TEST DOF - Kanyon'dan Emaar'a",
            description="Bu DÖF bildirim testleri için oluşturulmuştur. Kalite yöneticilerine bildirim gönderilip gönderilmediğini kontrol ediyoruz.",
            dof_type=1,  # Düzeltici Faaliyet
            dof_source=3,  # Müşteri Şikayeti
            status=DOFStatus.SUBMITTED,  # Gönderildi durumu
            priority=2,  # Orta öncelik
            created_by=kanyon_user.id,
            department_id=emaar_dept.id,  # Emaar departmanına atandı
            created_at=datetime.now()
        )
        
        # Veritabanına kaydet
        db.session.add(test_dof)
        db.session.flush()  # ID oluştur
        
        # DÖF aksiyon kaydı oluştur
        action = DOFAction(
            dof_id=test_dof.id,
            user_id=kanyon_user.id,
            action_type=1,  # Oluşturma
            comment="Test DÖF oluşturuldu",
            created_at=datetime.now()
        )
        db.session.add(action)
        
        # Bildirim gönder
        # 1. Kalite yöneticilerine bildirim
        quality_managers = User.query.filter_by(role=UserRole.QUALITY_MANAGER, active=True).all()
        print(f"{len(quality_managers)} kalite yöneticisi bulundu")
        
        for qm in quality_managers:
            notification = Notification(
                user_id=qm.id,
                dof_id=test_dof.id,
                message=f"Kanyon'dan TEST DÖF: '{test_dof.title}' başlıklı yeni bir DÖF oluşturuldu ve inceleme bekliyor.",
                created_at=datetime.now(),
                is_read=False
            )
            db.session.add(notification)
            print(f"Kalite yöneticisi {qm.username} için bildirim oluşturuldu")
            
        # 2. Emaar departman yöneticilerine bildirim
        emaar_managers = User.query.filter_by(department_id=emaar_dept.id, role=UserRole.DEPARTMENT_MANAGER).all()
        for manager in emaar_managers:
            notification = Notification(
                user_id=manager.id,
                dof_id=test_dof.id,
                message=f"Kanyon'dan departmanınıza yeni bir DÖF ({test_dof.title}) atandı.",
                created_at=datetime.now(),
                is_read=False
            )
            db.session.add(notification)
            print(f"Emaar departman yöneticisi {manager.username} için bildirim oluşturuldu")
            
        # Değişiklikleri kaydet
        db.session.commit()
        print(f"Test DÖF başarıyla oluşturuldu: ID={test_dof.id}")
        
        # Bildirimleri kontrol et
        print("\nBildirim durumu kontrolü:")
        all_notifications = Notification.query.filter_by(dof_id=test_dof.id).all()
        print(f"Bu DÖF için toplam {len(all_notifications)} bildirim oluşturuldu")
        
        # Kalite yöneticilerine giden bildirimleri kontrol et
        qm_notifications = Notification.query.join(User).filter(
            Notification.dof_id == test_dof.id,
            User.role == UserRole.QUALITY_MANAGER
        ).all()
        print(f"Kalite yöneticilerine giden bildirim sayısı: {len(qm_notifications)}")
        
        return test_dof.id

if __name__ == "__main__":
    dof_id = create_test_dof()
    if dof_id:
        print(f"\nÖNEMLİ: Lütfen şimdi DÖF detay sayfasını kontrol edin: http://localhost:5000/dof/{dof_id}")
        print("Ayrıca bildirim sayfasını kontrol edin: http://localhost:5000/notifications")
