"""
DÖF Oluşturma, Atama Test Script
Bu script, otomatik olarak DÖF oluşturur ve kullanıcının seçtiği departmana atar.
Bildirim sistemini test etmek için kullanılır.
"""
import os
import sys
import time
import random
from datetime import datetime
from flask import Flask, g, request
from sqlalchemy import text

# Proje klasörünü ekleyerek modülleri import edebilmemizi sağlar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Uygulama bağlamı içinde çalışması için gerekli importlar
from app import app, db
from models import DOF, DOFStatus, Department, User, UserRole
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
        
        # 2. Rastgele bir departman seç
        department = Department.query.order_by(db.func.random()).first()
        
        if not department:
            print("HATA: Aktif departman bulunamadı!")
            return None
            
        print(f"Test için departman seçildi: {department.name}")
        
        # 3. Rastgele bir başlık oluştur
        timestamp = datetime.now().strftime("%H:%M:%S")
        title = f"Test DÖF - Bildirim Testi - {timestamp}"
        
        # 4. Yeni DÖF oluştur
        new_dof = DOF(
            title=title,
            description="Bu bir test DÖF'tür. Bildirim sistemini test etmek için oluşturulmuştur.",
            type="PROCESS",
            priority="NORMAL",
            created_by=quality_manager.id,
            status=DOFStatus.DRAFT,
            created_at=datetime.now()
        )
        
        # 5. Veritabanına kaydet
        db.session.add(new_dof)
        db.session.commit()
        
        print(f"Yeni DÖF oluşturuldu! ID: {new_dof.id}, Başlık: {title}")
        return new_dof, department

def assign_dof_to_department(dof, department):
    """DÖF'ü belirtilen departmana atar"""
    
    with app.app_context():
        # 1. Kalite yöneticisini bul (atama işlemini yapacak kişi)
        quality_manager = User.query.filter_by(
            role=UserRole.QUALITY_MANAGER,
            active=True
        ).first()
        
        if not quality_manager:
            print("HATA: Kalite yöneticisi bulunamadı!")
            return False
        
        # 2. DÖF'ü güncelle
        dof.department_id = department.id
        dof.status = DOFStatus.ASSIGNED
        dof.assigned_at = datetime.now()
        
        # 3. Değişiklikleri kaydet
        db.session.commit()
        
        print(f"DÖF #{dof.id} {department.name} departmanına atandı")
        
        # 4. Bildirim gönder
        atama_mesaji = f"DÖF #{dof.id} - '{dof.title}' {department.name} departmanına atandı."
        
        # Request nesnesi için mock oluştur
        class MockRequest:
            host_url = "http://localhost:5000/"
        
        # g nesnesi için atama yap
        g.user = quality_manager
        
        # Flask request nesnesi taklit ediliyor
        with app.test_request_context('/'):
            bildirim_sayisi = notify_all_relevant_users(dof, "department_assign", quality_manager, atama_mesaji, send_email=True)
            
        print(f"Toplam {bildirim_sayisi} adet bildirim gönderildi")
        return True

def run_test():
    """Test senaryosunu çalıştırır"""
    print("DÖF Oluşturma/Atama Test Senaryosu Başlatılıyor...")
    print("-" * 50)
    
    # 1. DÖF oluştur
    result = create_test_dof()
    if not result:
        print("DÖF oluşturma başarısız oldu!")
        return
    
    dof, department = result
    
    # 2. Kısa bir bekleme süresi
    print("DÖF oluşturuldu, 3 saniye sonra departmana atanacak...")
    time.sleep(3)
    
    # 3. Departmana ata
    success = assign_dof_to_department(dof, department)
    
    if success:
        print(f"TEST BAŞARILI: DÖF #{dof.id} oluşturuldu, {department.name} departmanına atandı.")
        print(f"Bildirimler gönderildi. Lütfen bildirim kutunuzu kontrol edin.")
    else:
        print("TEST BAŞARISIZ: DÖF departmana atanamadı!")

if __name__ == "__main__":
    run_test()
