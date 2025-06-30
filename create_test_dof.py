"""
Basit DÖF Oluşturma Testi
Bu script, sadece yeni bir DÖF oluşturup departmana atar.
Daha sonra uygulamadan kontrol ederek bildirimleri test edebilirsiniz.
"""
import os
import sys
import time
from datetime import datetime

# Proje klasörünü ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Flask uygulaması ve modelleri import et
from app import app, db
from models import DOF, DOFStatus, DOFType, DOFSource, Department, User, UserRole

def create_dof_and_assign():
    """DÖF oluştur ve seçilen departmana ata"""
    
    with app.app_context():
        try:
            # 1. Kalite yöneticisini bul
            quality_manager = User.query.filter_by(
                role=UserRole.QUALITY_MANAGER,
                active=True
            ).first()
            
            if not quality_manager:
                print("Hata: Kalite yöneticisi bulunamadı!")
                return
            
            print(f"Kalite yöneticisi: {quality_manager.full_name}")
            
            # 2. Departmanları listele
            departments = Department.query.all()
            
            if not departments:
                print("Hata: Sistemde departman bulunamadı!")
                return
            
            print("\nMevcut Departmanlar:")
            print("-" * 40)
            
            for i, dept in enumerate(departments, 1):
                print(f"{i}. {dept.name} (ID: {dept.id})")
            
            # 3. Departman seçimi
            try:
                choice = int(input("\nAtamak istediğiniz departmanı seçin (numara): "))
                if 1 <= choice <= len(departments):
                    selected_dept = departments[choice-1]
                else:
                    print("Geçersiz seçim!")
                    return
            except ValueError:
                print("Geçersiz numara!")
                return
            
            # 4. DÖF oluştur
            timestamp = datetime.now().strftime("%H:%M:%S")
            title = f"Test DÖF - {timestamp}"
            
            new_dof = DOF(
                title=title,
                description="Bu bir test DÖF'tür. Bildirim sistemini test etmek için oluşturulmuştur.",
                dof_type=DOFType.CORRECTIVE,
                dof_source=DOFSource.OTHER,
                priority=2,
                created_by=quality_manager.id,
                status=DOFStatus.DRAFT
            )
            
            db.session.add(new_dof)
            db.session.commit()
            
            print(f"\nYeni DÖF oluşturuldu: ID: {new_dof.id}, Başlık: {title}")
            
            # 5. DÖF'ü departmana ata
            new_dof.department_id = selected_dept.id
            new_dof.status = DOFStatus.ASSIGNED
            new_dof.assigned_at = datetime.now()
            
            db.session.commit()
            
            print(f"DÖF #{new_dof.id} {selected_dept.name} departmanına atandı")
            
            print("\nTest tamamlandı!")
            print(f"Şimdi uygulamaya giriş yapıp bildirimleri kontrol edebilirsiniz.")
            print(f"- DÖF oluşturan ({quality_manager.full_name}) bildirim almalı")
            print(f"- Departman yöneticisi ({selected_dept.name}) bildirim almalı")
            print(f"- Kalite yöneticileri bildirim almalı")
            
        except Exception as e:
            print(f"Hata oluştu: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    create_dof_and_assign()
