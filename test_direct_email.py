"""
Doğrudan e-posta gönderim testi.
DÖF uygulama kodunda kullanılan kodla aynı şekilde e-posta gönderir.
"""
import sys
from app import app
from utils import send_email
from flask import current_app
from datetime import datetime

# Test alıcısı
if len(sys.argv) > 1:
    TEST_RECIPIENT = sys.argv[1]
else:
    TEST_RECIPIENT = input("E-posta gönderilecek adres: ")

with app.app_context():
    print(f"DÖF uygulama koduyla aynı şekilde e-posta gönderiliyor: {TEST_RECIPIENT}")
    
    # E-posta içeriği - DÖF oluşturma bildirimindeki gibi
    subject = "DÖF Sistemi - Test Bildirimi (Uygulama Kodu)"
    
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Test DÖF Bildirimi</h2>
            </div>
            
            <p>Sayın Yetkili,</p>
            
            <p>Test Kullanıcı tarafından "Test DÖF" başlıklı yeni bir DÖF oluşturuldu.</p>
            <p><b>Açıklama:</b> Bu bir test DÖF açıklamasıdır. Türkçe karakterler: ğüşıöçĞÜŞİÖÇ</p>
            
            <p>
                <a href="#" class="button">DÖF Detaylarını Görüntüle</a>
            </p>
            
            <p>Tarih/Saat: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
            
            <div class="footer">
                <p>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"Test DÖF Bildirimi\n\nTest Kullanıcı tarafından \"Test DÖF\" başlıklı yeni bir DÖF oluşturuldu.\n\nAçıklama: Bu bir test DÖF açıklamasıdır. Türkçe karakterler: ğüşıöçĞÜŞİÖÇ\n\nTarih/Saat: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\nBu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız."
    
    # Doğrudan e-posta gönder (asenkron değil)
    try:
        result = send_email(subject, [TEST_RECIPIENT], html_content, text_content)
        print(f"E-posta gönderim sonucu: {result}")
        print("E-posta gönderildi! Lütfen gelen kutunuzu kontrol edin.")
    except Exception as e:
        print("E-posta gönderimi başarısız!")
        print(f"Hata: {str(e)}")
        import traceback
        traceback.print_exc()
