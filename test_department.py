import os
# DATABASE_URL ayarını ekle
os.environ['DATABASE_URL'] = 'sqlite:///dof.db'

# Flask uygulamasını ve modelleri içe aktar
from app import app, db
from models import Department, DOF, User

# Test scripti - dashboard sorununu anlamak için
with app.app_context():
    # Tüm DÖF'leri ve atanan departmanlarını listeleyelim
    print("\n=== TÜM DÖF'LER VE DEPARTMANLARI ===")
    for dof in DOF.query.all():
        dept_name = dof.department.name if dof.department else "Atanmamış"
        dept_id = dof.department_id if dof.department_id else "Yok"
        
        print(f"DÖF ID: {dof.id}, Başlık: {dof.title}, Durum: {dof.status}")
        print(f"  Departman: {dept_name}, Departman ID: {dept_id}")
        print(f"  Oluşturan: {dof.created_by}")
    
    # Emaar kullanıcısını bulalım
    print("\n=== EMAAR KULLANICISI BİLGİLERİ ===")
    emaar_user = User.query.filter_by(username="emaar").first()
    if emaar_user:
        print(f"Emaar kullanıcısı ID: {emaar_user.id}")
        print(f"Emaar departman ID: {emaar_user.department_id}")
        if emaar_user.department:
            print(f"Emaar departman adı: {emaar_user.department.name}")
            
            # Emaar departmanının nasıl atandığı DÖF'leri bulalım
            print("\n=== EMAAR DEPARTMANINA ATANAN DÖF'LER ===")
            for dof in DOF.query.all():
                if dof.department and dof.department_id == emaar_user.department_id:
                    print(f"DÖF ID: {dof.id}, Departman: {dof.department.name}, Eşleşme: Evet (ID)")
                elif dof.department and dof.department.name == emaar_user.department.name:
                    print(f"DÖF ID: {dof.id}, Departman: {dof.department.name}, Eşleşme: Evet (İsim)")
                    print(f"  Ayrıntı: DÖF.dept_id={dof.department_id}, Emaar.dept_id={emaar_user.department_id}")
                else:
                    continue
    else:
        print("Emaar kullanıcısı bulunamadı")
