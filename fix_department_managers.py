from app import db
from app import create_app
from models import User, Department, DOF, UserRole
from flask import url_for

def fix_department_managers():
    """
    Departman yöneticilerinin izin sorununu düzeltmek için:
    1. Tüm departman yöneticilerini listeler
    2. Departman atamalarını doğru şekilde yapar
    3. DÖF atamalarını kontrol eder
    """
    app = create_app()
    with app.app_context():
        print("Departman yöneticilerini buluyorum...")
        
        # Tüm departman yöneticilerini bul
        managers = User.query.filter(User.role == UserRole.DEPARTMENT_MANAGER).all()
        print(f"{len(managers)} departman yöneticisi bulundu.")
        
        if not managers:
            # Departman yöneticisi yoksa, bazı kullanıcıları yönetici yap
            users = User.query.filter(User.role == UserRole.USER).all()
            departments = Department.query.all()
            
            if users and departments:
                # Her departman için bir yönetici ata
                for i, dept in enumerate(departments):
                    if i < len(users):
                        users[i].role = UserRole.DEPARTMENT_MANAGER
                        users[i].department_id = dept.id
                        print(f"Kullanıcı {users[i].username} {dept.name} departmanının yöneticisi yapıldı")
                
                db.session.commit()
                print("Departman yöneticileri oluşturuldu!")
                managers = User.query.filter(User.role == UserRole.DEPARTMENT_MANAGER).all()
        
        # Mevcut departman yöneticilerini listele
        print("\nMevcut departman yöneticileri:")
        for manager in managers:
            department = Department.query.get(manager.department_id) if manager.department_id else None
            dept_name = department.name if department else "Departman atanmamış"
            print(f"ID: {manager.id}, Kullanıcı: {manager.username}, Departman: {dept_name}")
            
            # Departman atanmamışsa, bu yöneticiye bir departman ata
            if not department:
                # Yöneticisi olmayan bir departman bul
                unassigned_dept = Department.query.filter(~Department.id.in_(
                    [m.department_id for m in managers if m.department_id]
                )).first()
                
                if unassigned_dept:
                    manager.department_id = unassigned_dept.id
                    print(f"{manager.username} kullanıcısına {unassigned_dept.name} departmanı atandı")
                    db.session.commit()
        
        # Departman yöneticisi olmayan kullanıcılar için
        print("\nDepartman atanmamış çalışanlar:")
        users_without_dept = User.query.filter(User.department_id == None).all()
        for user in users_without_dept:
            print(f"ID: {user.id}, Kullanıcı: {user.username}, Rol: {user.role}")
            
            # Bu kullanıcıya bir departman ata
            if user.role != UserRole.ADMIN:  # Admin hariç
                # Herhangi bir departmanı ata
                dept = Department.query.first()
                if dept:
                    user.department_id = dept.id
                    print(f"{user.username} kullanıcısına {dept.name} departmanı atandı")
                    db.session.commit()
        
        # DÖF kontrolü
        print("\nDepartman atanmamış DÖF'ler:")
        dofs_without_dept = DOF.query.filter(DOF.department_id == None, DOF.status >= 3).all()
        for dof in dofs_without_dept:
            print(f"DÖF ID: {dof.id}, Durum: {dof.status}")
            
            # Bu DÖF'e bir departman ata
            dept = Department.query.first()
            if dept:
                dof.department_id = dept.id
                print(f"DÖF {dof.id} için {dept.name} departmanı atandı")
                db.session.commit()
        
        print("\nİşlem tamamlandı!")

if __name__ == '__main__':
    fix_department_managers()
