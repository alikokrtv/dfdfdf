import os
# DATABASE_URL ayarını ekle
os.environ['DATABASE_URL'] = 'sqlite:///dof.db'

# Flask uygulamasını ve modelleri içe aktar
from app import app, db
from models import Department, DOF, User

# Kullanıcı departmanlarını düzeltme scripti
with app.app_context():
    print("=== BAŞLANGIÇ DURUMU ===")
    # Mevcut durumu göster
    emaar_user = User.query.filter_by(username="emaar").first()
    if emaar_user:
        print(f"Emaar kullanıcısı ID: {emaar_user.id}")
        print(f"Mevcut departman ID: {emaar_user.department_id}")
        
        # Emaar departmanını bul
        emaar_dept = Department.query.filter_by(name="Emaar").first()
        if emaar_dept:
            print(f"Emaar departmanı ID: {emaar_dept.id}")
            
            # Kullanıcıyı güncelle
            emaar_user.department_id = emaar_dept.id
            db.session.commit()
            
            # Değişikliği doğrula
            print("\n=== GÜNCELLEME SONRASI ===")
            print(f"Emaar kullanıcısı yeni departman ID: {emaar_user.department_id}")
            print(f"Departman adı: {emaar_user.department.name if emaar_user.department else 'Yok'}")
            
            # Departmanı Emaar olan DÖF'ler
            print("\n=== EMAAR DEPARTMANI DÖF'LERİ ===")
            emaar_dofs = DOF.query.filter_by(department_id=emaar_dept.id).all()
            for dof in emaar_dofs:
                print(f"DÖF ID: {dof.id}, Başlık: {dof.title}")
                # Şimdi eşleşme kontrolü
                is_match = emaar_user.department_id == dof.department_id
                print(f"  Departman eşleşiyor mu? {is_match}")
        else:
            print("Emaar departmanı bulunamadı!")
    else:
        print("Emaar kullanıcısı bulunamadı!")
