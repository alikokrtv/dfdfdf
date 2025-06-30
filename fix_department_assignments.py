#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Departman atama sorunlarını düzelten kapsamlı bir script.
Bu script şu işlemleri gerçekleştirir:
1. Departman-kullanıcı ilişkilerini düzeltir
2. Departman yöneticisi atamalarını düzeltir
3. Departmanı olmayan DÖF'leri düzeltir
"""
from app import app, db
from models import User, Department, DOF, UserRole
import logging
from flask import current_app
from datetime import datetime

def fix_assignments():
    """Tüm departman atama sorunlarını düzeltir"""
    print(f"=== Departman Atama Düzeltme Scripti - {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} ===")
    
    # Bilgi ekranı
    print("\n1. Mevcut Durum:")
    dept_count = Department.query.count()
    user_count = User.query.count()
    manager_count = User.query.filter_by(role=UserRole.DEPARTMENT_MANAGER).count()
    print(f"   - {dept_count} departman")
    print(f"   - {user_count} kullanıcı")
    print(f"   - {manager_count} departman yöneticisi")
    
    # Departman yöneticileri düzelt
    print("\n2. Departman Yöneticileri Düzeltiliyor:")
    fixed_managers = _fix_department_managers()
    
    # Kullanıcı departmanlarını düzelt
    print("\n3. Kullanıcı Departman Atamaları Düzeltiliyor:")
    fixed_users = _fix_user_departments()
    
    # DÖF departmanlarını düzelt
    print("\n4. DÖF Departman Atamaları Düzeltiliyor:")
    fixed_dofs = _fix_dof_departments()
    
    print("\n=== SONUÇ ===")
    print(f"- {len(fixed_managers)} departman yöneticisi düzeltildi")
    print(f"- {len(fixed_users)} kullanıcı departmanı düzeltildi")
    print(f"- {len(fixed_dofs)} DÖF departmanı düzeltildi")
    print(f"İşlem tamamlandı - {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    return {
        "fixed_managers": fixed_managers,
        "fixed_users": fixed_users,
        "fixed_dofs": fixed_dofs
    }

def _fix_department_managers():
    """Departman yöneticilerini düzeltir"""
    fixed_managers = []
    
    # Tüm departmanları ve yöneticilerini kontrol et
    departments = Department.query.all()
    for dept in departments:
        # Bu departman için yönetici var mı?
        manager = User.query.filter_by(department_id=dept.id, role=UserRole.DEPARTMENT_MANAGER).first()
        
        if not manager:
            print(f"   [!] Departman '{dept.name}' için yönetici atanmamış")
            
            # Bu departmandan herhangi bir kullanıcı var mı?
            dept_user = User.query.filter_by(department_id=dept.id).first()
            
            if dept_user:
                # Kullanıcı var, onu departman yöneticisi yap
                dept_user.role = UserRole.DEPARTMENT_MANAGER
                fixed_managers.append({
                    "user_id": dept_user.id,
                    "user_name": dept_user.full_name,
                    "department": dept.name,
                    "action": "Mevcut kullanıcı yönetici yapıldı"
                })
                print(f"   [+] '{dept_user.full_name}' kullanıcısı '{dept.name}' departmanının yöneticisi yapıldı")
            else:
                # Departmanda hiç kullanıcı yok - normal kullanıcılardan birini ata
                regular_user = User.query.filter_by(role=UserRole.USER).first()
                
                if regular_user:
                    regular_user.role = UserRole.DEPARTMENT_MANAGER
                    regular_user.department_id = dept.id
                    fixed_managers.append({
                        "user_id": regular_user.id,
                        "user_name": regular_user.full_name,
                        "department": dept.name,
                        "action": "Yeni kullanıcı yönetici yapıldı"
                    })
                    print(f"   [+] '{regular_user.full_name}' kullanıcısı '{dept.name}' departmanının yöneticisi yapıldı")
                else:
                    print(f"   [-] '{dept.name}' departmanı için yönetici atanamadı")
    
    # Değişiklikleri kaydet
    if fixed_managers:
        db.session.commit()
    
    return fixed_managers

def _fix_user_departments():
    """Kullanıcı departman atamalarını düzeltir"""
    fixed_users = []
    
    # Departmanı olmayan kullanıcıları bul
    users_without_dept = User.query.filter(User.department_id == None).all()
    
    if users_without_dept:
        print(f"   [!] {len(users_without_dept)} kullanıcının departmanı atanmamış")
        
        # Kullanıcı adından departman bulmaya çalış
        default_dept = Department.query.first()  # Hiçbir departman bulunamazsa varsayılan olarak ilk departmanı kullan
        
        for user in users_without_dept:
            # Kullanıcı adından departman bulmaya çalış
            possible_dept_name = user.username.split('@')[0].split('.')[0].capitalize()
            dept = Department.query.filter(Department.name.like(f"%{possible_dept_name}%")).first()
            
            if dept:
                user.department_id = dept.id
                fixed_users.append({
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "department": dept.name,
                    "action": "Kullanıcı adına göre departman atandı"
                })
                print(f"   [+] '{user.full_name}' kullanıcısına '{dept.name}' departmanı atandı")
            elif default_dept:
                user.department_id = default_dept.id
                fixed_users.append({
                    "user_id": user.id,
                    "user_name": user.full_name,
                    "department": default_dept.name,
                    "action": "Varsayılan departman atandı"
                })
                print(f"   [+] '{user.full_name}' kullanıcısına varsayılan '{default_dept.name}' departmanı atandı")
    else:
        print("   [+] Tüm kullanıcıların departmanı atanmış")
    
    # Değişiklikleri kaydet
    if fixed_users:
        db.session.commit()
    
    return fixed_users

def _fix_dof_departments():
    """DÖF departman atamalarını düzeltir"""
    fixed_dofs = []
    
    # Departmanı olmayan DÖF'leri bul
    dofs_without_dept = DOF.query.filter(DOF.department_id == None).all()
    
    if dofs_without_dept:
        print(f"   [!] {len(dofs_without_dept)} DÖF'ün departmanı atanmamış")
        
        default_dept = Department.query.first()  # Varsayılan departman
        
        for dof in dofs_without_dept:
            # DÖF'ü oluşturan kullanıcının departmanını kullan
            creator = User.query.get(dof.created_by) if dof.created_by else None
            
            if creator and creator.department_id:
                dof.department_id = creator.department_id
                dept_name = creator.department.name if creator.department else "Bilinmiyor"
                fixed_dofs.append({
                    "dof_id": dof.id,
                    "dof_title": dof.title,
                    "department": dept_name,
                    "action": "Oluşturan kullanıcının departmanı atandı"
                })
                print(f"   [+] '{dof.title}' DÖF'üne oluşturan kullanıcının departmanı '{dept_name}' atandı")
            elif default_dept:
                dof.department_id = default_dept.id
                fixed_dofs.append({
                    "dof_id": dof.id,
                    "dof_title": dof.title,
                    "department": default_dept.name,
                    "action": "Varsayılan departman atandı"
                })
                print(f"   [+] '{dof.title}' DÖF'üne varsayılan '{default_dept.name}' departmanı atandı")
    else:
        print("   [+] Tüm DÖF'lerin departmanı atanmış")
    
    # Değişiklikleri kaydet
    if fixed_dofs:
        db.session.commit()
    
    return fixed_dofs

if __name__ == "__main__":
    with app.app_context():
        try:
            results = fix_assignments()
            print("\nScript başarıyla tamamlandı.")
        except Exception as e:
            print(f"\nHata oluştu: {str(e)}")
            import traceback
            print(traceback.format_exc())
