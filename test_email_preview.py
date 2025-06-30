#!/usr/bin/env python3
"""
Gönderilecek e-postanın önizlemesini görmek için test scripti
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, UserRole, Department
from daily_email_scheduler import get_user_managed_departments, get_dof_statistics, generate_report_html
from datetime import datetime

def select_department():
    """Departman seçimi yap"""
    from models import Department
    
    # Aktif departmanları getir
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    
    if not departments:
        print("❌ Aktif departman bulunamadı")
        return None
    
    print("\n🏢 DEPARTMAN SEÇİMİ")
    print("=" * 50)
    print("Hangi departman için e-posta önizlemesi görmek istiyorsunuz?\n")
    
    # Departmanları listele
    for i, dept in enumerate(departments, 1):
        print(f"{i:2d}. {dept.name} (ID: {dept.id})")
    
    print(f"\n0. Çıkış")
    
    try:
        choice = input(f"\nSeçiminizi yapın (1-{len(departments)}): ").strip()
        
        if choice == "0":
            print("👋 Çıkılıyor...")
            return None
        
        choice_num = int(choice)
        if 1 <= choice_num <= len(departments):
            selected_dept = departments[choice_num - 1]
            print(f"\n✅ Seçilen departman: {selected_dept.name} (ID: {selected_dept.id})")
            return selected_dept
        else:
            print("❌ Geçersiz seçim!")
            return None
            
    except ValueError:
        print("❌ Lütfen geçerli bir sayı girin!")
        return None
    except KeyboardInterrupt:
        print("\n👋 İşlem iptal edildi.")
        return None

def test_email_preview():
    """E-posta önizlemesi oluştur"""
    
    with app.app_context():
        print("=" * 70)
        print("📧 E-POSTA ÖNİZLEME TESTİ")
        print("=" * 70)
        
        # Departman seçimi
        selected_dept = select_department()
        if not selected_dept:
            return
        
        # Test kullanıcısı bilgileri
        user_email = "ali.kok@pluskitchen.com.tr"
        
        print(f"\n{'='*50}")
        print(f"👤 Ali KOK için e-posta önizlemesi")
        print(f"📧 {user_email}")
        print(f"🏢 Departman: {selected_dept.name} (ID: {selected_dept.id})")
        print('='*50)
        
        # Kullanıcıyı bul (eğer yoksa mock user oluştur)
        user = User.query.filter_by(email=user_email).first()
        
        if not user:
            print(f"⚠️ Kullanıcı bulunamadı, test kullanıcısı oluşturuluyor...")
            # Mock user oluştur
            class MockUser:
                def __init__(self):
                    self.full_name = "Ali KOK"
                    self.role_name = "Test Kullanıcısı"
                    self.email = user_email
                    self.username = "ali.kok"
            user = MockUser()
        else:
            print(f"✅ Kullanıcı bulundu: {user.full_name}")
            print(f"🎭 Rol: {user.role_name}")
        
                # Seçilen departman için istatistikleri getir
        departments = [selected_dept]
        department_ids = [selected_dept.id]
        statistics = get_dof_statistics(department_ids)
        
        if not statistics:
            print("❌ İstatistik alınamadı")
            return
            
        print(f"\n📊 İstatistikler:")
        print(f"   📈 Açık DÖF: {statistics.get('total_open', 0)}")
        print(f"   ✅ Bu hafta kapatılan: {statistics.get('total_closed_week', 0)}")
        print(f"   ⏰ Yaklaşan termin: {statistics.get('total_upcoming', 0)}")
        print(f"   ⚠️ Gecikmiş: {statistics.get('total_overdue', 0)}")
        
        # Toplam DÖF kontrolü
        total_dofs = statistics.get('total_open', 0) + statistics.get('total_closed_week', 0)
        
        if total_dofs == 0:
            print("❌ Bu departman için DÖF bulunamadı, yine de e-posta önizlemesi oluşturuluyor...")
        else:
            print(f"✅ E-posta gönderilecek (Toplam DÖF: {total_dofs})")
        
        # HTML e-postası oluştur
        html_content = generate_report_html(user, departments, statistics)
        
        if html_content:
            # HTML dosyasını kaydet
            username = getattr(user, 'username', 'ali.kok')
            filename = f"email_preview_{username}_{selected_dept.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"📄 HTML önizleme kaydedildi: {filename}")
            print(f"🌐 Dosyayı tarayıcıda açarak e-postanın görünümünü kontrol edebilirsiniz")
            
            # E-posta konusunu göster
            subject = f"Günlük DÖF Raporu - {datetime.now().strftime('%d.%m.%Y')}"
            print(f"📧 E-posta konusu: {subject}")
            
            # İlk 500 karakteri göster
            print(f"\n📝 E-posta içeriği (ilk 500 karakter):")
            print("-" * 50)
            # HTML etiketlerini temizle
            import re
            clean_text = re.sub('<[^<]+?>', '', html_content)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            print(clean_text[:500] + "..." if len(clean_text) > 500 else clean_text)
            print("-" * 50)
        else:
            print("❌ HTML e-posta oluşturulamadı")

if __name__ == "__main__":
    print("📧 Ali KOK için e-posta önizleme testi")
    test_email_preview() 