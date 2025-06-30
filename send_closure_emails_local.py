#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kapatılan DÖF'ler için Tek Seferlik E-posta Gönderimi (SUNUCU VERSİYONU)
Son 7 gün içinde kapatılan DÖF'ler için e-posta bildirimi gönderir
"""

import pymysql
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, html_content, text_content):
    """E-posta gönder"""
    try:
        # SMTP ayarları - config.py'deki ayarları kullan
        smtp_server = "mail.pluskitchen.com.tr"
        smtp_port = 587
        smtp_user = "dof@pluskitchen.com.tr"
        smtp_password = "Dof2024!"
        
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
        
        # SMTP ile gönder
        server = smtplib.SMTP(smtp_server, smtp_port)
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
        # LOCALHOST BAĞLANTISI - Sunucuda çalıştırmak için
        connection = pymysql.connect(
            host='127.0.0.1',  # localhost
            port=3306,         # standart MySQL port
            user='root',       # MySQL kullanıcı adı
            password='255223Rtv',       # MySQL şifresi
            database='defaultdb',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # Son 7 gün içinde kapatılan DÖF'leri bul
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        query = """
        SELECT d.id, d.title, d.created_by, d.department_id, d.closed_at,
               creator.full_name as creator_name, creator.email as creator_email,
               dept.name as dept_name
        FROM dofs d
        LEFT JOIN users creator ON d.created_by = creator.id
        LEFT JOIN departments dept ON d.department_id = dept.id
        WHERE d.status = 6 AND d.closed_at >= %s
        ORDER BY d.closed_at DESC
        """
        
        cursor.execute(query, (seven_days_ago,))
        dofs = cursor.fetchall()
        
        print(f"📋 Son 7 günde kapatılan DÖF sayısı: {len(dofs)}")
        
        return dofs
        
    except Exception as e:
        print(f"❌ Veritabanı hatası: {str(e)}")
        print("💡 MySQL bağlantı ayarlarını kontrol edin:")
        print("   - Host: 127.0.0.1")
        print("   - Port: 3306") 
        print("   - User: root (veya uygun kullanıcı)")
        print("   - Password: (sunucudaki MySQL şifresi)")
        return []
    finally:
        if 'connection' in locals():
            connection.close()

def get_dof_stakeholders(dof_id, department_id, creator_id):
    """DÖF ile ilgili kullanıcıları getir"""
    try:
        # LOCALHOST BAĞLANTISI
        connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='255223Rtv',
            database='defaultdb',
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        stakeholders = []
        
        # 1. DÖF oluşturan
        if creator_id:
            cursor.execute("SELECT id, full_name, email FROM users WHERE id = %s AND active = 1", (creator_id,))
            creator = cursor.fetchone()
            if creator and creator[2]:  # email varsa
                stakeholders.append({
                    'id': creator[0],
                    'name': creator[1],
                    'email': creator[2],
                    'role': 'Oluşturan'
                })
        
        # 2. Departman yöneticileri
        if department_id:
            cursor.execute("""
                SELECT id, full_name, email 
                FROM users 
                WHERE department_id = %s AND role = 2 AND active = 1
            """, (department_id,))
            
            dept_managers = cursor.fetchall()
            for manager in dept_managers:
                if manager[2]:  # email varsa
                    stakeholders.append({
                        'id': manager[0],
                        'name': manager[1],
                        'email': manager[2],
                        'role': 'Departman Yöneticisi'
                    })
        
        # 3. Kalite yöneticileri
        cursor.execute("""
            SELECT id, full_name, email 
            FROM users 
            WHERE role = 3 AND active = 1
        """)
        
        quality_managers = cursor.fetchall()
        for qm in quality_managers:
            if qm[2]:  # email varsa
                stakeholders.append({
                    'id': qm[0],
                    'name': qm[1],
                    'email': qm[2],
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
    finally:
        if 'connection' in locals():
            connection.close()

def send_closure_notifications():
    """Ana fonksiyon - kapatılan DÖF'ler için e-posta gönder"""
    print("🚀 Kapatılan DÖF'ler için e-posta gönderimi başlıyor... (SUNUCU VERSİYONU)")
    print("=" * 70)
    
    # Kapatılan DÖF'leri getir
    closed_dofs = get_closed_dofs()
    
    if not closed_dofs:
        print("📭 Gönderilecek DÖF bulunamadı.")
        print("💡 Muhtemel nedenler:")
        print("   - Son 7 günde kapatılan DÖF yok")
        print("   - Veritabanı bağlantı sorunu")
        print("   - MySQL ayarları hatalı")
        return
    
    # Önce kimlere gönderileceğini göster
    print("\n📋 E-POSTA GÖNDERİM ÖZETİ:")
    print("=" * 70)
    
    all_recipients = []
    
    for dof in closed_dofs:
        dof_id, title, created_by, department_id, closed_at, creator_name, creator_email, dept_name = dof
        
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
        dof_id, title, created_by, department_id, closed_at, creator_name, creator_email, dept_name = dof
        
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
            
            # Sunucu URL'si (localhost yerine gerçek sunucu adresini kullanın)
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
            if send_email(stakeholder['email'], subject, html_content, text_content):
                total_emails_sent += 1
                print(f"     ✅ {stakeholder['name']} ({stakeholder['role']})")
            else:
                print(f"     ❌ {stakeholder['name']} ({stakeholder['role']})")
    
    print("\n" + "=" * 70)
    print(f"🎉 Tamamlandı! Toplam {total_emails_sent} e-posta gönderildi.")
    print(f"📊 {len(closed_dofs)} DÖF için bildirim işlendi.")

if __name__ == "__main__":
    send_closure_notifications() 