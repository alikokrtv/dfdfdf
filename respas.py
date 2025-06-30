import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash

sys.path.append(os.getcwd())
from models import User

# Railway veritabanı bağlantısı
DATABASE_URL = 'mysql+pymysql://root:TYaiJjHWFzFpLjizmCzEUQtnSKxBttJe@yamanote.proxy.rlwy.net:27282/railway'

# Engine ve Session oluştur
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Admin kullanıcısını bul
admin = session.query(User).filter_by(username='admin').first()

if admin:
    # Şifreyi değiştir
    admin.password = generate_password_hash('123456')
    admin.updated_at = datetime.now()
    session.commit()
    print("Admin şifresi başarıyla 123456 olarak değiştirildi")
else:
    print("Admin kullanıcısı bulunamadı")

session.close()
