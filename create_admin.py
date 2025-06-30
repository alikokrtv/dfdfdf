from app import app, db
from models import User, Department, UserRole
import datetime

def create_admin_user():
    with app.app_context():
        # Veritabanı tablolarını oluştur
        db.create_all()
        
        # Admin kullanıcısı zaten var mı kontrol et
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin kullanıcısı zaten mevcut.")
            return
        
        # Yeni admin kullanıcısı oluştur
        admin = User()
        admin.username = 'admin'
        admin.email = 'alikokrtv@gmail.com'
        admin.set_password('Admin123')
        admin.first_name = 'Admin'
        admin.last_name = 'User'
        admin.role = UserRole.ADMIN
        admin.active = True
        admin.created_at = datetime.datetime.now()
        
        # Kalite departmanı oluştur
        quality_dept = Department()
        quality_dept.name = 'Kalite Yönetimi'
        quality_dept.description = 'Kalite yönetim departmanı'
        quality_dept.is_active = True
        quality_dept.created_at = datetime.datetime.now()
        
        db.session.add(quality_dept)
        db.session.commit()
        
        # Admin kullanıcısını kaydet
        admin.department_id = quality_dept.id
        db.session.add(admin)
        db.session.commit()
        
        print("Admin kullanıcısı başarıyla oluşturuldu.")
        print("Kullanıcı adı: admin")
        print("Şifre: Admin123")

if __name__ == '__main__':
    create_admin_user()