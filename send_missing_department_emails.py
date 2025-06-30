#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Eksik Departman Atama E-postaları Gönderme Scripti
DÖF #28 ve #32 için İstinye departmanına e-posta gönderir
"""

import sys
import os
from datetime import datetime

# Mevcut dizini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import DOF, User, Department, UserRole
    from notification_system import send_email_to_user
    from utils import send_email
    import traceback

    def send_missing_emails():
        print("📧 Eksik Departman Atama E-postaları Gönderimi")
        print("=" * 60)
        
        with app.app_context():
            try:
                # Hedef DÖF'ler
                target_dof_ids = [28, 32]
                
                # İstinye departmanını bul
                istinye_dept = Department.query.filter(Department.name.like('%İstinye%')).first()
                if not istinye_dept:
                    print("❌ İstinye departmanı bulunamadı!")
                    return
                
                print(f"🏢 Hedef Departman: {istinye_dept.name} (ID: {istinye_dept.id})")
                
                # İstinye departman yöneticilerini bul
                istinye_managers = User.query.filter_by(
                    department_id=istinye_dept.id,
                    role=UserRole.DEPARTMENT_MANAGER,
                    active=True
                ).all()
                
                if not istinye_managers:
                    print("❌ İstinye departman yöneticisi bulunamadı!")
                    return
                
                print(f"👥 İstinye Departman Yöneticileri ({len(istinye_managers)} kişi):")
                for manager in istinye_managers:
                    print(f"   - {manager.full_name} ({manager.email})")
                
                print("\n" + "=" * 60)
                
                # Her DÖF için işlem yap
                total_emails_sent = 0
                
                for dof_id in target_dof_ids:
                    dof = DOF.query.get(dof_id)
                    if not dof:
                        print(f"❌ DÖF #{dof_id} bulunamadı!")
                        continue
                    
                    print(f"\n📋 DÖF #{dof.id}: {dof.title}")
                    print(f"   🏢 Mevcut Departman: {dof.department.name if dof.department else 'Yok'}")
                    print(f"   📅 Oluşturulma: {dof.created_at.strftime('%d.%m.%Y %H:%M')}")
                    
                    # DÖF'ün İstinye'ye atanıp atanmadığını kontrol et
                    if dof.department_id != istinye_dept.id:
                        print(f"   ⚠️  DÖF İstinye departmanına atanmamış! (Mevcut: {dof.department_id}, Hedef: {istinye_dept.id})")
                        continue
                    
                    # Her yöneticiye e-posta gönder
                    for manager in istinye_managers:
                        try:
                            # E-posta içeriği hazırla
                            subject = f"DÖF Sistemi Bildirim: {dof.title}"
                            
                            # Sunucu URL'si
                            base_url = app.config.get('BASE_URL', 'http://localhost:5000')
                            dof_url = f"{base_url}/dof/{dof.id}"
                            
                            # Departman atama mesajı
                            message = f"DÖF #{dof.id} - '{dof.title}' {istinye_dept.name} departmanına atandı."
                            
                            # HTML içeriği
                            html_content = f"""
                            <html>
                            <head>
                                <meta charset="UTF-8">
                                <style>
                                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                                    .header {{ background-color: #f8f8f8; padding: 10px; border-bottom: 1px solid #ddd; }}
                                    .footer {{ background-color: #f8f8f8; padding: 10px; border-top: 1px solid #ddd; margin-top: 20px; font-size: 12px; color: #777; }}
                                    .button {{ background-color: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; }}
                                    .highlight {{ color: #007bff; font-weight: bold; }}
                                    .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 4px; margin: 10px 0; }}
                                </style>
                            </head>
                            <body>
                                <div class="container">
                                    <div class="header">
                                        <h2>🏢 DÖF Sistemi - Departman Atama Bildirimi</h2>
                                    </div>
                                    
                                    <p>Sayın {manager.full_name},</p>
                                    
                                    <p><span class="highlight">DÖF #{dof.id}</span> - "{dof.title}" departmanınıza atanmıştır.</p>
                                    
                                    <div class="warning">
                                        <strong>📋 DÖF Detayları:</strong><br>
                                        • <strong>DÖF No:</strong> #{dof.id}<br>
                                        • <strong>Konu:</strong> {dof.title}<br>
                                        • <strong>Atanan Departman:</strong> {istinye_dept.name}<br>
                                        • <strong>Tarih:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M')}
                                    </div>
                                    
                                    <p>DÖF'ü incelemek ve gerekli aksiyonları almak için aşağıdaki butona tıklayabilirsiniz:</p>
                                    
                                    <p style="text-align: center;">
                                        <a href="{dof_url}" class="button">📋 DÖF Detaylarını Görüntüle</a>
                                    </p>
                                    
                                    <p><strong>Önemli:</strong> Bu DÖF için gerekli incelemeleri yapmanız ve aksiyonları almanız beklenmektedir.</p>
                                    
                                    <div class="footer">
                                        <p>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.</p>
                                        <p>DÖF Yönetim Sistemi - {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                                    </div>
                                </div>
                            </body>
                            </html>
                            """
                            
                            # Düz metin içeriği
                            text_content = f"""
                            DÖF Sistemi - Departman Atama Bildirimi
                            
                            Sayın {manager.full_name},
                            
                            DÖF #{dof.id} - "{dof.title}" departmanınıza atanmıştır.
                            
                            DÖF Detayları:
                            • DÖF No: #{dof.id}
                            • Konu: {dof.title}
                            • Atanan Departman: {istinye_dept.name}
                            • Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}
                            
                            DÖF detaylarını görüntülemek için: {dof_url}
                            
                            Bu DÖF için gerekli incelemeleri yapmanız ve aksiyonları almanız beklenmektedir.
                            
                            Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.
                            DÖF Yönetim Sistemi - {datetime.now().strftime('%d.%m.%Y %H:%M')}
                            """
                            
                            # E-posta gönder (sistem uyumlu utils.send_email kullanarak)
                            success = send_email(
                                subject=subject,
                                recipients=[manager.email],
                                body_html=html_content,
                                body_text=text_content
                            )
                            
                            if success:
                                total_emails_sent += 1
                                print(f"   ✅ E-posta gönderildi: {manager.full_name} ({manager.email})")
                            else:
                                print(f"   ❌ E-posta gönderilemedi: {manager.full_name} ({manager.email})")
                                
                        except Exception as e:
                            print(f"   ❌ E-posta gönderim hatası ({manager.email}): {str(e)}")
                            import traceback
                            print(f"      Hata detayı: {traceback.format_exc()}")
                
                print("\n" + "=" * 60)
                print(f"🎉 İşlem Tamamlandı!")
                print(f"📊 Toplam {total_emails_sent} e-posta gönderildi.")
                print(f"🔍 E-posta durumunu admin panelindeki 'E-posta Takip' sayfasından kontrol edebilirsiniz.")
                
                # DÖF oluşturanlarına da bilgilendirme e-postası gönder
                print(f"\n📤 DÖF Oluşturanlarına Bilgilendirme E-postaları...")
                
                for dof_id in target_dof_ids:
                    dof = DOF.query.get(dof_id)
                    if not dof or not dof.creator:
                        continue
                        
                    creator = dof.creator
                    if not creator.email:
                        continue
                    
                    try:
                        # Oluşturana bilgilendirme mesajı
                        subject = f"DÖF Sistemi Bildirim: {dof.title}"
                        message = f"DÖF #{dof.id} {istinye_dept.name} departmanına atandı."
                        
                        # HTML içeriği (kısa versiyon)
                        html_content = f"""
                        <html>
                        <head><meta charset="UTF-8"></head>
                        <body style="font-family: Arial, sans-serif;">
                            <h3>DÖF Sistemi Bildirim</h3>
                            <p>Sayın {creator.full_name},</p>
                            <p>Oluşturduğunuz <strong>DÖF #{dof.id}</strong> - "{dof.title}" {istinye_dept.name} departmanına atandı.</p>
                            <p><a href="{base_url}/dof/{dof.id}">DÖF Detaylarını Görüntüle</a></p>
                            <small>Bu e-posta otomatik olarak gönderilmiştir.</small>
                        </body>
                        </html>
                        """
                        
                        text_content = f"DÖF #{dof.id} {istinye_dept.name} departmanına atandı. Detaylar: {base_url}/dof/{dof.id}"
                        
                        success = send_email(
                            subject=subject,
                            recipients=[creator.email],
                            body_html=html_content,
                            body_text=text_content
                        )
                        
                        if success:
                            total_emails_sent += 1
                            print(f"   ✅ Oluşturana bildirim gönderildi: {creator.full_name} ({creator.email})")
                        else:
                            print(f"   ❌ Oluşturana bildirim gönderilemedi: {creator.full_name} ({creator.email})")
                            
                    except Exception as e:
                        print(f"   ❌ Oluşturana bildirim hatası ({creator.email}): {str(e)}")
                
                print(f"\n🎯 TOPLAM E-POSTA: {total_emails_sent}")
                
            except Exception as e:
                print(f"❌ Genel hata: {str(e)}")
                import traceback
                print(traceback.format_exc())

    if __name__ == "__main__":
        print("🚀 DÖF #28 ve #32 için İstinye departmanına eksik e-posta gönderimi başlıyor...")
        print("⚠️  Bu işlem sadece belirtilen DÖF'ler için çalışır.")
        
        # Onay iste
        confirmation = input("\n❓ Devam etmek istiyor musunuz? (EVET yazın): ").strip().upper()
        
        if confirmation == 'EVET':
            send_missing_emails()
        else:
            print("❌ İşlem iptal edildi.")
        
except Exception as e:
    print(f"❌ Import hatası: {str(e)}")
    import traceback
    print(traceback.format_exc()) 