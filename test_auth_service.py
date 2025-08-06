from app import app, db
from models import User, UserRole, Department, DOF, UserDepartmentMapping
from auth_service import AuthService

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
            
        # Bu departmanlardaki DÖF'leri say
        dept_ids = [dept.id for dept in managed_depts]
        all_dofs = DOF.query.filter(DOF.department_id.in_(dept_ids)).all()
        print(f'Bu departmanlardaki toplam DÖF sayısı: {len(all_dofs)}')
        
        # AuthService ile filtreleme test et
        base_query = DOF.query
        filtered_query = AuthService.filter_viewable_dofs(aykut, base_query)
        filtered_dofs = filtered_query.all()
        print(f'AuthService filtrelenmiş DÖF sayısı: {len(filtered_dofs)}')
        
        # Her departman için DÖF sayısını göster
        for dept in managed_depts:
            dept_dofs = DOF.query.filter_by(department_id=dept.id).all()
            print(f'  - {dept.name}: {len(dept_dofs)} DÖF')
            for dof in dept_dofs[:3]:  # İlk 3 DÖF'ü göster
                print(f'    * DÖF {dof.id}: {dof.title[:50]}...')
            if len(dept_dofs) > 3:
                print(f'    ... ve {len(dept_dofs) - 3} DÖF daha')
                
        # AuthService filtrelenmiş DÖF'leri göster
        print(f'\nAuthService filtrelenmiş DÖF\'ler:')
        for dof in filtered_dofs:
            print(f'  - DÖF {dof.id}: {dof.title[:50]}... (Dept: {dof.department.name if dof.department else "None"})')
                
    else:
        print('Aykut kullanıcısı bulunamadı!') 