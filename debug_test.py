import os
import sys

# DATABASE_URL ayarını ekle
os.environ['DATABASE_URL'] = 'sqlite:///dof.db'

from app import app, db
from models import User, DOF, Department, UserRole, DOFStatus, DOFAction, Notification

# Test betiği - DÖF sürecini simüle etmek için
# Flask uygulama bağlamını etkinleştir
with app.app_context():
    def print_separator():
        print("\n" + "="*50 + "\n")
    
    def print_user_info(user):
        print(f"Kullanıcı: {user.username}, ID: {user.id}")
        print(f"Departman: {user.department.name if user.department else 'Yok'}, ID: {user.department_id if user.department_id else 'Yok'}")
        print(f"Rol: {UserRole(user.role).name}")
    
    def print_dof_info(dof):
        print(f"DÖF ID: {dof.id}, Başlık: {dof.title}")
        print(f"Durum: {DOFStatus(dof.status).name}")
        print(f"Departman: {dof.department.name if dof.department else 'Yok'}, ID: {dof.department_id if dof.department_id else 'Yok'}")
        print(f"Oluşturan: {User.query.get(dof.created_by).username if dof.created_by else 'Yok'}")
    
    # Aktif kullanıcıları görüntüle
    print_separator()
    print("AKTİF KULLANICILAR:")
    users = User.query.all()
    for user in users:
        print_user_info(user)
        print("-"*30)
    
    # Departmanları görüntüle
    print_separator()
    print("DEPARTMANLAR:")
    departments = Department.query.all()
    for dept in departments:
        print(f"Departman ID: {dept.id}, Ad: {dept.name}")
    
    # Mevcut DÖF'leri görüntüle
    print_separator()
    print("MEVCUT DÖF'LER:")
    dofs = DOF.query.all()
    for dof in dofs:
        print_dof_info(dof)
        print("-"*30)
    
    # Departman eşleşme kontrolü
    print_separator()
    print("DEPARTMAN EŞLEŞMESİ KONTROLÜ:")
    emaar_user = User.query.filter_by(username="emaar").first()
    if not emaar_user:
        print("Emaar kullanıcısı bulunamadı!")
    else:
        print_user_info(emaar_user)
        print("\nEmaar kullanıcısı için atanan DÖF'ler:")
        
        # Emaar'a atanan DÖF'leri bul
        emaar_dept_name = emaar_user.department.name if emaar_user.department else None
        if emaar_dept_name:
            # ID bazlı sorgu
            assigned_by_id = DOF.query.filter_by(department_id=emaar_user.department_id).all()
            print(f"\nID ile eşleşen DÖF sayısı ({emaar_user.department_id}): {len(assigned_by_id)}")
            
            # İsim bazlı sorgu
            assigned_by_name = []
            for dof in DOF.query.all():
                if dof.department and dof.department.name == emaar_dept_name:
                    assigned_by_name.append(dof)
            
            print(f"İsim ile eşleşen DÖF sayısı ({emaar_dept_name}): {len(assigned_by_name)}")
            
            # Her iki sorgu sonucu arasındaki farkı kontrol et
            id_set = {dof.id for dof in assigned_by_id}
            name_set = {dof.id for dof in assigned_by_name}
            
            if id_set != name_set:
                print("UYARI: ID ve isim bazlı sorgu sonuçları farklı!")
                print(f"Sadece ID ile eşleşenler: {id_set - name_set}")
                print(f"Sadece isim ile eşleşenler: {name_set - id_set}")
            
            # DÖF detayları
            print("\nAtanan DÖF'lerin detayları:")
            for dof in assigned_by_name:
                print_dof_info(dof)
                # Şablon görüntülemesini kontrol et
                is_match_by_id = emaar_user.department_id == dof.department_id
                is_match_by_name = emaar_user.department and dof.department and emaar_user.department.name == dof.department.name
                
                print(f"ID bazlı eşleşme: {is_match_by_id}")
                print(f"İsim bazlı eşleşme: {is_match_by_name}")
                
                if is_match_by_id != is_match_by_name:
                    print("UYARI: ID ve isim eşleşmesi farklı sonuçlar veriyor!")
                
                print("-"*30)
        else:
            print("Emaar kullanıcısının departmanı yok!")
    
    print_separator()
    print("TEST TAMAMLANDI")
