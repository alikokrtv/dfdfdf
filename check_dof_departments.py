from app import app, db
from models import User, UserRole, Department, DOF

with app.app_context():
    # Tüm departmanları listele
    departments = Department.query.all()
    print("TÜM DEPARTMANLAR:")
    for dept in departments:
        print(f"  ID: {dept.id}, Ad: {dept.name}")
    
    print("\n" + "="*50)
    
    # Tüm DÖF'leri departman bazında say
    print("DÖF'LERİN DEPARTMAN DAĞILIMI:")
    for dept in departments:
        dof_count = DOF.query.filter_by(department_id=dept.id).count()
        if dof_count > 0:
            print(f"  {dept.name} (ID: {dept.id}): {dof_count} DÖF")
            
    print("\n" + "="*50)
    
    # Aykut'un yönettiği departmanları göster
    aykut = User.query.filter_by(username='aykutcandan').first()
    if aykut:
        managed_depts = aykut.get_managed_departments()
        print("AYKUT'UN YÖNETTİĞİ DEPARTMANLAR:")
        for dept in managed_depts:
            dof_count = DOF.query.filter_by(department_id=dept.id).count()
            print(f"  {dept.name} (ID: {dept.id}): {dof_count} DÖF")
            
        print("\n" + "="*50)
        
        # Aykut'un görmesi gereken DÖF'leri göster
        dept_ids = [dept.id for dept in managed_depts]
        dofs = DOF.query.filter(DOF.department_id.in_(dept_ids)).all()
        print(f"AYKUT'UN GÖRMESİ GEREKEN DÖF'LER ({len(dofs)} adet):")
        for dof in dofs:
            print(f"  DÖF {dof.id}: {dof.title[:60]}... (Dept: {dof.department.name if dof.department else 'None'})")
            
        # Database'deki diğer DÖF'leri göster
        other_dofs = DOF.query.filter(~DOF.department_id.in_(dept_ids)).all()
        print(f"\nAYKUT'UN GÖRMEDİĞİ DÖF'LER ({len(other_dofs)} adet):")
        for dof in other_dofs[:10]:  # İlk 10'unu göster
            print(f"  DÖF {dof.id}: {dof.title[:60]}... (Dept ID: {dof.department_id})")
        if len(other_dofs) > 10:
            print(f"  ... ve {len(other_dofs) - 10} DÖF daha") 