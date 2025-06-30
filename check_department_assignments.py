#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Departman atama ve kullanıcı-departman eşleştirmesi kontrol scripti
"""

import sys
import os
from datetime import datetime

# Mevcut dizini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import DOF, User, Department, UserRole
    import traceback

    def check_department_assignments():
        print("🏢 Departman Atama Kontrolü")
        print("=" * 60)
        
        with app.app_context():
            try:
                # 1. Tüm departmanları listele
                print("📋 DEPARTMANLAR:")
                departments = Department.query.all()
                for dept in departments:
                    print(f"   🏢 {dept.name} (ID: {dept.id})")
                
                print("\n" + "=" * 60)
                
                # 2. Departman yöneticilerini kontrol et
                print("👥 DEPARTMAN YÖNETİCİLERİ:")
                dept_managers = User.query.filter_by(role=UserRole.DEPARTMENT_MANAGER, active=True).all()
                
                for manager in dept_managers:
                    dept_name = manager.department.name if manager.department else "❌ DEPARTMAN YOK"
                    print(f"   👤 {manager.full_name} ({manager.email})")
                    print(f"      🏢 Departman: {dept_name} (ID: {manager.department_id})")
                    print()
                
                # 3. İstinye departmanını özel olarak kontrol et
                print("=" * 60)
                print("🔍 İSTİNYE DEPARTMANI DETAYI:")
                
                istinye_dept = Department.query.filter(Department.name.like('%İstinye%')).first()
                if istinye_dept:
                    print(f"   🏢 Departman: {istinye_dept.name} (ID: {istinye_dept.id})")
                    
                    # İstinye departmanındaki kullanıcılar
                    istinye_users = User.query.filter_by(department_id=istinye_dept.id, active=True).all()
                    print(f"   👥 Bu departmandaki kullanıcılar ({len(istinye_users)} kişi):")
                    
                    for user in istinye_users:
                        role_name = {
                            1: "Admin",
                            2: "Kalite Yöneticisi", 
                            3: "Kullanıcı",
                            4: "Departman Yöneticisi"
                        }.get(user.role, f"Bilinmeyen({user.role})")
                        
                        print(f"      👤 {user.full_name} ({user.email})")
                        print(f"         🎭 Rol: {role_name}")
                        print()
                else:
                    print("   ❌ İstinye departmanı bulunamadı!")
                
                # 4. Son DÖF'lerin departman ataması
                print("=" * 60)
                print("📋 SON DÖF'LERİN DEPARTMAN ATAMASI:")
                
                recent_dofs = DOF.query.filter(DOF.id.in_([28, 32])).all()
                for dof in recent_dofs:
                    print(f"   📋 DÖF #{dof.id}: {dof.title}")
                    if dof.department:
                        print(f"      🏢 Atanan Departman: {dof.department.name} (ID: {dof.department_id})")
                        
                        # Bu departmandaki yöneticiler
                        managers = User.query.filter_by(
                            department_id=dof.department_id, 
                            role=UserRole.DEPARTMENT_MANAGER,
                            active=True
                        ).all()
                        
                        print(f"      👤 Departman yöneticileri ({len(managers)} kişi):")
                        for manager in managers:
                            print(f"         - {manager.full_name} ({manager.email})")
                    else:
                        print(f"      ❌ Departman atanmamış (department_id: {dof.department_id})")
                    print()
                
            except Exception as e:
                print(f"❌ Hata: {str(e)}")
                import traceback
                print(traceback.format_exc())

    if __name__ == "__main__":
        check_department_assignments()
        
except Exception as e:
    print(f"❌ Import hatası: {str(e)}") 