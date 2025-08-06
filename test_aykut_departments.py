from app import app, db
from models import User, UserRole, Department, DOF, UserDepartmentMapping

with app.app_context():
    # Aykut kullanıcısını bul
    aykut = User.query.filter_by(username='aykutcandan').first()
    if aykut:
        print(f'Aykut bulundu: {aykut.username}, rol: {aykut.role}, rol adı: {aykut.role_name}')
        
        # Yönetilen departmanları getir
        managed_depts = aykut.get_managed_departments()
        print(f'Yönetilen departman sayısı: {len(managed_depts)}')
        for dept in managed_depts:
            print(f'  - {dept.name} (ID: {dept.id})')
            
        # UserDepartmentMapping kontrol et
        mappings = UserDepartmentMapping.query.filter_by(user_id=aykut.id).all()
        print(f'UserDepartmentMapping sayısı: {len(mappings)}')
        for mapping in mappings:
            print(f'  - {mapping.department.name if mapping.department else "None"} (Dept ID: {mapping.department_id})')
            
        # Bu departmanlardaki DÖF'leri say
        dept_ids = [dept.id for dept in managed_depts]
        dofs = DOF.query.filter(DOF.department_id.in_(dept_ids)).all()
        print(f'Bu departmanlardaki toplam DÖF sayısı: {len(dofs)}')
        
        # Her departman için DÖF sayısını göster
        for dept in managed_depts:
            dept_dofs = DOF.query.filter_by(department_id=dept.id).all()
            print(f'  - {dept.name}: {len(dept_dofs)} DÖF')
            for dof in dept_dofs[:3]:  # İlk 3 DÖF'ü göster
                print(f'    * DÖF {dof.id}: {dof.title[:50]}...')
            if len(dept_dofs) > 3:
                print(f'    ... ve {len(dept_dofs) - 3} DÖF daha')
                
    else:
        print('Aykut kullanıcısı bulunamadı!') 