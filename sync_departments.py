import os
from datetime import datetime
from app import app, db
from models import Department, DOF, User
from flask import current_app

def sync_user_departments():
    """
    Tüm kullanıcılar için departman eşleşmelerini kontrol eder ve düzeltir.
    
    1. Departman adı ile kullanıcı departman ID'si arasındaki tutarsızlıkları düzeltir
    2. Departmanı olmayan kullanıcıları raporlar
    3. Değişiklik yapılan ve yapılmayan kullanıcı sayısını raporlar
    """
    fixed_users = []
    missing_dept_users = []
    already_correct = 0
    
    # Tüm aktif kullanıcıları al
    all_users = User.query.filter_by(active=True).all()
    
    for user in all_users:
        # Kullanıcının bir departmana atanmış olması ancak departman ID'sinin olmaması
        # ya da departman ID'si olup da geçerli bir departmana işaret etmemesi durumlarını kontrol et
        if user.department_id:
            # Departman ID'si var, doğru departmana işaret ediyor mu?
            department = Department.query.get(user.department_id)
            
            if not department:
                # Departman bulunamadı, kullanıcının departman bilgisini düzelt
                # Kullanıcı adından departman bulmaya çalış (email veya kullanıcı adı)
                possible_dept_name = user.username.split('@')[0].split('.')[0].capitalize()
                possible_department = Department.query.filter(Department.name.like(f'%{possible_dept_name}%')).first()
                
                if possible_department:
                    user.department_id = possible_department.id
                    fixed_users.append({
                        'id': user.id, 
                        'name': user.full_name, 
                        'old_dept': None, 
                        'new_dept': possible_department.name
                    })
                else:
                    missing_dept_users.append({
                        'id': user.id, 
                        'name': user.full_name
                    })
            else:
                # Departman var ve geçerli
                already_correct += 1
                
        else:
            # Departman ID'si yok, kullanıcı adından departmanı bulmaya çalış
            possible_dept_name = user.username.split('@')[0].split('.')[0].capitalize()
            possible_department = Department.query.filter(Department.name.like(f'%{possible_dept_name}%')).first()
            
            if possible_department:
                user.department_id = possible_department.id
                fixed_users.append({
                    'id': user.id, 
                    'name': user.full_name, 
                    'old_dept': None, 
                    'new_dept': possible_department.name
                })
            else:
                missing_dept_users.append({
                    'id': user.id, 
                    'name': user.full_name
                })
    
    # Değişiklikleri kaydet
    if fixed_users:
        db.session.commit()
        
    return {
        'fixed_users': fixed_users,
        'missing_dept_users': missing_dept_users,
        'already_correct': already_correct,
        'total_users': len(all_users)
    }

def sync_dof_departments():
    """
    DÖF'lerin departman bilgilerinin tutarlılığını kontrol eder ve günceller.
    
    1. Departmanı olmayan DÖF'leri tespit eder
    2. Oluşturan kullanıcının departmanına göre departmanı günceller
    3. Değişiklik yapılan ve yapılmayan DÖF sayısını raporlar
    """
    fixed_dofs = []
    missing_dept_dofs = []
    already_correct = 0
    
    # Tüm DÖF'leri al
    all_dofs = DOF.query.all()
    
    for dof in all_dofs:
        if dof.department_id:
            # Departman ID'si var, doğru departmana işaret ediyor mu?
            department = Department.query.get(dof.department_id)
            
            if not department:
                # Departman bulunamadı, DÖF'ün departman bilgisini düzelt
                # Oluşturan kullanıcının departmanını kullan
                creator = User.query.get(dof.created_by) if dof.created_by else None
                
                if creator and creator.department_id:
                    dof.department_id = creator.department_id
                    fixed_dofs.append({
                        'id': dof.id, 
                        'title': dof.title, 
                        'old_dept': None, 
                        'new_dept': creator.department.name if creator.department else None
                    })
                else:
                    missing_dept_dofs.append({
                        'id': dof.id, 
                        'title': dof.title
                    })
            else:
                # Departman var ve geçerli
                already_correct += 1
        else:
            # Departman ID'si yok, oluşturan kullanıcının departmanını kullan
            creator = User.query.get(dof.created_by) if dof.created_by else None
            
            if creator and creator.department_id:
                dof.department_id = creator.department_id
                fixed_dofs.append({
                    'id': dof.id, 
                    'title': dof.title, 
                    'old_dept': None, 
                    'new_dept': creator.department.name if creator.department else None
                })
            else:
                missing_dept_dofs.append({
                    'id': dof.id, 
                    'title': dof.title
                })
    
    # Değişiklikleri kaydet
    if fixed_dofs:
        db.session.commit()
        
    return {
        'fixed_dofs': fixed_dofs,
        'missing_dept_dofs': missing_dept_dofs,
        'already_correct': already_correct,
        'total_dofs': len(all_dofs)
    }

# Bu script doğrudan çalıştırıldığında
if __name__ == "__main__":
    with app.app_context():
        print("===== DEPARTMAN-KULLANICI SENKRONIZASYONU =====")
        print(f"Başlangıç: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        
        # Kullanıcı departmanlarını senkronize et
        user_results = sync_user_departments()
        
        print(f"\n=== KULLANICI SONUÇLARI ({user_results['total_users']} kullanıcı) ===")
        print(f"Zaten doğru olan: {user_results['already_correct']}")
        print(f"Düzeltilen: {len(user_results['fixed_users'])}")
        print(f"Departmanı bulunamayan: {len(user_results['missing_dept_users'])}")
        
        if user_results['fixed_users']:
            print("\nDüzeltilen kullanıcılar:")
            for user in user_results['fixed_users']:
                print(f"  {user['name']} (ID: {user['id']}) -> {user['new_dept']}")
        
        if user_results['missing_dept_users']:
            print("\nDepartmanı bulunamayan kullanıcılar:")
            for user in user_results['missing_dept_users']:
                print(f"  {user['name']} (ID: {user['id']})")
        
        # DÖF departmanlarını senkronize et
        dof_results = sync_dof_departments()
        
        print(f"\n=== DÖF SONUÇLARI ({dof_results['total_dofs']} DÖF) ===")
        print(f"Zaten doğru olan: {dof_results['already_correct']}")
        print(f"Düzeltilen: {len(dof_results['fixed_dofs'])}")
        print(f"Departmanı bulunamayan: {len(dof_results['missing_dept_dofs'])}")
        
        if dof_results['fixed_dofs']:
            print("\nDüzeltilen DÖF'ler:")
            for dof in dof_results['fixed_dofs']:
                print(f"  {dof['title']} (ID: {dof['id']}) -> {dof['new_dept']}")
        
        if dof_results['missing_dept_dofs']:
            print("\nDepartmanı bulunamayan DÖF'ler:")
            for dof in dof_results['missing_dept_dofs']:
                print(f"  {dof['title']} (ID: {dof['id']})")
                
        print(f"\nBitiş: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
