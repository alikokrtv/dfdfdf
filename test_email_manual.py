#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Manuel e-posta gönderim testi
"""

import sys
import os
from datetime import datetime

# Mevcut dizini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import DOF, User, Department, UserRole
    from notification_system import notify_department_assignment, send_email_to_user
    from utils import send_email
    import traceback

    def test_manual_email():
        print("📧 Manuel E-posta Gönderim Testi")
        print("=" * 50)
        
        with app.app_context():
            try:
                # 1. En son DÖF'ü al
                dof = DOF.query.order_by(DOF.updated_at.desc()).first()
                if not dof:
                    print("❌ Hiç DÖF bulunamadı")
                    return
                
                print(f"📋 Test DÖF: #{dof.id} - {dof.title}")
                print(f"🏢 Atanan Departman: {dof.department.name if dof.department else 'Yok'}")
                
                # 2. Departman yöneticilerini bul
                if dof.department_id:
                    dept_managers = User.query.filter_by(
                        department_id=dof.department_id,
                        role=UserRole.DEPARTMENT_MANAGER,
                        active=True
                    ).all()
                    
                    print(f"👥 Departman yöneticileri ({len(dept_managers)} kişi):")
                    for manager in dept_managers:
                        print(f"   - {manager.full_name} ({manager.email})")
                    
                    if dept_managers:
                        # İlk yöneticiye test e-postası gönder
                        test_manager = dept_managers[0]
                        print(f"\n📧 {test_manager.full_name} adresine test e-postası gönderiliyor...")
                        
                        # Basit e-posta testi
                        subject = f"TEST - DÖF #{dof.id} Departman Atama Bildirimi"
                        message = f"DÖF #{dof.id} - '{dof.title}' {dof.department.name} departmanına atandı. (TEST E-POSTASI)"
                        
                        html_content = f"""
                        <html>
                        <body>
                            <h2>DÖF Sistemi TEST Bildirim</h2>
                            <p>Sayın {test_manager.full_name},</p>
                            <p>{message}</p>
                            <p><strong>Bu bir test e-postasıdır.</strong></p>
                        </body>
                        </html>
                        """
                        
                        result = send_email(
                            subject=subject,
                            recipients=[test_manager.email],
                            body_html=html_content,
                            body_text=message
                        )
                        
                        if result:
                            print("✅ Test e-postası başarıyla gönderildi!")
                        else:
                            print("❌ Test e-postası gönderilemedi!")
                            
                    else:
                        print("❌ Departman yöneticisi bulunamadı")
                else:
                    print("❌ DÖF'ün atanan departmanı yok")
                
                # 3. Bildirim sistemi testi
                print(f"\n🔔 Bildirim sistemi testi...")
                
                # Admin kullanıcısını bul
                admin = User.query.filter_by(role=UserRole.ADMIN).first()
                if admin and dof.department_id:
                    notification_count = notify_department_assignment(
                        dof_id=dof.id,
                        department_id=dof.department_id,
                        actor_id=admin.id
                    )
                    print(f"✅ {notification_count} bildirim gönderildi")
                else:
                    print("❌ Admin kullanıcısı bulunamadı veya DÖF departman bilgisi eksik")
                    
            except Exception as e:
                print(f"❌ Hata: {str(e)}")
                print("\n🔍 Detaylı hata bilgisi:")
                print(traceback.format_exc())

    if __name__ == "__main__":
        test_manual_email()
        
except ImportError as e:
    print(f"❌ Import hatası: {str(e)}")
except Exception as e:
    print(f"❌ Genel hata: {str(e)}")
    import traceback
    print(traceback.format_exc()) 