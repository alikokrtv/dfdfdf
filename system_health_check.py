#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sistem Sağlığı Kontrol Aracı
Bu script, sistemdeki verilerin tutarlılığını kontrol eder ve gereksiz setup scriptlerini belirler.
"""

from app import app, db
from models import User, Department, DOF, DOFAction, EmailSettings
import os
import logging
import sys

# Log ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("HealthCheck")

def print_separator(title=None):
    line = "=" * 70
    if title:
        print(f"\n{line}")
        print(f"{title.center(70)}")
        print(f"{line}\n")
    else:
        print(f"\n{line}\n")

def check_system_health():
    """
    Sistem sağlığını kontrol et
    """
    with app.app_context():
        print_separator("SİSTEM SAĞLIĞI KONTROL RAPORU")
        
        # 1. Kullanıcı ve e-posta tutarlılığı kontrolü
        print_separator("KULLANICILAR KONTROLÜ")
        users = User.query.all()
        problem_users = []
        
        print(f"Sistemde toplam {len(users)} kullanıcı var.")
        
        for user in users:
            issues = []
            # E-posta formatı kontrolü
            if user.email and "@example.com" in user.email:
                issues.append(f"Örnek e-posta kullanılıyor: {user.email}")
            
            # Boş veya geçersiz e-posta kontrolü
            if not user.email or len(user.email) < 5 or "@" not in user.email:
                issues.append(f"Geçersiz e-posta: {user.email}")
                
            # Aktif kullanıcı kontrolü
            if not user.is_active:
                issues.append("Kullanıcı aktif değil")
                
            # Departman kontrolü
            if not user.department_id:
                issues.append("Departman atanmamış")
                
            if issues:
                problem_users.append((user, issues))
                
        # Sorunlu kullanıcıları listele
        if problem_users:
            print(f"\n‼️ {len(problem_users)} sorunlu kullanıcı tespit edildi:")
            for user, issues in problem_users:
                print(f"  • {user.username} ({user.email}) - {user.role_name}")
                for issue in issues:
                    print(f"    - {issue}")
        else:
            print("✓ Tüm kullanıcı verileri tutarlı.")
            
        # 2. Departman kontrolü
        print_separator("DEPARTMANLAR KONTROLÜ")
        departments = Department.query.all()
        problem_departments = []
        
        print(f"Sistemde toplam {len(departments)} departman var.")
        
        for dept in departments:
            issues = []
            # Boş ad kontrolü
            if not dept.name or len(dept.name) < 2:
                issues.append("Geçersiz departman adı")
                
            # Aktif departman kontrolü
            if not dept.is_active:
                issues.append("Departman aktif değil")
                
            # Departmanda kullanıcı kontrolü
            user_count = User.query.filter_by(department_id=dept.id).count()
            if user_count == 0:
                issues.append("Departmanda hiç kullanıcı yok")
                
            if issues:
                problem_departments.append((dept, issues))
                
        # Sorunlu departmanları listele
        if problem_departments:
            print(f"\n‼️ {len(problem_departments)} sorunlu departman tespit edildi:")
            for dept, issues in problem_departments:
                print(f"  • {dept.name} (ID: {dept.id})")
                for issue in issues:
                    print(f"    - {issue}")
        else:
            print("✓ Tüm departman verileri tutarlı.")
            
        # 3. E-posta ayarları kontrolü
        print_separator("E-POSTA AYARLARI KONTROLÜ")
        email_settings = EmailSettings.query.first()
        
        if not email_settings:
            print("❌ E-posta ayarları tanımlanmamış!")
        else:
            print(f"✓ E-posta ayarları tanımlanmış:")
            print(f"  • SMTP Sunucu: {email_settings.smtp_host}:{email_settings.smtp_port}")
            print(f"  • Kullanıcı: {email_settings.smtp_user}")
            print(f"  • TLS/SSL: {'TLS' if email_settings.smtp_use_tls else 'SSL' if email_settings.smtp_use_ssl else 'Yok'}")
            
        # 4. Setup scriptleri kontrolü
        print_separator("SETUP SCRİPTLERİ KONTROLÜ")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        setup_scripts = []
        
        # Setup ile ilgili dosyaları bul
        for filename in os.listdir(base_dir):
            if filename.endswith('.py') and ('setup' in filename.lower() or 'create' in filename.lower()):
                setup_scripts.append(filename)
                
        if setup_scripts:
            print(f"⚠️ Sistemde {len(setup_scripts)} adet setup scripti tespit edildi:")
            for script in setup_scripts:
                print(f"  • {script}")
            print("\n⚠️ Bu scriptler birbiriyle çakışabilir ve veri tutarsızlığına neden olabilir.")
            print("⚠️ Önerilen çözüm: Tek bir setup scripti kullanılmalı ve diğerleri kaldırılmalıdır.")
        else:
            print("✓ Setup scripti bulunamadı.")
            
        # 5. DÖF kontrolü
        print_separator("DÖF VERİLERİ KONTROLÜ")
        dofs = DOF.query.all()
        problem_dofs = []
        
        print(f"Sistemde toplam {len(dofs)} DÖF kaydı var.")
        
        for dof in dofs:
            issues = []
            # Başlık kontrolü
            if not dof.title or len(dof.title) < 5:
                issues.append("Geçersiz DÖF başlığı")
                
            # Departman kontrolü
            if not dof.department_id:
                issues.append("Departman atanmamış")
                
            # Oluşturan kullanıcı kontrolü
            if not dof.created_by:
                issues.append("Oluşturan kullanıcı belirtilmemiş")
            else:
                creator = User.query.get(dof.created_by)
                if not creator:
                    issues.append(f"Oluşturan kullanıcı (ID: {dof.created_by}) sistemde bulunamadı")
                    
            # Atanan kullanıcı kontrolü
            if dof.assigned_to:
                assignee = User.query.get(dof.assigned_to)
                if not assignee:
                    issues.append(f"Atanan kullanıcı (ID: {dof.assigned_to}) sistemde bulunamadı")
                    
            # Aksiyon kontrolü
            action_count = DOFAction.query.filter_by(dof_id=dof.id).count()
            if action_count == 0 and dof.status != 0:  # Taslak değilse
                issues.append("DÖF aksiyonu kaydedilmemiş")
                
            if issues:
                problem_dofs.append((dof, issues))
                
        # Sorunlu DÖF'leri listele
        if problem_dofs:
            print(f"\n‼️ {len(problem_dofs)} sorunlu DÖF tespit edildi:")
            for dof, issues in problem_dofs:
                print(f"  • #{dof.id}: {dof.title}")
                for issue in issues:
                    print(f"    - {issue}")
        else:
            print("✓ Tüm DÖF verileri tutarlı.")
            
        # ÖZET
        print_separator("SİSTEM SAĞLIĞI ÖZETİ")
        
        total_issues = len(problem_users) + len(problem_departments) + len(problem_dofs)
        if not email_settings:
            total_issues += 1
            
        if total_issues > 0:
            print(f"⚠️ Sistemde toplam {total_issues} sorun tespit edildi.")
            print("⚠️ Önerilen eylemler:")
            
            if problem_users:
                print("  • Sorunlu kullanıcıları düzeltin veya kaldırın.")
                
            if problem_departments:
                print("  • Sorunlu departmanları düzeltin veya kaldırın.")
                
            if not email_settings:
                print("  • E-posta ayarlarını yapılandırın.")
                
            if setup_scripts:
                print("  • Kurulum scriptlerini tek bir scriptle birleştirin.")
                
            if problem_dofs:
                print("  • Sorunlu DÖF kayıtlarını düzeltin.")
        else:
            print("✅ Sistem sağlığı iyi durumda!")
            
        return total_issues == 0

if __name__ == "__main__":
    check_system_health()
