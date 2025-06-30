#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Basit SMTP e-posta testi için bağımsız script
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

def test_smtp():
    """
    SMTP bağlantısını doğrudan test eder
    """
    # Sabit SMTP ayarları
    smtp_server = "mail.kurumsaleposta.com"
    smtp_port = 465
    smtp_user = "df@beraber.com.tr"
    smtp_pass = "=z5-5MNKn=ip5P4@"
    sender_email = "info@pluskitchen.com.tr"
    recipient_email = "alikokrtv@gmail.com"  # Test için aynı adres
    
    print(f"SMTP Sunucu: {smtp_server}:{smtp_port}")
    print(f"Kullanıcı: {smtp_user}")
    print(f"E-posta gönderiyor... ", end="", flush=True)
    
    try:
        # SMTP bağlantısı kur
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Debugging için
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Giriş yap
        server.login(smtp_user, smtp_pass)
        print("Giriş başarılı!")
        
        # E-posta mesajını oluştur
        message = MIMEMultipart("alternative")
        message["Subject"] = "DÖF Sistemi SMTP Testi"
        message["From"] = sender_email
        message["To"] = recipient_email
        
        # İçerik ekle
        html_content = """
        <html>
          <body>
            <h2>DÖF Sistemi SMTP Test E-postası</h2>
            <p>Bu bir test e-postasıdır.</p>
            <p>SMTP bağlantısı başarıyla kuruldu ve e-posta gönderildi.</p>
          </body>
        </html>
        """
        text_content = "DÖF Sistemi SMTP Test E-postası\n\nBu bir test e-postasıdır.\nSMTP bağlantısı başarıyla kuruldu ve e-posta gönderildi."
        
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))
        
        # E-postayı gönder
        server.sendmail(sender_email, recipient_email, message.as_string())
        print(f"E-posta başarıyla gönderildi: {sender_email} -> {recipient_email}")
        
        # Bağlantıyı kapat
        server.quit()
        print("SMTP bağlantısı kapatıldı")
        return True
        
    except Exception as e:
        print(f"HATA: {str(e)}")
        return False

if __name__ == "__main__":
    print("DÖF Sistemi SMTP Test Aracı")
    print("--------------------------")
    test_smtp()
