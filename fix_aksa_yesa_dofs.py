from app import app, db
from models import User, UserRole, Department, DOF

with app.app_context():
    # Aksa-Yesa Proje departmanını bul
    aksa_yesa_dept = Department.query.filter_by(name='Aksa-Yesa Proje').first()
    if not aksa_yesa_dept:
        print("Aksa-Yesa Proje departmanı bulunamadı!")
        exit()
    
    print(f"Aksa-Yesa Proje departmanı bulundu: ID={aksa_yesa_dept.id}")
    
    # Aksa - Yesa PROJELER kullanıcısını bul
    aksa_yesa_user = User.query.filter_by(username='aksa_yesa_projeler').first()
    if not aksa_yesa_user:
        print("Aksa - Yesa PROJELER kullanıcısı bulunamadı!")
        # Alternatif olarak first_name veya last_name ile arayalım
        aksa_yesa_user = User.query.filter(
            (User.first_name.like('%Aksa%') | User.last_name.like('%Yesa%') | 
             User.first_name.like('%Yesa%') | User.last_name.like('%Aksa%'))
        ).first()
        
    if aksa_yesa_user:
        print(f"Aksa - Yesa PROJELER kullanıcısı bulundu: {aksa_yesa_user.username} (ID: {aksa_yesa_user.id})")
        
        # Bu kullanıcının oluşturduğu DÖF'leri bul
        created_dofs = DOF.query.filter_by(created_by=aksa_yesa_user.id).all()
        print(f"Bu kullanıcının oluşturduğu DÖF sayısı: {len(created_dofs)}")
        
        # Yanlış departmana atanmış DÖF'leri bul
        wrong_department_dofs = []
        for dof in created_dofs:
            if dof.department_id != aksa_yesa_dept.id:
                wrong_department_dofs.append(dof)
                print(f"  DÖF {dof.id}: {dof.title[:50]}... (Mevcut Dept: {dof.department.name if dof.department else 'None'}, Olması Gereken: {aksa_yesa_dept.name})")
        
        if wrong_department_dofs:
            print(f"\nToplam {len(wrong_department_dofs)} DÖF'ün department_id'si düzeltilecek.")
            
            # Düzeltme işlemi
            for dof in wrong_department_dofs:
                old_dept = dof.department.name if dof.department else 'None'
                dof.department_id = aksa_yesa_dept.id
                print(f"  DÖF {dof.id}: {old_dept} -> {aksa_yesa_dept.name}")
            
            # Değişiklikleri kaydet
            db.session.commit()
            print(f"\n✅ {len(wrong_department_dofs)} DÖF'ün department_id'si düzeltildi!")
        else:
            print("Düzeltilmesi gereken DÖF bulunamadı.")
    else:
        print("Aksa - Yesa PROJELER kullanıcısı bulunamadı!")
        
        # Alternatif: Başlığında "AKSA" veya "YESA" geçen DÖF'leri bul
        print("\nAlternatif: Başlığında 'AKSA' veya 'YESA' geçen DÖF'leri arıyorum...")
        from sqlalchemy import or_
        
        aksa_yesa_dofs = DOF.query.filter(
            or_(DOF.title.like('%AKSA%'), DOF.title.like('%YESA%'))
        ).all()
        
        print(f"Başlığında 'AKSA' veya 'YESA' geçen DÖF sayısı: {len(aksa_yesa_dofs)}")
        for dof in aksa_yesa_dofs:
            print(f"  DÖF {dof.id}: {dof.title[:50]}... (Dept: {dof.department.name if dof.department else 'None'})")
            
            # Bu DÖF'lerin department_id'sini Aksa-Yesa Proje'ye ata
            if dof.department_id != aksa_yesa_dept.id:
                old_dept = dof.department.name if dof.department else 'None'
                dof.department_id = aksa_yesa_dept.id
                print(f"    -> Düzeltildi: {old_dept} -> {aksa_yesa_dept.name}")
        
        if aksa_yesa_dofs:
            db.session.commit()
            print(f"\n✅ {len(aksa_yesa_dofs)} DÖF'ün department_id'si düzeltildi!") 