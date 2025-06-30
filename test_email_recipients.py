#!/usr/bin/env python3
"""
E-posta alıcılarını kontrol etmek için test scripti
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, UserRole, Department, UserDepartmentMapping, DirectorManagerMapping
from daily_email_scheduler import get_user_managed_departments

def test_email_recipients():
    """E-posta alıcılarını kontrol et"""
    
    with app.app_context():
        print("=" * 70)
        print("📧 E-POSTA ALICI KONTROLÜ")
        print("=" * 70)
        
        # Tüm rollerdeki kullanıcıları kontrol et
        all_users = User.query.filter_by(active=True).all()
        
        print(f"\n🔍 TOPLAM AKTİF KULLANICI: {len(all_users)}")
        print("-" * 50)
        
        role_counts = {}
        for user in all_users:
            role_name = user.role_name
            role_counts[role_name] = role_counts.get(role_name, 0) + 1
        
        for role, count in role_counts.items():
            print(f"👤 {role}: {count} kullanıcı")
        
        print("\n" + "=" * 70)
        print("📋 E-POSTA ALICI DETAYLARI")
        print("=" * 70)
        
        # E-posta alacak rollerdeki kullanıcıları getir
        target_roles = [UserRole.DEPARTMENT_MANAGER, UserRole.GROUP_MANAGER, UserRole.DIRECTOR]
        target_users = User.query.filter(
            User.role.in_(target_roles),
            User.active == True,
            User.email.isnot(None),
            User.email != ''
        ).all()
        
        print(f"\n📧 E-POSTA HEDEF KULLANICI SAYISI: {len(target_users)}")
        
        for user in target_users:
            print(f"\n👤 {user.full_name} ({user.role_name})")
            print(f"   📧 E-posta: {user.email}")
            print(f"   🏢 Departman ID: {user.department_id}")
            
            # Yönetilen departmanları kontrol et
            departments = get_user_managed_departments(user)
            
            if departments:
                print(f"   📊 Yönetilen Departmanlar ({len(departments)}):")
                for dept in departments:
                    print(f"      - {dept.name} (ID: {dept.id})")
            else:
                print(f"   ⚠️  YÖNETİLEN DEPARTMAN YOK!")
                
                # Detaylı analiz
                if user.role == UserRole.DEPARTMENT_MANAGER:
                    if user.department_id:
                        dept = Department.query.get(user.department_id)
                        if dept:
                            print(f"      💡 Departmanı var ama manager_id eşleşmiyor")
                            print(f"         Departman: {dept.name}, Manager ID: {dept.manager_id}")
                        else:
                            print(f"      ❌ Departman ID {user.department_id} bulunamadı")
                    else:
                        print(f"      ❌ Departman ID atanmamış")
                        
                elif user.role == UserRole.GROUP_MANAGER:
                    mappings = UserDepartmentMapping.query.filter_by(user_id=user.id).all()
                    print(f"      💡 UserDepartmentMapping sayısı: {len(mappings)}")
                    for mapping in mappings:
                        if mapping.department:
                            print(f"         - {mapping.department.name}")
                        else:
                            print(f"         - Departman ID {mapping.department_id} geçersiz")
                            
                elif user.role == UserRole.DIRECTOR:
                    director_mappings = DirectorManagerMapping.query.filter_by(director_id=user.id).all()
                    print(f"      💡 DirectorManagerMapping sayısı: {len(director_mappings)}")
                    for mapping in director_mappings:
                        if mapping.manager:
                            manager = mapping.manager
                            print(f"         - Bölge Müdürü: {manager.full_name}")
                            # Bu bölge müdürünün departmanları
                            manager_depts = get_user_managed_departments(manager)
                            for dept in manager_depts:
                                print(f"           └─ {dept.name}")
                        else:
                            print(f"         - Manager ID {mapping.manager_id} geçersiz")
        
        print("\n" + "=" * 70)
        print("📊 DEPARTMAN İLİŞKİLERİ KONTROLÜ")
        print("=" * 70)
        
        # UserDepartmentMapping kontrol
        udm_count = UserDepartmentMapping.query.count()
        print(f"\n🔗 UserDepartmentMapping kayıt sayısı: {udm_count}")
        
        udm_records = UserDepartmentMapping.query.all()
        for udm in udm_records:
            user = User.query.get(udm.user_id)
            dept = Department.query.get(udm.department_id)
            print(f"   👤 {user.full_name if user else 'UNKNOWN'} ↔ 🏢 {dept.name if dept else 'UNKNOWN'}")
        
        # DirectorManagerMapping kontrol
        dmm_count = DirectorManagerMapping.query.count()
        print(f"\n🔗 DirectorManagerMapping kayıt sayısı: {dmm_count}")
        
        dmm_records = DirectorManagerMapping.query.all()
        for dmm in dmm_records:
            director = User.query.get(dmm.director_id)
            manager = User.query.get(dmm.manager_id)
            print(f"   👑 {director.full_name if director else 'UNKNOWN'} ← 👤 {manager.full_name if manager else 'UNKNOWN'}")

if __name__ == "__main__":
    test_email_recipients() 