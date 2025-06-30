"""
DÖF sisteminde departman yöneticisi yetkilendirme sorunlarını düzeltir.
Bu script Railway'de çalıştırıldığında:
1. Departman yöneticisi rolündeki kullanıcıların doğru departmanlara atanmasını sağlar
2. DÖF'lerin doğru departmanlara atanmasını kontrol eder
"""

from flask import Flask
import os
import sys

# Ana uygulama klasörünü ekliyoruz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Uygulamayı oluşturuyoruz
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dof.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Modellerimizi oluşturuyoruz (doğrudan burada tanımlayarak import hatalarından kaçınıyoruz)
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# UserRole sınıfı (models.py'den)
class UserRole:
    ADMIN = 0  # Admin
    GROUP_OPERATIONS = 1  # Operasyon Grup Yöneticisi
    QUALITY_MANAGER = 2  # Kalite Yöneticisi
    GROUP_MANAGER = 3  # Grup Yöneticisi
    DEPARTMENT_MANAGER = 4  # Departman Yöneticisi
    USER = 5  # Normal Kullanıcı

# DOFStatus sınıfı (models.py'den)
class DOFStatus:
    DRAFT = 0  # Taslak
    SUBMITTED = 1  # Gönderildi
    IN_REVIEW = 2  # İncelemede
    ASSIGNED = 3  # Atandı
    IN_PROGRESS = 4  # Devam Ediyor
    RESOLVED = 5  # Çözüldü
    CLOSED = 6  # Kapatıldı
    REJECTED = 7  # Reddedildi

# Çalışan modeli
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.Integer, default=UserRole.USER)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    
    department = db.relationship('Department', back_populates='users')
    created_dofs = db.relationship('DOF', foreign_keys='DOF.created_by', back_populates='creator')
    assigned_dofs = db.relationship('DOF', foreign_keys='DOF.assigned_to', back_populates='assignee')
    
    def __repr__(self):
        return f'<User {self.username}>'

# Departman modeli
class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    users = db.relationship('User', back_populates='department')
    
    def __repr__(self):
        return f'<Department {self.name}>'

# DÖF modeli
class DOF(db.Model):
    __tablename__ = 'dofs'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    dof_type = db.Column(db.Integer, default=1)  # 1: Düzeltici, 2: Önleyici
    source = db.Column(db.Integer, default=1)
    status = db.Column(db.Integer, default=DOFStatus.DRAFT)
    
    created_date = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    source_department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Root cause analysis and action plan
    root_cause1 = db.Column(db.Text, nullable=True)
    root_cause2 = db.Column(db.Text, nullable=True)
    root_cause3 = db.Column(db.Text, nullable=True)
    root_cause4 = db.Column(db.Text, nullable=True)
    root_cause5 = db.Column(db.Text, nullable=True)
    action_plan = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by], back_populates='created_dofs')
    assignee = db.relationship('User', foreign_keys=[assigned_to], back_populates='assigned_dofs')
    department = db.relationship('Department', foreign_keys=[department_id])
    source_department = db.relationship('Department', foreign_keys=[source_department_id])

def fix_permissions_for_railway():
    """
    Railway'de çalıştığında tüm izin sorunlarını düzelten fonksiyon
    """
    with app.app_context():
        print("Departman yöneticisi kontrolleri başlatılıyor...")
        
        # Tüm departman yöneticilerini göster
        dept_managers = User.query.filter_by(role=UserRole.DEPARTMENT_MANAGER).all()
        print(f"Sistemde {len(dept_managers)} departman yöneticisi bulundu.")
        
        for manager in dept_managers:
            dept = Department.query.get(manager.department_id) if manager.department_id else None
            dept_name = dept.name if dept else "Departman atanmamış"
            print(f"Yönetici: {manager.username}, Departman: {dept_name}")
            
            # Eğer departmanı yoksa, bir departman ata
            if not dept:
                # Yöneticisi olmayan bir departman bul
                unassigned_dept = Department.query.filter(~Department.id.in_(
                    [m.department_id for m in dept_managers if m.department_id]
                )).first()
                
                if unassigned_dept:
                    manager.department_id = unassigned_dept.id
                    print(f"{manager.username} kullanıcısına {unassigned_dept.name} departmanı atandı")
                    db.session.commit()
        
        # Atanmış durumdaki DÖF'leri kontrol et
        assigned_dofs = DOF.query.filter_by(status=DOFStatus.ASSIGNED).all()
        print(f"\nAtanmış durumda {len(assigned_dofs)} DÖF bulundu.")
        
        for dof in assigned_dofs:
            assignee = User.query.get(dof.assigned_to) if dof.assigned_to else None
            dept = Department.query.get(dof.department_id) if dof.department_id else None
            
            print(f"DÖF ID: {dof.id}, Atanan: {assignee.username if assignee else 'Atanmamış'}, "
                  f"Departman: {dept.name if dept else 'Departman yok'}")
            
            # DÖF'ün departmanı yoksa, atanan kişinin departmanını ata
            if assignee and (not dept) and assignee.department_id:
                dof.department_id = assignee.department_id
                assigned_dept = Department.query.get(assignee.department_id)
                if assigned_dept:
                    print(f"DÖF {dof.id} için {assigned_dept.name} departmanı atandı")
                    db.session.commit()
            
            # DÖF'ün atanan kişisi yoksa, departman yöneticisini ata
            if dept and not assignee:
                try:
                    dept_manager = User.query.filter_by(
                        role=UserRole.DEPARTMENT_MANAGER, 
                        department_id=dept.id
                    ).first()
                    
                    if dept_manager:
                        dof.assigned_to = dept_manager.id
                        print(f"DÖF {dof.id} için {dept_manager.username} yöneticisi atandı")
                        db.session.commit()
                except Exception as e:
                    print(f"Yönetici atama hatası: {e}")
        
        print("\nİşlem tamamlandı!")

if __name__ == "__main__":
    try:
        fix_permissions_for_railway()
    except Exception as e:
        print(f"Hata oluştu: {e}")
