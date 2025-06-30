from flask import Flask
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# Mail ayarlarını al
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Kendi mail adresinizi girin
app.config['MAIL_PASSWORD'] = 'your-app-password'  # Mail şifrenizi girin
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'  # Gönderen mail adresi

mail = Mail(app)

def send_test_email():
    with app.app_context():
        try:
            subject = "DÖF Sistemi - Test E-postası"
            recipients = ["test-recipient@example.com"]  # Alıcı mail adresini girin
            
            body_html = """
            <html>
                <body>
                    <h2>DÖF Sistemi - Test E-postası</h2>
                    <p>Bu bir test e-postasıdır.</p>
                    <p>E-posta ayarlarınız başarıyla yapılandırılmıştır.</p>
                </body>
            </html>
            """
            
            msg = Message(subject, recipients=recipients)
            msg.html = body_html
            mail.send(msg)
            print("Test e-postası başarıyla gönderildi!")
            return True
        except Exception as e:
            print(f"E-posta gönderme hatası: {str(e)}")
            return False

if __name__ == "__main__":
    send_test_email()
