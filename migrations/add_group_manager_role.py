"""
Grup Yöneticisi rolünü ve Departman Grubu yapısını eklemek için migrasyon betiği
"""
from flask import current_app
import sys
import os

# Proje ana dizinini sys.path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import db
from models import UserRole, DepartmentGroup, GroupDepartment

def upgrade_database():
    """
    Veritabanı şemasını yükseltmek için gerekli işlemleri yapar
    """
    app = current_app._get_current_object()
    
    with app.app_context():
        # Yeni tabloları oluşturma
        db.create_all()
        
        # Mevcut departman yöneticilerinin rollerini güncelleme
        db.session.execute("""
            UPDATE users 
            SET role = 4 
            WHERE role = 3
        """)
        
        # Mevcut DepartmentManager tablosunu kaldırma (eğer varsa)
        db.session.execute("""
            DROP TABLE IF EXISTS department_managers
        """)
        
        # Departman tablosuna group_id sütununu ekleme
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('departments')]
        
        if 'group_id' not in columns:
            db.session.execute("""
                ALTER TABLE departments
                ADD COLUMN group_id INTEGER,
                ADD CONSTRAINT fk_departments_group
                FOREIGN KEY (group_id) REFERENCES department_groups (id)
            """)
        
        db.session.commit()
        print("Migrasyon başarıyla tamamlandı!")

def downgrade_database():
    """
    Veritabanını önceki haline döndürmek için gerekli işlemleri yapar
    """
    app = current_app._get_current_object()
    
    with app.app_context():
        # Departman yöneticilerinin rollerini eski haline getirme
        db.session.execute("""
            UPDATE users 
            SET role = 3 
            WHERE role = 4
        """)
        
        # DepartmentManager tablosunu tekrar oluşturma
        db.session.execute("""
            CREATE TABLE IF NOT EXISTS department_managers (
                id INTEGER PRIMARY KEY,
                department_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                is_primary BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Departman tablosundan group_id sütununu kaldırma
        inspector = db.inspect(db.engine)
        columns = [column['name'] for column in inspector.get_columns('departments')]
        
        if 'group_id' in columns:
            db.session.execute("""
                ALTER TABLE departments
                DROP COLUMN group_id
            """)
        
        # Yeni tabloları kaldırma
        GroupDepartment.__table__.drop(db.engine, checkfirst=True)
        DepartmentGroup.__table__.drop(db.engine, checkfirst=True)
        
        db.session.commit()
        print("Veritabanı önceki haline döndürüldü!")

if __name__ == "__main__":
    print("Bu betik direkt çalıştırılmamalıdır. Flask uygulama bağlamında çalıştırılmalıdır.")
