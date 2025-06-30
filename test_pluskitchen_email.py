#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plus Kitchen e-posta testi
Bu script, pluskitchen.com.tr adresine doğrudan e-posta göndermeyi test eder
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import sys
import time
from datetime import datetime

# Log ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("EmailTest")

def test_pluskitchen_email():
    """
    Plus Kitchen e-posta adresi testi
    """
    # SMTP ayarları
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "alikokrtv@gmail.com"
    smtp_pass = "iczu jvha gavw rnlh"
    sender_email = "alikokrtv@gmail.com"
    
    # Alıcılar
    recipients = [
        "ali.kok@pluskitchen.com.tr",
        "portal@pluskitchen.com.tr",
        "alikokrtv@gmail.com",  # Kontrol için bir kopyayı kendimize gönderelim
    ]
    
    print(f"Plus Kitchen e-posta adreslerine test gönderiliyor:")
    print(f"Alıcılar: {', '.join(recipients)}")
    
    try:
        # SMTP bağlantısı
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Ayrıntılı loglama açık
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Giriş
        print(f"SMTP sunucusuna giriş yapılıyor: {smtp_user}")
        server.login(smtp_user, smtp_pass)
        print("Giriş başarılı!")
        
        # Her alıcı için ayrı e-posta gönderelim
        for recipient in recipients:
            try:
                # E-posta hazırlama
                subject = f"Plus Kitchen E-posta Testi - {datetime.now().strftime('%H:%M:%S')}"
                
                # ASCII ile uyumlu içerik oluştur
                text_content = f"""
                Plus Kitchen E-posta Testi
                
                Bu e-posta {recipient} adresine gonderilmistir.
                Eger bu e-postayi goruyorsaniz, e-posta sistemi dogru calisiyor demektir.
                
                Gonderim zamani: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
                
                Bu bir test e-postasidir. Lutfen yanitlamayiniz.
                """
                
                html_content = f"""
                <html>
                    <body>
                        <h2>Plus Kitchen E-posta Testi</h2>
                        <p>Bu e-posta <strong>{recipient}</strong> adresine gonderilmistir.</p>
                        <p>Eger bu e-postayi goruyorsaniz, e-posta sistemi dogru calisiyor demektir.</p>
                        <p>Gonderim zamani: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
                        <hr>
                        <p><small>Bu bir test e-postasidir. Lutfen yanitlamayiniz.</small></p>
                    </body>
                </html>
                """
                
                # Basit bir mesaj oluştur
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = sender_email
                msg["To"] = recipient
                
                # İçerikleri ekle
                msg.attach(MIMEText(text_content, "plain"))
                msg.attach(MIMEText(html_content, "html"))
                
                # Gönder
                print(f"\nE-posta gonderiliyor: {recipient}")
                server.sendmail(sender_email, recipient, msg.as_string())
                print(f"E-posta basariyla gonderildi: {recipient}")
                
                # E-postalar arasında kısa bir bekleme
                if recipient != recipients[-1]:
                    time.sleep(1)
                    
            except Exception as e:
                print(f"HATA ({recipient}): {str(e)}")
        
        # Bağlantıyı kapat
        server.quit()
        print("\nSMTP baglantisi kapatildi")
        
    except Exception as e:
        print(f"Genel HATA: {str(e)}")
        
if __name__ == "__main__":
    print("\n========== PLUS KITCHEN E-POSTA TESTI ==========\n")
    test_pluskitchen_email()
    print("\n================================================\n")
