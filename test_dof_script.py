"""
DÖF Oluşturma ve Atama Test Scripti
Bu script, yeni bir DÖF oluşturur ve seçilen departmana atar.
Bildirim sistemini test etmek için kullanılır.
"""
import os
import sys
import time
from datetime import datetime
from flask import g

# Proje klasörünü ekleyerek modülleri import edebilmemizi sağlar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Uygulama bağlamı içinde çalışması için gerekli importlar
from app import app, db
from models import DOF, DOFStatus, DOFType, DOFSource, Department, User, UserRole
from notification_helper import notify_all_relevant_users

def create_test_dof():
    """Test amaçlı yeni bir DÖF oluşturur"""
    
    with app.app_context():
        # 1. Aktif bir kalite yöneticisi bul
        quality_manager = User.query.filter_by(
            role=UserRole.QUALITY_MANAGER,
            active=True
        ).first()
        
        if not quality_manager:
            print("HATA: Aktif kalite yöneticisi bulunamadı!")
            return None
            
        print(f"Kalite yöneticisi bulundu: {quality_manager.full_name}")
        
        # 2. Timestamp içeren bir başlık oluştur
        timestamp = datetime.now().strftime("%H:%M:%S")
        title = f"Test DÖF - Bildirim Testi - {timestamp}"
        
        # 3. Yeni DÖF oluştur
        new_dof = DOF(
            title=title,
            description="Bu bir test DÖF'tür. Bildirim sistemini test etmek için oluşturulmuştur.",
            dof_type=DOFType.CORRECTIVE,
            dof_source=DOFSource.OTHER,
            priority=2, # Orta öncelik
            created_by=quality_manager.id,
            status=DOFStatus.DRAFT,
            created_at=datetime.now()
        )
        
        # 4. Veritabanına kaydet
        db.session.add(new_dof)
        db.session.commit()
        
        print(f"Yeni DÖF oluşturuldu! ID: {new_dof.id}, Başlık: {title}")
        return new_dof, quality_manager

def list_departments():
    """Sistemdeki tüm departmanları listeler ve seçim yapmayı sağlar"""
    
    with app.app_context():
        departments = Department.query.all()
        
        if not departments:
            print("HATA: Sistemde departman bulunamadı!")
            return None
        
        print("\nMevcut Departmanlar:")
        print("-" * 40)
        
        for i, dept in enumerate(departments, 1):
            print(f"{i}. {dept.name} (ID: {dept.id})")
        
        try:
            choice = int(input("\nAtamak istediğiniz departmanı seçin (numara): "))
            if 1 <= choice <= len(departments):
                selected_dept = departments[choice-1]
                print(f"Seçilen departman: {selected_dept.name}")
                return selected_dept
            else:
                print("Hatalı seçim! Geçerli bir numara girin.")
                return list_departments()
        except ValueError:
            print("Hatalı giriş! Lütfen bir numara girin.")
            return list_departments()

def assign_dof_to_department(dof, department, quality_manager):
    """DÖF'ü belirtilen departmana atar"""
    
    with app.app_context():
        # 1. DÖF'ü güncelle
        dof.department_id = department.id
        dof.status = DOFStatus.ASSIGNED
        dof.assigned_at = datetime.now()
        
        # 2. Değişiklikleri kaydet
        db.session.commit()
        
        print(f"DÖF #{dof.id} {department.name} departmanına atandı")
        
        # 3. Bildirim gönder
        atama_mesaji = f"DÖF #{dof.id} - '{dof.title}' {department.name} departmanına atandı."
        
        # g nesnesi için atama yap (current_user)
        g.user = quality_manager
        
        # Flask request bağlamı içinde
        with app.test_request_context('/'):
            # Tüm ilgili kullanıcılara bildirim gönder
            bildirim_sayisi = notify_all_relevant_users(dof, "department_assign", quality_manager, atama_mesaji, send_email=True)
            
        print(f"Toplam {bildirim_sayisi} adet bildirim gönderildi")
        return bildirim_sayisi > 0

def run_test():
    """Test senaryosunu çalıştırır"""
    print("DÖF Oluşturma/Atama Test Senaryosu Başlatılıyor...")
    print("=" * 50)
    
    # 1. DÖF oluştur
    result = create_test_dof()
    if not result:
        print("DÖF oluşturma başarısız oldu!")
        return
    
    dof, quality_manager = result
    
    # 2. Departman seç
    department = list_departments()
    if not department:
        print("Departman seçimi başarısız oldu!")
        return
    
    # 3. Kısa bir bekleme süresi
    print("\nDÖF oluşturuldu, 3 saniye sonra departmana atanacak...")
    time.sleep(3)
    
    # 4. Departmana ata
    success = assign_dof_to_department(dof, department, quality_manager)
    
    if success:
        print(f"\nTEST BAŞARILI: DÖF #{dof.id} oluşturuldu, {department.name} departmanına atandı.")
        print(f"Bildirimler gönderildi. Lütfen bildirim kutunuzu ve e-posta kutunuzu kontrol edin.")
    else:
        print("\nTEST BAŞARISIZ: DÖF departmana atanamadı veya bildirimler gönderilemedi!")

if __name__ == "__main__":
    run_test()
