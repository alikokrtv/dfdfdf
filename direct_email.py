#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Doğrudan e-posta gönderimi için yardımcı araç
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import sys
import time
import os

# Loglama ayarı
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("email_logs.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("EmailSender")

def get_email_settings():
    """
    E-posta ayarlarını veritabanından çeker
    """
    try:
        from flask import current_app
        from app import app
        from models import EmailSettings
        
        with app.app_context():
            # Veritabanından e-posta ayarlarını al
            settings = EmailSettings.query.first()
            
            if settings:
                return {
                    'smtp_server': settings.smtp_host,
                    'smtp_port': settings.smtp_port,
                    'smtp_user': settings.smtp_user,
                    'smtp_pass': settings.smtp_pass,
                    'sender_email': settings.default_sender if settings.default_sender else settings.smtp_user,
                    'use_tls': settings.smtp_use_tls,
                    'use_ssl': settings.smtp_use_ssl
                }
    except Exception as e:
        logger.error(f"E-posta ayarları alınamadı: {str(e)}")
    
    # Varsayılan ayarlar (veritabanı kullanılamıyorsa)
    return {
        'smtp_server': "smtp.gmail.com",
        'smtp_port': 587,
        'smtp_user': "alikokrtv@gmail.com",
        'smtp_pass': "iczu jvha gavw rnlh",
        'sender_email': "alikokrtv@gmail.com",
        'use_tls': True,
        'use_ssl': False
    }

def send_direct_email(recipient, subject, html_content, text_content=None):
    """
    Doğrudan SMTP ile e-posta gönderir - Veritabanı ayarlarını kullanır
    """
    # E-posta ayarlarını veritabanından al
    settings = get_email_settings()
    
    # SMTP bilgilerini ayarla
    smtp_server = settings['smtp_server']
    smtp_port = settings['smtp_port']
    smtp_user = settings['smtp_user']
    smtp_pass = settings['smtp_pass']
    sender_email = settings['sender_email']
    use_tls = settings['use_tls']
    use_ssl = settings['use_ssl']
    
    logger.info(f"SMTP Ayarları: {smtp_server}:{smtp_port}, TLS: {use_tls}, SSL: {use_ssl}")
    
    # Test için yönlendirme (opsiyonel)
    force_recipient = None
    
    if force_recipient and recipient != force_recipient:
        logger.info(f"Orijinal alıcı: {recipient}, test için {force_recipient} adresine yönlendiriliyor")
        # Alıcı bilgisini içeriğe ekle
        html_content = f"<p><strong>Orijinal Alıcı:</strong> {recipient}</p>" + html_content
        if text_content:
            text_content = f"Orijinal Alıcı: {recipient}\n\n" + text_content
        # Alıcıyı değiştir
        recipient = force_recipient
    
    logger.info(f"E-posta gönderiliyor: {subject} -> {recipient}")
    
    try:
        # SMTP bağlantısı kur - SSL veya TLS için doğru sınıfı kullan
        logger.info(f"SMTP bağlantısı kuruluyor: {smtp_server}:{smtp_port}, SSL: {use_ssl}, TLS: {use_tls}")
        
        if use_ssl:
            # SSL bağlantısı (genellikle port 465)
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            server.ehlo()
        else:
            # Normal bağlantı (TLS için)
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()
        
        # Giriş yap
        logger.info(f"SMTP giriş yapılıyor: {smtp_user}")
        server.login(smtp_user, smtp_pass)
        
        # ASCII ile uyumluluk için Türkçe karakterleri değiştirelim
        # Not: UTF-8 kodlama çalışsa da, bazı SMTP sunucuları ASCII gerektiriyor
        def replace_turkish_chars(text):
            if not text:
                return text
            return text.replace("Ö", "O").replace("ö", "o").replace("Ü", "U").replace("ü", "u")\
                       .replace("İ", "I").replace("ı", "i").replace("Ğ", "G").replace("ğ", "g")\
                       .replace("Ç", "C").replace("ç", "c").replace("Ş", "S").replace("ş", "s")
        
        # ASCII-uyumlu konular ve içerikler
        subject_ascii = replace_turkish_chars(subject)
        html_content_ascii = replace_turkish_chars(html_content)
        text_content_ascii = replace_turkish_chars(text_content) if text_content else None
        
        # Mesajı oluştur
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject_ascii
        msg["From"] = sender_email
        msg["To"] = recipient
        msg["Reply-To"] = sender_email
        
        # Düz metin içeriği ekle
        if text_content_ascii:
            msg.attach(MIMEText(text_content_ascii, "plain"))
        
        # HTML içeriği ekle
        msg.attach(MIMEText(html_content_ascii, "html"))
        
        # Gönder
        logger.info(f"E-posta gönderiliyor: {sender_email} -> {recipient}")
        server.sendmail(sender_email, recipient, msg.as_string())
        
        # Bağlantıyı kapat
        server.quit()
        logger.info(f"E-posta başarıyla gönderildi: {recipient}")
        return True
    
    except Exception as e:
        logger.error(f"E-posta gönderimi başarısız: {str(e)}")
        return False

def batch_send_with_delay(recipients, subject, html_content, text_content=None, delay_seconds=2):
    """
    Birden fazla alıcıya belirli aralıklarla e-posta gönderir (throttling)
    """
    success_count = 0
    fail_count = 0
    
    logger.info(f"Toplu e-posta gönderimi başlıyor. Alıcı sayısı: {len(recipients)}")
    
    for i, recipient in enumerate(recipients):
        logger.info(f"[{i+1}/{len(recipients)}] E-posta gönderiliyor: {recipient}")
        
        if send_direct_email(recipient, subject, html_content, text_content):
            success_count += 1
        else:
            fail_count += 1
        
        # Son alıcı değilse bekle (throttling)
        if i < len(recipients) - 1:
            logger.info(f"{delay_seconds} saniye bekleniyor...")
            time.sleep(delay_seconds)
    
    logger.info(f"Toplu gönderim tamamlandı. Başarılı: {success_count}, Başarısız: {fail_count}")
    return success_count, fail_count

if __name__ == "__main__":
    # Test
    subject = "DÖF Sistemi Doğrudan E-posta Testi"
    html_content = """
    <html>
        <body>
            <h1>DÖF Sistemi</h1>
            <p>Bu bir test e-postasıdır.</p>
            <p>E-posta doğrudan SMTP üzerinden gönderilmiştir.</p>
        </body>
    </html>
    """
    text_content = "DÖF Sistemi\n\nBu bir test e-postasıdır.\nE-posta doğrudan SMTP üzerinden gönderilmiştir."
    
    if len(sys.argv) > 1:
        recipient = sys.argv[1]
    else:
        recipient = "alikokrtv@gmail.com"  # Varsayılan test alıcısı
    
    print(f"Test e-postası gönderiliyor: {recipient}")
    if send_direct_email(recipient, subject, html_content, text_content):
        print("E-posta başarıyla gönderildi!")
    else:
        print("E-posta gönderimi başarısız oldu.")
