"""
E-posta gönderim işlevini test etmek için basit bir script.
Bu script, utils.py içindeki send_email fonksiyonunu kullanarak test e-postası gönderir.
"""
import os
import sys
from app import app
from utils import send_email

# Test için e-posta alıcısı
if len(sys.argv) > 1:
    TEST_RECIPIENT = sys.argv[1]  # Komut satırından alıcı e-posta adresini al
else:
    TEST_RECIPIENT = input("Test e-postası gönderilecek e-posta adresini girin: ")

def test_email_sending():
    """Test e-postası gönder"""
    with app.app_context():
        print("Test e-postası gönderiliyor...")
        
        subject = "DÖF Sistemi - Test E-postası"
        # Tarih/saat bilgisi için datetime modülünü import et
        import datetime
        current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        body_html = """
        <html>
            <body>
                <h1>DÖF E-posta Testi</h1>
                <p>Bu bir test e-postasıdır. Eğer bu e-postayı alıyorsanız, DÖF sisteminden e-posta gönderimi çalışıyor demektir.</p>
                <p>Tarih/Saat: {}</p>
            </body>
        </html>
        """.format(current_time)
        
        try:
            result = send_email(subject, [TEST_RECIPIENT], body_html)
            print("E-posta gönderim sonucu:", result)
            print("E-posta gönderildi! Lütfen gelen kutunuzu kontrol edin.")
        except Exception as e:
            print("E-posta gönderimi başarısız!")
            print("Hata:", str(e))
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_email_sending()
