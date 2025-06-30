"""
Departman ve kullanıcı kurulum betiği
Bu betik çalıştırıldığında veritabanına departmanlar ve kullanıcılar eklenir
"""
from app import app, db
from models import User, Department, DepartmentGroup, GroupDepartment, UserRole
from datetime import datetime

def setup_system():
    with app.app_context():
        # Önce tabloları oluştur
        db.create_all()
        
        # 1. Kalite departmanını oluştur
        quality_dept = Department.query.filter_by(name='Kalite Yönetimi').first()
        if not quality_dept:
            quality_dept = Department(
                name='Kalite Yönetimi',
                description='Kalite süreçlerini yönetir',
                is_active=True,
                created_at=datetime.now()
            )
            db.session.add(quality_dept)
            db.session.commit()
            print(f"Kalite departmanı oluşturuldu. ID: {quality_dept.id}")
        
        # 2. Üretim departmanını oluştur
        production_dept = Department.query.filter_by(name='Üretim').first()
        if not production_dept:
            production_dept = Department(
                name='Üretim',
                description='Üretim süreçlerini yönetir',
                is_active=True,
                created_at=datetime.now()
            )
            db.session.add(production_dept)
            db.session.commit()
            print(f"Üretim departmanı oluşturuldu. ID: {production_dept.id}")
        
        # 3. Satış departmanını oluştur
        sales_dept = Department.query.filter_by(name='Satış').first()
        if not sales_dept:
            sales_dept = Department(
                name='Satış',
                description='Satış süreçlerini yönetir',
                is_active=True,
                created_at=datetime.now()
            )
            db.session.add(sales_dept)
            db.session.commit()
            print(f"Satış departmanı oluşturuldu. ID: {sales_dept.id}")
        
        # 4. İnsan Kaynakları departmanını oluştur
        hr_dept = Department.query.filter_by(name='İnsan Kaynakları').first()
        if not hr_dept:
            hr_dept = Department(
                name='İnsan Kaynakları',
                description='İK süreçlerini yönetir',
                is_active=True,
                created_at=datetime.now()
            )
            db.session.add(hr_dept)
            db.session.commit()
            print(f"İnsan Kaynakları departmanı oluşturuldu. ID: {hr_dept.id}")
            
        # Departman gruplarını oluştur
        # 1. Operasyon Grubu
        operations_group = DepartmentGroup.query.filter_by(name='Operasyon Grubu').first()
        if not operations_group:
            operations_group = DepartmentGroup(
                name='Operasyon Grubu',
                description='Üretim ve satış departmanlarını içerir',
                is_active=True,
                created_at=datetime.now()
            )
            db.session.add(operations_group)
            db.session.commit()
            print(f"Operasyon grubu oluşturuldu. ID: {operations_group.id}")
            
            # Üretim ve Satış departmanlarını Operasyon grubuna bağla
            if production_dept:
                production_dept.group_id = operations_group.id
            if sales_dept:
                sales_dept.group_id = operations_group.id
            db.session.commit()
        
        # 2. Yönetim Grubu
        management_group = DepartmentGroup.query.filter_by(name='Yönetim Grubu').first()
        if not management_group:
            management_group = DepartmentGroup(
                name='Yönetim Grubu',
                description='Kalite ve İK departmanlarını içerir',
                is_active=True,
                created_at=datetime.now()
            )
            db.session.add(management_group)
            db.session.commit()
            print(f"Yönetim grubu oluşturuldu. ID: {management_group.id}")
            
            # Kalite ve İK departmanlarını Yönetim grubuna bağla
            if quality_dept:
                quality_dept.group_id = management_group.id
            if hr_dept:
                hr_dept.group_id = management_group.id
            db.session.commit()
        
        # Kullanıcıları oluştur
        # 1. Admin kullanıcısı
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='alikokrtv@gmail.com',
                first_name='Admin',
                last_name='Kullanıcı',
                role=UserRole.ADMIN,
                department_id=quality_dept.id,
                active=True,
                created_at=datetime.now()
            )
            admin.set_password('Admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin kullanıcısı oluşturuldu.")
        
        # 2. Kalite yöneticisi
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
                created_at=datetime.now()
            )
            quality_manager.set_password('Quality123')
            db.session.add(quality_manager)
            db.session.commit()
            print("Kalite yöneticisi oluşturuldu.")
        
        # 3. Operasyon grubu yöneticisi
        operations_manager = User.query.filter_by(username='operations').first()
        if not operations_manager:
            operations_manager = User(
                username='operations',
                email='operations@example.com',
                first_name='Operasyon',
                last_name='Yöneticisi',
                role=UserRole.GROUP_MANAGER,
                department_id=quality_dept.id,
                active=True,
                created_at=datetime.now()
            )
            operations_manager.set_password('Operations123')
            db.session.add(operations_manager)
            db.session.commit()
            
            # Operasyon grubunun yöneticisi olarak atama
            if operations_group:
                operations_group.manager_id = operations_manager.id
                db.session.commit()
            print("Operasyon grup yöneticisi oluşturuldu.")
        
        # 4. Yönetim grubu yöneticisi
        management_manager = User.query.filter_by(username='management').first()
        if not management_manager:
            management_manager = User(
                username='management',
                email='management@example.com',
                first_name='Yönetim',
                last_name='Yöneticisi',
                role=UserRole.GROUP_MANAGER,
                department_id=quality_dept.id,
                active=True,
                created_at=datetime.now()
            )
            management_manager.set_password('Management123')
            db.session.add(management_manager)
            db.session.commit()
            
            # Yönetim grubunun yöneticisi olarak atama
            if management_group:
                management_group.manager_id = management_manager.id
                db.session.commit()
            print("Yönetim grup yöneticisi oluşturuldu.")
        
        # 5. Üretim departman yöneticisi
        production_manager = User.query.filter_by(username='production').first()
        if not production_manager:
            production_manager = User(
                username='production',
                email='production@example.com',
                first_name='Üretim',
                last_name='Yöneticisi',
                role=UserRole.DEPARTMENT_MANAGER,
                department_id=production_dept.id,
                active=True,
                created_at=datetime.now()
            )
            production_manager.set_password('Production123')
            db.session.add(production_manager)
            db.session.commit()
            
            # Üretim departmanının yöneticisi olarak atama
            if production_dept:
                production_dept.manager_id = production_manager.id
                db.session.commit()
            print("Üretim departman yöneticisi oluşturuldu.")
        
        # 6. Satış departman yöneticisi
        sales_manager = User.query.filter_by(username='sales').first()
        if not sales_manager:
            sales_manager = User(
                username='sales',
                email='sales@example.com',
                first_name='Satış',
                last_name='Yöneticisi',
                role=UserRole.DEPARTMENT_MANAGER,
                department_id=sales_dept.id,
                active=True,
                created_at=datetime.now()
            )
            sales_manager.set_password('Sales123')
            db.session.add(sales_manager)
            db.session.commit()
            
            # Satış departmanının yöneticisi olarak atama
            if sales_dept:
                sales_dept.manager_id = sales_manager.id
                db.session.commit()
            print("Satış departman yöneticisi oluşturuldu.")
        
        # 7. İK departman yöneticisi
        hr_manager = User.query.filter_by(username='hr').first()
        if not hr_manager:
            hr_manager = User(
                username='hr',
                email='hr@example.com',
                first_name='İK',
                last_name='Yöneticisi',
                role=UserRole.DEPARTMENT_MANAGER,
                department_id=hr_dept.id,
                active=True,
                created_at=datetime.now()
            )
            hr_manager.set_password('Hr123')
            db.session.add(hr_manager)
            db.session.commit()
            
            # İK departmanının yöneticisi olarak atama
            if hr_dept:
                hr_dept.manager_id = hr_manager.id
                db.session.commit()
            print("İK departman yöneticisi oluşturuldu.")
        
        # Normal kullanıcılar
        # 8. Üretim çalışanı
        prod_user = User.query.filter_by(username='produser').first()
        if not prod_user:
            prod_user = User(
                username='produser',
                email='produser@example.com',
                first_name='Üretim',
                last_name='Çalışanı',
                role=UserRole.USER,
                department_id=production_dept.id,
                active=True,
                created_at=datetime.now()
            )
            prod_user.set_password('Prod123')
            db.session.add(prod_user)
            db.session.commit()
            print("Üretim çalışanı oluşturuldu.")
        
        # 9. Satış çalışanı
        sales_user = User.query.filter_by(username='salesuser').first()
        if not sales_user:
            sales_user = User(
                username='salesuser',
                email='salesuser@example.com',
                first_name='Satış',
                last_name='Çalışanı',
                role=UserRole.USER,
                department_id=sales_dept.id,
                active=True,
                created_at=datetime.now()
            )
            sales_user.set_password('Sales123')
            db.session.add(sales_user)
            db.session.commit()
            print("Satış çalışanı oluşturuldu.")
        
        print("\nKurulum tamamlandı!")
        print("Oluşturulan kullanıcılar:")
        print("Admin: admin / Admin123")
        print("Kalite Yöneticisi: quality / Quality123")
        print("Operasyon Grup Yöneticisi: operations / Operations123")
        print("Yönetim Grup Yöneticisi: management / Management123")
        print("Üretim Departman Yöneticisi: production / Production123")
        print("Satış Departman Yöneticisi: sales / Sales123")
        print("İK Departman Yöneticisi: hr / Hr123")
        print("Üretim Çalışanı: produser / Prod123")
        print("Satış Çalışanı: salesuser / Sales123")

if __name__ == "__main__":
    print("Departman ve kullanıcı kurulumu başlatılıyor...")
    setup_system()
