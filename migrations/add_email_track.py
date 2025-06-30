"""
E-posta takip tablosunu oluşturmak için migrasyon betiği.
Bu betik email_tracks tablosunu veritabanına ekler.
"""

from app import app, db
from flask_migrate import Migrate, upgrade
import inspect
from models import EmailTrack

# Flask-Migrate yapılandırması
migrate = Migrate(app, db)

def create_email_track_table():
    """E-posta takip tablosunu oluştur"""
    with app.app_context():
        # Tablo zaten var mı kontrol et
        table_exists = False
        try:
            EmailTrack.query.limit(1).all()
            table_exists = True
            print("E-posta takip tablosu zaten mevcut.")
        except Exception as e:
            if 'no such table' in str(e).lower() or 'does not exist' in str(e).lower():
                table_exists = False
            else:
                print(f"Beklenmeyen hata: {str(e)}")
                return False
        
        if not table_exists:
            try:
                # EmailTrack modelinden tabloyu oluştur
                db.create_all(tables=[EmailTrack.__table__])
                print("E-posta takip tablosu başarıyla oluşturuldu.")
                return True
            except Exception as e:
                print(f"Tablo oluşturma hatası: {str(e)}")
                return False
        
        return True

if __name__ == "__main__":
    create_email_track_table()
