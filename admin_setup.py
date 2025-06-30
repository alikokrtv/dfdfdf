from app import app, db
from models import User, Department, DepartmentGroup, GroupDepartment, UserRole
from datetime import datetime

with app.app_context():
    # Kontrol et ve gerekirse tabloları oluştur
    db.create_all()
    
    # Admin kullanıcısı oluştur
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Önce Kalite departmanını oluştur
        quality_dept = Department.query.filter_by(name='Kalite Yönetimi').first()
        if not quality_dept:
            quality_dept = Department(
                name='Kalite Yönetimi',
                description='Kalite yönetim departmanı',
                is_active=True,
                created_at=datetime.now()
            )
            db.session.add(quality_dept)
            db.session.commit()
            print(f"Kalite departmanı oluşturuldu. ID: {quality_dept.id}")
        
        # Admin kullanıcısını oluştur
        admin = User(
            username='admin',
            email='alikokrtv@gmail.com',
            first_name='Admin',
            last_name='User',
            role=UserRole.ADMIN,
            department_id=quality_dept.id,
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        admin.set_password('Admin123')
        db.session.add(admin)
        db.session.commit()
        
        print("Admin kullanıcısı başarıyla oluşturuldu.")
        print("Kullanıcı adı: admin")
        print("Şifre: Admin123")
    else:
        print("Admin kullanıcısı zaten mevcut.")
    
    # Test departmanı oluştur
    test_dept = Department.query.filter_by(name='Test Departmanı').first()
    if not test_dept:
        test_dept = Department(
            name='Test Departmanı',
            description='Test amaçlı oluşturulan departman',
            is_active=True,
            created_at=datetime.now()
        )
        db.session.add(test_dept)
        db.session.commit()
        print(f"Test departmanı oluşturuldu. ID: {test_dept.id}")
        
        # Departman yöneticisi oluştur
        dept_manager = User(
            username='manager',
            email='manager@example.com',
            first_name='Departman',
            last_name='Yöneticisi',
            role=UserRole.DEPARTMENT_MANAGER,
            department_id=test_dept.id,
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        dept_manager.set_password('Manager123')
        db.session.add(dept_manager)
        
        # Test departmanının yöneticisini ayarla
        test_dept.manager_id = dept_manager.id
        db.session.commit()
        
        print("Departman yöneticisi başarıyla oluşturuldu.")
        print("Kullanıcı adı: manager")
        print("Şifre: Manager123")
    else:
        print("Test departmanı zaten mevcut.")
        
    # Kalite yöneticisi oluştur
    quality_manager = User.query.filter_by(username='quality').first()
    if not quality_manager:
        quality_manager = User(
            username='quality',
            email='quality@example.com',
            first_name='Kalite',
            last_name='Yöneticisi',
            role=UserRole.QUALITY_MANAGER,
            department_id=quality_dept.id,
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        quality_manager.set_password('Quality123')
        db.session.add(quality_manager)
        db.session.commit()
        
        print("Kalite yöneticisi başarıyla oluşturuldu.")
        print("Kullanıcı adı: quality")
        print("Şifre: Quality123")
    else:
        print("Kalite yöneticisi zaten mevcut.")
        
    # Grup oluştur
    operations_group = DepartmentGroup.query.filter_by(name='Operasyon Grubu').first()
    if not operations_group:
        operations_group = DepartmentGroup(
            name='Operasyon Grubu',
            description='Operasyonel departmanları içeren grup',
            is_active=True,
            created_at=datetime.now()
        )
        db.session.add(operations_group)
        db.session.commit()
        print(f"Operasyon grubu oluşturuldu. ID: {operations_group.id}")
    
        # Grup yöneticisi oluştur
        group_manager = User.query.filter_by(username='groupmanager').first()
        if not group_manager:
            group_manager = User(
                username='groupmanager',
                email='group@example.com',
                first_name='Grup',
                last_name='Yöneticisi',
                role=UserRole.GROUP_MANAGER,
                department_id=quality_dept.id,  # Kalite departmanına bağlı
                active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            group_manager.set_password('Group123')
            db.session.add(group_manager)
            db.session.commit()
            
            # Grup yöneticisini gruba ata
            operations_group.manager_id = group_manager.id
            db.session.commit()
            
            print("Grup yöneticisi başarıyla oluşturuldu.")
            print("Kullanıcı adı: groupmanager")
            print("Şifre: Group123")
        
        # Test departmanını gruba ekle
        if test_dept:
            test_dept.group_id = operations_group.id
            
            # Ayrıca GroupDepartment tablosuna da ekle
            group_dept_relation = GroupDepartment(
                group_id=operations_group.id,
                department_id=test_dept.id,
                created_at=datetime.now()
            )
            db.session.add(group_dept_relation)
            db.session.commit()
            print(f"Test departmanı operasyon grubuna eklendi.")
    else:
        print("Operasyon grubu zaten mevcut.")
