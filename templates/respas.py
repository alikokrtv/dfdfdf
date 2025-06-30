from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.password = generate_password_hash('yeni_şifre')
        db.session.commit()
        print("Admin şifresi başarıyla değiştirildi")
    else:
        print("Admin kullanıcısı bulunamadı")