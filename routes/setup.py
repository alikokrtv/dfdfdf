from flask import Blueprint, flash, redirect, url_for
from app import db
from models import User, Department, UserRole
from datetime import datetime

setup_bp = Blueprint('setup', __name__)

@setup_bp.route('/setup/init')
def initialize_system():
    """Sistemi başlangıç verisiyle doldur"""
    try:
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
            
            flash('Admin kullanıcısı oluşturuldu. Kullanıcı adı: admin, Şifre: Admin123', 'success')
        
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
            
            flash('Departman yöneticisi oluşturuldu. Kullanıcı adı: manager, Şifre: Manager123', 'success')
        
        # Kalite yöneticisi oluştur
        quality_manager = User.query.filter_by(username='quality').first()
        if not quality_manager:
            quality_dept = Department.query.filter_by(name='Kalite Yönetimi').first()
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
            
            flash('Kalite yöneticisi oluşturuldu. Kullanıcı adı: quality, Şifre: Quality123', 'success')
        
        flash('Sistem başarıyla kuruldu!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('auth.login'))
