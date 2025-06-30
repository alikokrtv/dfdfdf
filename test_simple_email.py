#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
En basit SMTP e-posta testi - Hiçbir Flask bağımlılığı olmadan
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import time

def simple_email_test():
    # SMTP ayarları
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "alikokrtv@gmail.com"
    smtp_pass = "iczu jvha gavw rnlh"
    sender_email = "alikokrtv@gmail.com"
    recipient_email = "alikokrtv@gmail.com"  # Kendi adresinize gönderme
    
    print(f"SMTP sunucusuna bağlanılıyor: {smtp_server}:{smtp_port}")
    
    try:
        # SMTP oturumu aç
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Debug modunu açalım
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Giriş yap
        print("SMTP sunucusuna giriş yapılıyor...")
        server.login(smtp_user, smtp_pass)
        print("Giriş başarılı!")
        
        # Mesaj oluştur
        print("E-posta mesajı hazırlanıyor...")
        subject = "DÖF Sistemi Test E-postası " + time.strftime("%H:%M:%S")
        body = f"""
        <html>
        <body>
            <h2>Bu bir test e-postasıdır</h2>
            <p>E-posta gönderim saati: {time.strftime("%d.%m.%Y %H:%M:%S")}</p>
            <p>Bu e-posta basitçe SMTP ile gönderilmiştir.</p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email
        
        msg.attach(MIMEText(body, "html"))
        
        # Gönder
        print(f"E-posta gönderiliyor: {recipient_email}")
        server.sendmail(sender_email, recipient_email, msg.as_string())
        print("E-posta başarıyla gönderildi!")
        
        # Kapat
        server.quit()
        print("SMTP bağlantısı kapatıldı")
        return True
        
    except Exception as e:
        print(f"HATA: {str(e)}")
        return False

if __name__ == "__main__":
    print("Basit SMTP E-posta Testi")
    print("------------------------")
    simple_email_test()
    print("------------------------")
    print("Test tamamlandı!")
