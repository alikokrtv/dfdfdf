#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Kalite yöneticilerine doğrudan e-posta gönderme aracı
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import sys
import time
from datetime import datetime

def send_quality_email():
    # SMTP ayarları (sabit)
    smtp_server = "mail.kurumsaleposta.com"
    smtp_port = 465
    smtp_user = "df@beraber.com.tr"
    smtp_pass = "=z5-5MNKn=ip5P4@"
    sender_email = "info@pluskitchen.com.tr"
    
    # Alıcılar (kalite yöneticileri)
    recipients = [
        "ali.kok@pluskitchen.com.tr",
        "quality@example.com",  # Bu adrese gönderimi test et
        "alikokrtv@gmail.com"   # Kendimize bir kopya
    ]
    
    print(f"Kalite yöneticilerine e-posta gönderiliyor:")
    print(f"Alıcılar: {', '.join(recipients)}")
    
    try:
        # SMTP bağlantısı kur
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Debug loglaması
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Giriş yap
        print(f"SMTP sunucusuna giriş yapılıyor: {smtp_user}")
        server.login(smtp_user, smtp_pass)
        print("Giriş başarılı!")
        
        # Her alıcı için ayrı e-posta gönder
        for recipient in recipients:
            try:
                # Konu ve içerik
                timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
                subject = f"DÖF Sistemi Kalite Bildirim Testi - {timestamp}"
                
                html_content = f"""
                <html>
                    <body>
                        <h2>Kalite Yöneticisi Bildirim Testi</h2>
                        <p>Bu e-posta DÖF sisteminden <strong>{recipient}</strong> adresine doğrudan gönderilmiştir.</p>
                        <p>Eğer bu e-postayı görüyorsanız, bildirim sistemi doğru çalışıyor demektir.</p>
                        <p>Gönderim zamanı: {timestamp}</p>
                        <hr>
                        <p><small>Bu bir test e-postasıdır. Lütfen yanıtlamayınız.</small></p>
                    </body>
                </html>
                """
                
                # Mesajı oluştur
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = sender_email
                msg["To"] = recipient
                msg["Reply-To"] = sender_email
                
                msg.attach(MIMEText(html_content, "html"))
                
                # Gönder
                print(f"E-posta gönderiliyor: {recipient}")
                server.sendmail(sender_email, recipient, msg.as_string())
                print(f"E-posta başarıyla gönderildi: {recipient}")
                
                # E-postalar arasında kısa bir bekleme
                if recipient != recipients[-1]:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"HATA ({recipient}): {str(e)}")
        
        # Bağlantıyı kapat
        server.quit()
        print("SMTP bağlantısı kapatıldı")
        return True
        
    except Exception as e:
        print(f"Genel HATA: {str(e)}")
        return False

if __name__ == "__main__":
    print("Kalite Yöneticilerine Doğrudan E-posta Gönderme")
    print("----------------------------------------------")
    send_quality_email()
    print("----------------------------------------------")
    print("İşlem tamamlandı!")
