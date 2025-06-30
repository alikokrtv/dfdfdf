#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kapatılan DÖF'ler için Tek Seferlik E-posta Gönderimi (FLASK VERSİYONU)
Sistemin mevcut config ve veritabanı bağlantısını kullanır
"""

import sys
import os
from datetime import datetime, timedelta

# Mevcut dizini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Flask app'ını import et
from app import app, db
from models import DOF, User, Department, UserRole

def send_email_direct(to_email, subject, html_content, text_content):
    """Doğrudan SMTP ile e-posta gönder"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # SMTP ayarları - Flask app config'den al
        smtp_server = app.config.get('MAIL_SERVER', 'mail.kurumsaleposta.com')
        smtp_port = app.config.get('MAIL_PORT', 465)
        smtp_user = app.config.get('MAIL_USERNAME', 'df@beraber.com.tr')
        smtp_password = app.config.get('MAIL_PASSWORD', '=z5-5MNKn=ip5P4@')
        use_ssl = app.config.get('MAIL_USE_SSL', True)
        use_tls = app.config.get('MAIL_USE_TLS', False)
        
        # E-posta oluştur
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # HTML ve text parçalarını ekle
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # SMTP ile gönder - SSL/TLS ayarlarına göre
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
        
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ E-posta gönderildi: {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ E-posta gönderim hatası ({to_email}): {str(e)}")
        return False

def get_closed_dofs():
    """Son 7 gün içinde kapatılan DÖF'leri getir"""
    try:
        # Son 7 gün içinde kapatılan DÖF'leri bul
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        # Flask-SQLAlchemy kullanarak sorgula - Model özelliklerini kullan
        closed_dofs = DOF.query.filter(
            DOF.status == 6,  # CLOSED
            DOF.closed_at >= seven_days_ago
        ).order_by(
            DOF.closed_at.desc()
        ).all()
        
        print(f"📋 Son 7 günde kapatılan DÖF sayısı: {len(closed_dofs)}")
        
        return closed_dofs
        
    except Exception as e:
        print(f"❌ Veritabanı hatası: {str(e)}")
        return []

def get_dof_stakeholders(dof_id, department_id, creator_id):
    """DÖF ile ilgili kullanıcıları getir"""
    try:
        stakeholders = []
        
        # 1. DÖF oluşturan
        if creator_id:
            creator = User.query.filter_by(id=creator_id, active=True).first()
            if creator and creator.email:
                stakeholders.append({
                    'id': creator.id,
                    'name': creator.full_name,
                    'email': creator.email,
                    'role': 'Oluşturan'
                })
        
        # 2. Departman yöneticileri
        if department_id:
            dept_managers = User.query.filter_by(
                department_id=department_id,
                role=UserRole.DEPARTMENT_MANAGER,
                active=True
            ).all()
            
            for manager in dept_managers:
                if manager.email:
                    stakeholders.append({
                        'id': manager.id,
                        'name': manager.full_name,
                        'email': manager.email,
                        'role': 'Departman Yöneticisi'
                    })
        
        # 3. Kalite yöneticileri
        quality_managers = User.query.filter_by(
            role=UserRole.QUALITY_MANAGER,
            active=True
        ).all()
        
        for qm in quality_managers:
            if qm.email:
                stakeholders.append({
                    'id': qm.id,
                    'name': qm.full_name,
                    'email': qm.email,
                    'role': 'Kalite Yöneticisi'
                })
        
        # Tekrarları kaldır (aynı kişi birden fazla rolde olabilir)
        unique_stakeholders = []
        seen_emails = set()
        
        for stakeholder in stakeholders:
            if stakeholder['email'] not in seen_emails:
                unique_stakeholders.append(stakeholder)
                seen_emails.add(stakeholder['email'])
        
        return unique_stakeholders
        
    except Exception as e:
        print(f"❌ Stakeholder getirme hatası: {str(e)}")
        return []

def send_closure_notifications():
    """Ana fonksiyon - kapatılan DÖF'ler için e-posta gönder"""
    print("🚀 Kapatılan DÖF'ler için e-posta gönderimi başlıyor... (FLASK VERSİYONU)")
    print("=" * 70)
    
    # Flask app context'i oluştur
    with app.app_context():
        # Veritabanı bağlantısını test et
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("✅ Veritabanı bağlantısı başarılı")
        except Exception as e:
            print(f"❌ Veritabanı bağlantı hatası: {str(e)}")
            return
        
        # Kapatılan DÖF'leri getir
        closed_dofs = get_closed_dofs()
        
        if not closed_dofs:
            print("📭 Gönderilecek DÖF bulunamadı.")
            print("💡 Muhtemel nedenler:")
            print("   - Son 7 günde kapatılan DÖF yok")
            print("   - DÖF'ler farklı durumda (status != 6)")
            return
        
        # Önce kimlere gönderileceğini göster
        print("\n📋 E-POSTA GÖNDERİM ÖZETİ:")
        print("=" * 70)
        
        all_recipients = []
        
        for dof in closed_dofs:
            dof_id = dof.id
            title = dof.title
            created_by = dof.created_by
            department_id = dof.department_id
            closed_at = dof.closed_at
            
            # Creator ve Department bilgilerini ayrı olarak al
            creator_name = "Bilinmiyor"
            if dof.creator:
                creator_name = dof.creator.full_name
            
            dept_name = "Bilinmiyor"
            if dof.department:
                dept_name = dof.department.name
            
            print(f"\n📧 DÖF #{dof_id} - {title}")
            print(f"   📅 Kapatılma: {closed_at}")
            print(f"   🏢 Departman: {dept_name}")
            
            # İlgili kullanıcıları getir
            stakeholders = get_dof_stakeholders(dof_id, department_id, created_by)
            
            print(f"   👥 Bildirim alacak kişiler ({len(stakeholders)} kişi):")
            for stakeholder in stakeholders:
                print(f"      - {stakeholder['name']} ({stakeholder['role']}) - {stakeholder['email']}")
                all_recipients.append(stakeholder['email'])
        
        # Toplam özet
        unique_recipients = list(set(all_recipients))
        print(f"\n📊 TOPLAM ÖZET:")
        print(f"   🔢 DÖF Sayısı: {len(closed_dofs)}")
        print(f"   📧 Toplam E-posta: {len(all_recipients)}")
        print(f"   👤 Benzersiz Alıcı: {len(unique_recipients)}")
        
        # Onay iste
        print(f"\n❓ Bu {len(all_recipients)} e-postayı göndermek istiyor musunuz?")
        confirmation = input("   Devam etmek için 'EVET' yazın (diğer herhangi bir tuş = iptal): ").strip().upper()
        
        if confirmation != 'EVET':
            print("❌ İşlem iptal edildi.")
            return
        
        print("\n🚀 E-posta gönderimi başlıyor...")
        print("=" * 70)
        
        total_emails_sent = 0
        
        for dof in closed_dofs:
            dof_id = dof.id
            title = dof.title
            created_by = dof.created_by
            department_id = dof.department_id
            closed_at = dof.closed_at
            
            # Department bilgisini al
            dept_name = "Bilinmiyor"
            if dof.department:
                dept_name = dof.department.name
            
            print(f"\n📧 DÖF #{dof_id} - {title}")
            print(f"   Kapatılma: {closed_at}")
            print(f"   Departman: {dept_name}")
            
            # İlgili kullanıcıları getir
            stakeholders = get_dof_stakeholders(dof_id, department_id, created_by)
            
            print(f"   📮 {len(stakeholders)} kişiye e-posta gönderiliyor...")
            
            # Her stakeholder'a e-posta gönder
            for stakeholder in stakeholders:
                # E-posta içeriği - Sistem şablonuyla uyumlu
                subject = f"DÖF #{dof_id} - Kapatıldı"
                
                # Sunucu URL'si
                server_url = "http://localhost:5000"  # Gerekirse değiştirin
                
                html_content = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                        .header {{ background-color: #f8f8f8; padding: 10px; border-bottom: 1px solid #ddd; }}
                        .footer {{ background-color: #f8f8f8; padding: 10px; border-top: 1px solid #ddd; margin-top: 20px; font-size: 12px; color: #777; }}
                        .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; }}
                        .highlight {{ color: #007bff; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>DÖF Sistemi Bildirim</h2>
                        </div>
                        
                        <p>Sayın {stakeholder['name']},</p>
                        
                        <p><span class="highlight">DÖF #{dof_id}</span> - "{title}" kalite departmanı tarafından <strong>KAPATILDI</strong>.</p>
                        
                        <p>DÖF detaylarını görüntülemek için aşağıdaki butona tıklayabilirsiniz:</p>
                        
                        <p>
                            <a href="{server_url}/dof/{dof_id}" class="button">DÖF Detaylarını Görüntüle</a>
                        </p>
                        
                        <p>Tarih/Saat: {closed_at.strftime('%d.%m.%Y %H:%M') if closed_at else datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                        
                        <div class="footer">
                            <p>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                text_content = f"""
                DÖF Sistemi Bildirim
                
                Sayın {stakeholder['name']},
                
                DÖF #{dof_id} - "{title}" kalite departmanı tarafından KAPATILDI.
                
                DÖF detaylarını görüntülemek için: {server_url}/dof/{dof_id}
                
                Tarih/Saat: {closed_at.strftime('%d.%m.%Y %H:%M') if closed_at else datetime.now().strftime('%d.%m.%Y %H:%M')}
                
                Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.
                """
                
                # E-posta gönder
                if send_email_direct(stakeholder['email'], subject, html_content, text_content):
                    total_emails_sent += 1
                    print(f"     ✅ {stakeholder['name']} ({stakeholder['role']})")
                else:
                    print(f"     ❌ {stakeholder['name']} ({stakeholder['role']})")
        
        print("\n" + "=" * 70)
        print(f"🎉 Tamamlandı! Toplam {total_emails_sent} e-posta gönderildi.")
        print(f"📊 {len(closed_dofs)} DÖF için bildirim işlendi.")

if __name__ == "__main__":
    send_closure_notifications() 